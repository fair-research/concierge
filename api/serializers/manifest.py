"""
Serializers for the Globus Manifest Spec

More info here https://globusonline.github.io/manifests/overview.html
"""
import logging
import uuid
import urllib
from rest_framework import serializers
from rest_framework.exceptions import ValidationError

import api.exc
import api.models
import api.serializers.transfer
import api.transfer

log = logging.getLogger(__name__)


class ManifestURL(serializers.Field):
    """
    Manifests look like:
    88b9b278-d301-11e9-8df7-7200012a1360.data.globus.org/share/godata/file1.txt

    where '.data.globus.org' signifies this is a globus endpoint.
    """
    ENDPOINT_SUFFIX = '.data.globus.org'

    def to_representation(self, value):
        return value

    def to_internal_value(self, data):

        # URLs may omit the fake http protocol
        if '://' not in data and not data.startswith('http://'):
            data = f'http://{data}'
        purl = urllib.parse.urlparse(data)

        if not purl.netloc.endswith('.data.globus.org'):
            raise ValidationError(f'{purl.netloc}: Manifest endpoints must '
                                  f"have a '{self.ENDPOINT_SUFFIX}' suffix")
        endpoint = purl.netloc.replace(self.ENDPOINT_SUFFIX, '')
        try:
            uuid.UUID(endpoint)
        except ValueError:
            raise ValidationError('Globus Endpoint is not a UUID: '
                                  f'{data}')

        return {
            'endpoint': endpoint,
            'path': purl.path,
        }


class ManifestChecksumSerializer(serializers.Serializer):
    algorithm = serializers.CharField()
    value = serializers.CharField()


class ManifestItemSerializer(serializers.Serializer):
    source_ref = ManifestURL()
    dest_path = serializers.CharField()
    checksum = ManifestChecksumSerializer(required=False)


class ManifestSerializer(serializers.Serializer):

    manifest_items = serializers.ListField(child=ManifestItemSerializer())
    destination = ManifestURL()

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
