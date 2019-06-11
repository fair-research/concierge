from __future__ import unicode_literals
import logging
from rest_framework.exceptions import APIException
from rest_framework import status

log = logging.getLogger(__name__)


class ConciergeException(APIException):
    default_detail = 'Service temporarily unavailable, try again later.'
    default_code = 'service_unavailable'
    default_status_code = status.HTTP_500_INTERNAL_SERVER_ERROR

    def __init__(self, *args, **kwargs):
        super(ConciergeException, self).__init__(*args, **kwargs)
        self.code = kwargs.get('code', self.default_code)
        self.status_code = kwargs.get('status_code', self.default_status_code)
        self.detail = args[0] if args else self.default_detail
        log.debug('Request error, Detail: "{}", Code: "{}", Status: "{}"'
                  .format(self.detail, self.code, self.status_code))


class NoDataToTransfer(ConciergeException):
    default_status_code = status.HTTP_400_BAD_REQUEST
    default_detail = 'No valid data found concierge service can transfer'
    default_code = 'no_data_to_transfer'


class GlobusTransferException(ConciergeException):
    default_status_code = status.HTTP_400_BAD_REQUEST
    default_detail = 'Error starting Globus Transfer'
    default_code = 'globus_error'


class ServiceAuthException(ConciergeException):
    default_status_code = status.HTTP_403_FORBIDDEN
    default_detail = 'A Concierge subservice was unable to authenticate with '\
                     'the credentials provided'
    default_code = 'subservice_auth_error'
