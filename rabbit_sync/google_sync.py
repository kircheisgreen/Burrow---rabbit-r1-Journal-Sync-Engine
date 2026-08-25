import os
import logging
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from rabbit_sync.config import SCOPES  

def authenticate_google(client_secret_path, token_path='token.json'):
    """Handles OAuth2 flows for Google APIs authorization utilizing clean global scopes."""
    creds = None
    target_token_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), token_path)
    
    if os.path.exists(target_token_path):
        try:
            creds = Credentials.from_authorized_user_file(target_token_path, SCOPES)
        except Exception:
            pass
            
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(client_secret_path, SCOPES)
            creds = flow.run_local_server(port=0)
        with open(target_token_path, 'w') as token:
            token.write(creds.to_json())
    return creds

def get_or_create_folder(drive_service, folder_name, parent_id=None):
    """Finds or creates folders recursively within Google Drive filesystem contexts."""
    query = f"name = '{folder_name}' and mimeType = 'application/vnd.google-apps.folder' and trashed = false"
    if parent_id:
        query += f" and '{parent_id}' in parents"
    
    results = drive_service.files().list(q=query, fields="files(id, name)").execute()
    folders = results.get('files', [])
    
    if folders:
        return folders[0]['id']
    
    body = {'name': folder_name, 'mimeType': 'application/vnd.google-apps.folder'}
    if parent_id:
        body['parents'] = [parent_id]
    
    folder = drive_service.files().create(body=body, fields='id').execute()
    return folder.get('id')

def fetch_all_drive_folders(drive_service):
    """Queries Google Drive for all active folders to populate the GUI dropdown selection element."""
    folders = [{"name": "My Drive (Root)", "id": "root"}]
    try:
        page_token = None
        while True:
            query = "mimeType = 'application/vnd.google-apps.folder' and trashed = false"
            results = drive_service.files().list(
                q=query,
                spaces='drive',
                fields='nextPageToken, files(id, name)',
                pageToken=page_token,
                pageSize=100
            ).execute()
            
            for f in results.get('files', []):
                folders.append({"name": f['name'], "id": f['id']})
                
            page_token = results.get('nextPageToken', None)
            if not page_token:
                break
    except Exception:
        pass
    return folders
