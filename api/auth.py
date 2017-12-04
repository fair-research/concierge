from rest_framework.authentication import TokenAuthentication
from rest_framework.exceptions import AuthenticationFailed
import globus_sdk

class GlobusTokenAuthentication(TokenAuthentication):

    keyword = 'Bearer'

    def authenticate_credentials(self, key):


        raise Exception("this happened")
        ac = globus_sdk.AuthClient(authorizer=
                                   globus_sdk.AccessTokenAuthorizer(key))
        try:
            email = ac.oauth2_userinfo().get('email')
            if not email:
                raise AuthenticationFailed('Failed to get email identity, scope'
                                           ' on app needs to be set.')
            return email
        except globus_sdk.exc.AuthAPIError:
            raise AuthenticationFailed('Expired or invalid Globus Auth '
                                          'code.')

