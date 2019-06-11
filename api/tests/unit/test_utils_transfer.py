from api import utils


def test_catalog_transfer_manifest_no_bag_dirs(testbag, scratch_space_dir):
    bagit_bag = utils.extract_bag(testbag)
    catalog, err_catalog = utils.catalog_transfer_manifest([bagit_bag],
                                                           bag_dirs=False)
    assert err_catalog == {}
    assert isinstance(catalog, dict)
    print(list(catalog.values()))
    for src, dest in list(catalog.values())[0]:
        assert src == dest


def test_catalog_transfer_manifest_bag_dirs(testbag, scratch_space_dir):
    bagit_bag = utils.extract_bag(testbag)
    catalog, err_catalog = utils.catalog_transfer_manifest([bagit_bag],
                                                           bag_dirs=True)
    assert err_catalog == {}
    assert isinstance(catalog, dict)
    print(list(catalog.values()))
    for src, dest in list(catalog.values())[0]:
        assert src != dest
