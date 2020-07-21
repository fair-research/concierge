import pytest
import os
import shutil
import uuid
import time
import minid
import json
from unittest.mock import Mock

from rest_framework.test import APIClient
from social_django.models import UserSocialAuth

import api.utils
import api.auth
from api.tests.unit.mocks import TEST_BAG, MINID_RESPONSE
from api.models import ConciergeToken


TEST_FOLDER = '/tmp/concierge_unit_tests/'


@pytest.fixture
def scratch_space_dir(settings):
    settings.BAG_STAGING_DIR = TEST_FOLDER
    if os.path.exists(TEST_FOLDER):
        shutil.rmtree(TEST_FOLDER)
    os.mkdir(TEST_FOLDER)
    return TEST_FOLDER


@pytest.fixture
def testbag(scratch_space_dir):
    testbag = os.path.join(scratch_space_dir, os.path.basename(TEST_BAG))
    shutil.copyfile(TEST_BAG, testbag)
    return testbag


@pytest.fixture
def mock_download_returns_testbag(monkeypatch, testbag):
    monkeypatch.setattr(api.utils, 'download_bag', Mock(return_value=testbag))


@pytest.fixture
def globus_response():
    class MockGlobusResponse():
        def __init__(self, data):
            self.data = data
    return MockGlobusResponse


@pytest.fixture
def mock_minid_client(monkeypatch, globus_response):
    mc_inst = Mock()
    mc_inst.check.return_value = globus_response(MINID_RESPONSE)
    monkeypatch.setattr(minid, 'MinidClient', Mock(return_value=mc_inst))
    return minid.MinidClient


@pytest.fixture
def dependent_tokens(settings):
    return {
      settings.MINID_SCOPE: {
        'access_token': 'mock_minid_access_token'
      },
      settings.TRANSFER_SCOPE: {
        'access_token': 'mock_transfer_access_token'
      }
    }


@pytest.fixture
def mock_auth_client(monkeypatch):
    monkeypatch.setattr(api.auth, 'get_auth_client', Mock())
    return api.auth.get_auth_client()


@pytest.fixture
@pytest.mark.django_db
def mock_user(django_user_model):
    bob = django_user_model(username='bob@globus.org')
    bob.save()
    usa = UserSocialAuth(uid=uuid.uuid1(), provider='globus', user=bob)
    usa.save()
    return bob


@pytest.fixture
def api_cli(concierge_token):
    """returns an Authenticated API Client."""
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION=f'Bearer {concierge_token.id}')
    return client


@pytest.fixture
@pytest.mark.django_db
def concierge_token(mock_user, dependent_tokens, settings):
    now = time.time()
    expires_at = 60 * 60 * 24 + now
    # We'll by default set last introspection to now, which simulates the
    # user having previously made a call with this token that triggered an
    # introspection. That means ALL test API calls with this token will be
    # cached and will never attempt to introspect.
    ts = ConciergeToken(id='mock_concierge_token', user=mock_user,
                        issued_at=now, expires_at=expires_at,
                        last_introspection=now, scope=settings.CONCIERGE_SCOPE)
    ts.dependent_tokens_cache = json.dumps(dependent_tokens, indent=2)
    ts.save()
    return ts
