"""
Serializers for the Globus Automate Spec
https://action-provider-tools.readthedocs.io/en/latest/action_provider_interface.html  # noqa
"""
import logging
from rest_framework import serializers
from rest_framework_dataclasses.serializers import DataclassSerializer
from globus_action_provider_tools.data_types import ActionStatusValue, ActionStatus, ActionRequest


import gap.models

log = logging.getLogger(__name__)

THIRTY_DAYS = 60 * 60 * 24 * 30


class ActionCreateSerializer(DataclassSerializer, serializers.ModelSerializer):
    request_id = serializers.CharField(required=False)
    release_after = serializers.CharField(required=False, default=THIRTY_DAYS)
    action_id = serializers.UUIDField(read_only=True)

    class Meta:
        dataclass = ActionRequest
        model = gap.models.Action

    def create(self, validated_data):
        action = gap.models.Action.objects.create(
            request_id=validated_data.request_id,
            creator=self.context['request'].user,
            display_status=ActionStatusValue.INACTIVE.value,
            release_after=validated_data.release_after,
        )
        # Get the serializer for the 'body' object, or the object which has been
        # set for doing the work.
        body_serializer_cls = self.context['view'].body_serializer_class
        body_serializer = body_serializer_cls(data=validated_data.body, context=self.context)
        body_serializer.is_valid(raise_exception=True)
        body_obj = body_serializer.create(body_serializer.validated_data)
        body_obj.action = action
        body_obj.save()
        log.debug(f'Successfully created body object {body_obj}!')
        return action


class ActionStatusSerializer(DataclassSerializer):
    status = serializers.CharField()

    class Meta:
        dataclass = ActionStatus
        model = gap.models.Action
        depth = 1
