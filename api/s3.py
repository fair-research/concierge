import os
import logging
import boto3
from django.conf import settings

log = logging.getLogger(__name__)


def get_local_file(resource):
    return os.path.join(settings.AWS_STAGING_DIR, resource)


def get_s3_object(resource):
    folder = settings.AWS_FOLDER_TEST if settings.DEBUG else settings.AWS_FOLDER
    return os.path.join(folder, resource)


def get_s3_bucket():
    s3 = boto3.resource('s3', aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                        aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY)
    return s3.Bucket(settings.AWS_BUCKET_NAME)


def upload(filename):
    resource = get_s3_object(os.path.basename(filename))
    log.debug(f'Uploading local {filename} to resource {resource}')
    get_s3_bucket().upload_file(filename, resource, ExtraArgs={'ACL': 'bucket-owner-full-control'})


def download(resource):
    local_file = get_local_file(resource)
    log.debug(f'Downloading {local_file}')
    get_s3_bucket().download_file(get_s3_object(resource), local_file)
    return local_file
