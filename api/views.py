from __future__ import unicode_literals
import logging
from django.contrib.auth import logout as django_logout
from django.shortcuts import redirect
from rest_framework import viewsets, permissions, response
from rest_framework.request import Request
from gap.views import ActionViewSet
from gap.serializers import ActionSerializer
from gap.models import Action
from api.models import Manifest, ManifestTransfer
from api.auth import GlobusSessionAuthentication, IsOwnerOrReadOnly, IsOwner
from api.transfer import get_transfer_client

from api.serializers.manifest import ManifestListSerializer, ManifestTransferSerializer
from api.serializers.transfer import TransferSerializer
from api.serializers.automate import ManifestTransferActionSerializer, ManifestTransferActionStatusSerializer

log = logging.getLogger(__name__)


class ManifestViewSet(viewsets.ModelViewSet):
    """
    list: List all manifests.
    retrieve: Fetch and display the contents of a Manifest. Allowed by anyone. \
    Supports query param ``format`` with valid values ``globus_manifest``, ``remote_file_manifest`` \
    or ``bdbag``.
    create: Create a Manifest using the Globus Manifest spec. Must be Authenticated.
    delete: Delete a manifest. Only allowed by owner.
    """
    serializer_class = ManifestListSerializer
    queryset = Manifest.objects.all()
    permission_classes = (IsOwnerOrReadOnly,)
    http_method_names = ['head', 'get', 'post', 'delete']


class TransferViewSet(viewsets.ModelViewSet):
    """
    list: List all of a user's previously transferred manifests
    retrieve: Get the status for an existing manifest transfer
    create: Transfer a Manifest using an identifier or any previously created manifests (uuid)
    """
    serializer_class = ManifestTransferSerializer
    permission_classes = (permissions.IsAuthenticated, IsOwner)
    queryset = ManifestTransfer.objects.all()
    http_method_names = ['head', 'get', 'post']


# class TransferManifestViewSet(viewsets.ModelViewSet):
#     """
#     create:
#     Transfer a Globus Manifest. More info can be found at the
#     following location https://globusonline.github.io/manifests/overview.html
#
#     Note, you must end source directories with '/' to denote a directory.
#
#     list:
#     List the previous manifests you have transferred
#
#     detail:
#     Get more information about a specific Manifest you have transferred
#     """
#     permission_classes = (permissions.IsAuthenticated,)
#     serializer_class = TransferManifestSerializer
#     http_method_names = ['get', 'post', 'head']
#
#     def get_queryset(self):
#         if self.request.user.is_authenticated:
#             return TransferManifest.objects.filter(user=self.request.user)
#         return []


class TransferManifestActionViewSet(ActionViewSet):
    """
    Automate action for transferring a given manifest.
    https://globusonline.github.io/manifests/overview.html

    run: Start a transfer for a Globus Manifest. Will include a separate transfer for
         each unique source endpoint in the manifest provided.
    list: List the current user's previous transfers
    introspect: See the JSON Schema for transferring a manifest via a Globus Flow
    status: Get status for a Manifest Transfer. Will remain ACTIVE until each transfer
            has been completed. Returns SUCCEEDED if all transfers completed without
            error and FAILED otherwise.
    release: Deletes the stored data for this action.
    cancel: Cancel all active transfers.
    """
    serializer_class = ManifestTransferActionSerializer
    create_serializer_class = ManifestTransferActionSerializer
    status_serializer_class = ManifestTransferActionStatusSerializer

    def get_manifest(self, action=None, action_id=None):
        # log.debug(self.kwargs)
        if not action:
            if not action_id:
                action = self.get_object()
            else:
                action = Action.objects.get(action_id=action_id)
        log.debug(f'Fetching manifest with action action {action}')
        return ManifestTransfer.objects.get(action=action)

    def cancel(self, request, action_id):
        obj = self.get_manifest(action_id)
        if obj.action.display_status != 'ACTIVE':
            return self.status(request, action_id)
        tc = get_transfer_client(request.auth)
        task = tc.cancel_task(str(obj.transfer.task_id))
        obj.action.set_completed(status='FAILED')
        obj.action.details = task.data
        action_serializer = ActionSerializer(obj.action)
        return response.Response(action_serializer.data)

    def status(self, request, action_id):
        obj = self.get_manifest(action_id)
        action = obj.action
        # from pprint import pprint
        # pprint(task.data)
        if action.display_status == 'ACTIVE':
            tc = get_transfer_client(request.auth)
            log.debug(f'Manifest {obj} fetching task {obj.transfer.task_id}')
            task = tc.get_task(str(obj.transfer.task_id))
            action.status = task['nice_status']
            transfer_to_action_status = {
                'ACTIVE': 'ACTIVE',
                'ACCEPTED': 'ACTIVE',
                'PAUSED': 'INACTIVE',
                'SUCCEEDED': 'SUCCEEDED',
                'FAILED': 'FAILED'
            }
            action.display_status = transfer_to_action_status[task['status']]
            action.save()
            action.details = task.data
        action_serializer = ActionSerializer(action)
        return response.Response(action_serializer.data)


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
