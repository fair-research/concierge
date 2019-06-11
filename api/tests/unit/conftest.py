import pytest
import os
import shutil
from unittest.mock import Mock

from api import utils, minid
from api.tests.unit.mocks import (TEST_BAG, MOCK_TOKENS,
                                  MOCK_IDENTIFIERS_GET_RESPONSE)
from api.models import TokenStore


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
    monkeypatch.setattr(utils, 'download_bag', Mock(return_value=testbag))


@pytest.fixture
def mock_identifiers_client(monkeypatch):
    mock_cli = Mock()
    data = Mock()
    data.data = MOCK_IDENTIFIERS_GET_RESPONSE
    get_identifier = Mock(return_value=data)
    mock_cli.get_identifier = get_identifier
    load_cli = Mock(return_value=mock_cli)
    monkeypatch.setattr(minid, 'load_identifiers_client', load_cli)
    return mock_cli


@pytest.fixture
@pytest.mark.django_db
def mock_user_bob(django_user_model):
    bob = django_user_model(username='bob')
    bob.save()
    ts = TokenStore(user=bob)
    ts.tokens = MOCK_TOKENS
    ts.save()
    return bob
