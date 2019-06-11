from rest_framework.views import exception_handler
from api.exc import ConciergeException


def concierge_exception_handler(exc, context):
    """
    Taken from:
    https://www.django-rest-framework.org/api-guide/exceptions/#custom-exception-handling  # noqa
    """
    # Call REST framework's default exception handler first,
    # to get the standard error response.
    response = exception_handler(exc, context)

    # Now add the HTTP status code to the response.
    if response is not None:
        if isinstance(exc, ConciergeException):
            response.data['status_code'] = exc.status_code
        else:
            response.data['status_code'] = response.status_code

    return response
