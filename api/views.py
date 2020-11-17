from __future__ import unicode_literals
import logging
from django.contrib.auth import logout as django_logout
from django.shortcuts import redirect
from django.core.exceptions import ValidationError
from rest_framework import viewsets, permissions, response
from rest_framework.request import Request
from rest_framework.response import Response
from gap.views import ActionViewSet
from api.models import Manifest, ManifestTransfer
from api.auth import GlobusSessionAuthentication, IsOwnerOrReadOnly, IsOwner
from api.transfer import get_transfer_client

from api.serializers.manifest import ManifestListSerializer, ManifestTransferSerializer
from api.serializers.automate import ManifestTransferActionSerializer
from globus_action_provider_tools.data_types import ActionStatusValue

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

    # def retrieve(self, request, *args, **kwargs):
    #     log.debug(request, args, kwargs)
    #     return super().retrieve(request, *args, **kwargs)

    def delete(self, request, *args, **kwargs):
        return self.destroy(request, *args, **kwargs)


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

    def get_object(self):
        return ManifestTransfer.objects.get(manifest=self.kwargs['manifest_id'],
                                            id=self.kwargs['manifest_transfer_id'])

    def retrieve(self, response, *args, **kwargs):
        # if self.kwargs.get('manifest_id') and self.kwargs.get('manifest_transfer_id'):
        try:
            return super().retrieve(response, *args, **kwargs)
        except KeyError:
            return Response({'error': 'You must provide both manifest_id and manifest_transfer_id'},
                            status=400)
        except ValidationError as ve:
            return Response({'error': ve.messages[0]}, 400)
        except ManifestTransfer.DoesNotExist as dne:
            return Response({'error': str(dne)}, 404)


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
    details_object = ManifestTransfer
    body_serializer_class = detail_serializer_class = ManifestTransferActionSerializer

    def cancel(self, request, action_id):
        obj = self.get_manifest(action_id)
        if obj.action.display_status != 'ACTIVE':
            return self.status(request, action_id)
        tc = get_transfer_client(request.auth)
        tc.cancel_task(str(obj.transfer.task_id))
        return super().cancel(request, action_id)

    def status(self, request, action_id=None):
        obj = self.get_details_object(action_id)
        action = obj.action
        if action.display_status in ['INACTIVE', 'ACTIVE']:
            for transfer in obj.transfers.all():
                log.debug(f'Updating Transfer {transfer}')
                transfer.update()
            tstatus = [t.status for t in obj.transfers.all()]
            if 'FAILED' in tstatus:
                action.status = ActionStatusValue.FAILED
                action.display_status = ActionStatusValue.FAILED.name
            elif all((s == 'SUCCEEDED') for s in tstatus):
                action.status = ActionStatusValue.SUCCEEDED.name
                action.display_status = ActionStatusValue.SUCCEEDED.name
            action.save()
        return super().status(request, action_id)


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
