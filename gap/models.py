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

    # class DisplayNames(models.IntegerChoices):
    #     ACTIVE = 0, _('ACTIVE')
    #     INACTIVE = 1, _('INACTIVE')
    #     SUCCEEDED = 2, _('SUCCEEDED')
    #     FAILED = 3, _('FAILED')
    #     RELEASED = 4, _('RELEASED')

    action_id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    request_id = models.CharField(max_length=256)
    creator = models.ForeignKey(User, on_delete=models.CASCADE)
    monitor_by = models.ManyToManyField(GlobusURN, related_name='monitor_by')
    manager_by = models.ManyToManyField(GlobusURN, related_name='manager_by')
    status = models.CharField(max_length=256)
    display_status = models.CharField(max_length=32, default=ActionStatusValue.INACTIVE)
    start_time = models.DateTimeField(max_length=256, auto_now_add=True)
    completion_time = models.DateTimeField(max_length=256, null=True)
    release_after = models.IntegerField(default=DEFAULT_RELEASE_AFTER)

    @property
    def details(self):
        return getattr(self, '_details', {})

    @details.setter
    def details(self, value):
        self._details = value

    def set_completed(self, status):
        self.display_status = status
        self.completion_time = datetime.datetime.now()


class TestAction(models.Model):
    action = models.ForeignKey(Action, on_delete=models.CASCADE)
    detail = models.CharField(max_length=256)
