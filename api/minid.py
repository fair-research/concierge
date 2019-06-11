from __future__ import unicode_literals
import logging
import globus_sdk
from minid_client import minid_client_api
from identifiers_client.identifiers_api import IdentifierClient
from django.conf import settings
from api.models import TokenStore

log = logging.getLogger(__name__)


def load_identifiers_client(user):
    token = TokenStore.get_id_token(user)
    log.debug('Identifier user {}, has token: {}' .format(user, bool(token)))
    ac = globus_sdk.AccessTokenAuthorizer(token) if token else None
    cfg = {'app_name': 'Concierge Service', 'authorizer': ac}
    return IdentifierClient(**cfg)


def create_minid(user, filename, locations, metadata={},
                 visible_to=('public',), test=True):
    checksum = minid_client_api.compute_checksum(filename)
    ic = load_identifiers_client(user)
    log.debug('checksum: {}'.format(checksum))
    namespace = (settings.TEST_IDENTIFIER_NAMESPACE
                 if test else settings.IDENTIFIER_NAMESPACE)
    log.debug('Test is {}, using namespace {}'.format(test, namespace))

    kwargs = {
        'namespace': namespace,
        'visible_to': visible_to,
        'location': locations,
        'checksums': [{
          'function': 'sha256',
          'value': checksum
        }],
        'metadata': metadata
    }
    minid = ic.create_identifier(**kwargs)
    log.debug('Created new minid for user {}: {}'.format(user.username, minid))

    return minid
