"""
Serializers for the Globus Automate Spec
https://action-provider-tools.readthedocs.io/en/latest/action_provider_interface.html  # noqa
"""
import logging
from rest_framework import serializers

import gap.models

log = logging.getLogger(__name__)


class ActionSerializer(serializers.ModelSerializer):

    request_id = serializers.CharField(write_only=True)
    body = serializers.JSONField(write_only=True)

    class Meta:
        model = gap.models.Action
        fields = '__all__'
        read_only_fields = ['action_id', 'user', 'status', 'display_status',
                            'details', 'start_time', 'completion_time',
                            'release_after']

    def create(self, validated_data):
        '^(urn:globus:(auth:identity|groups:id):([a-fA-F0-9]{8}-[a-fA-F0-9]{4}-[a-fA-F0-9]{4}-[a-fA-F0-9]{4}-[a-fA-F0-9]{12}))|public$'
        data = dict(
            status='STARTED',
            user=self.context['request'].user,
            # monitor_by='public',
            # manage_by='public',
            # release_after=request.release_after or "P30D",
            display_status=self.Meta.model.DisplayNames.SUCCEEDED.name,
        )
        return gap.models.Action.objects.create(**data)
