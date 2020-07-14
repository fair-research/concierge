from __future__ import unicode_literals
from django.urls import path, include
from rest_framework import routers, permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from api.views import BagViewSet, StageBagViewSet, logout


router = routers.DefaultRouter()

router.register(r'bags', BagViewSet, basename='bag')
router.register(r'stagebag', StageBagViewSet, basename='stagebag')

schema_view = get_schema_view(
    openapi.Info(
        title="Concierge Service API",
        default_version='v1',
        description="We handle your BDBags with care.",
        contact=openapi.Contact(email="support@globus.org"),
        license=openapi.License(name="Apache2"),
    ),
    public=True,
    permission_classes=(permissions.AllowAny,),
)

# Inlcude the schema view in our urls.
urlpatterns = [
    path('api/', include(router.urls)),
    path('', schema_view.with_ui('swagger', cache_timeout=0),
         name='schema-swagger-ui'),
    # Allows interactive dashboard login/logout
    path('', include('social_django.urls', namespace='social')),
    path('logout/', logout, name='logout')
]
