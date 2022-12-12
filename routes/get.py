import os
from datetime import datetime
from flask import Blueprint, request, abort, send_from_directory
import common.sharepoint as sharepoint_common

get = Blueprint('get', __name__)


@get.route('/')
def index():
    response = {
        "status": 200,
        "name": "python-sharepoint-application",
        "version_api": "v1",
        "version_code": "1.0.0",
        "hostname": "",
        "datetime_request": datetime.now()
    }
    return response


@get.route('/site-name/<string:site_name>')
def get_site_id_by_name(site_name: str):
    # request header
    tenant_id = request.headers.get('tenant-id')
    client_id = request.headers.get('client-id')
    client_secret = request.headers.get('client-secret')

    # check existence of headers and parameters
    check_existence([tenant_id, client_id, client_secret, site_name])

    # login to sharepoint
    sharepoint = sharepoint_common.Sharepoint(tenant_id, client_id, client_secret)

    # get data
    site_id = sharepoint.get_site_id_by_name(site_name)
    if not site_id:
        abort(404)

    return site_id


@get.route('/site-id/<string:site_id>/drive-name/<string:drive_name>')
def get_drive_id_by_name(site_id: str, drive_name: str):
    # request header
    tenant_id = request.headers.get('tenant-id')
    client_id = request.headers.get('client-id')
    client_secret = request.headers.get('client-secret')

    # check existence of headers and parameters
    check_existence([tenant_id, client_id, client_secret, site_id, drive_name])

    # login to sharepoint
    sharepoint = sharepoint_common.Sharepoint(tenant_id, client_id, client_secret)

    # get data
    drive_id = sharepoint.get_drive_id_by_name(site_id, drive_name)
    if not drive_id:
        abort(404)

    return drive_id


@get.route('/site-id/<string:site_id>/drive-id/<string:drive_id>/children')
def list_drive_items_by_id(site_id: str, drive_id: str):
    # request header
    tenant_id = request.headers.get('tenant-id')
    client_id = request.headers.get('client-id')
    client_secret = request.headers.get('client-secret')

    # check existence of headers and parameters
    check_existence([tenant_id, client_id, client_secret, site_id, drive_id])

    # login to sharepoint
    sharepoint = sharepoint_common.Sharepoint(tenant_id, client_id, client_secret)

    # get data
    drive_id = sharepoint.list_drive_items_by_id(site_id, drive_id)
    if not drive_id:
        abort(404)

    return drive_id

@get.route('/site-id/<string:site_id>/drive-id/<string:drive_id>/item-name/<string:item_name>')
def get_item_id_by_name(site_id: str, drive_id: str, item_name: str):
    # request header
    tenant_id = request.headers.get('tenant-id')
    client_id = request.headers.get('client-id')
    client_secret = request.headers.get('client-secret')

    # check existence of headers and parameters
    check_existence([tenant_id, client_id, client_secret, site_id, drive_id, item_name])

    # login to sharepoint
    sharepoint = sharepoint_common.Sharepoint(tenant_id, client_id, client_secret)

    # get data
    item_id = sharepoint.get_item_id_by_name(site_id, drive_id, item_name)
    if not item_id:
        abort(404)

    return item_id


@get.route('/site-id/<string:site_id>/item-id/<string:item_id>')
def download_item_by_id(site_id: str, item_id: str):
    # request header
    tenant_id = request.headers.get('tenant-id')
    client_id = request.headers.get('client-id')
    client_secret = request.headers.get('client-secret')

    # check existence of headers and parameters
    check_existence([tenant_id, client_id, client_secret, site_id, item_id])

    # login to sharepoint
    sharepoint = sharepoint_common.Sharepoint(tenant_id, client_id, client_secret)

    # get data
    download_directory = os.getenv('LOCAL_FOLDER')
    downloaded_item = sharepoint.download_item_by_id(site_id, item_id, download_directory)
    if not downloaded_item:
        abort(404)

    return send_from_directory(download_directory, downloaded_item)


def check_existence(variables):
    for var in variables:
        if var is None:
            abort(400)