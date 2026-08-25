import base64
import re
import html
import datetime
import logging
from googleapiclient.discovery import build

def extract_email_body(payload):
    """Recursively processes email payload structures to safely extract text content."""
    # Scenario A: Single-part email structures
    body_data = payload.get('body', {}).get('data', '')
    if body_data:
        return base64.urlsafe_b64decode(body_data).decode('utf-8', errors='ignore')
        
    # Scenario B: Multi-part nested email structures (MIME multipart)
    parts = payload.get('parts', [])
    for part in parts:
        mime_type = part.get('mimeType', '')
        if mime_type == 'text/plain':
            data = part.get('body', {}).get('data', '')
            if data:
                return base64.urlsafe_b64decode(data).decode('utf-8', errors='ignore')
        elif mime_type == 'text/html':
            data = part.get('body', {}).get('data', '')
            if data:
                return base64.urlsafe_b64decode(data).decode('utf-8', errors='ignore')
        # Recursive fallback check if parts are nested deeper (e.g. multipart/alternative)
        if 'parts' in part:
            nested_body = extract_email_body(part)
            if nested_body:
                return nested_body
                
    return ""

def fetch_journals_from_gmail(creds, log_callback=print):
    """Scans user inbox for journal summaries pushed from rabbit@r1.rabbit.tech."""
    log_callback("Scanning Gmail inbox for journals from rabbit@r1.rabbit.tech...")
    journals = []
    
    try:
        gmail_service = build('gmail', 'v1', credentials=creds)
        # Search query constraints matching sender parameters
        query = "from:rabbit@r1.rabbit.tech"
        results = gmail_service.users().messages().list(userId='me', q=query, maxResults=50).execute()
        messages = results.get('messages', [])
        
        if not messages:
            log_callback("No emails found from rabbit@r1.rabbit.tech in this inbox batch.")
            return []
            
        log_callback(f"Found {len(messages)} matching email records. Parsing message bodies...")
        for msg in messages:
            msg_id = msg['id']
            m_data = gmail_service.users().messages().get(userId='me', id=msg_id, format='full').execute()
            
            # Safely parse header configurations
            headers = m_data.get('payload', {}).get('headers', [])
            subject = "Gmail Journal Sync"
            for h in headers:
                if h.get('name', '').lower() == 'subject':
                    subject = h.get('value', 'Gmail Journal Sync')
                    break
                    
            internal_date = m_data.get('internalDate', '0')
            try:
                raw_date = datetime.datetime.fromtimestamp(int(internal_date) / 1000).strftime('%Y-%m-%d')
            except Exception:
                raw_date = datetime.date.today().strftime('%Y-%m-%d')
            
            # FIXED: Core fallback multi-part extraction strategy pipeline
            payload = m_data.get('payload', {})
            body = extract_email_body(payload)
            
            # If the body is completely empty, fall back to the email subject line as content
            if not body.strip():
                body = f"[Journal Summary Content]\nSubject: {subject}"
            
            # Clean up and sanitize remaining HTML structural tags
            if "<html>" in body.lower() or "<div>" in body.lower() or "<p>" in body.lower():
                body = re.sub(r'<[^<]+?>', '', body)  # Strip tags
                body = html.unescape(body)
                
            # Normalize trailing linebreaks to prevent structural text collisions
            body = re.sub(r'\n\s*\n', '\n\n', body).strip()
                
            journals.append({
                "id": msg_id,
                "content": body,
                "summary": subject,
                "createdAt": raw_date
            })
            
        return journals
    except Exception as e:
        log_callback(f"Gmail parsing subsystem anomaly: {str(e)}")
        return []
