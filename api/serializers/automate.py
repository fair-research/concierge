import logging
from rest_framework import serializers
from api.serializers.manifest import ManifestTransferSerializer
from gap.serializers import ActionCreateSerializer, ActionStatusSerializer
import api.models
import gap.models

log = logging.getLogger(__name__)


class ManifestTransferActionBodySerializer(ManifestTransferSerializer):
    """
    {
  "request_id": "string",
  "release_after": 0,
  "body": {
    "manifest_id": "ac0d1e13-363b-4580-81e2-2ff74f7a6014",
    "destination": "globus://ac0d1e13-363b-4580-81e2-2ff74f7a6014/~/"
  }
}
    """

    manifest_id = serializers.UUIDField(source='manifest.id')

    def create(self, validated_data):
        validated_data['manifest_id'] = validated_data['manifest'].pop('id')
        return super().create(validated_data)


class ManifestTransferActionDetailSerializer(ManifestTransferActionBodySerializer):
    pass


class ManifestTransferActionStatusSerializer(ActionStatusSerializer):

    details = ManifestTransferActionDetailSerializer(write_only=True)

    class Meta:
        model = gap.models.Action
        # fields = '__all__'
        exclude = ('creator',)
        read_only_fields = ['id', 'transfers']
        # depth = 1


class ManifestTransferActionSerializer(ActionCreateSerializer):

    body = ManifestTransferActionBodySerializer(write_only=True)
    # details = ManifestTransferActionStatusSerializer(read_only=True)

    class Meta:
        model = gap.models.Action
    #     # fields = '__all__'
        exclude = ['creator', 'manager_by', 'monitor_by']
    #     # exclude = ['creator']
        read_only_fields = ['id', 'transfers', 'status', 'action_id', 'completion_time']
        write_only_fields = ['request_id']
    #     # depth = 1

    def create(self, validated_data):
        tm = ManifestTransferActionBodySerializer(context=self.context).create(validated_data['body'])
        tm.action = super().create(validated_data)
        tm.save()
        log.debug(f'Action {tm.action} created with transfer manifest {tm}')
        return tm.action
