import os

# Global configuration variables and constants
# Ensure the "www." and explicit full URLs are completely pristine
SCOPES = [
    'https://www.googleapis.com/auth/documents', 
    'https://www.googleapis.com/auth/drive',
    'https://mail.google.com/'
]

# Log file destination path
LOG_FILE_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "sync_service.log")
