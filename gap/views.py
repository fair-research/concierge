import logging
from django.urls import path, include
from rest_framework import viewsets, permissions, serializers
from rest_framework.response import Response
from gap.models import Action
from rest_framework.schemas.openapi import SchemaGenerator
from gap.serializers import ActionSerializer, ActionCreateSerializer, ActionStatusSerializer

log = logging.getLogger(__name__)


class IsAuthenticatedOrIntrospect(permissions.BasePermission):
    """This is an automate based custom permission. It requires auth on each method,
    except for the 'introspect' method, which is public and allowed by any user."""

    def has_permission(self, request, view):
        is_introspect = view.action_map.get(request.method.lower()) == 'introspect'
        return is_introspect or request.user.is_authenticated


class ActionViewSet(viewsets.ModelViewSet):
    """
    run: Run the action, either stand alone or as part of an Automate Flow.
    list: Lists all of the user's current actions which have not been released
    introspect: Returns a schema which lists all possible values allowed by this Automate Action
    status: Returns status on the current action.
    release: Deletes the stored data for this action.
    cancel: Stops the current action, if the action supports it.
    """
    permission_classes = (IsAuthenticatedOrIntrospect,)
    serializer_class = ActionSerializer
    http_method_names = ['get', 'post', 'head']
    queryset = Action.objects.all()
    lookup_field = 'action_id'
    create_serializer_class = ActionCreateSerializer
    status_serializer_class = ActionStatusSerializer

    @classmethod
    def urls(cls):
        return [
            path('', cls.as_view({'get': 'introspect'}, serializer_class=serializers.Serializer)),
            # path('list', cls.as_view({'get': 'list'})),
            path('run', cls.as_view({'post': 'run'}, serializer_class=cls.create_serializer_class)),
            path('<action_id>/status', cls.as_view({'get': 'status'}, serializer_class=cls.status_serializer_class)),
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
        # Generate a path based on the standard automate URLs above
        patterns = [path(request.path, include(self.urls()))]
        generator = SchemaGenerator(patterns=patterns)
        return Response(generator.get_schema())

    def status(self, request, action_id):
        return self.retrieve(request, action_id)

    def release(self, request, action_id):
        log.debug('Calling Release')
        self.get_object().delete()
        return Response({'released': True})

    def cancel(self, request, action_id):
        log.debug('Calling Cancel')
        return Response({'error': 'This action cannot be canceled.'}, status=405)
