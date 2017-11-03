from django.conf.urls import url, include
from rest_framework import routers
from rest_framework.schemas import get_schema_view
from rest_framework_swagger.renderers import SwaggerUIRenderer, OpenAPIRenderer
from api.views import BagViewSet


router = routers.DefaultRouter()
router.register(r'bags', BagViewSet)

schema_view = get_schema_view(title='Bag API', renderer_classes=[OpenAPIRenderer, SwaggerUIRenderer])

# Inlcude the schema view in our urls.
urlpatterns = [
    url(r'^', schema_view, name="docs"),
    url(r'^api/', include(router.urls)),
]