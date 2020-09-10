import uuid
import datetime
from django.db import models
from django.contrib.auth.models import User
# from django.utils.translation import gettext_lazy as _


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
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    status = models.CharField(max_length=256)
    # display_status = models.IntegerField(
    #     # max_length=2,
    #     choices=DisplayNames.choices,
    #     default=DisplayNames.INACTIVE,
    # )    # details_cache = models.TextField()
    start_time = models.DateTimeField(max_length=256, auto_now_add=True)
    completion_time = models.DateTimeField(max_length=256, null=True)
    release_after = models.CharField(max_length=256, default='P30D')

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
