import os
import json
import uuid
import boto3
from minid_client import minid_client_api
from bdbag import bdbag_api

from app import app

def create_bag_archive(metadata):
    bag_name = "/tmp/bag_tmp/%s" % str(uuid.uuid4())
    metadata_file = "/tmp/bag_tmp/%s" % str(uuid.uuid4())
    with open(metadata_file, 'w') as f:
        f.write(json.dumps(metadata))

    os.mkdir(bag_name)
    bdbag_api.make_bag(bag_name,
                   algs=['md5', 'sha256'],
                   metadata={'Creator-Name': 'Encode2BDBag Service'},
                   remote_file_manifest=metadata_file
                   )
    bdbag_api.archive_bag(bag_name, app.config['BAG_ARCHIVE_FORMAT'])

    archive_name = '{}.{}'.format(bag_name, app.config['BAG_ARCHIVE_FORMAT'])
    bdbag_api.revert_bag(bag_name)
    os.remove(metadata_file)
    return archive_name


def _register_minid(filename, aws_bucket_filename, minid_email, minid_title, minid_test):
    checksum = minid_client_api.compute_checksum(filename)
    return minid_client_api.register_entity(app.config['MINID_SERVER'],
                                         checksum,
                                         minid_email,
                                         app.config['MINID_SERVICE_TOKEN'],
                                         ["https://s3.amazonaws.com/%s/%s" % (app.config['BUCKET_NAME'], aws_bucket_filename)],
                                         minid_title,
                                         minid_test)

def create_minid(filename, aws_bucket_filename, minid_user, minid_email, minid_title, minid_test):
    minid = _register_minid(filename, aws_bucket_filename, minid_email, minid_title, minid_test)
    if not minid \
            and not minid_client_api.get_user(
                app.config['MINID_SERVER'],
                minid_email).get('user'):
        minid_client_api.register_user(app.config['MINID_SERVER'],
                                       minid_email,
                                       minid_user,
                                       '', # ORCID is not currently used
                                       app.config['MINID_SERVICE_TOKEN'])
        minid = _register_minid(filename, aws_bucket_filename, minid_email)
        if not minid:
            raise Exception("Failed to register minid and user autoregistration failed")
    return minid

def upload_to_s3(filename, key):
    s3 = boto3.resource('s3', aws_access_key_id=app.config['AWS_ACCESS_KEY_ID'], aws_secret_access_key=app.config['AWS_SECRET_ACCESS_KEY'])
    data = open(filename, 'rb')
    s3.Bucket(app.config['BUCKET_NAME']).put_object(Key=key, Body=data)


