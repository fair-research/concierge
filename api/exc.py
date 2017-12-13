import logging
from rest_framework.exceptions import APIException
from rest_framework import status

log = logging.getLogger(__name__)


class ConciergeException(APIException):
    default_detail = 'Service temporarily unavailable, try again later.'
    default_code = 'service_unavailable'

    def __init__(self, *args, **kwargs):
        log.debug('Request error, Detail: "{}", Code: "{}"'.format(
            kwargs.get('detail'), kwargs.get('code')))
        super(ConciergeException, self).__init__(*args, **kwargs)


class GlobusTransferException(ConciergeException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = 'Error starting Globus Transfer'
    default_code = 'globus_error'
