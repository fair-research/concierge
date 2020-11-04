import logging
from rest_framework import serializers
from api.serializers.manifest import ManifestTransferSerializer

log = logging.getLogger(__name__)


class ManifestTransferActionSerializer(ManifestTransferSerializer):
    """
    {
  "request_id": "string",
  "release_after": 0,
  "body": {
    "manifest_id": "54eaa70c-84dc-48f2-ae60-1b88aa03d3ec",
    "destination": "globus://ac0d1e13-363b-4580-81e2-2ff74f7a6014/~/"
  }
}
    """

    manifest_id = serializers.UUIDField(source='manifest.id')
