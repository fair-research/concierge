import logging
# from api.serializers.manifest import TransferManifestSerializer
from api.serializers.transfer import TransferSerializer
from gap.serializers import ActionSerializer

log = logging.getLogger(__name__)


class TransferManifestActionSerializer(ActionSerializer):
    body = TransferSerializer(write_only=True)

    def create(self, validated_data):
        tm = TransferSerializer(context=self.context).create(validated_data['body'])
        tm.action = super().create(validated_data)
        tm.save()
        return tm.action
