import logging
from django.urls import path
from rest_framework import viewsets, permissions, serializers
from rest_framework.response import Response
from gap.models import Action
from gap.serializers import ActionSerializer

log = logging.getLogger(__name__)


class ActionViewSet(viewsets.ModelViewSet):
    """
    run: Run the action, either stand alone or as part of an Automate Flow.
    list: Lists all of the user's current actions which have not been released
    introspect: Returns a schema which lists all possible values allowed by this Automate Action
    status: Returns status on the current action.
    release: Deletes the stored data for this action.
    cancel: Stops the current action, if the action supports it.
    """
    permission_classes = (permissions.IsAuthenticated,)
    serializer_class = ActionSerializer
    http_method_names = ['get', 'post', 'head']
    queryset = Action.objects.all()
    lookup_field = 'action_id'

    @classmethod
    def urls(cls):
        return [
            path('', cls.as_view({'get': 'introspect'})),
            # path('list', cls.as_view({'get': 'list'})),
            path('run', cls.as_view({'post': 'run'})),
            path('<action_id>/status', cls.as_view({'get': 'status'})),
            path('<action_id>/cancel', cls.as_view({'post': 'cancel'}, serializer_class=serializers.Serializer)),
            path('<action_id>/release', cls.as_view({'post': 'release'}, serializer_class=serializers.Serializer)),
        ]

    def run(self, request):
        request_id = request.data.get('request_id')
        if request_id:
            previous_action = Action.objects.filter(request_id=request_id)
            if previous_action:
                return self.status(request, action_id=previous_action.first().action_id)
        return super().create(request)

    def introspect(self, request):
        return Response({'error': 'Not Implemented'})

    def status(self, request, action_id):
        return self.retrieve(request, action_id)

    def release(self, request, action_id):
        log.debug('Calling Release')
        self.get_object().delete()
        return Response({'released': True})

    def cancel(self, request, action_id):
        log.debug('Calling Cancel')
        return Response({'error': 'This action cannot be canceled.'}, status=405)
