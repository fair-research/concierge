import os
from rest_framework import serializers
from api.models import Bag, StageBag
from api.utils import create_bag_archive, create_minid, upload_to_s3
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

    class Meta:
        model = StageBag
        fields = '__all__'

    def create(self, validated_data):
        # NONE OF THIS WORKS YET
        # location = validated_data['location']
        # globus_destination_endpoint, globus_destination_path = location.replace('globus://', '').split(':')
        # payload = {}
        # for bag_minid in validated_data['bad_minids']:
        #     fetch_bag(bag_minid)
        #     manifests = get_bag_manifest()
        #     for manifest in manifests:
        #         previous_data = payload.get(manifest['globus_endpoint'], [])
        #         new_data = previous_data.append(manifest['urls'])
        #         payload[manifest['globus_endpoint']] = new_data

        # tc = globus_sdk.TransferClient(...)
        # for globus_source_endpoint, data in payload:
        #     tdata = globus_sdk.TransferData(tc,
        #                                 globus_source_endpoint,
        #                                 globus_destination_endpoint,
        #                                 label="SDK example",
        #                                 sync_level="checksum"
        #                                 )
        #     for source_path in data:
        #         tdata.add_item("/source/path/dir/", validated_data['prefix'] + "/dest/path/dir/",
        #         recursive = True)
        #     transfer_result = tc.submit_transfer(tdata)



        return StageBag.objects.create(**validated_data)
