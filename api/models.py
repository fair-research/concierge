from __future__ import unicode_literals
import logging
import json
from django.db import models
from django.contrib.auth.models import User

log = logging.getLogger(__name__)


class TokenStore(models.Model):

    ID_SCOPE = ('https://auth.globus.org/scopes/identifiers.globus.org/'
                'create_update')



    user = models.ForeignKey(User, on_delete=models.CASCADE)
    token_store = models.TextField(blank=True)

    @property
    def tokens(self):
        return json.loads(self.token_store) if self.token_store else {}

    @tokens.setter
    def tokens(self, value):
        self.token_store = json.dumps(value) if value else json.dumps({})

    @staticmethod
    def get_token(user, token_name):
        ts = TokenStore.objects.get(user=user)
        tokens = {t['resource_server']: t for t in ts.tokens}
        token = tokens.get(token_name)
        log.debug('{} token for {} exists: {}'.format(token_name, user,
                                                      bool(token)))
        return token['access_token'] if token else None

    @staticmethod
    def get_id_token(user):
        return TokenStore.get_token(user, TokenStore.ID_SCOPE)

    @staticmethod
    def get_transfer_token(user):
        return TokenStore.get_token(user, 'transfer.api.globus.org')


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
    transfer_catalog = models.TextField()
    error_catalog = models.TextField()
    transfer_task_ids = models.TextField()
