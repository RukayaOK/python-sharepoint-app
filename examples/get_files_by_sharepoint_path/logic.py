import os
import json
import common.sharepoint as sharepoint
from datetime import datetime, timedelta

def validate_configuration():
    pass 

# Get SharePoint File IDs to download
def get_sharepoint_files_to_download(configuration):

    # Initialise SharePoint
    sharepoint_client = sharepoint.Sharepoint(
        os.getenv('TENANT_ID')
        , os.getenv('CLIENT_ID')
        , os.getenv('CLIENT_SECRET')
    )

    # Loop through SharePoint Configuration
    for sharepoint_configuration in sharepoint_configurations:
        
        # get sharepoint site id
        sharepoint_site_id = sharepoint_client.get_site_id_by_name(sharepoint_configuration['site_name'])
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
        # get folder and subfolder structure 
        structured_folder_items = folder_items['items_parent_child_ids']

        # create empty list for files to download
        files_to_download = []
        # get folders and files in configuration to loop through
        sharepoint_folder_configuration = sharepoint_configuration['folder_and_file_paths']
        for folder_paths in sharepoint_folder_configuration:
            
            # looks up folder items and filter if file_names are specified
            folder_items = sharepoint_client.list_drive_items_by_path(sharepoint_site_id, folder_paths['folder_path'], folder_paths['file_names'])
            
            # add look back days
            if folder_paths['look_back_days']:
                folder_items = [dict(folder_item, **{'look_back_days':folder_paths['look_back_days']}) for folder_item in folder_items]
            else:
                folder_items = [dict(folder_item, **{'look_back_days':sharepoint_configuration['default_look_back_days']}) for folder_item in folder_items]
            
            # add items to files_to_download list (keep folders in the list for now as need to grab their id fo subfolder loop)
            files_to_download.extend(folder_items)
            
            # if configuration asks you to loop through files 
            if folder_paths['get_subfolder_files']:
                # if folder with just folders in it then should not have a file_names filter so will have result here
                sub_folders = structured_folder_items[folder_items[0]['parent_id']]
                # loop through subfolders and add items to files to download
                for sub_folder in sub_folders:
                    sub_folder_items = sharepoint_client.list_drive_items_by_id(sharepoint_site_id, sub_folder['id'])
                    # add look back days to each document
                    if folder_paths['look_back_days']:
                        sub_folder_items = [dict(sub_folder_item, **{'look_back_days':folder_paths['look_back_days']}) for sub_folder_item in sub_folder_items]
                    else:
                        sub_folder_items = [dict(sub_folder_item, **{'look_back_days':sharepoint_configuration['default_look_back_days']}) for sub_folder_item in sub_folder_items]
                    for sub_folder_item in sub_folder_items:
                        if sub_folder_item['content_type'] == 'Document':
                            # add items to files_to_download list
                            files_to_download.append(sub_folder_item)
        
        # remove any folders in the list
        files_to_download = [ files for files in files_to_download if files['content_type'] == 'Document']

    return files_to_download

def filter_files_by_lookup_days(sharepoint_files_to_download):
    sharepoint_files_to_download_time_restricted = []
    for sharepoint_file_to_download in sharepoint_files_to_download:
        datelimit = (datetime.today() - timedelta(days=sharepoint_file_to_download['look_back_days'])).date()
        if datetime.fromisoformat(sharepoint_file_to_download['created_date_time']).date() > datelimit:
            sharepoint_files_to_download_time_restricted.append(sharepoint_file_to_download) 
    
    return sharepoint_files_to_download_time_restricted


# SharePoint Configuration
config_directory="./config"
sharepoint_configurations=[]
# Loop through files in config directory and return list of configuration
for filename in os.listdir(config_directory):
    with open(os.path.join(config_directory, filename)) as file:
        sharepoint_configurations.append(json.load(file))

# SharePoint Files to Download
sharepoint_files = get_sharepoint_files_to_download(config_directory)
sharepoint_files = filter_files_by_lookup_days(sharepoint_files)


