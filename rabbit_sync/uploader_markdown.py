import os
import hashlib
import re  # FIXED: Added missing regular expressions module import

from googleapiclient.http import MediaFileUpload
from rabbit_sync.uploader_api_wrapper import execute_api_call_with_backoff, get_existing_file_metadata

def calculate_text_md5(text_string):
    return hashlib.md5(text_string.encode('utf-8')).hexdigest()

def sync_as_markdown_file(drive_service, target_folder_id, title, display_name, styled_segments, dedup_active):
    """Compiles styled segments directly into an equivalent Markdown file with layout styles."""
    md_compiled_payload = f"# {title}\n\n"
    md_compiled_payload += '<div style="font-family: Arial, sans-serif; line-height: 1.6; color: #212529; max-width: 800px; margin: 0 auto;">\n\n'
    
    for seg in styled_segments:
        if seg["is_header"]:
            md_compiled_payload += f'## <font color="{seg["hex"]}"><b>{seg["text"]}</b></font>\n\n'
        elif seg["list_style"] is not None:
            weight_style = "font-weight: bold;" if seg["bold"] else "font-weight: normal;"
            md_compiled_payload += f'<p style="color: {seg["hex"]}; {weight_style} margin-left: 20px; margin-bottom: 6px;">{seg["list_prefix"]}{seg["text"]}</p>\n'
        else:
            weight_style = "font-weight: bold;" if seg["bold"] else "font-weight: normal;"
            md_compiled_payload += f'<p style="color: {seg["hex"]}; {weight_style} margin-bottom: 12px;">{seg["text"]}</p>\n\n'
            
    md_compiled_payload += "</div>\n"
    
    local_checksum = calculate_text_md5(md_compiled_payload)
    existing_id, cloud_checksum = get_existing_file_metadata(drive_service, target_folder_id, display_name)
    if dedup_active and existing_id and cloud_checksum == local_checksum: 
        return

    # Clean the file title text to generate a valid local operating system filename format
    safe_title = re.sub(r'[^\w\s\d_.-]', '', title).strip().replace(' ', '_')
    filename = f"temp_upload_{safe_title}.md"
    
    # Wrapped the file-write block tightly to ensure the stream closes immediately after writing
    with open(filename, "w", encoding="utf-8") as f: 
        f.write(md_compiled_payload)
        
    try:
        # Pass the cleanly closed file handle block to the Google API multipart stream builder
        media = MediaFileUpload(filename, mimetype='text/plain', resumable=True)
        if existing_id: 
            execute_api_call_with_backoff(drive_service.files().update(fileId=existing_id, media_body=media))
        else:
            meta = {'name': display_name, 'mimeType': 'text/plain', 'parents': [target_folder_id]}
            execute_api_call_with_backoff(drive_service.files().create(body=meta, media_body=media))
            
        # Explicitly delete the media connection wrapper to release Windows thread locks before attempting deletion
        del media
    finally:
        # Safe deletion gate check prevents thread crashes if network failures lock the file channel
        if os.path.exists(filename): 
            try:
                os.remove(filename)
            except Exception:
                pass
