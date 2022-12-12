import os
from flask import Blueprint, request, abort
import common.sharepoint as sharepoint_common

put = Blueprint('put', __name__)


@put.route('/site-id/<string:site_id>/drive-id/<string:drive_id>', methods=['PUT'])
def upload_file_to_drive(site_id: str, drive_id: str):
    # request header
    tenant_id = request.headers.get('tenant-id')
    client_id = request.headers.get('client-id')
    client_secret = request.headers.get('client-secret')

    # parameters
    uploaded_file = request.files['file']

    # check existence of headers and parameters
    check_existence([tenant_id, client_id, client_secret, site_id, drive_id, uploaded_file])

    # login to sharepoint
    sharepoint = sharepoint_common.Sharepoint(tenant_id, client_id, client_secret)

    uploaded_file.save(os.path.join(os.getenv('LOCAL_REQUESTS_DOWNLOADS_FOLDER'), uploaded_file.filename))
    sharepoint.upload_file_to_drive(site_id, os.getenv('LOCAL_REQUESTS_DOWNLOADS_FOLDER'), uploaded_file.filename
                                    , drive_id, uploaded_file.filename)

    return f"Uploaded {uploaded_file.filename}"


def check_existence(variables):
    for var in variables:
        if var is None:
            abort(400)