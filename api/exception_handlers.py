import logging
from rest_framework.views import exception_handler
from api.exc import ConciergeException, TokenInactive
from django.shortcuts import redirect
from django.contrib.auth import logout as django_logout

log = logging.getLogger(__name__)


def concierge_exception_handler(exc, context):
    """
    Taken from:
    https://www.django-rest-framework.org/api-guide/exceptions/#custom-exception-handling  # noqa
    """
    # Call REST framework's default exception handler first,
    # to get the standard error response.
    response = exception_handler(exc, context)

    if isinstance(exc, TokenInactive):
        log.debug('Popping Django session due to Token inactivity exc')
        django_logout(context['request'])
        return redirect('/')

    if response is not None:
        if isinstance(exc, ConciergeException):
            response.data['status_code'] = exc.status_code
        else:
            response.data['status_code'] = response.status_code

    return response
