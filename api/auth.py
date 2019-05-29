from __future__ import unicode_literals
import logging
from datetime import timedelta
from django.utils import timezone
from django.conf import settings
from rest_framework.authentication import TokenAuthentication
from rest_framework.exceptions import AuthenticationFailed
from rest_framework import permissions
import globus_sdk


# from api.models import TokenStore
from django.contrib.auth.models import User
import api


log = logging.getLogger(__name__)


class IsOwnerOrReadOnly(permissions.BasePermission):
    """Specify which permissions a valid Globus user should have. We currently
    don't have any reason to restrict them from calling any views as long as
    they are a valid user."""

    def has_permission(self, request, view):
        """Only authenticated Globus users have access to write. Anon users
        can only read and list."""
        return request.user.is_authenticated or \
            request.method in permissions.SAFE_METHODS

    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True

        # Write permissions are only allowed to the owner.
        return obj.user == request.user


class GlobusTokenAuthentication(TokenAuthentication):
    """
    Simple token based authentication for Globus Auth.
    Clients should authenticate by passing the token key in the "Authorization"
    HTTP header, prepended with the string "Bearer".  For example:
        Authorization: Bearer 401f7ac837da42b97f613d789819ff93537bee6a

    https://github.com/encode/django-rest-framework/blob/master/rest_framework/authentication.py#L145 # noqa
    """

    keyword = 'Bearer'

    def authenticate_credentials(self, key):
        ac = globus_sdk.ConfidentialAppAuthClient(settings.GLOBUS_KEY,
                                                  settings.GLOBUS_SECRET)
        try:
            info = ac.oauth2_token_introspect(key).data
            pu = info.get('username')
            if not pu:
                token_expired()
            user = User.objects.filter(username=pu).first()
            if not user:
                user = User(username=pu, email=info.get('email'))
                user.save()
                log.debug('Created user {}, using concierge for the first time'
                          '!'.format(user))
            ts = api.models.TokenStore.objects.filter(user=user).first()
            if not ts:
                ts = api.models.TokenStore(user=user)
            ts.tokens = {t['resource_server']: t
                         for t in ac.oauth2_get_dependent_tokens(key).data}
            ts.save()
            log.debug('Concierge service authenticated user: {}, ({})'
                      ''.format(user.username, user.email))
            return user, key
        except globus_sdk.exc.AuthAPIError:
            self.token_expired()


def token_expired():
    raise AuthenticationFailed(detail={
           'detail': 'Expired or invalid Globus Auth',
           'code': 'InvalidOrExpired'})


def get_transfer_token(user):
    return api.models.TokenStore.get_transfer_token(user) or \
           load_globus_access_token(user, 'transfer.api.globus.org')


def load_globus_access_token(user, token_name):
    """Load a globus token from a user object. This only works if a user has
    logged in via OAUTH directly through the Django interface."""
    if not user:
        return None
    if user.is_authenticated:
        tok_list = user.social_auth.get(provider='globus').extra_data
        if token_name == 'auth.globus.org':
            return tok_list['access_token']
        if tok_list.get('other_tokens'):
            service_tokens = {t['resource_server']: t
                              for t in tok_list['other_tokens']}
            service_token = service_tokens.get(token_name)
            if service_token:
                exp_td = timedelta(seconds=service_token['expires_in'])
                if user.last_login + exp_td < timezone.now():
                    raise token_expired()
                return service_token['access_token']
            else:
                raise ValueError(
                    'Attempted to load {} for user {}, but no '
                    'tokens existed with the name {}, only {}'
                    ''.format(token_name, user, token_name,
                              list(service_tokens.keys())))
