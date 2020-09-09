import logging
from rest_framework import serializers
from api.serializers.manifest import ManifestTransferSerializer
from gap.serializers import ActionCreateSerializer, ActionStatusSerializer
import api.models
import gap.models

log = logging.getLogger(__name__)


class ManifestTransferActionBodySerializer(ManifestTransferSerializer):

    manifest_transfer_id = serializers.ReadOnlyField(source='id')

    class Meta:
        model = api.models.ManifestTransfer
        fields = ('manifest_transfer_id', 'manifest', 'destination', 'transfers')
        # fields = '__all__'
        read_only_fields = ['transfers']
        # depth = 1


class ManifestTransferActionSerializer(ActionCreateSerializer):

    body = ManifestTransferActionBodySerializer(write_only=True)

    class Meta:
        model = gap.models.Action
        # fields = '__all__'
        exclude = ('user',)
        read_only_fields = ['id', 'transfers']
        # depth = 1

    def create(self, validated_data):
        tm = ManifestTransferSerializer(context=self.context).create(validated_data['body'])
        tm.action = super().create(validated_data)
        tm.save()
        return tm.action


class ManifestTransferActionDetailSerializer(ManifestTransferActionBodySerializer):
    pass


class ManifestTransferActionStatusSerializer(ActionStatusSerializer):

    details = ManifestTransferActionDetailSerializer(write_only=True)

    class Meta:
        model = gap.models.Action
        # fields = '__all__'
        exclude = ('user',)
        read_only_fields = ['id', 'transfers']
        # depth = 1
