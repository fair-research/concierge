from rest_framework import viewsets
from api.models import Bag, StageBag
from api.serializers import BagSerializer, StageBagSerializer


class BagViewSet(viewsets.ModelViewSet):
    queryset = Bag.objects.all()
    serializer_class = BagSerializer


class StageBagViewSet(viewsets.ModelViewSet):
    queryset = StageBag.objects.all()
    serializer_class = StageBagSerializer
