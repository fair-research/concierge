import logging
import uuid
import urllib
from rest_framework import serializers
from rest_framework.exceptions import ValidationError

import api.models

log = logging.getLogger(__name__)


class GlobusURL(serializers.Field):
    """
    A valid Globus URL for which we can derive both an endpoint
    and a path. Can be used for a source or destination, as either
    a filename or a directory.
    * https://<globus_endpoint>.data.globus.org/foo/bar (gcs v4)
    * https://f8d036.eb38.dn.glob.us/home/jsmit/manifests (gcs v5)
    * https://<globus_endpoint>.e.globus.org/ (gcs v4 — petrel)
    * globus://<globus_endpoint>/foo/bar
    """
    GCS_V4_HTTP_SUFFIXES = ['.data.globus.org', '.e.globus.org']
    GCS_V5_HTTP_SUFFIXES = ['.dn.glob.us']
    PROTOCOLS = ['https', 'http', 'globus']

    def to_representation(self, value):
        return value

    def to_internal_value(self, data):
        purl = urllib.parse.urlparse(data)
        if not purl.netloc:
            log.debug('User specified Globus URL without protocol, '
                      'assuming http')
            purl = urllib.parse.urlparse(f'http://{data}')

        endpoint = None
        if purl.scheme in ['http', 'https', '']:
            gcs_v4_suffixes = [s for s in self.GCS_V4_HTTP_SUFFIXES
                               if purl.netloc.endswith(s)]
            if any(gcs_v4_suffixes):
                log.debug(f'Parsed GCS V4 suffix {gcs_v4_suffixes[0]}')
                endpoint = purl.netloc.replace(gcs_v4_suffixes[0], '')

            gcs_v5_suffixes = [s for s in self.GCS_V5_HTTP_SUFFIXES
                               if purl.netloc.endswith(s)]
            if any(gcs_v5_suffixes):
                raise ValidationError('GCS v5 HTTP Endpoints are not '
                                      'supported yet.')
        elif purl.scheme == 'globus':
            endpoint = purl.netloc
        else:
            raise ValidationError('Protocol must be one of: '
                                  f'{",".join(self.PROTOCOLS)} for {data}')

        if endpoint is None:
            raise ValidationError(f'Unable to parse Globus URL: {data}')

        try:
            uuid.UUID(endpoint)
        except ValueError:
            raise ValidationError('Globus Endpoint is not a UUID: '
                                  f'{data}')

        return {
            'endpoint': endpoint,
            'path': purl.path,
        }


class TransferSerializer(serializers.ModelSerializer):
    user = serializers.ReadOnlyField(source='user.username')

    class Meta:
        model = api.models.Transfer
        read_only_fields = ()
        exclude = ('id',)
