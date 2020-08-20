import os
import json
import logging

from django.conf import settings
import api.s3

log = logging.getLogger(__name__)

# def download_bag(url):
#     """Given a URL, download an archived bag and return the path where it has
#     been downloaded."""
#     bag_name = os.path.basename(url)
#     local_bag_archive = os.path.join(create_unique_folder(), bag_name)
#     r = requests.get(url, stream=True)
#     if r.status_code == 200:
#         with open(local_bag_archive, 'wb') as f:
#             for chunk in r.iter_content(HTTP_CHUNK_SIZE):
#                 f.write(chunk)
#     return local_bag_archive
#
#
# def extract_bag(local_bag_archive_path):
#     """Unachive a local bdbag, and return the local path. Places the unachived
#     bag next to the archived one, minus the archived bag's extension."""
#     local_bag, _ = os.path.splitext(local_bag_archive_path)
#     bdbag_api.extract_bag(local_bag_archive_path, os.path.dirname(local_bag))
#     bagit_bag = bagit.Bag(local_bag)
#     return bagit_bag


def download_manifest(url):
    """Given a URL, download an archived bag and return the path where it has
    been downloaded."""
    # dirname = os.path.join(settings.BAG_STAGING_DIR,
    #                        os.path.basename(os.path.dirname(url)))
    # local_archive = os.path.join(settings.BAG_STAGING_DIR, os.path.basename(url))
    # if not os.path.exists(dirname):
    #     os.mkdir(dirname)
    # r = requests.get(url, stream=True)
    # if r.status_code == 200:
    #     log.debug('Downloaded manifest to {}'.format(local_archive))
    #     with open(local_archive, 'wb') as f:
    #         for chunk in r.iter_content(HTTP_CHUNK_SIZE):
    #             f.write(chunk)
    # return local_archive


def rfm_to_gm(remote_file_manifest):
    manifest = []
    for rfm in remote_file_manifest:
        hashes = [{'algorithm': k, 'value': v} for k, v in rfm.items()
                  if k in settings.SUPPORTED_CHECKSUMS]
        precedence = ['sha512', 'sha256', 'sha1', 'md5']
        hashes.sort(key=lambda x: precedence.index(x['algorithm']))
        ent = {'source_ref': rfm['url'], 'dest_path': rfm['filename']}
        if hashes:
            ent['checksum'] = hashes[0]
        manifest.append(ent)
    return manifest


def gm_to_rfm(manifest_items):

    rfm = []
    for man_item in manifest_items:
        rfme = {'url': man_item['source_ref'],
                'length': 0,
                'filename': man_item['dest_path']}
        if man_item.get('checksum'):
            rfme[man_item['checksum']['algorithm']] = man_item['checksum']['value']
        rfm.append(rfme)
    return rfm


def get_globus_manifest(key):
    return rfm_to_gm(get_remote_file_manifest(str(key)))


# def get_remote_file_manifest(location):
#     bag = extract_bag(download_manifest(location))
#     hashes = {fname: fhashes
#               for fname, fhashes in bag.entries.items()
#               if fname.startswith('data/')}
#     # from pprint import pprint
#     # pprint(hashes)
#     entries = []
#     for url, size, filename in bag.fetch_entries():
#         purl = urllib.parse.urlparse(url)
#         gurl = urllib.parse.urlunparse((purl.scheme, purl.netloc,
#                                         purl.path.lstrip('/data'), '', '', ''))
#         gfilename = filename.lstrip('/data')
#         entry = {'url': gurl, 'filename': gfilename, 'length': size}
#         entry.update(hashes.get(filename, {}))
#         entries.append(entry)
#     return entries

def get_remote_file_manifest(key):
    local_file = api.s3.get_local_file(str(key))
    if os.path.exists(local_file):
        log.info(f'Using Cached local resource {key}')
    else:
        log.warning('Downloads are not ever cleared! Disk space may run out one day!')
        local_file = api.s3.download(str(key))
    with open(local_file) as f:
        return json.load(f)['remote_file_manifest']


def upload_remote_file_manifest(key, remote_file_manifest):
    data = {'remote_file_manifest': remote_file_manifest}
    filename = os.path.join(settings.BAG_STAGING_DIR, str(key))
    with open(filename, 'w') as f:
        f.write(json.dumps(data))
    return api.s3.upload(filename)
