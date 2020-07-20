import logging
from rest_framework import serializers

import api.exc
import api.models

log = logging.getLogger(__name__)


class TransferSerializer(serializers.ModelSerializer):
    user = serializers.ReadOnlyField(source='user.username')

    class Meta:
        model = api.models.Transfer
        read_only_fields = ()
        exclude = ('id',)
