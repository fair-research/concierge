import logging
from django.urls import path, include
from rest_framework import viewsets, serializers, status
from rest_framework.response import Response
from gap.models import Action
from rest_framework.schemas.openapi import SchemaGenerator
from gap import permissions
from gap.serializers import ActionCreateSerializer, ActionStatusSerializer

log = logging.getLogger(__name__)


class ActionViewSet(viewsets.ModelViewSet):
    """
    title, subtitle, description, keywords
    run: Run the action, either stand alone or as part of an Automate Flow.
    list: Lists all of the user's current actions which have not been released
    introspect: Returns a schema which lists all possible values allowed by this Automate Action
    status: Returns status on the current action.
    release: Deletes the stored data for this action.
    cancel: Stops the current action, if the action supports it.
    """
    permission_classes = (permissions.IsVisibleTo, permissions.IsRunnableBy)
    http_method_names = ['get', 'post', 'head']
    queryset = Action.objects.all()
    details_obj = None
    lookup_field = 'action_id'
    detail_serializer_class = serializers.Serializer
    body_serializer_class = serializers.Serializer
    request_serializer_class = ActionCreateSerializer
    status_serializer_class = ActionStatusSerializer
    visible_to = [permissions.PUBLIC]
    runnable_by = [permissions.ALL_AUTHENTICATED_USERS]
    # https://action-provider-tools.readthedocs.io/en/latest/action_provider_interface.html#action-provider-document-types  # noqa
    api_version = '1.0'
    synchronous = False
    log_supported = False

    @classmethod
    def urls(cls):
        class BodySerializer(cls.request_serializer_class):
            body = cls.body_serializer_class

        class DetailSerializer(cls.status_serializer_class):
            detail = cls.detail_serializer_class

        return [
            path('', cls.as_view({'get': 'introspect'}, serializer_class=serializers.Serializer)),
            # path('list', cls.as_view({'get': 'list'})),
            path('run', cls.as_view({'post': 'run'}, serializer_class=BodySerializer)),
            path('<action_id>/status', cls.as_view({'get': 'status'}, serializer_class=DetailSerializer)),
            path('<action_id>/cancel', cls.as_view({'post': 'cancel'}, serializer_class=DetailSerializer)),
            path('<action_id>/release', cls.as_view({'post': 'release'}, serializer_class=DetailSerializer)),
        ]

    def create(self, request, *args, **kwargs):
        """Create is overridden in rest_framework in order to handle fetching the extra
        'body' object for the response, which is saved in a separate model."""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        data = serializer.data
        details_instance = self.get_details_object(serializer.instance.action_id)
        details_serializer = self.body_serializer_class(details_instance)
        data['body'] = details_serializer.data
        headers = self.get_success_headers(serializer.data)
        return Response(data, status=status.HTTP_201_CREATED, headers=headers)

    def retrieve(self, request, *args, **kwargs):
        """retrieve is overridden in rest_framework to handle setting the extra 'details'
        object, which is stored on a subclassed model."""
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        data = serializer.data
        # Get 'details' object containing all the data/work for this automate action.
        details_instance = self.get_details_object(data['action_id'])
        details_serializer = self.detail_serializer_class(details_instance)
        data['details'] = details_serializer.data
        return Response(data)

    def get_details_object(self, action_id):
        if self.details_object is None:
            raise AttributeError(f'You must set "details_object=<Your Model Object> for {self}')
        return self.details_object.objects.get(action_id=action_id)

    def run(self, request):
        request_id = request.data.get('request_id')
        if request_id:
            log.debug(f'Found request_id {request_id} for user {request.user}')
            try:
                previous_action = Action.objects.get(request_id=request_id, creator=request.user)
                return Response(self.status_serializer_class(previous_action).data)
            except Action.DoesNotExist:
                pass
        return self.create(request)

    def introspect(self, request):
        """
        description = ActionProviderDescription(
        globus_auth_scope=config.our_scope,
        title="What Time Is It Right Now?",
        admin_contact="support@whattimeisrightnow.example",
        synchronous=False,
        input_schema=schema,
        api_version="1.0",
        subtitle=(
            "From the makers of Philbert: "
            "Another exciting promotional tie-in for whattimeisitrightnow.com"
        ),
        description="",
        keywords=["time", "whattimeisitnow", "productivity"],
        visible_to=["all_authenticated_users"],
        runnable_by=["all_authenticated_users"],
        administered_by=["support@whattimeisrightnow.example"],
        )
        """
        # Generate a path based on the standard automate URLs above
        patterns = [path(request.path, include(self.urls()))]
        generator = SchemaGenerator(patterns=patterns)
        return Response(generator.get_schema())

    def status(self, request, action_id=None):
        return self.retrieve(request, action_id)

    def release(self, request, action_id):
        log.debug('Calling Release')
        self.get_object().delete()
        return Response({'released': True})

    def cancel(self, request, action_id):
        log.debug('Calling Cancel')
        return Response({'error': 'This action cannot be canceled.'}, status=405)
