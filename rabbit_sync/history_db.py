import os
import json
import logging

DB_PATH = "sync_history.json"

def load_history():
    """Loads previous sync state tracking arrays from the database file."""
    if os.path.exists(DB_PATH):
        try:
            with open(DB_PATH, "r") as f: 
                return json.load(f)
        except Exception as e: 
            logging.error(f"Failed to load sync_history.json database: {str(e)}")
            return {}
    return {}

def save_history(history):
    """Commits processed session states permanently onto disk files."""
    with open(DB_PATH, "w") as f: 
        json.dump(history, f, indent=4)
