from __future__ import unicode_literals
import logging
from rest_framework.authentication import TokenAuthentication
from rest_framework.exceptions import AuthenticationFailed
from rest_framework.permissions import BasePermission
import globus_sdk

log = logging.getLogger(__name__)


class GlobusUserAllowAny(BasePermission):
    """Specify which permissions a valid Globus user should have. We currently
    don't have any reason to restrict them from calling any views as long as
    they are a valid user."""

    def has_permission(self, request, view):
        return True


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
        auth_client = globus_sdk.AuthClient(
            authorizer=globus_sdk.AccessTokenAuthorizer(key))
        try:
            email = auth_client.oauth2_userinfo().get('email')
            if not email:
                raise AuthenticationFailed('Failed to get email identity, '
                                           'scope on app needs to be set.')
            log.debug('Authenticated user: {}'.format(email))

            return auth_client, key
        except globus_sdk.exc.AuthAPIError:
            raise AuthenticationFailed('Expired or invalid Globus Auth '
                                       'code.')
