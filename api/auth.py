from __future__ import unicode_literals
import logging
from django.conf import settings
from rest_framework.authentication import TokenAuthentication
from rest_framework.exceptions import AuthenticationFailed
from rest_framework import permissions
import globus_sdk

#from api.models import GlobusUser
from django.contrib.auth.models import User
from api.models import TokenStore

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
            log.debug(info)
            pu = info.get('username')
            log.debug('logging in user: {}'.format(pu))
            user = User.objects.filter(username=pu).first()
            if not user:
                user = User(username=pu, email=info.get('email'))
                user.save()
                log.debug('Created user {}, using concierge for the first time'
                          '!'.format(user))
            ts = TokenStore.objects.filter(user=user).first()
            if not ts:
                ts = TokenStore(user=user)
            ts.tokens = ac.oauth2_get_dependent_tokens(key).data
            ts.save()
            log.debug('Concierge service authenticated user: {}, ({})'
                      ''.format(user.username, user.email))
            return user, key
        except globus_sdk.exc.AuthAPIError:
            raise AuthenticationFailed(detail={
                   'detail': 'Expired or invalid Globus Auth',
                   'code': 'InvalidOrExpired'})
