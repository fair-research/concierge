import uuid

from api.serializers.manifest import TransferManifestSerializer

ep1 = f'{str(uuid.uuid1())}.data.globus.org'
ep2 = f'{str(uuid.uuid1())}.data.globus.org'


def test_valid_transfer_manifest():
    man = {
        'manifest': {
            'manifest_items': [
                {
                    'source_ref': f'{ep1}/share/godata/file1.txt',
                    'dest_path': 'file1.from_manifest.txt',
                    'checksum': {
                        'algorithm': 'md5',
                        'value': '5bbf5a52328e7439ae6e719dfe712200'
                    }
                },
                {
                    'source_ref': f'{ep1}/share/godata/',
                    'dest_path': 'my/godata/files'
                }
            ],
            'destination': f'{ep2}/files'
        }
    }

    serializer = TransferManifestSerializer(data=man)
    valid = serializer.is_valid()
    assert serializer.errors == {}
    assert valid is True


def test_empty_manifest_items():
    serializer = TransferManifestSerializer(data={
        'manifest': {
            'manifest_items': [],
            'destination': f'{ep2}/files',
        }
    })
    assert not serializer.is_valid()
    assert serializer.errors['manifest']['manifest_items']


def test_differing_sources():
    serializer = TransferManifestSerializer(data={
        'manifest': {
            'manifest_items': [
                {'source_ref': f'{ep1}/foo.txt', 'dest_path': 'foo.txt'},
                {'source_ref': f'{ep2}/bar.txt', 'dest_path': 'bar.txt'}
            ],
            'destination': f'{ep2}/files/',
        }
    })
    assert not serializer.is_valid()
    assert serializer.errors['manifest']['manifest_items']


def test_missing_destination():
    serializer = TransferManifestSerializer(data={
        'manifest': {
            'manifest_items': [
                {'source_ref': f'{ep1}/foo.txt', 'dest_path': 'foo.txt'}
            ]
        }
    })
    assert not serializer.is_valid()
    assert serializer.errors['manifest']['destination']


def test_missing_dest_path():
    serializer = TransferManifestSerializer(data={
        'manifest': {
            'manifest_items': [
                {'source_ref': f'{ep1}/foo.txt'},
            ],
            'destination': f'{ep2}/files/',
        }
    })
    assert not serializer.is_valid()
    assert serializer.errors['manifest']['manifest_items'][0]['dest_path']
