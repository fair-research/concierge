from __future__ import unicode_literals
import os
import re
import json
import logging
import urllib
import uuid
from django.conf import settings
from rest_framework import serializers
from rest_framework.exceptions import ValidationError
import globus_sdk
from minid import MinidClient
from api.models import Bag, StageBag
from api.utils import (create_bag_archive, upload_to_s3,
                       fetch_bags, catalog_transfer_manifest, transfer_catalog,
                       verify_remote_file_manifest)
from api.minid import load_minid_client
from api.exc import GlobusTransferException

log = logging.getLogger(__name__)


class RemoteURL(serializers.Field):
    """
    Color objects are serialized into 'rgb(#, #, #)' notation.
    """
    def to_representation(self, value):
        return value

    def to_internal_value(self, data):

        purl = urllib.parse.urlparse(data)
        if purl.scheme not in settings.SUPPORTED_BAG_PROTOCOLS:
            raise ValidationError('Unsupported protocol, expected one of: '
                                  f'{settings.SUPPORTED_BAG_PROTOCOLS}')

        if purl.scheme == 'globus':
            try:
                uuid.UUID(purl.netloc)
            except ValueError:
                raise ValidationError('Globus Endpoint is not a UUID: '
                                      f'{data}')

        return data


class RemoteFileManifestEntrySerializer(serializers.Serializer):

    SUPPORTED_CHECKSUMS = ['md5', 'sha256']

    url = RemoteURL()
    length = serializers.IntegerField()
    filename = serializers.CharField(max_length=256)
    md5 = serializers.CharField(max_length=32, required=False)
    sha256 = serializers.CharField(max_length=64, required=False)

    def validate(self, data):
        if not any(data.get(f) for f in self.SUPPORTED_CHECKSUMS):
            raise ValidationError(f'Required one of '
                                  f'{self.SUPPORTED_CHECKSUMS}')
        return data


class BagCreateListSerializer(serializers.HyperlinkedModelSerializer):
    """Older serializer used to serialize bags. This object isn't well
    normalized, and the next version will shift to using the separate
    serializers below."""

    minid = serializers.CharField(max_length=255, read_only=True)
    user = serializers.ReadOnlyField(source='user.username')
    minid_metadata = serializers.JSONField(required=False, write_only=True)
    minid_location = serializers.JSONField(read_only=True)
    minid_test = serializers.BooleanField(required=False,
                                          default=settings.DEFAULT_TEST_MINIDS)
    # Deprecated, all minids are public.
    minid_visible_to = serializers.JSONField(required=False, write_only=True)
    bag_name = serializers.CharField(allow_blank=True, max_length=128,
                                     required=False)
    bag_metadata = serializers.JSONField(required=False)
    bag_ro_metadata = serializers.JSONField(required=False)
    remote_file_manifest = RemoteFileManifestEntrySerializer(required=True,
                                                             many=True,
                                                             write_only=True)
    verify_remote_files = serializers.BooleanField(required=False)

    class Meta:
        model = Bag
        fields = ('id', 'user', 'url', 'minid', 'minid_metadata',
                  'minid_location', 'minid_test', 'minid_visible_to',
                  'bag_name', 'bag_metadata', 'bag_ro_metadata',
                  'remote_file_manifest', 'verify_remote_files')

    def validate_bag_name(self, bag_name):
        if re.search(r'[^\w_\-\.]', bag_name):
            raise ValidationError('Only [-_.] special characters allowed in '
                                  'filename.')
        return bag_name

    def validate(self, data):
        if data.get('verify_remote_files'):
            data['remote_file_manifest'] = verify_remote_file_manifest(
                self.context['request'].auth,
                data['remote_file_manifest']
            )
        return data

    def create(self, validated_data):
        validated_manifest = validated_data['remote_file_manifest']

        bag_metadata = validated_data.get('metadata')
        bag_filename = create_bag_archive(validated_manifest, bag_metadata,
                                          validated_data.get('ro_metadata'),
                                          validated_data.get('bag_name'))

        location = upload_to_s3(bag_filename)
        user = self.context['request'].user

        validated_data['location'] = location
        metad = validated_data.get('minid_metadata')
        test = validated_data.get('minid_test')
        checksums = [{
            'function': 'sha256',
            'value': MinidClient.compute_checksum(bag_filename)
        }]
        mc = load_minid_client(self.context['request'].auth)
        minid = mc.register(checksums, title=bag_filename,
                            locations=[location], metadata=metad, test=test)
        m_id = mc.to_identifier(minid['identifier'], identifier_type='minid')
        os.remove(bag_filename)
        return Bag.objects.create(user=user, minid=m_id, location=location)


class StageBagSerializer(serializers.HyperlinkedModelSerializer):

    id = serializers.IntegerField(read_only=True)
    minids = serializers.JSONField(required=True)
    user = serializers.ReadOnlyField(source='user.username')
    bag_dirs = serializers.BooleanField(required=False, default=False)
    transfer_label = serializers.CharField(write_only=True)
    transfer_catalog = serializers.JSONField(read_only=True)
    error_catalog = serializers.JSONField(read_only=True)
    transfer_task_ids = serializers.JSONField(read_only=True)
    task_catalog = serializers.JSONField(read_only=True)
    files_transferred = serializers.JSONField(read_only=True)
    status = serializers.CharField(read_only=True)

    class Meta:
        model = StageBag
        fields = '__all__'

    def to_representation(self, obj):
        ret_val = super(StageBagSerializer, self).to_representation(obj)
        ret_val['minids'] = json.loads(obj.minids)
        if ret_val.get('transfer_catalog'):
            ret_val['transfer_catalog'] = json.loads(obj.transfer_catalog)
        if ret_val.get('error_catalog'):
            ret_val['error_catalog'] = json.loads(obj.error_catalog)
        if ret_val.get('transfer_task_ids'):
            ret_val['transfer_task_ids'] = json.loads(obj.transfer_task_ids)
        if ret_val.get('task_catalog'):
            log.debug(obj.task_catalog)
            ret_val['task_catalog'] = json.loads(obj.task_catalog)
        return ret_val

    def to_internal_value(self, obj):
        obj['minids'] = json.dumps(obj['minids'])
        ret_val = super(StageBagSerializer, self).to_internal_value(obj)
        return ret_val

    def validate_minids(self, minids):
        try:
            mval = json.loads(minids)
            if not isinstance(mval, list):
                raise ValidationError('Minids must be an array')
        except Exception:
            raise ValidationError('Minids must be an array')
        return minids

    def create(self, validated_data):
        try:
            minids = json.loads(validated_data['minids'])
            bagit_bags = fetch_bags(self.context['request'].auth, minids)
            transfer_label = validated_data.pop('transfer_label')
            bag_dirs = validated_data.pop('bag_dirs')
            catalog, error_catalog = catalog_transfer_manifest(
                bagit_bags, bag_dirs=bag_dirs)
            task_ids = transfer_catalog(
                self.context['request'].auth,
                catalog,
                validated_data['destination_endpoint'],
                validated_data['destination_path_prefix'],
                label=transfer_label
                )
            stage_bag_data = {'user': self.context['request'].user,
                              'transfer_catalog': json.dumps(catalog),
                              'error_catalog': json.dumps(error_catalog),
                              'transfer_task_ids': json.dumps(task_ids),
                              }
            stage_bag_data.update(validated_data)
            return StageBag.objects.create(**stage_bag_data)
        except globus_sdk.exc.TransferAPIError as te:
            log.debug(te)
            raise GlobusTransferException(detail={'error': te.message,
                                          'code': te.code})


class MinidSerializer(serializers.Serializer):
    metadata = serializers.JSONField(required=False)
    test = serializers.BooleanField(required=False,
                                    default=settings.DEFAULT_TEST_MINIDS)
    identifier = serializers.CharField(max_length=255, read_only=True)
    location = serializers.ListField(child=serializers.CharField(),
                                     read_only=True)


class BagMetadataSerializer(serializers.ModelSerializer):
    user = serializers.ReadOnlyField(source='user.username')
    name = serializers.CharField(allow_blank=True, max_length=128,
                                 required=False)
    minid = MinidSerializer()
    metadata = serializers.JSONField(required=False, write_only=True)
    ro_metadata = serializers.JSONField(required=False, write_only=True)

    class Meta:
        model = Bag
        fields = ('id', 'user', 'name', 'minid', 'metadata', 'ro_metadata')


class BagSerializer(BagMetadataSerializer):
    remote_file_manifest = RemoteFileManifestEntrySerializer(
        required=True, many=True, write_only=True
    )
