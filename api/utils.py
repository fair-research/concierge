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
import bagit
from bdbag import bdbag_api
from identifier_client.identifier_api import IdentifierClientError

from api.models import Bag, TokenStore
from api.exc import ConciergeException, ServiceAuthException
from api.minid import load_identifier_client
from api.auth import load_globus_access_token

log = logging.getLogger(__name__)
# When doing a GET request for binary files, load chunks in 1 kilobyte
# increments
HTTP_CHUNK_SIZE = 2**10


def validate_remote_files_manifest(remote_files_manifest, transfer_token):
    transfer_authorizer = globus_sdk.AccessTokenAuthorizer(transfer_token)
    tc = globus_sdk.TransferClient(authorizer=transfer_authorizer)

    new_manifest = []
    for record in remote_files_manifest:
        surl = urlsplit(record['url'])
        if surl.scheme not in settings.SUPPORTED_STAGING_PROTOCOLS:
            new_manifest.append(record)
            log.debug('Verification skipped record {} (non-globus)'.format(
                record['name']
            ))
            continue
        globus_endpoint = surl.netloc.replace(':', '')
        tc.endpoint_autoactivate(globus_endpoint)
        new_man = _walk_globus_path(tc, globus_endpoint, surl.path)
        new_manifest += new_man

    return new_manifest


def _walk_globus_path(client, globus_endpoint, path):
    """Walk the filesystem on the endpoint to find all of the files within
    a directory. Called recursively on all dirs. Returns a list of all files
    under the given path with the following format:
    {
        'filename': 'foo.txt',
        'url': gloubs:///car/bar/foo.txt,
        'size': 123456
    }
    """
    log.debug('Walking path to validate files: '
              '{}:{}'.format(globus_endpoint, path))
    ls_info = client.operation_ls(globus_endpoint, path=path)
    # Recursion base case, return if top level is file.
    if ls_info['DATA_TYPE'] == 'file':
        return [{
                'url': 'globus://{}:{}'.format(globus_endpoint,
                                               ls_info['path']),
                'filename': join(path, ls_info['path']),
                'size': ls_info['size']}]
    # Loop through all files in the 'ls', capture data, and recurse again if
    # we encounter a folder.
    files = []
    for file in ls_info['DATA']:
        if file['type'] == 'file':
            files.append({
                'url': 'globus://{}:{}'.format(globus_endpoint,
                                               join(path, file['name'])),
                'filename': file['name'],
                'size': file['size']})
        elif file['type'] == 'dir':
            files += _walk_globus_path(client, globus_endpoint,
                                       join(path, file['name']))
        else:
            log.warning('Encountered strange file type while validating path '
                        '"{}:{}" File data: {}'.format(globus_endpoint, path,
                                                       file))
            continue
    return files


def create_bag_archive(manifest, bag_metadata, ro_metadata):
    try:
        bag_name = join(settings.BAG_STAGING_DIR, str(uuid.uuid4()))
        remote_manifest_filename = join(settings.BAG_STAGING_DIR,
                                        str(uuid.uuid4()))

        with open(remote_manifest_filename, 'w') as f:
            f.write(json.dumps(manifest))

        os.mkdir(bag_name)
        bdbag_api.make_bag(bag_name,
                           metadata=bag_metadata,
                           ro_metadata=ro_metadata,
                           remote_file_manifest=remote_manifest_filename,
                           )
        bdbag_api.archive_bag(bag_name, settings.BAG_ARCHIVE_FORMAT)

        archive_name = '{}.{}'.format(bag_name, settings.BAG_ARCHIVE_FORMAT)
        os.remove(remote_manifest_filename)
        return archive_name
    except Exception as e:
        raise ConciergeException(str(e), code='bdbag_creation_error')


def upload_to_s3(filename, key):
    s3 = boto3.resource('s3', aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                        aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY)
    with open(filename, 'rb') as data:
        s3.Bucket(settings.AWS_BUCKET_NAME).upload_fileobj(
            data,
            key,
            ExtraArgs={'ACL': 'public-read'}
        )


def _resolve_minids_to_bags(bag_minids, user):
    bags = Bag.objects.filter(minid_id__in=bag_minids)
    bags = list(bags)
    if len(bags) != len(bag_minids):
        bad_bags = [b for b in bag_minids
                    if b not in [bg.minid_id for bg in bags]]
        for minid in bad_bags:
            try:
                ic = load_identifier_client()
                minid = ic.get_identifier(minid).data
                if not minid['location']:
                    raise ConciergeException({'error': 'Minid has no location '
                                             '{}'.format(minid)})
                loc = minid['location'][0]
                b = Bag.objects.create(user=user, minid_id=minid, location=loc)
                b.save()
                bags.append(b)
            except IdentifierClientError as ice:
                log.exception(ice)
                log.error('User {} unable to resolve minid data.'.format(user))
    return bags


def fetch_bags(minids, user):
    """Given a list of minid bag models, follow their location and
    fetch the data associated with them, if it doesn't already
    exist on the filesystem. Returns a list of bagit bag objects"""
    bags = _resolve_minids_to_bags(minids, user)
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


def get_transfer_token(user):
    return TokenStore.get_transfer_token(user) or \
           load_globus_access_token(user, 'transfer.api.globus.org')

def transfer_catalog(user, transfer_manifest, dest_endpoint, dest_prefix,
                     sync_level=settings.GLOBUS_DEFAULT_SYNC_LEVEL):
    task_ids = []
    transfer_token = get_transfer_token(user)
    transfer_authorizer = globus_sdk.AccessTokenAuthorizer(transfer_token)
    tc = globus_sdk.TransferClient(authorizer=transfer_authorizer)
    tc.endpoint_autoactivate(dest_endpoint)
    if not transfer_manifest:
        raise ValidationError('No valid data to transfer',
                              code='no_data')
    for globus_source_endpoint, data_list in transfer_manifest.items():
        log.debug('Starting transfer from {} to {}:{} containing {} files'
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
