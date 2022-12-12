from flask import Blueprint, request, abort
import common.sharepoint as sharepoint_common

patch = Blueprint('patch', __name__)


@patch.route('/site-id/<string:site_id>/item-id/<string:item_id>/target-folder-id/<string:target_folder_id>/target-file-name/<string:target_file_name>', methods=['PATCH'])
def move_item_to_drive(site_id: str, item_id: str, target_folder_id: str, target_file_name: str):
    # request header
    tenant_id = request.headers.get('tenant-id')
    client_id = request.headers.get('client-id')
    client_secret = request.headers.get('client-secret')

    # check existence of headers and parameters
    check_existence([tenant_id, client_id, client_secret, site_id, item_id, target_folder_id, target_file_name])

    # login to sharepoint
    sharepoint = sharepoint_common.Sharepoint(tenant_id, client_id, client_secret)

    # get data
    moved_item = sharepoint.move_item_to_new_drive(site_id, item_id, target_folder_id, target_file_name)
    if not moved_item:
        abort(404)

    return f"moved item {item_id} to drive {target_folder_id} with target item name: {target_file_name}"


def check_existence(variables):
    for var in variables:
        if var is None:
            abort(400)
