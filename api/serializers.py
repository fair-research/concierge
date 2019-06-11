from __future__ import unicode_literals
import os
import re
import json
import logging
from django.conf import settings
from rest_framework import serializers
from rest_framework.exceptions import ValidationError
import globus_sdk
from api.models import Bag, StageBag
from api.utils import (create_bag_archive, upload_to_s3,
                       fetch_bags, catalog_transfer_manifest, transfer_catalog,
                       verify_remote_file_manifest)
from api.minid import create_minid
from api.exc import GlobusTransferException

log = logging.getLogger(__name__)


class BagSerializer(serializers.HyperlinkedModelSerializer):

    minid = serializers.CharField(max_length=255, read_only=True)
    minid_metadata = serializers.JSONField(required=False, write_only=True)
    minid_location = serializers.JSONField(read_only=True)
    minid_test = serializers.BooleanField(required=False,
                                          default=settings.DEFAULT_TEST_MINIDS)
    minid_visible_to = serializers.JSONField(required=False, write_only=True)
    bag_name = serializers.CharField(allow_blank=True, max_length=128,
                                     required=False)
    bag_metadata = serializers.JSONField(required=False)
    bag_ro_metadata = serializers.JSONField(required=False)
    remote_file_manifest = serializers.JSONField(required=True,
                                                 write_only=True)
    verify_remote_files = serializers.BooleanField(required=False)

    class Meta:
        model = Bag
        fields = ('id', 'url', 'minid', 'minid_metadata', 'minid_location',
                  'minid_test', 'minid_visible_to', 'bag_name', 'bag_metadata',
                  'bag_ro_metadata', 'remote_file_manifest',
                  'verify_remote_files')

    def validate_bag_name(self, bag_name):
        if re.search(r'[^\w_\-\.]', bag_name):
            raise ValidationError('Only [-_.] special characters allowed in '
                                  'filename.')
        return bag_name

    def validate_remote_file_manifest(self, manifest):
        if not isinstance(manifest, list):
            raise ValidationError('Manifest must be a list')
        for record in manifest:
            if not isinstance(record, dict):
                raise ValidationError('Every record in the remote file'
                                      'manifest must be a simple object')
            fname, url = record.get('filename'), record.get('url')
            if not fname or not url:
                raise ValidationError('Error in remote file manifest, '
                                      'bad "filename" or "URL"')
        log.debug('Remote File Manifest field check: PASSED.')
        return manifest

    def validate(self, data):
        if data.get('verify_remote_files'):
            data['remote_file_manifest'] = verify_remote_file_manifest(
                self.context['request'].user,
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
        metad, visible_to, test = (validated_data.get('minid_metadata'),
                                   validated_data.get('visible_to') or
                                   ('public',),
                                   validated_data.get('minid_test'))
        minid = create_minid(user, bag_filename, [location], metad,
                             visible_to, test)
        os.remove(bag_filename)
        return Bag.objects.create(user=user, minid=minid['identifier'],
                                  location=location)


class StageBagSerializer(serializers.HyperlinkedModelSerializer):

    id = serializers.IntegerField(read_only=True)
    minids = serializers.JSONField(required=True)
    bag_dirs = serializers.BooleanField(required=False, default=False)
    transfer_catalog = serializers.JSONField(read_only=True)
    error_catalog = serializers.JSONField(read_only=True)
    transfer_task_ids = serializers.JSONField(read_only=True)
    task_catalog = serializers.JSONField(read_only=True)
    files_transferred = serializers.JSONField(read_only=True)
    status = serializers.CharField(read_only=True)

    class Meta:
        model = StageBag
        exclude = ('user',)

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
            bagit_bags = fetch_bags(self.context['request'].user, minids)
            bag_dirs = validated_data.pop('bag_dirs')
            catalog, error_catalog = catalog_transfer_manifest(
                bagit_bags, use_bag_dirs=bag_dirs)
            task_ids = transfer_catalog(
                self.context['request'].user,
                catalog,
                validated_data['destination_endpoint'],
                validated_data['destination_path_prefix']
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
