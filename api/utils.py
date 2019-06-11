from __future__ import unicode_literals
import datetime
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
from identifiers_client.identifiers_api import IdentifierClientError

from api.models import Bag
from api.exc import NoDataToTransfer, ConciergeException
from api import minid
from api.auth import get_transfer_token

log = logging.getLogger(__name__)
# When doing a GET request for binary files, load chunks in 1 kilobyte
# increments
HTTP_CHUNK_SIZE = 2**10


def load_transfer_client(user):
    transfer_token = get_transfer_token(user)
    transfer_authorizer = globus_sdk.AccessTokenAuthorizer(transfer_token)
    return globus_sdk.TransferClient(authorizer=transfer_authorizer)


def verify_remote_file_manifest(user, remote_file_manifest):
    tc = load_transfer_client(user)

    new_manifest = []
    for record in remote_file_manifest:
        surl = urlsplit(record['url'])
        if surl.scheme not in settings.SUPPORTED_STAGING_PROTOCOLS:
            new_manifest.append(record)
            log.debug('Verification skipped record {} (non-globus)'.format(
                record['filename']
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


def create_unique_folder():
    name = join(settings.BAG_STAGING_DIR, str(uuid.uuid4()))
    while os.path.exists(name):
        name = join(settings.BAG_STAGING_DIR, str(uuid.uuid4()))
    os.mkdir(name)
    return name


def create_bag_archive(manifest, bag_metadata, ro_metadata, name):
    try:
        if not name:
            now = datetime.datetime.now()
            name = 'Concierge-Bag-{}'.format(now.strftime('%B-%d-%Y'))

        base_folder = create_unique_folder()
        bag_name = join(base_folder, name)
        os.mkdir(bag_name)

        remote_manifest_filename = join(base_folder, str(uuid.uuid4()))
        with open(remote_manifest_filename, 'w') as f:
            f.write(json.dumps(manifest))

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


def get_s3_key(filename):
    return os.path.join(
        settings.AWS_FOLDER,
        os.path.basename(os.path.dirname(filename)),
        os.path.basename(filename)
    )


def upload_to_s3(filename):
    key = get_s3_key(filename)
    s3 = boto3.resource('s3', aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                        aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY)
    with open(filename, 'rb') as data:
        s3.Bucket(settings.AWS_BUCKET_NAME).upload_fileobj(
            data,
            key,
            ExtraArgs={'ACL': 'public-read'}
        )
    loc = 'https://s3.amazonaws.com/{}/{}'.format(settings.AWS_BUCKET_NAME,
                                                  key)
    return loc


def _resolve_minids_to_bags(user, minids):
    bags = Bag.objects.filter(minid__in=minids)
    bags = list(bags)
    if len(bags) != len(minids):
        bad_bags = [b for b in minids
                    if b not in [bg.minid for bg in bags]]
        for bag_minid in bad_bags:
            try:
                ic = minid.load_identifiers_client(user)
                minid_resp = ic.get_identifier(bag_minid).data
                if not minid_resp['location']:
                    raise ConciergeException({'error': 'Minid has no location '
                                             '{}'.format(minid)})
                loc = minid_resp['location'][0]
                b = Bag.objects.create(user=user, minid=minid, location=loc)
                b.save()
                bags.append(b)
            except IdentifierClientError as ice:
                log.exception(ice)
                log.error('User {} unable to resolve minid data.'.format(user))
    return bags


def download_bag(url):
    """Given a URL, download an archived bag and return the path where it has
    been downloaded."""
    bag_name = os.path.basename(url)
    local_bag_archive = os.path.join(create_unique_folder(), bag_name)
    r = requests.get(url, stream=True)
    if r.status_code == 200:
        with open(local_bag_archive, 'wb') as f:
            for chunk in r.iter_content(HTTP_CHUNK_SIZE):
                f.write(chunk)
    return local_bag_archive


def extract_bag(local_bag_archive_path):
    """Unachive a local bdbag, and return the local path. Places the unachived
    bag next to the archived one, minus the archived bag's extension."""
    local_bag, _ = os.path.splitext(local_bag_archive_path)
    bdbag_api.extract_bag(local_bag_archive_path, os.path.dirname(local_bag))
    bagit_bag = bagit.Bag(local_bag)
    return bagit_bag


def fetch_bags(user, minids):
    """Given a list of minid bag models, follow their location and
    fetch the data associated with them, if it doesn't already
    exist on the filesystem. Returns a list of bagit bag objects"""
    bags = _resolve_minids_to_bags(user, minids)
    return [extract_bag(download_bag(bag.location)) for bag in bags]


def catalog_transfer_manifest(bagit_bags, bag_dirs=False):
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
            payload = endpoint_catalog.get(surl.netloc, [])
            if bag_dirs:
                bag_name = os.path.basename(bag.path)
                payload.append((surl.path, os.path.join(bag_name, filename)))
            else:
                payload.append((surl.path, surl.path))
            endpoint_catalog[surl.netloc] = payload
    if not endpoint_catalog:
        raise NoDataToTransfer(f'Unable to transfer {error_catalog}')
    return endpoint_catalog, error_catalog


def transfer_catalog(user, transfer_manifest, dest_endpoint, dest_prefix,
                     label=None,
                     sync_level=settings.GLOBUS_DEFAULT_SYNC_LEVEL):
    task_ids = []
    tc = load_transfer_client(user)
    tc.endpoint_autoactivate(dest_endpoint)
    if not transfer_manifest:
        raise ConciergeException('No valid data to transfer',
                                 code='no_data')
    label = label or settings.SERVICE_NAME
    for globus_source_endpoint, data_list in transfer_manifest.items():
        log.debug('{} starting transfer from {} to {}:{} containing {} files'
                  .format(user, globus_source_endpoint, dest_endpoint,
                          dest_prefix,
                          len(data_list)))
        tc.endpoint_autoactivate(globus_source_endpoint)
        tdata = globus_sdk.TransferData(tc,
                                        globus_source_endpoint,
                                        dest_endpoint,
                                        label=label,
                                        sync_level=sync_level
                                        )
        for source, destination in data_list:
            tdata.add_item(source, os.path.join(dest_prefix, destination))
        task = tc.submit_transfer(tdata)
        task_ids.append(task['task_id'])
    return task_ids
