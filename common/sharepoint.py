#!/usr/local/bin/python3
from datetime import datetime
import sys
import requests
import os
import cgi
import shutil
import common.logger as logger_common

sharepoint_url = os.getenv('SHAREPOINT_URL')


class Singleton(type):
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
        else:
            cls._instances[cls].__init__(*args, **kwargs)
        return cls._instances[cls]


class Sharepoint(metaclass=Singleton):
    def __init__(self, tenant_id, client_id, client_secret):
        self.grant_type = 'client_credentials'
        self.tenant_id = tenant_id
        self.client_id = client_id
        self.client_secret = client_secret
        self.scope = f"{sharepoint_url}/.default"

    # SHAREPOINT LOGIN
    def login(self):
        data = {
            'grant_type': self.grant_type,
            'client_id': self.client_id,
            'client_secret': self.client_secret,
            'scope': self.scope
        }

        try:
            response = requests.post(f'https://login.microsoftonline.com/{self.tenant_id}/oauth2/v2.0/token', data=data)

            # check rest request was successful
            if response.status_code in (200, 201, 204):
                logger_common.logger.info(
                    f'logged into sharepoint with application id: {self.client_id}. Response: {response.status_code}')
                return response.json().get('access_token')

            # if rest request unsuccessful
            else:
                logger_common.logger.error(
                    f'cannot login to sharepoint with application id: {self.client_id}. Error: {response.status_code} - {response.content}')

        # if attempt at rest request failed or above failed to return results
        except Exception as e:
            logger_common.logger.error(e, exc_info=True)
            logger_common.logger.error(
                f'cannot login to sharepoint with application id: {self.client_id}')

    def get_site_id_by_name(self, site_name):
        access_token = self.login()
        header = {
            "Authorization": "Bearer " + access_token,
            "Content-Type": "application/json",
            "If-Match": '*'
        }

        try:
            response = requests.get(
                f"{sharepoint_url}/v1.0/sites?search={site_name}",
                headers=header)

            # check rest request was successful
            if response.status_code in (200, 201, 204):
                logger_common.logger.info(
                    f'retrieved sharepoint site: {site_name}. Info: {response.status_code}')
                sites = response.json().get('value')

                # search for site name and return first one
                for site in sites:
                    if site['displayName'] == site_name:
                        site_id = site['id'].split(",")[1]

                return site_id

            # if rest request unsuccessful
            else:
                logger_common.logger.error(
                    f'cannot get sharepoint site: {site_name}. Error: {response.status_code} - {response.content}')

        # if attempt at rest request failed or above failed to return results
        except Exception as e:
            logger_common.logger.error(e, exc_info=True)
            logger_common.logger.error(
                f'cannot get sharepoint site:  {site_name}')

    # Get name and ID of root drive
    def get_root_drive_details(self, site_id):
        access_token = self.login()
        header = {
            "Authorization": "Bearer " + access_token,
            "Content-Type": "application/json",
            "If-Match": '*'
        }

        try:
            response = requests.get(
                f"{sharepoint_url}/v1.0/sites/{site_id}/drive/root",
                headers=header)
            # check rest request was successful
            if response.status_code in (200, 201, 204):
                logger_common.logger.info(
                    f'retrieved root drive details. Info: {response.status_code}')
                return {
                            "name" : response.json().get('name'),
                            "id" : response.json().get('id')
                    }

            # if rest request unsuccessful
            else:
                logger_common.logger.error(
                    f'cannot get folder: root drive. Error: {response.status_code} - {response.content}')

        # if attempt at rest request failed or above failed to return results
        except Exception as e:
            logger_common.logger.error(e, exc_info=True)
            logger_common.logger.error(
                f'cannot get root drive details.')
    
    # Get Name and ID of Sharepoint List(s)
    def get_list_details(self, site_id, list_name=[]): 
        access_token = self.login()
        header = {
            "Authorization": "Bearer " + access_token,
            "Content-Type": "application/json",
            "If-Match": '*',
            "Prefer": 'allowthrottleablequeries'
        }

        try:
            if response.status_code in (200, 201, 204):
                logger_common.logger.info(
                    f'retrieved list details. Info: {response.status_code}')
                response = requests.get(
                f"{sharepoint_url}/v1.0/sites/{site_id}/lists",
                headers=header)
                
                if len(list_name) == 0:
                    return [ { 'name': item['name'], 'id': item['id'] } for item in response.json().get('value')]
                else:
                    return [ { 'name': item['name'], 'id': item['id'] } for item in response.json().get('value') if item['name'] in list_name ]
            else:
              logger_common.logger.error(
                    f'cannot get list: details. Error: {response.status_code} - {response.content}')
                
        except Exception as e:
            logger_common.logger.error(e, exc_info=True)
            logger_common.logger.error(
                f'cannot get list: details')
    
    # Get Parent and Child structure using IDs 
    def get_parent_child_structure_by_ids(self, items, child_id_key, parent_id_key, *args):
        """
        Groups all children ids under their parent id
        
        :param obj:
                    items = [
                                {'id': 1, 'parent': None, 'some_arg': 'folder'},
                                {'id': 2, 'parent': 1, 'some_arg': 'folder'},
                                {'id': 3, 'parent': 2, 'some_arg': 'folder'},
                                {'id': 4, 'parent': 3, 'some_arg': 'file'},
                                {'id': 5, 'parent': None, 'some_arg': 'folder'},
                                {'id': 6, 'parent': 1, 'some_arg': 'file'},
                                {'id': 7, 'parent': 2, 'some_arg': 'folder'},
                            ]
        :param child_id_key: 'id'
        :param parent_id_key: 'parent'
        :param *args: 'some_arg' <-- the name of any extra keys to be associated with the child
        :return map of parents mapped to list of children
            {1: [{'id': 2, 'some_arg': 'folder'}, {'id': 6, 'some_arg': 'file'}, {'id': 3, 'some_arg': 'folder'}, {'id': 7, 'some_arg': 'folder'}, {'id': 4, 'some_arg': 'file'}], 2: [{'id': 3, 'some_arg': 'folder'}, {'id': 7, 'some_arg': 'folder'}, {'id': 4, 'some_arg': 'file'}, {'id': 4, 'some_arg': 'file'}], 3: [{'id': 4, 'some_arg': 'file'}], 4: [], 5: [], 6: [], 7: []}
        """
        def crawl_relatives(relatives, families):
            if len(relatives) and len(families[relatives[0][child_id_key]]) and families[relatives[0][child_id_key]][0] != relatives[-1][child_id_key]:
                crawl_relatives(families[relatives[0][child_id_key]], families)
                relatives += families[relatives[0][child_id_key]]


        families = {item[child_id_key]: [] for item in items}

        for item in items:
            if item[parent_id_key] is not None:
                item_dict = {}
                if args:
                    for a in args:
                        item_dict[child_id_key] = item[child_id_key]
                        item_dict[a] = item[a]
                else:
                    item_dict[child_id_key] = item[child_id_key]
                
                families[item[parent_id_key]].append(item_dict)
            
        
        for relatives in families.values():
            crawl_relatives(relatives, families)
        
        families = {k: [dict(s) for s in set(frozenset(d.items()) for d in v)] for k, v in families.items()}

        return families
    
    # List folder, subfolder and file details (returns items and parent-child structured items)
    def list_drives_and_items(self, site_id, list_id, root_drive_id, folders_only=False): 
        access_token = self.login()
        header = {
            "Authorization": "Bearer " + access_token,
            "Content-Type": "application/json",
            "If-Match": '*',
            "Prefer": 'allowthrottleablequeries'
        }

        # filter to append
        if folders_only:
            uri_filter = "&$filter=fields/ContentType eq 'Folder'"
        else:
            uri_filter = ""

        try:
            response = requests.get(
            f"{sharepoint_url}/v1.0/sites/{site_id}/lists/{list_id}/items?$expand=driveItem,fields{uri_filter}",
            headers=header)

            # check rest request was successful
            if response.status_code in (200, 201, 204):
                logger_common.logger.info(
                    f'list subfolders and files in folder. Info: {response.status_code}')

                
                # get relevant item details
                items = [
                    {
                        'name': item['driveItem']['name'],
                        'id': item['driveItem']['id'],
                        'parent_id': item['driveItem']['parentReference']['id'],
                        #'parent_name': item['driveItem']['parentReference']['name'],
                        'content_type': item.get('contentType', {}).get('name')
                    }
                for item in response.json().get('value')]
                # add root drive details
                items.append({ 'name': 'Root Drive', 'id': root_drive_id, 'parent_id': None, 'content_type': 'Folder'})      

                # get parent-child item structure
                structured_items = self.get_parent_child_structure_by_ids(items, 'id', 'parent_id', 'name', 'content_type')

                return {
                            "items": items, 
                            "items_parent_child_ids": structured_items
                        }
            
            # if rest request unsuccessful
            else:
                logger_common.logger.error(
                    f'cannot get items. Error: {response.status_code} - {response.content}')
                
        except Exception as e:
            logger_common.logger.error(e, exc_info=True)
            logger_common.logger.error(
                f'error')

    # List folder and file details by path
    def list_drive_items_by_path(self, site_id, drive_path, target_item_names=[]):
        access_token = self.login()
        header = {
            "Authorization": "Bearer " + access_token,
            "Content-Type": "application/json",
            "If-Match": '*'
        }

        try:
            response = requests.get(
            f"{sharepoint_url}/v1.0/sites/{site_id}/drive/root:/{drive_path}:/children",
            headers=header)
            
            # check rest request was successful
            if response.status_code in (200, 201, 204):
                logger_common.logger.info(
                    f'retrieved items: Info: {response.status_code}')

                items = [
                        {
                            'name': item['name'],
                            'id': item['id'],
                            'parent_id': item['parentReference']['id'],
                            #'parent_name': item['parentReference']['name'],
                            'content_type': 'Document' if item.get('@microsoft.graph.downloadUrl', {}) else 'Folder'
                        }
                    for item in response.json().get('value')]
                
                
                if len(target_item_names) == 0:
                    return items
                else:
                    target_items_named = []
                    for target_item in target_item_names:
                        # throws error if file name doesn't exist
                        lookup = next(filter(lambda x: x['name'] == target_item, items), None)
                        if not lookup:
                            sys.exit(f"{target_item} does not exist")
                            #raise ValueError(f"{target_item} does not exist")
                            
                        target_items_named.append(lookup)
                    return target_items_named
            
            # if rest request unsuccessful
            else:
                logger_common.logger.error(
                    f'Cannot get items in drive path: {drive_path}. Error: {response.status_code} - {response.content}')

        except Exception as e:
            logger_common.logger.error(e, exc_info=True)
            logger_common.logger.error(
                f'error')
        
        """
        Note: If a collection exceeds the default page size (200 items), 
        the @odata.nextLink property is returned in the response to indicate 
        more items are available and provide the request URL for the next page of items.
        """

    def get_drive_id_by_name(self, site_id, drive_name):
        access_token = self.login()
        header = {
            "Authorization": "Bearer " + access_token,
            "Content-Type": "application/json",
            "If-Match": '*'
        }

        try:
            response = requests.get(
                f"{sharepoint_url}/v1.0/sites/{site_id}/drive/root/search(q='{drive_name}')",
                headers=header)
            drive_id = ""
            # check rest request was successful
            if response.status_code in (200, 201, 204):
                logger_common.logger.info(
                    f'retrieved folder: {drive_name}. Info: {response.status_code}')
                drives = response.json().get('value')

                # search for folder name and return id
                for drive in drives:
                    if drive['name'] == drive_name:
                        drive_id = drive['id']

                return drive_id

            # if rest request unsuccessful
            else:
                logger_common.logger.error(
                    f'cannot get folder: {drive_name}. Error: {response.status_code} - {response.content}')

        # if attempt at rest request failed or above failed to return results
        except Exception as e:
            logger_common.logger.error(e, exc_info=True)
            logger_common.logger.error(
                f'cannot get folder:  {drive_name}')

    def list_drive_items_by_id(self, site_id, drive_id, target_item_names=[]):
        access_token = self.login()
        header = {
            "Authorization": "Bearer " + access_token,
            "Content-Type": "application/json",
            "If-Match": '*'
        }

        try:
            response = requests.get(f"{sharepoint_url}/v1.0/sites/{site_id}/drive/items/{drive_id}/children",
                                    headers=header)

            # check rest request was successful
            if response.status_code in (200, 201, 204):
                logger_common.logger.info(
                    f'retrieved items: Info: {response.status_code}')

                items = [
                        {
                            'name': item['name'],
                            'id': item['id'],
                            'parent_id': item['parentReference']['id'],
                            'content_type': 'Document' if item.get('@microsoft.graph.downloadUrl', {}) else 'Folder'
                        }
                    for item in response.json().get('value')]
                
                
                if len(target_item_names) == 0:
                    return items
                else:
                    target_items_named = []
                    for target_item in target_item_names:
                        # throws error if file name doesn't exist
                        lookup = next(filter(lambda x: x['name'] == target_item, items), None)
                        if not lookup:
                            sys.exit(f"{target_item} does not exist")
                            #raise ValueError(f"{target_item} does not exist")
                            
                        target_items_named.append(lookup)
                    return target_items_named
            
            # if rest request unsuccessful
            else:
                logger_common.logger.error(
                    f'Cannot list items in for drive id: {drive_id}. Error: {response.status_code} - {response.content}')

        except Exception as e:
            logger_common.logger.error(e, exc_info=True)
            logger_common.logger.error(
                f'Cannot list items in for drive id: {drive_id}')

    def get_item_id_by_name(self, site_id, drive_id, item_name):
        access_token = self.login()
        header = {
            "Authorization": "Bearer " + access_token,
            "Content-Type": "application/json",
            "If-Match": '*'
        }

        try:
            response = requests.get(f"{sharepoint_url}/v1.0/sites/{site_id}/drive/items/{drive_id}/children",
                                    headers=header)

            item_id = ""
            # check rest request was successful
            if response.status_code in (200, 201, 204):
                logger_common.logger.info(
                    f'retrieved item: {item_name}. Info: {response.status_code}')
                items = response.json().get('value')

                # search for item name and return id
                for item in items:
                    if item['name'] == item_name:
                        item_id = item['id']

                return item_id

            # if rest request unsuccessful
            else:
                logger_common.logger.error(
                    f'cannot get item: {item_name}. Error: {response.status_code} - {response.content}')


        # if attempt at rest request failed or above failed to return results
        except Exception as e:
            logger_common.logger.error(e, exc_info=True)
            logger_common.logger.error(
                f'cannot get item:  {item_name}')

    def download_item_by_id(self, site_id, item_id, local_file_directory):
        access_token = self.login()
        header = {
            "Authorization": "Bearer " + access_token,
            "Content-Type": "application/json",
            "If-Match": '*'
        }

        try:
            response = requests.get(
                f"{sharepoint_url}/v1.0/sites/{site_id}/drive/items/{item_id}/content",
                stream=True, headers=header)

            filename = ""
            # check rest request was successful
            if response.status_code in (200, 201, 204):
                logger_common.logger.info(
                    f'downloaded item: {item_id}. Info: {response.status_code}')
                params = cgi.parse_header(
                    response.headers.get('Content-Disposition', ''))[-1]

                if 'filename' not in params:
                    logger_common.logger.error(
                        f'Could not find a file for download. Error: {response.status_code} - {response.content}')

                filename = os.path.basename(params['filename'])
                abs_path = os.path.join(local_file_directory, filename)

                with open(abs_path, 'wb') as target:
                    # response.raw.decode_content = True
                    shutil.copyfileobj(response.raw, target)

                    return filename

            # if rest request unsuccessful
            else:
                logger_common.logger.error(
                    f'Could not download a file. Error: {response.status_code} - {response.content}')


        # if attempt at rest request failed or above failed to return results
        except Exception as e:
            logger_common.logger.error(e, exc_info=True)
            logger_common.logger.error(
                f'Could not find a file for download')

    def move_item_to_new_drive(self, site_id, item_id, target_folder_id, target_file_name):
        access_token = self.login()
        header = {
            "Authorization": "Bearer " + access_token,
            "Content-Type": "application/json",
            "If-Match": '*'
        }

        data = {
            'parentReference': {
                'id': target_folder_id
            },
            'name': target_file_name
        }

        try:
            response = requests.patch(
                f"{sharepoint_url}/v1.0/sites/{site_id}/drive/items/{item_id}",
                data=str(data), headers=header)

            # check rest request was successful
            if response.status_code in (200, 201, 204):
                logger_common.logger.info(
                    f'moved item: {item_id} to folder: {target_folder_id} with filename {target_file_name}. Info: {response.status_code}')
                return response

            # if rest request unsuccessful
            else:
                logger_common.logger.error(
                    f'Could not move file. Error: {response.status_code} - {response.content}')

        # if attempt at rest request failed or above failed to return results
        except Exception as e:
            logger_common.logger.error(e, exc_info=True)
            logger_common.logger.error(
                f'Could not move file')

    def upload_file_to_drive(self, site_id, local_file_path, local_file_name, target_drive_id, target_file_name):
        access_token = self.login()
        header = {
            "Authorization": "Bearer " + access_token,
            "Content-Type": "application/json",
            "If-Match": '*'
        }

        file_path = os.path.join(local_file_path, local_file_name)

        try:
            response = requests.put(
                f"{sharepoint_url}/v1.0/sites/{site_id}/drive/items/{target_drive_id}:/{target_file_name}:/content"
                , stream=True, headers=header, data=open(file_path, 'rb'))

            # check rest request was successful
            if response.status_code in (200, 201, 204):
                logger_common.logger.info(
                    f'uploaded file: {file_path} to SharePoint folder: {target_drive_id} with filename {target_file_name}. Info: {response.status_code}')
                return response

            # if rest request unsuccessful
            else:
                logger_common.logger.error(
                    f'Could not upload file. Error: {response.status_code} - {response.content}')

            # if attempt at rest request failed or above failed to return results
        except Exception as e:
            logger_common.logger.error(e, exc_info=True)
            logger_common.logger.error(
                f'Could not upload file')

    def delete_item_by_id(self, site_id, item_id):
        access_token = self.login()
        header = {
            "Authorization": "Bearer " + access_token,
            "Content-Type": "application/json",
            "If-Match": '*'
        }

        try:
            response = requests.delete(
                f"{sharepoint_url}/v1.0/sites/{site_id}/drive/items/{item_id}"
                , headers=header)

            # check rest request was successful
            if response.status_code in (200, 201, 204):
                logger_common.logger.info(
                    f'deleted item: {item_id}. Info: {response.status_code}')
                return response

            # if rest request unsuccessful
            else:
                logger_common.logger.error(
                    f'Could not delete item {item_id}. Error: {response.status_code} - {response.content}')

            # if attempt at rest request failed or above failed to return results
        except Exception as e:
            logger_common.logger.error(e, exc_info=True)
            logger_common.logger.error(
                f'Could not delete item {item_id}')


if __name__ == '__main__':
    sharepoint = Sharepoint(os.getenv('TENANT_ID')
                            , os.getenv('CLIENT_ID')
                            , os.getenv('CLIENT_SECRET')
                            )

    site_id = sharepoint.get_site_id_by_name(os.getenv('SHAREPOINT_SITE'))

    drive_id = sharepoint.get_drive_id_by_name(site_id, os.getenv('SHAREPOINT_FOLDER'))

    drive_items = sharepoint.list_children(site_id, drive_id)

    """
    file_id = sharepoint.get_item_id_by_name(site_id, drive_id, os.getenv('SHAREPOINT_FILE'))

    download_file = sharepoint.download_item_by_id(site_id, file_id, os.getenv('LOCAL_SHAREPOINT_DOWNLOADS_FOLDER'))

    new_drive_id = sharepoint.get_drive_id_by_name(site_id, os.getenv('NEW_SHAREPOINT_FOLDER'))

    moved_item = sharepoint.move_item_to_new_drive(site_id, file_id, new_drive_id, os.getenv('NEW_SHAREPOINT_FILENAME'))

    upload_file = sharepoint.upload_file_to_drive(site_id, os.getenv('LOCAL_SHAREPOINT_DOWNLOADS_FOLDER'),
                                                  os.getenv('SHAREPOINT_FILE'),
                                                  drive_id, os.getenv('SHAREPOINT_FILE'))

    new_file_id = sharepoint.get_item_id_by_name(site_id, new_drive_id, os.getenv('NEW_SHAREPOINT_FILENAME'))

    delete_item = sharepoint.delete_item_by_id(site_id, file_id)

    """
