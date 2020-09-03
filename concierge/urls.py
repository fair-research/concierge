from __future__ import unicode_literals
from django.urls import path, include
from django.conf import settings
from rest_framework import permissions, serializers
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from api.views import logout, ManifestViewSet, TransferViewSet, TransferManifestActionViewSet
from api.serializers.manifest import GlobusManifestSerializer, RemoteFileManifestSerializer, ManifestListSerializer

api = openapi.Info(
    title="Concierge Service API",
    default_version='v2',
    description=settings.SERVICE_DESCRIPTION,
    contact=openapi.Contact(email="support@globus.org"),
    license=openapi.License(name="Apache2"),
)

schema_view = get_schema_view(
    api,
    public=True,
    permission_classes=(permissions.AllowAny,),
)

manifests = [
    # List all manifests, agostic of type
    path('', ManifestViewSet.as_view({'get': 'list'}, serializer_class=ManifestListSerializer)),
    # GET/CREATE as Gloubs Manifest
    path('globus_manifest/',
         ManifestViewSet.as_view({'post': 'create'}, serializer_class=GlobusManifestSerializer)),
    path('<pk>/', ManifestViewSet.as_view({'get': 'retrieve',
                                           'delete': 'delete'}, serializer_class=serializers.Serializer)),
    # path('<pk>/', ManifestViewSet.as_view({'delete': 'delete'}, serializer_class=serializers.Serializer)),
    # path('<pk>/globus_manifest/',
    #      ManifestViewSet.as_view({'get': 'retrieve'}, serializer_class=GlobusManifestSerializer)),
    # GET/CREATE as remote file manifest
    path('remote_file_manifest/',
         ManifestViewSet.as_view({'post': 'create'}, serializer_class=RemoteFileManifestSerializer)),
    # path('<pk>/remote_file_manifest/',
    #      ManifestViewSet.as_view({'get': 'retrieve'}, serializer_class=RemoteFileManifestSerializer)),
    # path('<pk>/bdbag/',
    #      ManifestViewSet.as_view({'get': 'retrieve'}, serializer_class=serializers.Serializer)),
    path('<manifest_uuid>/transfer/', TransferViewSet.as_view({'post': 'create'}),),
    path('<manifest_uuid>/transfer/<transfer_manifest_uuid>/',
         TransferViewSet.as_view({'get': 'retrieve'}, serializer_class=serializers.Serializer)),
    path('transfer/',
         TransferViewSet.as_view({'get': 'list'}, serializer_class=serializers.Serializer)),
]

# Include the schema view in our urls.
urlpatterns = [
    path('api/manifest/', include(manifests)),
    path('api/automate/transfer/',
         include(TransferManifestActionViewSet.urls())),
    path('schema.json', schema_view.without_ui(cache_timeout=0), name='schema-json'),
    path('', schema_view.with_ui('swagger', cache_timeout=0),
         name='schema-swagger-ui'),
    # Allows interactive dashboard login/logout
    path('', include('social_django.urls', namespace='social')),
    path('logout/', logout, name='logout'),
]
