import time
import random
from googleapiclient.errors import HttpError

def execute_api_call_with_backoff(api_command, max_retries=5):
    """Executes a Google API request command sequence wrapped inside an automated exponential backoff."""
    retries = 0
    api_command.http.timeout = 15
    while True:
        try:
            return api_command.execute()
        except HttpError as error:
            if error.resp.status in (429, 500, 502, 503, 504) and retries < max_retries:
                sleep_time = (2 ** retries) + random.uniform(0.1, 1.0)
                time.sleep(sleep_time)
                retries += 1
            else:
                raise error
        except Exception as t_err:
            if retries < max_retries:
                time.sleep(1)
                retries += 1
            else:
                raise t_err

def get_existing_file_metadata(drive_service, folder_id, filename):
    """Queries target destination folder to retrieve the file ID and cloud MD5 Checksum value."""
    query = f"name = '{filename}' and '{folder_id}' in parents and trashed = false"
    try:
        results = execute_api_call_with_backoff(drive_service.files().list(q=query, fields="files(id, name, md5Checksum)"))
        files = results.get('files', [])
        if files: 
            return files[0]['id'], files[0].get('md5Checksum')
    except Exception: 
        pass
    return None, None
