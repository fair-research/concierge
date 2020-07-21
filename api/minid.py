from __future__ import unicode_literals
import logging
import globus_sdk
import minid

from django.conf import settings

log = logging.getLogger(__name__)


def load_minid_client(token_obj):
    m_token = token_obj.get_token(settings.MINID_SCOPE)
    authorizer = globus_sdk.AccessTokenAuthorizer(m_token)
    return minid.MinidClient(authorizer=authorizer)


def create_minid(user, filename, locations, metadata=None, test=True):
    mc = load_minid_client(user)
    checksums = [{
          'function': 'sha256',
          'value': minid.MinidClient.compute_checksum(filename)
        }]
    return mc.register(checksums, title=filename, locations=locations,
                       test=test, metadata=metadata)
