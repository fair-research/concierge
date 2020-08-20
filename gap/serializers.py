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
    details = serializers.JSONField(read_only=True)

    class Meta:
        model = gap.models.Action
        exclude = ['user']
        # fields = '__all__'
        read_only_fields = ['action_id', 'user', 'status', 'display_status',
                            'details', 'start_time', 'completion_time',
                            'release_after']

    def create(self, validated_data):
        '^(urn:globus:(auth:identity|groups:id):([a-fA-F0-9]{8}-[a-fA-F0-9]{4}-[a-fA-F0-9]{4}-[a-fA-F0-9]{4}-[a-fA-F0-9]{12}))|public$'  # noqa
        data = dict(
            status='INACTIVE',
            user=self.context['request'].user,
            # monitor_by='public',
            # manage_by='public',
            request_id=validated_data.get('request_id'),
            release_after=validated_data.get('release_after', 'P30D'),
            display_status=self.Meta.model.DisplayNames.ACTIVE.name,
        )
        return gap.models.Action.objects.create(**data)
