from __future__ import unicode_literals
import logging
import globus_sdk
import json
from minid_client import minid_client_api
from identifier_client.identifier_api import IdentifierClient
from django.conf import settings
from api.models import TokenStore

log = logging.getLogger(__name__)


def create_minid(filename, aws_bucket_filename, minid_title, user):
    checksum = minid_client_api.compute_checksum(filename)
    locations = ["https://s3.amazonaws.com/%s/%s" % (
                             settings.AWS_BUCKET_NAME,
                             aws_bucket_filename)]
    log.debug('Computed Minid Checksum.')
    token = TokenStore.get_id_token(user)
    ic = IdentifierClient('Identifier',
                          base_url='https://identifiers.globus.org/',
                          app_name='Concierge Service',
                          authorizer=globus_sdk.AccessTokenAuthorizer(token))
    log.debug('checksub: {}'.format(checksum))
    kwargs = {
          'namespace': settings.IDENTIFIER_NAMESPACE,
          'visible_to': json.dumps(['public']),
          'location': json.dumps(locations),
          'checksums': json.dumps([{
              'function': 'sha256',
              'value': checksum
          }]),
          'metadata': json.dumps({
              'Title': minid_title
          })
              }
    minid = ic.create_identifier(**kwargs)
    log.debug('Created new minid for user {}: {}'.format(user.username, minid))

    return minid
