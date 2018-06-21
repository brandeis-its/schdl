from __future__ import (division, absolute_import, print_function,
                        unicode_literals)

import logging
import os
import shutil
from google.cloud import storage

from schdl import app

LOGGER = logging.getLogger(__name__)


def upload(stream, name, mimetype):
    if app.config.get('SCHDL_GCS_USE_LOCAL_DIR'):
        return _local_upload(stream, name)
    client = _get_client()
    bucket = app.config['SCHDL_GCS_BUCKET']
    client.bucket(bucket).blob(name).upload_from_file(stream, content_type=mimetype)
    return True


def download(stream, name):
    if app.config.get('SCHDL_GCS_USE_LOCAL_DIR'):
        return _local_download(stream, name)
    client = _get_client()
    bucket = app.config['SCHDL_GCS_BUCKET']
    client.bucket(bucket).blob(name).download_to_file(stream)
    return True


def delete(name):
    if app.config.get('SCHDL_GCS_USE_LOCAL_DIR'):
        return _local_delete(name)
    client = _get_client()
    bucket = app.config['SCHDL_GCS_BUCKET']
    client.bucket(bucket).blob(name).delete()
    return True

def _get_client():
    if 'SERVICE_ACCOUNT_JSON' in app.config:
        return storage.Client.from_service_account_json(
            app.config['SERVICE_ACCOUNT_JSON'])
    else:
        return storage.Client()

def _local_pathname(name):
    return os.path.join(app.config['SCHDL_GCS_LOCAL_DIR'],
                        app.config['SCHDL_GCS_BUCKET'],
                        name)


def _local_upload(stream, name):
    pathname = _local_pathname(name)
    dirname = os.path.dirname(pathname)
    if not os.path.isdir(dirname):
        os.makedirs(dirname)
    with open(pathname, 'w') as out_stream:
        shutil.copyfileobj(stream, out_stream)
    return True


def _local_download(stream, name):
    pathname = _local_pathname(name)
    with open(pathname) as in_stream:
        shutil.copyfileobj(in_stream, stream)
    return True


def _local_delete(name):
    pathname = _local_pathname(name)
    os.unlink(pathname)
    return True
