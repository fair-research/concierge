from __future__ import unicode_literals
from django.urls import path, include
from django.conf import settings
from rest_framework import routers, permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from api.views import (
    BagViewSet, StageBagViewSet, logout, BagManifestViewSet,
    TransferManifestViewSet,
)

router = routers.DefaultRouter()

router.register(r'bags', BagViewSet, basename='bag')
router.register(r'stagebag', StageBagViewSet, basename='stagebag')
router.register(r'transfer_manifest', TransferManifestViewSet,
                basename='transfer_manifest')

schema_view = get_schema_view(
    openapi.Info(
        title="Concierge Service API",
        default_version='v1',
        description=settings.SERVICE_DESCRIPTION,
        contact=openapi.Contact(email="support@globus.org"),
        license=openapi.License(name="Apache2"),
    ),
    public=True,
    permission_classes=(permissions.AllowAny,),
)

# Inlcude the schema view in our urls.
urlpatterns = [
    path('api/', include(router.urls)),
    path('api/bag_manifest/', BagManifestViewSet.as_view({'post': 'create'})),
    path('schema.json', schema_view.without_ui(cache_timeout=0), name='schema-json'),
    path('', schema_view.with_ui('swagger', cache_timeout=0),
         name='schema-swagger-ui'),
    # Allows interactive dashboard login/logout
    path('', include('social_django.urls', namespace='social')),
    path('logout/', logout, name='logout')
]
