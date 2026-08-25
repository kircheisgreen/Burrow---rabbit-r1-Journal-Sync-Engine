import re

def sanitize_prefix(text):
    """Sanitizes text strings to remove Windows filesystem forbidden characters."""
    if not text: 
        return ""
    # Strip common forbidden file naming special characters
    clean = re.sub(r'[\\/*?:"<>|]', "", text)
    # Truncate to a compact length to prevent nested path limits truncation faults
    return clean.strip()[:35]
