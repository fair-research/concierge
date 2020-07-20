from __future__ import unicode_literals
import os
import logging
import urllib
from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from api.serializers.bag import (
    BagMetadataSerializer, RemoteFileManifestEntrySerializer
)
from api.serializers.manifest import (
    ManifestURL, ManifestChecksumSerializer, ManifestItemSerializer
)
from api.exc import ConciergeException
from api.models import Bag
from api.utils import bag_and_tag

log = logging.getLogger(__name__)


class BagManifestItemSerializer(serializers.Serializer):
    """Same as the Manifest Item Serializer but missing the 'dest' field,
    which is not supported by the BDBag spec."""
    source_ref = ManifestURL()
    checksum = ManifestChecksumSerializer()

    required = ['source_ref', 'checksum']


class BagManifestSerializer(serializers.Serializer):
    manifest_items = ManifestItemSerializer(required=True,
                                            many=True,
                                            write_only=True)
    bag = BagMetadataSerializer(required=False)

    def manifest_to_rfm(self, manifest_items):
        rfm = []
        for man_item in manifest_items:
            checksum = man_item.get('checksum', {})
            if checksum:
                checksum = {checksum['algorithm']: checksum['value']}
            globus_url = urllib.parse.urlunparse(
                ('globus', man_item['source_ref']['endpoint'],
                 man_item['source_ref']['path'], '', '', '')
            )
            filename = os.path.basename(globus_url)
            rfm_data = dict(url=globus_url, filename=filename, length=0,
                            **checksum)
            rfm_ent = RemoteFileManifestEntrySerializer(data=rfm_data)
            if not rfm_ent.is_valid():
                log.error(f'Error converting Manifest into '
                          f'Remote File Manifest: {rfm_ent.errors}')
                raise ConciergeException('Manifest format could not be '
                                         'converted into a valid RFM!')
            rfm.append(rfm_ent.data)
        return rfm

    def validate_manifest_items(self, manifest_items):
        if not all(m.get('checksum') for m in manifest_items):
            raise ValidationError('Manifests must have checksums to be '
                                  'converted into BDBags.')

        algs = RemoteFileManifestEntrySerializer.SUPPORTED_CHECKSUMS
        if not all(m['checksum']['algorithm'] in algs for m in manifest_items):
            raise ValidationError('Checksum algorithms limited to: '
                                  f'{", ".join(algs)}')
        return manifest_items

    def create(self, validated_data):
        data = bag_and_tag(
            self.context['request'].auth,
            self.manifest_to_rfm(validated_data['manifest_items']),
            validated_data.get('bag', {}),
            validated_data.get('minid', {})
        )
        data['bag']['user'] = self.context['request'].user
        data['bag']['minid'] = data.pop('minid')
        Bag.objects.create(
            user=data['bag']['user'],
            minid=data['bag']['minid'],
            location=data['bag']['location'],
        )
        return data
