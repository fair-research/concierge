from __future__ import unicode_literals
import os
from os.path import join
import json
import uuid
import requests
import logging
import boto3
import globus_sdk
from six.moves.urllib_parse import urlsplit
from django.conf import settings
from minid_client import minid_client_api
import bagit
from bdbag import bdbag_api

from api.models import Bag
from api.exc import ConciergeException

log = logging.getLogger(__name__)
# When doing a GET request for binary files, load chunks in 1 kilobyte
# increments
HTTP_CHUNK_SIZE = 2**10


def create_bag_archive(metadata, bag_algorithms=('md5', 'sha256'),
                       **bag_metadata):
    bag_name = join(settings.BAG_STAGING_DIR, str(uuid.uuid4()))
    remote_manifest_filename = join(settings.BAG_STAGING_DIR,
                                    str(uuid.uuid4()))

    remote_manifest_formatted = _format_remote_file_manifest(metadata,
                                                             bag_algorithms)
    with open(remote_manifest_filename, 'w') as f:
        f.write(json.dumps(remote_manifest_formatted))

    os.mkdir(bag_name)
    bdbag_api.make_bag(bag_name,
                       algs=bag_algorithms,
                       metadata=dict(bag_metadata),
                       remote_file_manifest=remote_manifest_filename,
                       )
    bdbag_api.archive_bag(bag_name, settings.BAG_ARCHIVE_FORMAT)

    archive_name = '{}.{}'.format(bag_name, settings.BAG_ARCHIVE_FORMAT)
    os.remove(remote_manifest_filename)
    return archive_name


def _format_remote_file_manifest(manifest, algorithms):
    for file in manifest:
        # If hash doesn't exist, add the empty string for each algorithm entry
        algs = {alg: file.get(alg, '') for alg in algorithms}
        file.update(algs)
        file['length'] = file.get('length', 0)
    return manifest


def _register_minid(filename, aws_bucket_filename,
                    minid_email, minid_title, minid_test, globus_auth_token):
    checksum = minid_client_api.compute_checksum(filename)
    locations = ["https://s3.amazonaws.com/%s/%s" % (
                             settings.AWS_BUCKET_NAME,
                             aws_bucket_filename
                        )]
    return minid_client_api.\
        register_entity(
                        settings.MINID_SERVER,
                        checksum,
                        minid_email,
                        None,
                        #settings.MINID_SERVICE_TOKEN,
                        locations,
                        minid_title,
                        minid_test,
                        globus_auth_token=globus_auth_token
                        )


def create_minid(filename, aws_bucket_filename, minid_user,
                 minid_email, minid_title, minid_test, globus_auth_token):
    try:

        minid = _register_minid(filename, aws_bucket_filename,
                                minid_email, minid_title, minid_test,
                                globus_auth_token=globus_auth_token)

    except minid_client_api.MinidAPIException as minid_exc:
        if minid_exc.type == 'UserNotRegistered':
            minid_client_api.register_user(settings.MINID_SERVER,
                                           minid_email,
                                           minid_user,
                                           '',  # ORCID is not currently used
                                           globus_auth_token=globus_auth_token
                                           )
            minid = _register_minid(filename, aws_bucket_filename,
                                    minid_email, minid_title, minid_test,
                                    globus_auth_token=globus_auth_token)
        else:
            raise
    return minid


def upload_to_s3(filename, key):
    s3 = boto3.resource('s3', aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                        aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY)
    with open(filename, 'rb') as data:
        s3.Bucket(settings.AWS_BUCKET_NAME).upload_fileobj(
            data,
            key,
            ExtraArgs={'ACL': 'public-read'}
        )


def _resolve_minids_to_bags(bag_minids):
    bags = Bag.objects.filter(
        minid_id__in=bag_minids)
    if len(bags) != len(bag_minids):
        bad_bags = [b for b in bag_minids
                    if b not in [bg.minid_id for bg in bags]]
        raise ConciergeException({
            'error': 'Bags not created with the concierge service are not '
                     'supported yet: {}'.format(','.join(bad_bags)),
            'bags': bad_bags
        })
    return bags


def fetch_bags(minids):
    """Given a list of minid bag models, follow their location and
    fetch the data associated with them, if it doesn't already
    exist on the filesystem. Returns a list of bagit bag objects"""
    bags = _resolve_minids_to_bags(minids)
    bagit_bags = []
    for bag in bags:
        bag_name = os.path.basename(bag.location)
        local_bag_archive = os.path.join(settings.BAG_STAGING_DIR, bag_name)
        if not os.path.exists(local_bag_archive):
            r = requests.get(bag.location, stream=True)
            if r.status_code == 200:
                with open(local_bag_archive, 'wb') as f:
                    for chunk in r.iter_content(HTTP_CHUNK_SIZE):
                        f.write(chunk)
        local_bag, _ = os.path.splitext(local_bag_archive)
        if not os.path.exists(local_bag):
            bdbag_api.extract_bag(local_bag_archive,
                                  os.path.dirname(local_bag))
        bagit_bag = bagit.Bag(local_bag)
        bagit_bags.append(bagit_bag)
    return bagit_bags


def catalog_transfer_manifest(bagit_bags):
    """Given a list of bagit bags, return a catalogue of all files
    organized by endpoint, and the list of files that can't be
    transferred.

    Returns tuple: ( catalog_dict, error_catalog_dict )
    Example: (
        {
            '<Endpoint UUID>': ['filename1', 'filename2'],
            '<Endpoint UUID>': ['filename3', 'filename4']
        },
        {
            'unsupported_protocol': ['filename5', 'filename6']
        }
    )
    """
    endpoint_catalog = {}
    error_catalog = {}
    for bag in bagit_bags:
        for url, size, filename in bag.fetch_entries():
            surl = urlsplit(url)
            if surl.scheme not in settings.SUPPORTED_STAGING_PROTOCOLS:
                prot_errors = error_catalog.get('unsupported_protocol', [])
                prot_errors.append(url)
                error_catalog['unsupported_protocol'] = prot_errors
                continue
            globus_endpoint = surl.netloc.replace(':', '')
            payload = endpoint_catalog.get(globus_endpoint, [])
            payload.append(surl.path)
            endpoint_catalog[globus_endpoint] = payload
    if not endpoint_catalog:
        raise ConciergeException({
            'error': 'No valid data to transfer',
            'error_catalog': error_catalog
        })
    return endpoint_catalog, error_catalog


def transfer_catalog(transfer_manifest, dest_endpoint,
                     dest_prefix, transfer_token,
                     sync_level=settings.GLOBUS_DEFAULT_SYNC_LEVEL):
    task_ids = []
    transfer_authorizer = globus_sdk.AccessTokenAuthorizer(transfer_token)
    tc = globus_sdk.TransferClient(authorizer=transfer_authorizer)
    tc.endpoint_autoactivate(dest_endpoint)
    if not transfer_manifest:
        raise ValidationError('No valid data to transfer',
                              code='no_data')
    for globus_source_endpoint, data_list in transfer_manifest.items():
        log.debug('Starting transfer from {} to {}:{} contaiting {} files'
                  .format(globus_source_endpoint, dest_endpoint, dest_prefix,
                          len(data_list)))
        tc.endpoint_autoactivate(globus_source_endpoint)
        tdata = globus_sdk.TransferData(tc,
                                        globus_source_endpoint,
                                        dest_endpoint,
                                        label=settings.SERVICE_NAME,
                                        sync_level=sync_level
                                        )
        for item in data_list:
            tdata.add_item(
                item,
                '/'.join((dest_prefix, item))
            )
        task = tc.submit_transfer(tdata)
        task_ids.append(task['task_id'])
    return task_ids
