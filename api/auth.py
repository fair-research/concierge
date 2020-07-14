from __future__ import unicode_literals
import logging
from django.contrib.auth.models import User
from django.conf import settings
from rest_framework.authentication import (
    SessionAuthentication, TokenAuthentication
)
from rest_framework.exceptions import AuthenticationFailed
from rest_framework import permissions
from social_django.models import UserSocialAuth
import globus_sdk

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


def get_auth_client():
    return globus_sdk.ConfidentialAppAuthClient(settings.GLOBUS_KEY,
                                                settings.GLOBUS_SECRET)


def get_or_create_user(token_details):
    """
    Get a Django User with a matching Globus uuid (sub) or create
    one if it does not exist. The UserSocialAuth user instance is
    created whether or not a user logged in via social auth or
    simply passed a token into the API. This allows the user to
    do either in either order.
    token_details -- Token response details from introspecting a
    Globus Token
    """
    try:
        return UserSocialAuth.objects.get(uid=token_details['sub']).user
    except UserSocialAuth.DoesNotExist:
        name = token_details['name'].split(' ', 1)
        first_name, last_name = name if len(name) > 1 else (name, '')
        user = User(username=token_details['username'],
                    first_name=first_name, last_name=last_name,
                    email=token_details['email'])
        user.save()
        usa = UserSocialAuth(user=user, provider='globus',
                             uid=token_details['sub'])
        usa.save()
        return user


def introspect_globus_token(raw_token):
    """Introspect the Globus token to check if it is active.

    Introspections are cached for a short duration set by
    settings.GLOBUS_INTROSPECTION_CACHE_EXPIRATION. If many introspections
    (api calls) happen within the cache window, the last introspection will
    be trusted and the Globus Auth intropection call will be skipped.

    If the token is revoked by Globus Auth, an AuthenticationFailed exception
    will be raised.

    A valid token for first time use will result in user creation based on the
    uuid 'sub' field on the token data. """
    try:
        ctoken = api.models.ConciergeToken.objects.get(pk=raw_token)
        if not ctoken.introspection_cache_expired:
            return ctoken
    except api.models.ConciergeToken.DoesNotExist:
        ctoken = None
    try:
        ac = get_auth_client()
        log.debug('Cache Exp or new token, introspecting...')
        token_details = ac.oauth2_token_introspect(raw_token).data
        if token_details['active'] is False:
            log.debug('Auth failed, token is not active.')
            raise AuthenticationFailed('Token is not Active')
        if not ctoken:
            user = get_or_create_user(token_details)
            log.debug(f'Creating new Concierge Token for {user}')
            ctoken = api.models.ConciergeToken(
                id=raw_token, user=user,
                expires_at=token_details['exp'],
                issued_at=token_details['iat'],
                scope=token_details['scope']
            )
        ctoken.reset_introspection_cache()
        # Ensure dependent tokens are cached
        ctoken.get_cached_dependent_tokens()
        ctoken.save()
        log.debug(f'Auth Successful for user {ctoken.user}')
        return ctoken
    except globus_sdk.exc.AuthAPIError as ae:
        log.exception(ae)
        raise AuthenticationFailed('Encountered an error in Globus Auth')


class GlobusTokenAuthentication(TokenAuthentication):
    """
    Simple token based authentication for Globus Auth.
    Clients should authenticate by passing the token key in the "Authorization"
    HTTP header, prepended with the string "Bearer".  For example:
        Authorization: Bearer 401f7ac837da42b97f613d789819ff93537bee6a

    https://github.com/encode/django-rest-framework/blob/master/rest_framework/authentication.py#L145 # noqa
    """

    keyword = 'Bearer'

    def authenticate_credentials(self, raw_token):
        concierge_token = introspect_globus_token(raw_token)
        return concierge_token.user, concierge_token


class GlobusSessionAuthentication(SessionAuthentication):
    """
    Authenticate a user with Python Social Auth. This will store a concierge
    token on the UserSocialAuth object, which is then introspected here
    upon requests through the Swagger API. The Session is used to link the
    user/browser to the UserSocialAuth object, but is not used authorize
    Concierge API requests. Instead, the concierge token is fetched from the
    UserSocialAuth object and passed as if the user was using
    GlobusTokenAuthentication.
    """

    def authenticate(self, request):
        result = super().authenticate(request)
        if result is None:
            return result
        user, _ = result
        social_auth = user.social_auth.get(provider='globus')
        tokens = social_auth.extra_data['other_tokens']
        ctoken = [t for t in tokens
                  if t.get('scope') == settings.CONCIERGE_SCOPE]
        if not ctoken:
            raise AuthenticationFailed('User does not have a vaild token')
        concierge_token = introspect_globus_token(ctoken[0]['access_token'])
        return concierge_token.user, concierge_token
