from rest_framework import viewsets
from api.models import Bag
from api.serializers import BagSerializer


class BagViewSet(viewsets.ModelViewSet):
    queryset = Bag.objects.all()
    serializer_class = BagSerializer
