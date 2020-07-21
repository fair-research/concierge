from __future__ import unicode_literals
import logging
from django.contrib.auth import logout as django_logout
from django.shortcuts import redirect
from rest_framework import viewsets, permissions
from rest_framework.request import Request
from api.models import Bag, StageBag, TransferManifest
from api.auth import GlobusSessionAuthentication

from api.serializers.bag import BagCreateListSerializer, StageBagSerializer
from api.serializers.bag_manifest import BagManifestSerializer
from api.serializers.manifest import TransferManifestSerializer
from api.serializers.transfer import TransferSerializer

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
    serializer_class = BagCreateListSerializer
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


class BagManifestViewSet(viewsets.ModelViewSet):
    """
    create:
    Create a Bag with a Minid given a Globus "Manifest Items" object. More info
    can be found here: https://globusonline.github.io/manifests/overview.html

    In order to create a BDBag from a Globus Manifest, each Manifest Item must
    have a checksum.

    All other 'bag' fields are optional.
    """
    permission_classes = (permissions.IsAuthenticated,)
    serializer_class = BagManifestSerializer
    http_method_names = ['post', 'head']


class TransferViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = (permissions.IsAuthenticated,)
    serializer_class = TransferSerializer


class TransferManifestViewSet(viewsets.ModelViewSet):
    """
    create:
    Transfer a Globus Manifest. More info can be found at the
    following location https://globusonline.github.io/manifests/overview.html

    Note, you must end source directories with '/' to denote a directory.

    list:
    List the previous manifests you have transferred

    detail:
    Get more information about a specific Manifest you have transferred
    """
    permission_classes = (permissions.IsAuthenticated,)
    serializer_class = TransferManifestSerializer
    http_method_names = ['get', 'post', 'head']

    def get_queryset(self):
        if self.request.user.is_authenticated:
            return TransferManifest.objects.filter(user=self.request.user)
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
