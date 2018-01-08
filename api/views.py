from __future__ import unicode_literals
from rest_framework import viewsets
from api.models import Bag, StageBag
from api.serializers import BagSerializer, StageBagSerializer
from api.auth import IsOwnerOrReadOnly


class BagViewSet(viewsets.ModelViewSet):
    permission_classes = (IsOwnerOrReadOnly,)
    queryset = Bag.objects.all()
    serializer_class = BagSerializer


class StageBagViewSet(viewsets.ModelViewSet):
    permission_classes = (IsOwnerOrReadOnly,)
    queryset = StageBag.objects.all()
    serializer_class = StageBagSerializer
