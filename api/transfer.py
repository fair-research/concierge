import os
import logging
from django.conf import settings
import globus_sdk

from api.exc import GlobusTransferException

log = logging.getLogger(__name__)


def get_transfer_client(ctoken_obj):
    """
    Get a transfer client from a ConciergeToken (request.auth obj)
    """
    transfer_token = ctoken_obj.get_token(settings.TRANSFER_SCOPE)
    transfer_authorizer = globus_sdk.AccessTokenAuthorizer(transfer_token)
    return globus_sdk.TransferClient(authorizer=transfer_authorizer)


def submit_transfer(auth, source_endpoint, destination_endpoint, data,
                    **kwargs):
    """
    transfer kwargs:
    label="Manifest Service Request xxxx-yy-zzzz",
    verify_checksum=True,
    notify_on_succeeded=False,
    notify_on_failed=False,
    notify_on_inactive=False,
    submission_id=submission_id
    """
    try:
        tc = get_transfer_client(auth)
        # tc.endpoint_autoactivate(source_endpoint)
        # tc.endpoint_autoactivate(destination_endpoint)
        tdata = globus_sdk.TransferData(tc, source_endpoint,
                                        destination_endpoint, **kwargs)
        for src, dest, is_dir, algorithm, checksum in data:
            if is_dir is True:
                tdata.add_item(src, dest, recursive=True)
            else:
                tdata.add_item(src, dest, external_checksum=checksum,
                               checksum_algorithm=algorithm)
        return tc.submit_transfer(tdata).data
    except globus_sdk.exc.TransferAPIError as tapie:
        # Service Unavailable (503) if Globus Screws up, otherwise assume
        # the user screwed up with a 400
        status_code = 503 if tapie.http_status >= 500 else 400
        if status_code == 503:
            log.critical('Upstream Globus Transfer error!')
            log.exception(tapie)
        raise GlobusTransferException(tapie.message,
                                      status_code=status_code, code=tapie.code)


def get_task(auth, task_id):
    return get_tasks(auth, [task_id])[0]


def get_tasks(auth, task_ids):
    tc = get_transfer_client(auth)
    return [tc.get_task(task_id) for task_id in task_ids]


def transfer_manifest(auth, globus_manifest, destination):
    """
    Submit a validated Globus Manifest. This is intended to be called via
    a serializer after validation has been completed.
    :param auth: request.auth object which should be a ConciergeToken obj
    :param globus_manifest: api.serializers.manifest.ManifestSerializer
    :return:
    """
    transfer_kwargs = {}
    manifest_items = globus_manifest['manifest_items']

    # Activate all endpoints. There may be many source endpoints
    source_eps = {m['source_ref']['endpoint'] for m in manifest_items}
    tc = get_transfer_client(auth)
    for ep in set(list(source_eps) + [destination['endpoint']]):
        log.debug(f'Auto-activating Globus endpoint: {ep}')
        try:
            tc.endpoint_autoactivate(ep)
        except globus_sdk.exc.TransferAPIError as tapie:
            raise GlobusTransferException(f'Failed to auto-activate endpoint {ep}',
                                          status_code=400, code=tapie.code)

    # Collect all files and start the transfer
    transfer_data = dict()
    for item in manifest_items:
        endpoint = item['source_ref']['endpoint']
        if not transfer_data.get(endpoint):
            transfer_data[endpoint] = globus_sdk.TransferData(
                tc, endpoint, destination['endpoint'], **transfer_kwargs
            )
        src = item['source_ref']['path']
        dest = os.path.join(destination['path'], item['dest_path'])
        is_dir = src.endswith('/')
        if is_dir:
            transfer_data[endpoint].add_item(src, dest, recursive=True)
        # @HACK -- Using checksums at this point does not account for endpoints which do not
        # support the given algorithm. This is a HUGE problem for sha256, which currently
        # fails for any endpoint (and I'm not really sure why)
        # Until we can properly fall back on md5 or no checksum, this should be disabled, as
        # it effectively prevents transfers for unsupported checksums.
        elif item.get('checksum') and False:
            log.debug(item['checksum'])
            transfer_data[endpoint].add_item(src, dest,
                                             external_checksum=item['checksum']['value'],
                                             checksum_algorithm=item['checksum']['algorithm'])
        else:
            transfer_data[endpoint].add_item(src, dest)

    transfers = []
    for transfer_data in transfer_data.values():
        try:
            log.debug('Submitting Transfer')
            transfers.append(tc.submit_transfer(transfer_data).data)
        except globus_sdk.exc.TransferAPIError as tapie:
            # Service Unavailable (503) if Globus Screws up, otherwise assume
            # the user screwed up with a 400
            status_code = 503 if tapie.http_status >= 500 else 400
            if status_code == 503:
                log.critical('Upstream Globus Transfer error!')
                log.exception(tapie)
            raise GlobusTransferException(tapie.message,
                                          status_code=status_code, code=tapie.code)
    log.debug('All transfers submitted successfully')
    return transfers
