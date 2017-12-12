import os
import json
import logging
from django.conf import settings
from rest_framework import serializers
from rest_framework.exceptions import ValidationError
import globus_sdk
from api.models import Bag, StageBag
from api.utils import (create_bag_archive, create_minid, upload_to_s3,
                       fetch_bags, catalog_transfer_manifest, transfer_catalog)
from api.exc import ConciergeException, GlobusTransferException

log = logging.getLogger(__name__)


class BagSerializer(serializers.HyperlinkedModelSerializer):

    minid_id = serializers.CharField(max_length=255, read_only=True)
    minid_user = serializers.CharField(allow_blank=False, max_length=255,
                                       required=True)
    minid_title = serializers.CharField(allow_blank=False, max_length=255,
                                        required=True)
    remote_files_manifest = serializers.JSONField(required=True)
    location = serializers.CharField(max_length=255, read_only=True)

    class Meta:
        model = Bag
        fields = ('id', 'url', 'minid_id', 'minid_user', 'minid_email',
                  'minid_title', 'remote_files_manifest', 'location')

    def create(self, validated_data):
        validated_manifest = validated_data['remote_files_manifest']

        bag_metadata = {'Creator-Name': validated_data['minid_user']}
        bag_filename = create_bag_archive(validated_manifest, **bag_metadata)

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
                             True)

        os.remove(bag_filename)
        return Bag.objects.create(minid_id=minid,
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
        fields = '__all__'

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
            bag_minids = json.loads(validated_data['bag_minids'])
            bags = Bag.objects.filter(
                minid_id__in=bag_minids)
            if len(bags) != len(bag_minids):
                raise ValidationError({
                    'bag_minids': 'Non-registered concierge bags not '
                                  'supported yet.',
                    'bags': [b for b in bag_minids
                                   if b not in [bg.minid_id for bg in bags]]
                })
            bagit_bags = fetch_bags(bags)
            catalog, error_catalog = catalog_transfer_manifest(bagit_bags)
            if not catalog:
                raise ValidationError({
                    'bag_minids': 'No valid data to transfer',
                    'error_catalog': error_catalog
                })
            task_ids = transfer_catalog(
                catalog,
                validated_data['destination_endpoint'],
                validated_data['destination_path_prefix'],
                validated_data['transfer_token']
                )
            stage_bag_data = {
                              'transfer_catalog': json.dumps(catalog),
                              'error_catalog': json.dumps(error_catalog),
                              'transfer_task_ids': json.dumps(task_ids),
                              }
            stage_bag_data.update(validated_data)
            return StageBag.objects.create(**stage_bag_data)
        except globus_sdk.exc.TransferAPIError as te:
            if te.code == 'NoCredException':
                raise GlobusTransferException(detail={'error': te.message})
