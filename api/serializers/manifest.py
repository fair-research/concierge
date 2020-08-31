"""
Serializers for the Globus Manifest Spec

More info here https://globusonline.github.io/manifests/overview.html
"""
import logging
from rest_framework import serializers
from rest_framework.exceptions import ValidationError

import api.exc
import api.models
import api.serializers.transfer
import api.transfer
import api.manifest

log = logging.getLogger(__name__)


class ManifestListSerializer(serializers.ModelSerializer):

    class Meta:
        fields = '__all__'
        model = api.models.Manifest


class RemoteFileManifestEntrySerializer(serializers.Serializer):

    SUPPORTED_CHECKSUMS = ['md5', 'sha256']

    url = api.serializers.transfer.GlobusURL()
    length = serializers.IntegerField()
    filename = serializers.CharField(max_length=256)
    md5 = serializers.CharField(max_length=32, required=False)
    sha256 = serializers.CharField(max_length=64, required=False)

    def validate(self, data):
        if not any(data.get(f) for f in self.SUPPORTED_CHECKSUMS):
            raise ValidationError(f'Required one of '
                                  f'{self.SUPPORTED_CHECKSUMS}')
        return data


class RemoteFileManifestSerializer(serializers.ModelSerializer):
    remote_file_manifest = RemoteFileManifestEntrySerializer(many=True)

    class Meta:
        fields = '__all__'
        read_only_fields = ['user', 'location']
        model = api.models.Manifest

    def create(self, validated_data):
        model = api.models.Manifest.objects.create(user=self.context['request'].user)
        api.manifest.upload_remote_file_manifest(model.id, validated_data['remote_file_manifest'])
        # Since validated_data already contains the RFM, pass it here to avoid a second fetch.
        validated_data.update(dict(user=model.user, id=model.id))
        return validated_data


class GlobusManifestChecksumSerializer(serializers.Serializer):
    algorithm = serializers.CharField()
    value = serializers.CharField()


class GlobusManifestItemSerializer(serializers.Serializer):
    source_ref = api.serializers.transfer.GlobusURL()
    dest_path = serializers.CharField()
    checksum = GlobusManifestChecksumSerializer(required=False)


class GlobusManifestSerializer(serializers.ModelSerializer):

    manifest_items = GlobusManifestItemSerializer(many=True)
    # destination = api.serializers.transfer.GlobusURL()

    class Meta:
        fields = '__all__'
        model = api.models.Manifest
        read_only_fields = ['user', 'location']

    def create(self, validated_data):
        rfm = api.manifest.gm_to_rfm(validated_data['manifest_items'])
        model = api.models.Manifest.objects.create(user=self.context['request'].user)
        api.manifest.upload_remote_file_manifest(model.id, rfm)
        # Since validated_data already contains the RFM,
        validated_data.update(dict(user=model.user, id=model.id))
        return validated_data

    # def validate_manifest_items(self, data):
    #     eps = {mi['source_ref']['endpoint'] for mi in data}
    #     if len(eps) != 1:
    #         raise ValidationError(
    #             'Manifest endpoints MUST all originate from the '
    #             f'same Globus endpoint (got: {", ".join(eps)})'
    #         )
    #     return data


# class TransferManifestSerializer(serializers.ModelSerializer):
#     manifest = ManifestSerializer(write_only=True)
#     user = serializers.ReadOnlyField(source='user.username')
#
#     class Meta:
#         model = api.models.TransferManifest
#         fields = ('id', 'user', 'manifest', 'transfer')
#         read_only_fields = ['transfer']
#         depth = 1
#
#     def create(self, validated_data):
#         auth = self.context['request'].auth
#         manifest = validated_data['manifest']
#         transfer = api.transfer.transfer_manifest(auth, manifest)
#         tinfo = {i: transfer.get(i) for i in ['submission_id', 'task_id']}
#         tinfo['status'] = transfer['code']
#         tinfo['user'] = auth.user
#
#         transfer_model = api.models.Transfer(**tinfo)
#         transfer_model.save()
#         return api.models.TransferManifest.objects.create(
#             user=auth.user, transfer=transfer_model)