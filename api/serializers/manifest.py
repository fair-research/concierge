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

log = logging.getLogger(__name__)


class ManifestChecksumSerializer(serializers.Serializer):
    algorithm = serializers.CharField()
    value = serializers.CharField()


class ManifestItemSerializer(serializers.Serializer):
    source_ref = api.serializers.transfer.GlobusURL()
    dest_path = serializers.CharField()
    checksum = ManifestChecksumSerializer(required=False)


class ManifestSerializer(serializers.Serializer):

    manifest_items = serializers.ListField(child=ManifestItemSerializer(),
                                           min_length=1)
    destination = api.serializers.transfer.GlobusURL()

    def validate_manifest_items(self, data):
        eps = {mi['source_ref']['endpoint'] for mi in data}
        if len(eps) != 1:
            raise ValidationError(
                'Manifest endpoints MUST all originate from the '
                f'same Globus endpoint (got: {", ".join(eps)})'
            )
        return data


class TransferManifestSerializer(serializers.ModelSerializer):
    manifest = ManifestSerializer(write_only=True)
    user = serializers.ReadOnlyField(source='user.username')

    class Meta:
        model = api.models.TransferManifest
        fields = ('id', 'user', 'manifest', 'transfer')
        read_only_fields = ['transfer']
        depth = 1

    def create(self, validated_data):
        auth = self.context['request'].auth
        manifest = validated_data['manifest']
        transfer = api.transfer.transfer_manifest(auth, manifest)
        tinfo = {i: transfer.get(i) for i in ['submission_id', 'task_id']}
        tinfo['status'] = transfer['code']
        tinfo['user'] = auth.user

        transfer_model = api.models.Transfer(**tinfo)
        transfer_model.save()
        return api.models.TransferManifest.objects.create(
            user=auth.user, transfer=transfer_model)
