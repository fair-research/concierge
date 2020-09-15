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

    user = serializers.ReadOnlyField(source='user.username')

    class Meta:
        fields = ('id', 'user')
        model = api.models.Manifest
        read_only_fields = ['id', 'user']


class RemoteFileManifestEntrySerializer(serializers.Serializer):

    SUPPORTED_CHECKSUMS = ['md5', 'sha256']

    url = api.serializers.transfer.GlobusURL(help_text='URL to a file located on a Globus endpoint')
    length = serializers.IntegerField(help_text='Length of the file')
    filename = serializers.CharField(max_length=256, help_text='Filename of the file')
    md5 = serializers.CharField(max_length=32, required=False, help_text='MD5 checksum of the file')
    sha256 = serializers.CharField(max_length=64, required=False, help_text='SHA256 checksum of the file')

    def validate(self, data):
        if not any(data.get(f) for f in self.SUPPORTED_CHECKSUMS):
            raise ValidationError(f'Required one of '
                                  f'{self.SUPPORTED_CHECKSUMS}')
        return data


class RemoteFileManifestSerializer(serializers.ModelSerializer):
    user = serializers.ReadOnlyField(source='user.username')
    remote_file_manifest = RemoteFileManifestEntrySerializer(many=True, help_text='List of Remote File Manifest '
                                                                                  'Entries')

    class Meta:
        fields = '__all__'
        read_only_fields = ['user']
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
    source_ref = api.serializers.transfer.GlobusURL(help_text='URL to a file or directory located on a Globus '
                                                              'endpoint')
    dest_path = serializers.CharField(help_text='Filename or dir path to name the "source_ref" resource on transfer')
    checksum = GlobusManifestChecksumSerializer(required=False)


class GlobusManifestSerializer(serializers.ModelSerializer):

    manifest_id = serializers.ReadOnlyField(source='id')
    manifest_items = GlobusManifestItemSerializer(many=True)
    user = serializers.ReadOnlyField(source='user.username')

    class Meta:
        fields = ('manifest_id', 'user', 'manifest_items')
        model = api.models.Manifest
        read_only_fields = ['manifest_id', 'user']

    def create(self, validated_data):
        rfm = api.manifest.gm_to_rfm(validated_data['manifest_items'])
        model = api.models.Manifest.objects.create(user=self.context['request'].user)
        location = api.manifest.upload_remote_file_manifest(model.id, rfm)
        model.location = location
        model.save()
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


class ManifestTransferSerializer(serializers.ModelSerializer):
    manifest_id = serializers.ReadOnlyField(source='manifest.id')
    manifest_transfer_id = serializers.ReadOnlyField(source='id')

    user = serializers.ReadOnlyField(source='user.username')
    status = serializers.ReadOnlyField()
    destination = api.serializers.transfer.GlobusURL(
        help_text='Globus endpoint and path destination to transfer manifest files',
        write_only=True,
    )

    class Meta:
        model = api.models.ManifestTransfer
        exclude = ('action', 'id', 'manifest')
        read_only_fields = ['manifest_transfer_id', 'user', 'status', 'transfers']
        depth = 1

    def create(self, validated_data):
        manifest_id = self.context['view'].kwargs['manifest_id']
        manifest = api.models.Manifest.objects.get(id=manifest_id)
        try:
            rfm = RemoteFileManifestSerializer(manifest)
            gm_data = api.manifest.rfm_to_gm(rfm.to_internal_value(rfm.data))
        except Exception:
            gm = GlobusManifestSerializer(manifest)
            gm_data = gm.to_internal_value(gm.data)
        auth = self.context['request'].auth
        dest = validated_data['destination']
        transfers = api.transfer.transfer_manifest(auth, gm_data, dest)
        manifest_transfer = api.models.ManifestTransfer.objects.create(
            user=auth.user, manifest=manifest, destination=dest
        )
        for transfer in transfers:
            transfer_m = api.models.Transfer.objects.create(**dict(
                submission_id=transfer.get('submission_id'),
                task_id=transfer.get('task_id'),
                status=transfer.get('code'),
                user=auth.user,
            ))
            manifest_transfer.transfers.add(transfer_m)
        return manifest_transfer
