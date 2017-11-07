from django.db import models


class Bag(models.Model):
    minid_id = models.CharField(max_length=30)
    minid_email = models.CharField(max_length=255)
    location = models.CharField(max_length=255)

    minid_user = ''
    minid_title = ''
    minid_test = False
    remote_files_manifest = {}


class StageBag(models.Model):

    location = models.CharField(max_length=512)
    bag_minids = models.TextField()
    # TODO: Find actual length of transfer token
    transfer_token = models.CharField(max_length=64)
