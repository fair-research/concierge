from __future__ import unicode_literals
import logging
from rest_framework.authentication import TokenAuthentication
from rest_framework.exceptions import AuthenticationFailed
from rest_framework import permissions
import globus_sdk

# from api.models import GlobusUser
from django.contrib.auth.models import User

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
        auth_client = globus_sdk.AuthClient(
            authorizer=globus_sdk.AccessTokenAuthorizer(key))
        try:

            info = auth_client.oauth2_userinfo()
            log.debug(info)
            pu = info.get('preferred_username')
            email = info.get('email')

            if not pu or not email:
                log.error('Unable to get email for user, was "email" '
                          'included in scopes?')
                raise AuthenticationFailed('Unable to verify user email')
            user = User.objects.filter(username=pu).first()
            if not user:
                user = User(email=pu, username=pu)
                user.save()
                log.debug('Created user {}, using concierge for the first time'
                          '!'.format(user))
            # user_info = auth_client.get_identities(usernames=[email])
            # try:
            #     log.debug(user_info.data)
            #     user_uuid = user_info.data['identities'][0]['id']
            # except KeyError:
            #     raise AuthenticationFailed(
            #         'Failed to verify email "{}"'.format(email))

            #user = GlobusUser.objects.filter(uuid=user_uuid).first()
            # if not user:
                #user_info = auth_client.get_identities(usernames=[email])
                # log.debug('ID Info: {}'.format(user_info))
            log.debug('Concierge service authenticated user: {}'.format(email))

            return user, key
        except globus_sdk.exc.AuthAPIError:
            raise AuthenticationFailed(detail={
                   'detail': 'Expired or invalid Globus Auth',
                   'code': 'InvalidOrExpired'})
