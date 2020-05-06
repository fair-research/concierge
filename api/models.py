from __future__ import unicode_literals
import logging
import json
from functools import reduce
from globus_sdk import AccessTokenAuthorizer, TransferClient
from django.db import models
from django.contrib.auth.models import User

log = logging.getLogger(__name__)


class TokenStore(models.Model):

    ID_SCOPE = 'identifiers.globus.org'

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
        token = TokenStore.objects.get(user=user).tokens.get(token_name)
        log.debug('{} token for {} exists: {}'.format(token_name, user,
                                                      bool(token)))
        return token['access_token'] if token else None

    @staticmethod
    def get_id_token(user):
        return TokenStore.get_token(user,
                                    '85114005-42e6-4671-a73a-0a40150c2b88')

    @staticmethod
    def get_transfer_token(user):
        return TokenStore.get_token(user, 'transfer.api.globus.org')


class Bag(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    minid = models.CharField(max_length=30)
    location = models.CharField(max_length=255)


class StageBag(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    destination_endpoint = models.CharField(max_length=512)
    destination_path_prefix = models.CharField(max_length=255, blank=True)
    minids = models.TextField()
    transfer_catalog = models.TextField()
    task_catalog = models.TextField()
    files_transferred = models.IntegerField(blank=True, null=True)
    status = models.CharField()
    error_catalog = models.TextField()
    transfer_task_ids = models.TextField()

    @property
    def status(self):
        token = TokenStore.get_transfer_token(self.user)
        tc = TransferClient(authorizer=AccessTokenAuthorizer(token))
        old = json.loads(self.task_catalog or '{}')
        tasks = {t: tc.get_task(t).data
                 for t in json.loads(self.transfer_task_ids)
                 if not old.get(t) or old[t]['status'] == 'ACTIVE'}
        old.update(tasks)
        tasks = old

        transferred = [t['files_transferred'] for t in tasks.values()]
        log.debug(transferred)
        self.files_transferred = reduce(lambda x, y: x + y, transferred)
        log.debug(self.files_transferred)
        self.task_catalog = json.dumps(tasks)
        self.save()
        statuses = [s['status'] for s in tasks.values()]
        if any(filter(lambda stat: stat in ['INACTIVE', 'FAILED'], statuses)):
            return 'FAILED'
        if any(filter(lambda stat: stat == 'ACTIVE', statuses)):
            return 'ACTIVE'
        return 'SUCCEEDED'
