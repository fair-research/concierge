import os
from api import utils


def test_unpack_bag(testbag, scratch_space_dir):
    assert len(os.listdir(scratch_space_dir)) == 1
    utils.extract_bag(testbag)
    assert len(os.listdir(scratch_space_dir)) == 2


def test_fetch_bags(mock_download_returns_testbag, scratch_space_dir,
                    concierge_token, mock_minid_client):
    utils.fetch_bags(concierge_token, ['foo'])
    assert len(os.listdir(scratch_space_dir)) == 2


def test_create_unique_folder(scratch_space_dir):
    utils.create_unique_folder()
    assert len(os.listdir(scratch_space_dir)) == 1
    utils.create_unique_folder()
    assert len(os.listdir(scratch_space_dir)) == 2
