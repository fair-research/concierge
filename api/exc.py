from rest_framework.exceptions import APIException
from rest_framework import status


class ConciergeException(APIException):
    default_detail = 'Service temporarily unavailable, try again later.'
    default_code = 'service_unavailable'


class GlobusTransferException(ConciergeException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = 'Error starting Globus Transfer'
    default_code = 'globus_error'
