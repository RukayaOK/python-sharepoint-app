from flask import Blueprint, request, abort
import common.sharepoint as sharepoint_common

put = Blueprint('put', __name__)

@put.route('/site-id/<string:site_id>/drive-id/<string:drive_id>/target-folder-id/<string:target_folder_id>/target-file-name/<string:target_file_name>', methods=['PATCH'])
def upload_file():
    uploaded_file = request.files['file']
    if uploaded_file.filename != '':
        uploaded_file.save(uploaded_file.filename)
    return 1


def check_existence(variables):
    for var in variables:
        if var is None:
            abort(400)