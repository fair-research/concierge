from __future__ import unicode_literals
import logging
from rest_framework.exceptions import APIException
from rest_framework import status

log = logging.getLogger(__name__)


class ConciergeException(APIException):
    default_detail = 'Service temporarily unavailable, try again later.'
    default_code = 'service_unavailable'

    def __init__(self, *args, **kwargs):
        super(ConciergeException, self).__init__(*args, **kwargs)
        log.debug('Request error, Detail: "{}", Code: "{}"'.format(
            self.detail, kwargs.get('code')))


class GlobusTransferException(ConciergeException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = 'Error starting Globus Transfer'
    default_code = 'globus_error'


class ServiceAuthException(ConciergeException):
    status_code = status.HTTP_403_FORBIDDEN
    default_detail = 'A Concierge subservice was unable to authenticate with '\
                     'the credentials provided'
    default_code = 'subservice_auth_error'
