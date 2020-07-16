from __future__ import unicode_literals
import logging
from django.contrib.auth import logout as django_logout
from django.shortcuts import redirect
from rest_framework import viewsets, permissions
from rest_framework.request import Request
from api.models import Bag, StageBag
from api.auth import GlobusSessionAuthentication

from api.serializers import BagSerializer, StageBagSerializer

log = logging.getLogger(__name__)


class BagViewSet(viewsets.ModelViewSet):
    """
    The Bag view lists all of the BDBags created through this service.

    retrieve:
    Fetch a specific bag for further details

    list:
    Fetch the bags you have previously created.
    """
    permission_classes = (permissions.IsAuthenticated,)
    serializer_class = BagSerializer
    http_method_names = ['get', 'post', 'head']

    def get_queryset(self):
        if self.request.user.is_authenticated:
            return Bag.objects.filter(user=self.request.user)
        return []


class StageBagViewSet(viewsets.ModelViewSet):
    permission_classes = (permissions.IsAuthenticated,)
    serializer_class = StageBagSerializer
    http_method_names = ['get', 'post', 'head']

    def get_queryset(self):
        if self.request.user.is_authenticated:
            return StageBag.objects.filter(user=self.request.user)
        return []


def logout(request, next='/'):
    """
    Revoke the users tokens and pop their Django session. Users will be
    redirected to the query parameter 'next' if it is present. If the 'next'
    query parameter 'next' is not present, the parameter next will be used
    instead.
    """
    if request.user.is_authenticated:
        r = Request(request, authenticators=(GlobusSessionAuthentication(),))
        r.auth.revoke_token()
        django_logout(request)
    return redirect(request.GET.get('next', next))
