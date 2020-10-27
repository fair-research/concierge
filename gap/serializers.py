"""
Serializers for the Globus Automate Spec
https://action-provider-tools.readthedocs.io/en/latest/action_provider_interface.html  # noqa
"""
import logging
from rest_framework import serializers
from globus_action_provider_tools.data_types import ActionStatusValue


import gap.models

log = logging.getLogger(__name__)
#
#
# class GlobusURNField(serializers.Field):
#     # '^(urn:globus:(auth:identity|groups:id):([a-fA-F0-9]{8}-[a-fA-F0-9]{4}-[a-fA-F0-9]{4}-[a-fA-F0-9]{4}-[a-fA-F0-9]{12}))|public$'  # noqa
#     # WILL PROBABLY BE REPLACED BY GLOBUS ACTION PROVIDER TOOLS
#     def to_representation(self, value):
#         return value['urn']
#
#     def to_internal_value(self, data):
#
#         return {
#             'urn': data,
#         }


class ActionSerializer(serializers.ModelSerializer):
    """
           status=ActionStatusValue.ACTIVE,
        creator_id=request.auth.effective_identity,  # type: ignore
        label=req.get("label", None),
        monitor_by=req.get("monitor_by", request.auth.identities),  # type: ignore
        manage_by=req.get("manage_by", request.auth.identities),  # type: ignore
        start_time=str(now),
        completion_time=None,
        release_after=req.get("release_after", "P30D"),
        display_status=ActionStatusValue.ACTIVE.name,
        details=results,
    """

    request_id = serializers.CharField(write_only=True)
    release_after = serializers.IntegerField(write_only=True,
                                             default=gap.models.DEFAULT_RELEASE_AFTER)
    # details = serializers.JSONField(read_only=True)
    display_status = serializers.CharField(source='DisplayFields.get_display_status_display', read_only=True)



    class Meta:
        model = gap.models.Action
        exclude = ['creator', 'manager_by', 'monitor_by']
        # fields = '__all__'
        # read_only_fields = ['action_id', 'user', 'status', 'display_status',
        #                     'details', 'start_time', 'completion_time',
        #                     'release_after']

    def create(self, validated_data):
        data = dict(
            status='INACTIVE',
            creator=self.context['request'].user,
            # monitor_by='public',
            # manage_by='public',
            request_id=validated_data.get('request_id'),
            release_after=validated_data.get('release_after', 'P30D'),
            display_status=ActionStatusValue.INACTIVE.name,
        )
        return gap.models.Action.objects.create(**data)


class ActionCreateSerializer(ActionSerializer):

    body = serializers.JSONField(write_only=True)

    class Meta:
        model = gap.models.Action
        fields = ['request_id', 'body', 'release_after']


class ActionDetailSerializer(ActionSerializer):

    body = serializers.JSONField(read_only=True)


class ActionStatusSerializer(ActionSerializer):

    details = serializers.JSONField(read_only=True)

    class Meta:
        model = gap.models.Action
        # fields = '__all__'
        exclude = ['creator', 'manager_by', 'monitor_by']
        # read_only_fields = ['id', 'transfers']
        # depth = 1
