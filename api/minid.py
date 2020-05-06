from __future__ import unicode_literals
import logging
import globus_sdk
from minid import MinidClient
from api.models import TokenStore

log = logging.getLogger(__name__)


def load_minid_client(user):
    token = TokenStore.get_id_token(user)
    log.debug('Identifier user {}, has token: {}' .format(user, bool(token)))
    ac = globus_sdk.AccessTokenAuthorizer(token) if token else None
    return MinidClient(authorizer=ac)


def create_minid(user, filename, locations, metadata=None, test=True):
    mc = load_minid_client(user)
    checksums = [{
          'function': 'sha256',
          'value': MinidClient.compute_checksum(filename)
        }]
    minid = mc.register(checksums, title=filename, locations=locations,
                        test=test, metadata=metadata)
    return minid
