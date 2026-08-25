import base64
import mimetypes
import os
import re
import tempfile
from html.parser import HTMLParser
from urllib.parse import unquote, urlparse

import requests
from googleapiclient.http import MediaFileUpload

from rabbit_sync.uploader_api_wrapper import execute_api_call_with_backoff, get_existing_file_metadata


class _ImageSourceParser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.sources = []

    def handle_starttag(self, tag, attrs):
        if tag.lower() != "img":
            return
        source = dict(attrs).get("src")
        if source:
            self.sources.append(source.strip())


def extract_image_sources(html_body):
    parser = _ImageSourceParser()
    parser.feed(html_body or "")
    parser.close()
    return parser.sources


def _decode_image_source(source):
    if source.startswith("data:"):
        header, encoded_data = source.split(",", 1)
        match = re.match(r"data:([^;]+)(;base64)?", header, flags=re.IGNORECASE)
        mime_type = match.group(1) if match else "application/octet-stream"
        if match and match.group(2):
            return base64.b64decode(encoded_data), mime_type
        return unquote(encoded_data).encode("utf-8"), mime_type

    response = requests.get(source, timeout=30)
    response.raise_for_status()
    return response.content, response.headers.get("Content-Type", "application/octet-stream").split(";", 1)[0]


def _image_extension(source, mime_type):
    extension = os.path.splitext(urlparse(source).path)[1].lower()
    if extension in {".jpg", ".jpeg", ".png", ".gif", ".webp", ".bmp", ".tif", ".tiff", ".svg"}:
        return extension
    return mimetypes.guess_extension(mime_type) or ".bin"


def upload_journal_images(drive_service, target_folder_id, journal_title, html_body, log_callback=None):
    sources = extract_image_sources(html_body)
    uploaded = 0
    for index, source in enumerate(sources, start=1):
        extension = ".bin"
        filename = None
        try:
            image_data, mime_type = _decode_image_source(source)
            extension = _image_extension(source, mime_type)
            safe_title = re.sub(r"[^A-Za-z0-9_.-]+", "_", journal_title).strip("._") or "journal"
            display_name = f"{safe_title}_image_{index:02d}{extension}"
            existing_id, _ = get_existing_file_metadata(drive_service, target_folder_id, display_name)

            with tempfile.NamedTemporaryFile(delete=False, suffix=extension) as image_file:
                image_file.write(image_data)
                filename = image_file.name

            media = MediaFileUpload(filename, mimetype=mime_type, resumable=True)
            try:
                if existing_id:
                    execute_api_call_with_backoff(
                        drive_service.files().update(fileId=existing_id, media_body=media)
                    )
                else:
                    metadata = {
                        "name": display_name,
                        "mimeType": mime_type,
                        "parents": [target_folder_id],
                    }
                    execute_api_call_with_backoff(
                        drive_service.files().create(body=metadata, media_body=media)
                    )
            finally:
                del media
            uploaded += 1
            if log_callback:
                log_callback(f"Uploaded journal image: [{display_name}]")
        except Exception as error:
            if log_callback:
                log_callback(f"⚠️ Journal image could not be uploaded from [{source}]: {error}")
        finally:
            if filename and os.path.exists(filename):
                try:
                    os.remove(filename)
                except OSError:
                    pass

    if log_callback and sources:
        log_callback(f"Journal image upload complete: {uploaded}/{len(sources)} image(s) uploaded.")
    return uploaded
