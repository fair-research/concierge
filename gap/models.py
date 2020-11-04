import uuid
import datetime
from django.db import models
from django.contrib.auth.models import User
from django.utils.translation import gettext_lazy as _
from globus_action_provider_tools.data_types import (
    ActionStatus,
    ActionStatusValue,
)

DEFAULT_RELEASE_AFTER = 60 * 60 * 24 * 30

COMPLETE_STATES = (ActionStatusValue.SUCCEEDED, ActionStatusValue.FAILED)
INCOMPLETE_STATES = (ActionStatusValue.ACTIVE, ActionStatusValue.INACTIVE)


class GlobusURN(models.Model):
    urn = models.CharField(primary_key=True, max_length=256)


class Action(models.Model):
    lookup_field = 'action_id'

    action_id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    request_id = models.CharField(max_length=256, null=True)
    creator = models.ForeignKey(User, on_delete=models.CASCADE)
    status = models.CharField(max_length=256)
    display_status = models.CharField(max_length=32, default=ActionStatusValue.INACTIVE)
    start_time = models.DateTimeField(max_length=256, auto_now_add=True)
    completion_time = models.DateTimeField(max_length=256, null=True)
    release_after = models.IntegerField(default=DEFAULT_RELEASE_AFTER)

    @property
    def body(self):
        """This is a bit of a hack, since the create serializer expects Actions
        to have a body, it will attempt to retrieve the 'body' of a given action.
        Since action bodies are stored in separate models and the lookup is handled
        in the view, this simply returns {}"""
        return {}
