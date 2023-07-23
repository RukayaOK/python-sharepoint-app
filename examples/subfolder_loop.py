import os 
import common.sharepoint as sharepoint

"""
Loop through SharePoint folders and subfolders and get files
"""

# Folders to get files from
sharepoint_site_name = "Test Site"
sharepoint_folder_configuration = [
        {
            "folder_path": "/Three/Nested/Folders",
            "file_names": [],
            "get_subfolder_files": True
        },
        {
            "folder_path": "/Some Folder/With",
            "file_names": ["A File.docx", "Another File.docx"],
            "get_subfolder_files": True
        }
]

# Loop through folders and subfolders
sharepoint_client = sharepoint.Sharepoint(os.getenv('TENANT_ID')
                        , os.getenv('CLIENT_ID')
                        , os.getenv('CLIENT_SECRET')
                        )

# get sharepoint site id
sharepoint_site_id = sharepoint_client.get_site_id_by_name(sharepoint_site_name)

# get sharepoint root id
sharepoint_root_drive_id = sharepoint_client.get_root_drive_details(sharepoint_site_id)['id']

# get sharepoint list id
sharepoint_root_list_id = sharepoint_client.get_list_details(sharepoint_site_id, ['Shared Documents'])
sharepoint_root_list_id = sharepoint_root_list_id[0]['id']

# only need to do this if one get_sub_folder = True
folder_items = sharepoint_client.list_drives_and_items(
    sharepoint_site_id
    , sharepoint_root_list_id
    , sharepoint_root_drive_id
    )

# 
files_to_download = []

# get folder items - parent-child relationship
structured_folder_items = folder_items['items_parent_child_ids']

# get files to download
for folder_paths in sharepoint_folder_configuration:
    # looks up folder items and filters if file_name set
    folder_items = sharepoint_client.list_drive_items_by_path(sharepoint_site_id, folder_paths['folder_path'], folder_paths['file_names'])
    files_to_download.extend(folder_items)
    
    if folder_paths['get_subfolder_files']:
        # if folder with just folders in it then should not have a file_names filter so will have result here
        sub_folders = structured_folder_items[folder_items[0]['parent_id']]
        # loop through subfolders and add items to files to download
        for sub_folder in sub_folders:
            sub_folder_items = sharepoint_client.list_drive_items_by_id(sharepoint_site_id, sub_folder['id'])
            for sub_folder_item in sub_folder_items:
                if sub_folder_item['content_type'] == 'Document':
                    files_to_download.append(sub_folder_item)

files_to_download = [ files for files in files_to_download if files['content_type'] == 'Document']


print(files_to_download)
