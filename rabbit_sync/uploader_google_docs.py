from googleapiclient.discovery import build
from rabbit_sync.uploader_api_wrapper import execute_api_call_with_backoff, get_existing_file_metadata

def sync_as_google_doc_file(creds, drive_service, target_folder_id, title, display_name, styled_segments):
    """Converts HTML styled segments directly to equivalent Google Docs structure, layout, and styling."""
    docs_service = build('docs', 'v1', credentials=creds)
    existing_id, _ = get_existing_file_metadata(drive_service, target_folder_id, display_name)
    
    if existing_id:
        doc_id = existing_id
        doc_obj = execute_api_call_with_backoff(docs_service.documents().get(documentId=doc_id))
        body_content = doc_obj.get('body', {}).get('content', [])
        end_index = body_content[-1].get('endIndex', 2) if body_content else 2
        if end_index > 2:
            clear_req = [{'deleteContentRange': {'range': {'startIndex': 1, 'endIndex': end_index - 1}}}]
            execute_api_call_with_backoff(docs_service.documents().batchUpdate(documentId=doc_id, body={'requests': clear_req}))
    else:
        doc = execute_api_call_with_backoff(docs_service.documents().create(body={'title': title}))
        doc_id = doc.get('documentId')
        prev_p = ",".join(execute_api_call_with_backoff(drive_service.files().get(fileId=doc_id, fields='parents')).get('parents', []))
        execute_api_call_with_backoff(drive_service.files().update(fileId=doc_id, addParents=target_folder_id, removeParents=prev_p))

    flattened_doc_body = ""
    for seg in styled_segments: 
        flattened_doc_body += f"{seg['text']}\n\n"

    execute_api_call_with_backoff(docs_service.documents().batchUpdate(documentId=doc_id, body={
        'requests': [{'insertText': {'location': {'index': 1}, 'text': str(flattened_doc_body)}}]
    }))
    
    style_requests = []
    scan_index = 1
    numbered_list_start = None
    for seg in styled_segments:
        segment_length = len(seg['text']) + 2 
        end_bound = scan_index + segment_length
        
        style_requests.append({
            'updateTextStyle': {
                'range': {'startIndex': scan_index, 'endIndex': end_bound - 1},
                'textStyle': {
                    'foregroundColor': {'color': {'rgbColor': seg["rgb"]}},
                    'bold': seg["bold"],
                    'fontSize': {'magnitude': 13 if seg["is_header"] else 11, 'unit': 'PT'},
                    'weightedFontFamily': {'fontFamily': 'Arial'}
                },
                'fields': 'foregroundColor,bold,fontSize,weightedFontFamily'
            }
        })
        
        if seg["list_style"] == "NUMBERED":
            if numbered_list_start is None:
                numbered_list_start = scan_index
        else:
            if numbered_list_start is not None:
                style_requests.append({
                    'createParagraphBullets': {
                        'range': {'startIndex': numbered_list_start, 'endIndex': scan_index - 1},
                        'bulletPreset': 'NUMBERED_DECIMAL_NESTED'
                    }
                })
                numbered_list_start = None

        if seg["list_style"] == "BULLET":
            preset_template = "NUMBERED_DECIMAL_NESTED" if seg["list_style"] == "NUMBERED" else "BULLET_DISC_CIRCLE_SQUARE"
            style_requests.append({
                'createParagraphBullets': {
                    'range': {'startIndex': scan_index, 'endIndex': end_bound - 1},
                    'bulletPreset': preset_template
                }
            })
        else:
            style_requests.append({
                'updateParagraphStyle': {
                    'range': {'startIndex': scan_index, 'endIndex': end_bound - 1},
                    'paragraphStyle': {
                        'lineSpacing': 140, 
                        'spaceBelow': {'magnitude': 10 if seg["is_header"] else 6, 'unit': 'PT'}
                    },
                    'fields': 'lineSpacing,spaceBelow'
                }
            })
        scan_index = end_bound

    if numbered_list_start is not None:
        style_requests.append({
            'createParagraphBullets': {
                'range': {'startIndex': numbered_list_start, 'endIndex': scan_index - 1},
                'bulletPreset': 'NUMBERED_DECIMAL_NESTED'
            }
        })

    if style_requests: 
        execute_api_call_with_backoff(docs_service.documents().batchUpdate(documentId=doc_id, body={'requests': style_requests}))
