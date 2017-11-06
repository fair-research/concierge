from django.db import models


class Bag(models.Model):
    minid_id = models.CharField(max_length=30)
    minid_email = models.CharField(max_length=255)
    location = models.CharField(max_length=255)

    minid_user = ''
    minid_title = ''
    minid_test = False
    remote_files_manifest = {}
