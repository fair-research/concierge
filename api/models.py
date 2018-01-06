from __future__ import unicode_literals
from django.db import models
from django.contrib.auth.models import User


class GlobusUser(User):
    uuid = models.UUIDField(primary_key=True, editable=False)


class Bag(models.Model):
    user = models.ForeignKey(GlobusUser, on_delete=models.CASCADE)
    minid_id = models.CharField(max_length=30)
    minid_email = models.CharField(max_length=255)
    location = models.CharField(max_length=255)

    minid_user = ''
    minid_title = ''
    minid_test = False
    remote_files_manifest = {}


class StageBag(models.Model):
    user = models.ForeignKey(GlobusUser, on_delete=models.CASCADE)
    destination_endpoint = models.CharField(max_length=512)
    destination_path_prefix = models.CharField(max_length=255)
    bag_minids = models.TextField()
    transfer_token = models.CharField(max_length=255)
    transfer_catalog = models.TextField()
    error_catalog = models.TextField()
    transfer_task_ids = models.TextField()
