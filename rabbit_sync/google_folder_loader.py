from googleapiclient.discovery import build
from rabbit_sync.google_sync import authenticate_google, fetch_all_drive_folders

def async_load_drive_directories(state, log_callback):
    """Connects to Google Drive to query folder tree components."""
    try:
        creds = authenticate_google(state.client_secret_var.get())
        drive_service = build('drive', 'v3', credentials=creds)
        state.drive_folders_cache = fetch_all_drive_folders(drive_service)
        
        display_names = [f["name"] for f in state.drive_folders_cache]
        if state.folder_dropdown:
            state.folder_dropdown['values'] = display_names
        log_callback(f"🚀 System Progress: Successfully loaded {len(display_names) - 1} distinct Google Drive folder locations.")
    except Exception as e:
        log_callback(f"⚠️ Google API Error: Could not list directory folders: {str(e)}")
