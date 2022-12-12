from flask import Blueprint, request, abort
import common.sharepoint as sharepoint_common


delete = Blueprint('delete', __name__)


@delete.route('/site-id/<string:site_id>/item-id/<string:item_id>', methods=['DELETE'])
def delete_item_by_id(site_id: str, item_id: str):
    # request header
    tenant_id = request.headers.get('tenant-id')
    client_id = request.headers.get('client-id')
    client_secret = request.headers.get('client-secret')

    # check existence of headers and parameters
    check_existence([tenant_id, client_id, client_secret, site_id, item_id])

    # login to sharepoint
    sharepoint = sharepoint_common.Sharepoint(tenant_id, client_id, client_secret)

    # get data
    delete_item = sharepoint.delete_item_by_id(site_id, item_id)
    if not item_id:
        abort(404)

    return f"Deleted item with id {item_id}"


def check_existence(variables):
    for var in variables:
        if var is None:
            abort(400)