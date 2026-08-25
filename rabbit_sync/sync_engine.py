import os
import json
import logging
import gc
import re
import time
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

from rabbit_sync.cron_logger import init_cron_logging
from rabbit_sync.rabbit_api import fetch_rabbit_journals
from rabbit_sync.gmail_api import fetch_journals_from_gmail
from rabbit_sync.google_sync import authenticate_google, get_or_create_folder
from rabbit_sync.utils import parse_metadata, extract_and_color_speakers

from rabbit_sync.history_db import load_history, save_history, DB_PATH
from rabbit_sync.uploader import upload_processed_file, get_existing_file_metadata
from rabbit_sync.uploader_images import upload_journal_images
from rabbit_sync.sanitizers import sanitize_prefix
from rabbit_sync.outline_processor import process_colored_markdown_outline, process_colored_docs_outline

from rabbit_sync.transformers import (
    transform_to_cornell, transform_to_outlining, 
    transform_to_mindmap_text, transform_to_boxing
)

from rabbit_sync.visualizer import generate_mindmap_svg, convert_svg_to_png_bytes, convert_svg_to_pdf_bytes

init_cron_logging()

def run_headless_sync(token, client_secret, active_workflows, log_callback=None, force_sync=False, master_parent_id=None, source_mode="Rabbit Hole", format_mode="Google Doc", image_mode="SVG", dedup_mode=False):
    """Executes the pipeline mapping files and visualization graphics with deep diagnostic payload logging."""
    execution_context = "BACKGROUND SCHEDULER TASK" if log_callback is None else "INTERACTIVE GUI CLIENT"
    logging.info("=" * 80)
    logging.info(f"🔔 CRON TRIGGER DETECTED: Engine loop woke up successfully via {execution_context}!")
    logging.info(f"⚙️ Parameters: Source=[{source_mode}] | Format=[{format_mode}] | Image=[{image_mode}] | Dedup=[{dedup_mode}]")
    logging.info("=" * 80)

    if log_callback: 
        log_callback(f"Initializing execution core pipeline...")
        
    history = load_history()
    config_fingerprint = f"{'|'.join(sorted(active_workflows)) if active_workflows else 'Flat'}_{format_mode}_{image_mode}_{source_mode}_mindmap_diagnostic_logging_v1"
    root_anchor = master_parent_id if master_parent_id and master_parent_id != "root" else None
    
    try:
        creds = authenticate_google(client_secret, token_path=os.path.join(os.path.dirname(DB_PATH), 'token.json'))
        drive_service = build('drive', 'v3', credentials=creds)
        
        if source_mode == "Google Mail":
            journals = fetch_journals_from_gmail(creds, log_callback=log_callback)
        else:
            journals = fetch_rabbit_journals(token, log_callback=log_callback)
            
        if not journals:
            logging.info("No journals loaded to process.")
            if log_callback: log_callback("No journals loaded to process.")
            return True

        for item in journals:
            j_id = item.get('id') or "unkn_" + str(item.get('createdAt'))
            content = item.get('content') or item.get('summary') or ''
            journal_header = item.get('summary') or "Rabbit Journal Entry"
            
            if not content.strip(): continue
            if not force_sync and j_id in history and history[j_id] == config_fingerprint:
                continue
                
            # Dynamic Historical Target Folders Sorting Pass
            cached_item_date = item.get('createdAt') or item.get('createdOn')
            if cached_item_date and re.search(r'\d{4}-\d{2}-\d{2}', str(cached_item_date)):
                doc_date = str(cached_item_date).strip()[:10]
                lecturer, _, has_meta = parse_metadata(content, fallback_date=doc_date)
            else:
                raw_date = item.get('createdAt', 'Unspecified-Date')[:10]
                lecturer, doc_date, has_meta = parse_metadata(content, fallback_date=raw_date)
            
            current_parent_id = get_or_create_folder(drive_service, lecturer, parent_id=root_anchor)
            journal_date_folder_id = get_or_create_folder(
                drive_service, doc_date, parent_id=current_parent_id
            )
            target_folder_id = journal_date_folder_id
            source_aria_label = str(item.get("sourceAriaLabel") or "").strip()
            if source_aria_label:
                target_folder_id = get_or_create_folder(
                    drive_service,
                    source_aria_label,
                    parent_id=journal_date_folder_id,
                )
                if log_callback:
                    log_callback(f"Using journal source subfolder: [{source_aria_label}]")
            else:
                target_folder_id = journal_date_folder_id
                if log_callback:
                    log_callback(f"No SVG aria-label found; returned to parent journal date folder: [{doc_date}]")
            
            base_name = f"Journal - {doc_date}"
            clean_pref = sanitize_prefix(journal_header)
            
            if clean_pref.lower() in ["august 20", "august 18", "august 13", "august 7", "august 3"]:
                base_title = base_name
            else:
                base_title = f"{clean_pref} - {base_name}" if clean_pref else base_name
                
            text_segments = extract_and_color_speakers(content)
            
            if log_callback: log_callback(f"Syncing main transcript row -> Folder: [{doc_date}] Title: [{base_title}]")
            upload_journal_images(
                drive_service,
                target_folder_id,
                base_title,
                content,
                log_callback=log_callback,
            )
            upload_processed_file(creds, drive_service, target_folder_id, base_title, content, format_mode, text_segments, dedup_active=dedup_mode)

            # State tracking bucket to capture generated suffix content blocks for visualization maps
            mindmap_formatted_text = None

            # Note-Taking Framework Suffix Copy Variations Outputs Generation
            for workflow in active_workflows:
                suffix_title = f"{base_title}_{workflow.replace(' ', '')}"
                
                if workflow == "Cornell Method":
                    wf_text = transform_to_cornell(base_name, content)
                    upload_processed_file(creds, drive_service, target_folder_id, suffix_title, wf_text, format_mode, dedup_active=dedup_mode)
                    
                elif workflow == "Outlining":
                    raw_outline = transform_to_outlining(base_name, content)
                    if format_mode == "Markdown":
                        wf_text = process_colored_markdown_outline(raw_outline)
                        upload_processed_file(creds, drive_service, target_folder_id, suffix_title, wf_text, format_mode, dedup_active=dedup_mode)
                    else:
                        docs_outline_segments = process_colored_docs_outline(raw_outline)
                        upload_processed_file(creds, drive_service, target_folder_id, suffix_title, raw_outline, format_mode, docs_outline_segments, dedup_active=dedup_mode)
                        
                elif workflow == "Mind Mapping":
                    # Use the same journal title/content that is being converted to the base output,
                    # then transform that exact source into the Mind Mapping document payload.
                    mindmap_formatted_text = transform_to_mindmap_text(base_title, content)
                    upload_processed_file(creds, drive_service, target_folder_id, suffix_title, mindmap_formatted_text, format_mode, dedup_active=dedup_mode)
                    
                elif workflow == "Boxing":
                    wf_text = transform_to_boxing(base_name, content)
                    upload_processed_file(creds, drive_service, target_folder_id, suffix_title, wf_text, format_mode, dedup_active=dedup_mode)

            # Diagram Visualizer MindMap Graphic Generation Node
            if "Mind Mapping" in active_workflows:
                # Render the visualization from the generated Mind Mapping document text, not from the raw transcript.
                target_visual_source = mindmap_formatted_text if mindmap_formatted_text else transform_to_mindmap_text(base_title, content)
                
                # =========================================================================
                # 🔍 CRITICAL DIAGNOSTIC LOGGING BLOCK: AUDIT ACTIVE MINDMAP PAYLOAD
                # =========================================================================
                is_using_suffix_variable = (mindmap_formatted_text is not None)
                raw_size = len(content)
                payload_size = len(target_visual_source)
                
                if log_callback:
                    log_callback("\n" + "="*70)
                    log_callback("⚙️ DIAGNOSTIC AUDIT: MindMap Visualization Payload Initialization Check")
                    log_callback(f"🔹 Source File Target Name: [{base_title}_MindMapping]")
                    log_callback(f"🔹 Variable Channel Linkage: {'✅ SUCCESS - Utilizing converted suffix outline variable' if is_using_suffix_variable else '⚠️ FALLBACK - Recalculated locally inside map condition'}")
                    log_callback(f"🔹 Raw Transcript Size: {raw_size} chars | MindMap Payload Size: {payload_size} chars")
                    
                    # Log snippet verification bounds to reveal internal hierarchical symbols
                    snippet_preview = target_visual_source[:200].replace('\n', ' \\n ')
                    log_callback(f"🔹 Text Snippet Fed to Renderer: \"{snippet_preview}...\"")
                    log_callback("="*70 + "\n")
                # =========================================================================

                svg_string = generate_mindmap_svg(base_title, target_visual_source)
                img_name = f"temp_map_{j_id}"
                
                ext = "svg" if image_mode == "SVG" else "pdf" if image_mode == "PDF" else "png"
                mimetype = "image/svg+xml" if image_mode == "SVG" else "application/pdf" if image_mode == "PDF" else "image/png"
                image_title = f"{sanitize_prefix(journal_header)} - MindMap Visualization - {doc_date}.{ext}" if clean_pref else f"MindMap Visualization - {doc_date}.{ext}"
                filename = f"{img_name}.{ext}"
                
                if image_mode == "SVG":
                    with open(filename, "w", encoding="utf-8") as f: f.write(svg_string)
                elif image_mode == "PDF":
                    pdf_data = convert_svg_to_pdf_bytes(svg_string)
                    with open(filename, "wb") as f: f.write(pdf_data)
                else:
                    png_data = convert_svg_to_png_bytes(svg_string)
                    with open(filename, "wb") as f: f.write(png_data)
                    
                existing_img_id, cloud_md5 = get_existing_file_metadata(drive_service, target_folder_id, image_title)
                media = MediaFileUpload(filename, mimetype=mimetype)
                
                if existing_img_id:
                    drive_service.files().update(fileId=existing_img_id, media_body=media).execute()
                else:
                    meta = {'name': image_title, 'mimeType': mimetype, 'parents': [target_folder_id]}
                    drive_service.files().create(body=meta, media_body=media).execute()

                    
                del media
                gc.collect()
                if os.path.exists(filename): os.remove(filename)
                
            history[j_id] = config_fingerprint
            save_history(history)
            logging.info(f"Successfully finalized execution run: {base_title}")
            
        logging.info("--- Sync Cycle Completed Successfully ---")
        if log_callback: log_callback("Sync cycle execution complete.")
        return True
    except Exception as e:
        logging.exception("Sync thread pipeline structural breakdown.")
        if log_callback: log_callback(f"Critical Subsystem Fault: {str(e)}")
        return False
