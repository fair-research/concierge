import os
from rest_framework import serializers
from api.models import Bag, StageBag
from api.utils import (create_bag_archive, create_minid, upload_to_s3,
                       fetch_bags, catalog_transfer_manifest, transfer_catalog)
from django.conf import settings


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

    bag_minids = serializers.JSONField(required=True)
    transfer_catalog = serializers.JSONField(read_only=True)
    error_catalog = serializers.JSONField(read_only=True)
    transfer_task_ids = serializers.JSONField(read_only=True)

    class Meta:
        model = StageBag
        fields = '__all__'

    def create(self, validated_data):
        bags = Bag.objects.filter(minid_id__in=validated_data['bag_minids'])
        bagit_bags = fetch_bags(bags)
        catalog, error_catalog = catalog_transfer_manifest(bagit_bags)
        task_ids = transfer_catalog(catalog,
                                    validated_data['destination_endpoint'],
                                    validated_data['destination_path_prefix'],
                                    validated_data['transfer_token']
                                    )
        stage_bag_data = {
                          'transfer_catalog': catalog,
                          'error_catalog': error_catalog,
                          'transfer_task_ids': task_ids,
                          }
        stage_bag_data.update(validated_data)
        return StageBag.objects.create(**stage_bag_data)
