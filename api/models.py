import os
from django.db import models
from django.conf import settings

# from api.utils import create_bag_archive, create_minid, upload_to_s3


# Create your models here.

class Bag(models.Model):
    minid_id = models.CharField(max_length=30)
    minid_email = models.CharField(max_length=255)
    location = models.CharField(max_length=255)

    _minid_user = ''
    _minid_title = ''
    _minid_test = False
    _remote_files_manifest = {}

    @property
    def minid_user(self):
        return self._minid_user

    @minid_user.setter
    def minid_user(self, value):
        self._minid_user = value

    @property
    def minid_title(self):
        return self._minid_title

    @minid_title.setter
    def minid_title(self, value):
        self._minid_title = value

    @property
    def minid_test(self):
        return self._minid_test

    @minid_test.setter
    def minid_test(self, value):
        self._minid_test = value

    @property
    def remote_files_manifest(self):
        return self._minid_test

    @remote_files_manifest.setter
    def remote_files_manifest(self, value):
        self._remote_files_manifest = value


    @classmethod
    def from_db(cls, db, field_names, values):
        return super(Bag, cls).from_db(db, field_names, values)



