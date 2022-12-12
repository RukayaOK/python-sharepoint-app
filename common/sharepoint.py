#!/usr/local/bin/python3
from datetime import datetime

import requests
import os
import cgi
import shutil
import common.logger as logger_common

sharepoint_url = os.getenv('SHAREPOINT_URL')


class Singleton (type):
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
        else:
            cls._instances[cls].__init__(*args, **kwargs)
        return cls._instances[cls]


class Sharepoint(metaclass=Singleton):
    def __call__(self):
        return self

    def spam(self):
        print(id(self))

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

    def upload_file_to_drive(self, site_id, drive_id, local_file_path, local_file_name, uploaded_file_name):
        access_token = self.login()
        header = {
            "Authorization": "Bearer " + access_token,
            "Content-Type": "application/json",
            "If-Match": '*'
        }

        file_path = os.path.join(local_file_path, local_file_name)

        try:
            response = requests.put(
                f"{sharepoint_url}/v1.0/sites/{site_id}/drive/items/{drive_id}:/{uploaded_file_name}:/content"
                , stream=True, headers=header, data=open(file_path, 'rb'))

            # check rest request was successful
            if response.status_code in (200, 201, 204):
                logger_common.logger.info(
                    f'uploaded file: {file_path} to SharePoint folder: {drive_id} with filename {local_file_name}. Info: {response.status_code}')
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

    a = Sharepoint(os.getenv('TENANT_ID')
                   , os.getenv('CLIENT_ID')
                   , os.getenv('CLIENT_SECRET')
                )

    site_id = a.get_site_id_by_name(os.getenv('SHAREPOINT_SITE'))

    drive_id = a.get_drive_id_by_name(site_id, os.getenv('SHAREPOINT_FOLDER'))

    file_id = a.get_item_id_by_name(site_id, drive_id, os.getenv('SHAREPOINT_FILE'))

    download_file = a.download_item_by_id(site_id, file_id, os.getenv('LOCAL_FOLDER'))

    new_drive_id = a.get_drive_id_by_name(site_id, os.getenv('NEW_SHAREPOINT_FOLDER'))

    """
    moved_item = a.move_item_to_new_drive(site_id, file_id, new_drive_id, os.getenv('NEW_SHAREPOINT_FILENAME'))
    
    
    upload_file = a.upload_file_to_drive(site_id, drive_id, os.getenv('LOCAL_FOLDER'), os.getenv('SHAREPOINT_FILE'),
                                         os.getenv('SHAREPOINT_FILE'))

    new_file_id = a.get_item_id_by_name(site_id, new_drive_id, os.getenv('NEW_SHAREPOINT_FILENAME'))

    delete_item = a.delete_item_by_id(site_id, file_id)
    """


