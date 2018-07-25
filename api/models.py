from __future__ import unicode_literals
import json
from django.db import models
from django.contrib.auth.models import User
from django.conf import settings


class TokenStore(models.Model):

    ID_SCOPE = ('https://auth.globus.org/scopes/identifiers.globus.org/create_update')


    user = models.ForeignKey(User, on_delete=models.CASCADE)
    token_store = models.TextField(blank=True)

    @property
    def tokens(self):
        return json.loads(self.token_store) if self.token_store else {}

    @tokens.setter
    def tokens(self, value):
        self.token_store = json.dumps(value) if value else json.dumps({})

    @staticmethod
    def get_id_token(user):
        ts = TokenStore.objects.get(user=user)
        tokens = {t['scope']: t for t in ts.tokens}
        return tokens[TokenStore.ID_SCOPE]['access_token']



class Bag(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    minid_id = models.CharField(max_length=30)
    minid_email = models.CharField(max_length=255)
    location = models.CharField(max_length=255)

    minid_user = ''
    minid_title = ''
    minid_test = False
    remote_files_manifest = {}


class StageBag(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    destination_endpoint = models.CharField(max_length=512)
    destination_path_prefix = models.CharField(max_length=255)
    bag_minids = models.TextField()
    transfer_token = models.CharField(max_length=255)
    transfer_catalog = models.TextField()
    error_catalog = models.TextField()
    transfer_task_ids = models.TextField()
