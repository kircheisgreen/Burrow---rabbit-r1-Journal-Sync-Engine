import os

# Import decentralized functional sub-modules
from rabbit_sync.uploader_api_wrapper import get_existing_file_metadata
from rabbit_sync.uploader_html_parser import convert_html_to_styled_segments
from rabbit_sync.uploader_markdown import sync_as_markdown_file
from rabbit_sync.uploader_google_docs import sync_as_google_doc_file
from rabbit_sync.uploader_pdf import sync_as_pdf_file

def upload_processed_file(creds, drive_service, target_folder_id, title, raw_html, format_mode, text_segments=None, dedup_active=False):
    """
    Unified router routing layout payloads straight to modular sub-drivers.
    HONORS AND CONVERTS ISOLATED JOURNAL HTML SCHEMAS ACCORDING TO DOCUMENT FORMAT PICK.
    """
    ext = "md" if format_mode == "Markdown" else "pdf" if format_mode == "PDF" else "txt"
    display_name = f"{title}.{ext}" if format_mode != "Google Doc" else title

    # 1. Parse un-sanitized structural content HTML using elements tokenizer
    styled_segments = convert_html_to_styled_segments(raw_html)
    if not styled_segments: 
        return

    # 2. Route straight down to specialized layout targets
    if format_mode == "Markdown":
        sync_as_markdown_file(
            drive_service=drive_service,
            target_folder_id=target_folder_id,
            title=title,
            display_name=display_name,
            styled_segments=styled_segments,
            dedup_active=dedup_active
        )
    elif format_mode == "PDF":
        sync_as_pdf_file(
            drive_service=drive_service,
            target_folder_id=target_folder_id,
            title=title,
            display_name=display_name,
            styled_segments=styled_segments,
            dedup_active=dedup_active,
        )
    else:
        sync_as_google_doc_file(
            creds=creds,
            drive_service=drive_service,
            target_folder_id=target_folder_id,
            title=title,
            display_name=display_name,
            styled_segments=styled_segments
        )
