from __future__ import unicode_literals
from django.conf.urls import url, include
from rest_framework import routers
from rest_framework.schemas import get_schema_view
from rest_framework_swagger.renderers import SwaggerUIRenderer, OpenAPIRenderer
from api.views import BagViewSet, StageBagViewSet


router = routers.DefaultRouter()
router.register(r'bags', BagViewSet)
router.register(r'stagebag', StageBagViewSet)

schema_view = get_schema_view(title='Concierge API',
                              renderer_classes=[
                                  OpenAPIRenderer,
                                  SwaggerUIRenderer
                              ]
                              )

# Inlcude the schema view in our urls.
urlpatterns = [
    url(r'^api/', include(router.urls)),
    url(r'^', schema_view, name="docs"),
]
