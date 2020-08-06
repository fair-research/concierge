from django.db import models
from django.contrib.auth.models import User


class Action(models.Model):
    class DisplayNames(models.IntegerChoices):
        ACTIVE = 0, 'ACTIVE'
        INACTIVE = 1, 'INACTIVE'
        SUCCEEDED = 2, 'SUCCEEDED'
        FAILED = 3, 'FAILED'
        RELEASED = 4, 'RELEASED'

    action_id = models.CharField(max_length=256)
    request_id = models.CharField(max_length=256)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    status = models.CharField(max_length=256)
    display_status = models.CharField(
        max_length=2,
        choices=DisplayNames.choices,
        default=DisplayNames.INACTIVE,
    )    # details_cache = models.TextField()
    start_time = models.DateTimeField(max_length=256, auto_now_add=True)
    completion_time = models.DateTimeField(max_length=256, auto_now_add=True)
    release_after = models.CharField(max_length=256, default='P30D')


class TestAction(models.Model):
    action = models.ForeignKey(Action, on_delete=models.CASCADE)
    detail = models.CharField(max_length=256)
