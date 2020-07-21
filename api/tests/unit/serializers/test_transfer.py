import uuid
import pytest

from rest_framework.exceptions import ValidationError
from api.serializers.transfer import GlobusURL


@pytest.mark.parametrize('globus_url', [
    # Manifests GCS V4 Endpoints
    f'http://{str(uuid.uuid1())}.data.globus.org/foo.txt',
    f'{str(uuid.uuid1())}.data.globus.org/foo.txt',
    f'http://{str(uuid.uuid1())}.data.globus.org',
    f'https://{str(uuid.uuid1())}.data.globus.org/foo.txt',
    # Petrel GCS V4 Endpoints
    f'http://{str(uuid.uuid1())}.e.globus.org/foo.txt',
    f'{str(uuid.uuid1())}.e.globus.org/foo.txt',
    f'http://{str(uuid.uuid1())}.e.globus.org',
    f'https://{str(uuid.uuid1())}.e.globus.org/foo.txt',
    # Globus Protocol
    f'globus://{str(uuid.uuid1())}/foo.txt',
])
def test_valid_globus_urls(globus_url):
    url_components = list(GlobusURL().to_internal_value(globus_url).keys())
    assert url_components == ['endpoint', 'path']


@pytest.mark.parametrize('globus_url', [
    # No endpoint
    f'http://example.com',
    f'globus://example.com/foo.txt',
    # Wrong protocol
    f'ftp://{str(uuid.uuid1())}/foo.txt',
    # Manifests GCS V5 Endpoints (not supported yet)
    f'http://{str(uuid.uuid1())}.dn.glob.us/foo.txt',
    f'https://{str(uuid.uuid1())}.dn.glob.us/foo.txt',
    f'{str(uuid.uuid1())}.dn.glob.us/foo.txt',
    # Random user junk we should probably expect anyways
    f'A random wild string appeared!',
])
def test_invalid_globus_urls(globus_url):
    with pytest.raises(ValidationError):
        GlobusURL().to_internal_value(globus_url)
