from __future__ import unicode_literals
import os
import json
import logging
from django.conf import settings
from rest_framework import serializers
from rest_framework.exceptions import ValidationError
import globus_sdk
from api.models import Bag, StageBag
from api.utils import (create_bag_archive, create_minid, upload_to_s3,
                       fetch_bags, catalog_transfer_manifest, transfer_catalog,
                       validate_remote_files_manifest)
from api.exc import GlobusTransferException

log = logging.getLogger(__name__)


class BagSerializer(serializers.HyperlinkedModelSerializer):

    minid_id = serializers.CharField(max_length=255, read_only=True)
    minid_user = serializers.CharField(allow_blank=False, max_length=255,
                                       required=True)
    minid_title = serializers.CharField(allow_blank=False, max_length=255,
                                        required=True)
    remote_files_manifest = serializers.JSONField(required=True)
    metadata = serializers.JSONField(required=False)
    ro_metadata = serializers.JSONField(required=False)
    location = serializers.CharField(max_length=255, read_only=True)
    transfer_token = serializers.CharField(write_only=True, required=False)
    verify_remote_files = serializers.BooleanField(required=False)

    class Meta:
        model = Bag
        fields = ('id', 'url', 'minid_id', 'minid_user', 'minid_email',
                  'minid_title', 'remote_files_manifest', 'metadata',
                  'ro_metadata', 'location', 'transfer_token',
                  'verify_remote_files')

    def validate_remote_files_manifest(self, manifest):
        for record in manifest:
            fname, url = record.get('filename'), record.get('url')
            if not fname or not url:
                raise ValidationError('Error in remote file manifest, '
                                      'bad "filename" or "URL"')
        return manifest

    def validate(self, data):
        ver, tok = data.get('verify_remote_files'), data.get('transfer_token')
        if ver:
            if not tok:
                raise ValidationError('Verify Remote files set to true, but '
                                      'no Globus Transfer Token provided')
            data['remote_files_manifest'] = validate_remote_files_manifest(
                data['remote_files_manifest'], tok)
        return data

    def create(self, validated_data):
        validated_manifest = validated_data['remote_files_manifest']

        bag_metadata = validated_data.get('metadata') or \
            {'bag_metadata': {'Creator-Name': validated_data['minid_user']}}
        bag_filename = create_bag_archive(validated_manifest, bag_metadata,
                                          validated_data.get('ro_metadata'))

        s3_bag_filename = os.path.basename(bag_filename)
        upload_to_s3(bag_filename, s3_bag_filename)

        validated_data['location'] = "https://s3.amazonaws.com/%s/%s" % \
                                     (settings.AWS_BUCKET_NAME,
                                      s3_bag_filename)

        minid = create_minid(bag_filename,
                             s3_bag_filename,
                             validated_data['minid_user'],
                             validated_data['minid_email'],
                             validated_data['minid_title'],
                             settings.MINID_TEST,
                             self.context['request'].auth)

        os.remove(bag_filename)
        return Bag.objects.create(user=self.context['request'].user,
                                  minid_id=minid,
                                  minid_email=validated_data['minid_email'],
                                  location=validated_data['location'])


class StageBagSerializer(serializers.HyperlinkedModelSerializer):

    id = serializers.IntegerField(read_only=True)
    bag_minids = serializers.JSONField(required=True)
    transfer_token = serializers.CharField(write_only=True, required=True)
    transfer_catalog = serializers.JSONField(read_only=True)
    error_catalog = serializers.JSONField(read_only=True)
    transfer_task_ids = serializers.JSONField(read_only=True)

    class Meta:
        model = StageBag
        exclude = ('user',)

    def to_representation(self, obj):
        ret_val = super(StageBagSerializer, self).to_representation(obj)
        ret_val['bag_minids'] = json.loads(obj.bag_minids)
        if ret_val.get('transfer_catalog'):
            ret_val['transfer_catalog'] = json.loads(obj.transfer_catalog)
        if ret_val.get('error_catalog'):
            ret_val['error_catalog'] = json.loads(obj.error_catalog)
        if ret_val.get('transfer_task_ids'):
            ret_val['transfer_task_ids'] = json.loads(obj.transfer_task_ids)
        return ret_val

    def to_internal_value(self, obj):
        obj['bag_minids'] = json.dumps(obj['bag_minids'])
        ret_val = super(StageBagSerializer, self).to_internal_value(obj)
        return ret_val

    def create(self, validated_data):
        try:
            minids = json.loads(validated_data['bag_minids'])
            bagit_bags = fetch_bags(minids, self.context['request'].user)
            catalog, error_catalog = catalog_transfer_manifest(bagit_bags)
            task_ids = transfer_catalog(
                catalog,
                validated_data['destination_endpoint'],
                validated_data['destination_path_prefix'],
                validated_data['transfer_token']
                )
            stage_bag_data = {'user': self.context['request'].user,
                              'transfer_catalog': json.dumps(catalog),
                              'error_catalog': json.dumps(error_catalog),
                              'transfer_task_ids': json.dumps(task_ids),
                              }
            stage_bag_data.update(validated_data)
            return StageBag.objects.create(**stage_bag_data)
        except globus_sdk.exc.TransferAPIError as te:
            raise GlobusTransferException(detail={'error': te.message,
                                          'code': te.code})
