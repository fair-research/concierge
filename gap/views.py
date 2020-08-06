import logging
from rest_framework import viewsets, permissions, serializers, mixins, generics
from rest_framework.response import Response
from gap.models import Action
from gap.serializers import ActionSerializer

log = logging.getLogger(__name__)


class ActionRunViewSet(viewsets.ModelViewSet):
    """
    create:
    globus-automate action run
      --action-url http://localhost:8000/api/automate/manifest
      --action-scope https://auth.globus.org/scopes/524361f2-e4a9-4bd0-a3a6-03e365cac8a9/concierge
      --body '{"Hello": "World"}'
    """
    permission_classes = (permissions.IsAuthenticated,)
    serializer_class = ActionSerializer
    http_method_names = ['post', 'head']


class ActionDetailViewSet(viewsets.ModelViewSet):
    """
    create:
    globus-automate action run
      --action-url http://localhost:8000/api/automate/manifest
      --action-scope https://auth.globus.org/scopes/524361f2-e4a9-4bd0-a3a6-03e365cac8a9/concierge
      --body '{"Hello": "World"}'
    """
    permission_classes = (permissions.IsAuthenticated,)
    serializer_class = ActionSerializer
    http_method_names = ['get', 'post', 'head']

    def get_queryset(self):
        if self.request.user.is_authenticated:
            return self.serializer_class.Meta.model.objects.filter(user=self.request.user)
        return []


class ActionReleaseCancelViewSet(mixins.RetrieveModelMixin, viewsets.GenericViewSet):

    permission_classes = (permissions.IsAuthenticated,)
    serializer_class = serializers.Serializer
    http_method_names = ['post', 'head']
    queryset = Action.objects.all()
    #
    # def get_queryset(self, pk):
    #     return Action.objects.all()

    def release(self, request, pk):
        log.debug('Calling Release')
        obj = self.get_object()
        # obj.delete()
        return Response({'released': True})

    def cancel(self, request, pk):
        log.debug('Calling Cancel')
        obj = self.get_object()
        # obj.delete()
        return Response({'canceled': True})

# TESTING
from api.serializers.manifest import TransferManifestSerializer


class ManifestTransferActionSerializer(ActionSerializer):
    body = TransferManifestSerializer(write_only=True)

    def create(self, validated_data):
        action = super().create(validated_data)
        action.save()
        tm = TransferManifestSerializer(context=self.context).create(validated_data['body'])
        tm.action = action
        return tm


class TransferManifestRunViewSet(ActionRunViewSet):
    serializer_class = ManifestTransferActionSerializer
