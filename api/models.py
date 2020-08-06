from __future__ import unicode_literals
import logging
import json
import time
from functools import reduce
from django.db import models
from django.contrib.auth.models import User
from django.conf import settings

import api

log = logging.getLogger(__name__)


class ConciergeToken(models.Model):

    ID_SCOPE = 'identifiers.globus.org'
    SCOPE_PERMISSIONS = {
        settings.CONCIERGE_SCOPE: [
            settings.MINID_SCOPE, settings.TRANSFER_SCOPE,
        ]
    }

    id = models.CharField(max_length=128, primary_key=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    scope = models.CharField(max_length=128)
    issued_at = models.FloatField()
    expires_at = models.FloatField()
    last_introspection = models.FloatField()
    dependent_tokens_cache = models.TextField(blank=True)

    @property
    def introspection_cache_expired(self):
        """Introspection cache is the length of time we can trust the token id
        between user invocations of this API. This is a balance of security
        and not overloading the Globus Auth servers with requests."""
        last_use = time.time() - self.last_introspection
        log.debug(f'Last use was {last_use}')
        limit = settings.GLOBUS_INTROSPECTION_CACHE_EXPIRATION
        return last_use > limit

    @property
    def token_expired(self):
        log.debug(f'Token expires in {self.expires_at - time.time()} secs')
        return time.time() > self.expires_at

    def get_cached_dependent_tokens(self):
        if self.dependent_tokens_cache:
            return json.loads(self.dependent_tokens_cache)
        else:
            ac = api.auth.get_auth_client()
            response = ac.oauth2_get_dependent_tokens(self.id).data
            by_scope = {toks['scope']: toks for toks in response}
            self.dependent_tokens_cache = json.dumps(by_scope)
            self.save()
            return by_scope

    def reset_introspection_cache(self):
        self.last_introspection = time.time()
        self.save()

    def get_token(self, service):
        if service not in self.SCOPE_PERMISSIONS[self.scope]:
            raise api.exc.InsufficientScopesException(f'{service} not covered '
                                                      f'by scope {self.scope}')
        tokens = self.get_cached_dependent_tokens()
        return tokens[service]['access_token']

    def revoke_token(self):
        ac = api.auth.get_auth_client()
        ac.oauth2_revoke_token(self.id)
        log.debug(f'Revoking token for user {self.user} scope {self.scope}')
        self.delete()

    @classmethod
    def from_user(cls, user):
        tokens = [t for t in cls.objects.filter(user=user)
                  if not t.token_expired]
        if tokens:
            return tokens[0]


class Bag(models.Model):
    user = models.ForeignKey(User, related_name='bags',
                             on_delete=models.CASCADE)
    minid = models.CharField(max_length=30)
    location = models.CharField(max_length=255)


class StageBag(models.Model):
    user = models.ForeignKey(User, related_name='stagebags',
                             on_delete=models.CASCADE)
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
        ctoken = ConciergeToken.from_user(self.user)
        tc = api.utils.load_transfer_client(ctoken)
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


class Transfer(models.Model):
    user = models.ForeignKey(User, related_name='transfers',
                             on_delete=models.CASCADE)
    submission_id = models.UUIDField()
    task_id = models.UUIDField()
    start_time = models.DateTimeField(auto_now_add=True)
    completion_time = models.DateTimeField(null=True)
    status = models.CharField(max_length=32)


class TransferManifest(models.Model):
    user = models.ForeignKey(User, related_name='manifests',
                             on_delete=models.CASCADE)
    transfer = models.ForeignKey(Transfer, on_delete=models.CASCADE)
    action = models.ForeignKey('gap.Action', models.SET_NULL,
                               blank=True, null=True,)
