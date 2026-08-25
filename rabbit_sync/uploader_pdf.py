import hashlib
import os
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer
from googleapiclient.http import MediaFileUpload

from rabbit_sync.uploader_api_wrapper import execute_api_call_with_backoff, get_existing_file_metadata
from rabbit_sync.pdf_fonts import register_unicode_fonts


def _pdf_color(hex_color):
    try:
        return colors.HexColor(hex_color)
    except (TypeError, ValueError):
        return colors.HexColor("#212529")

def _normalize_pdf_text(text):
    return str(text).replace("\u00ad", " ").replace("\u2010", " ").replace("\u2011", " ").replace("\u25a0", " ")


def _build_pdf(filename, title, styled_segments):
    document = SimpleDocTemplate(
        filename,
        pagesize=letter,
        rightMargin=0.7 * inch,
        leftMargin=0.7 * inch,
        topMargin=0.7 * inch,
        bottomMargin=0.7 * inch,
    )
    styles = getSampleStyleSheet()
    regular_font, bold_font = register_unicode_fonts()
    story = []

    title_style = ParagraphStyle(
        "JournalTitle",
        parent=styles["Title"],
        fontName=bold_font,
        fontSize=16,
        leading=20,
        textColor=colors.HexColor("#212529"),
        spaceAfter=14,
    )
    story.append(Paragraph(escape(_normalize_pdf_text(title)), title_style))

    for segment in styled_segments:
        text = _normalize_pdf_text(segment["text"])
        if not text.strip():
            story.append(Spacer(1, 6))
            continue

        text = escape(text)
        if segment["list_prefix"]:
            text = escape(_normalize_pdf_text(segment["list_prefix"])) + text
        if segment["bold"]:
            text = f"<b>{text}</b>"

        style = ParagraphStyle(
            "JournalSegment",
            parent=styles["BodyText"],
            fontName=bold_font if segment["bold"] else regular_font,
            fontSize=13 if segment["is_header"] else 10.5,
            leading=17 if segment["is_header"] else 14,
            textColor=_pdf_color(segment["hex"]),
            spaceAfter=8 if segment["is_header"] else 5,
        )
        story.append(Paragraph(text, style))

    document.build(story)


def sync_as_pdf_file(drive_service, target_folder_id, title, display_name, styled_segments, dedup_active):
    """Render styled journal segments to PDF and upload the resulting file to Drive."""
    safe_title = "".join(character for character in title if character.isalnum() or character in " ._-").strip()
    filename = f"temp_upload_{safe_title or 'journal'}.pdf"
    local_checksum = None

    try:
        _build_pdf(filename, title, styled_segments)
        with open(filename, "rb") as pdf_file:
            local_checksum = hashlib.md5(pdf_file.read()).hexdigest()

        existing_id, cloud_checksum = get_existing_file_metadata(
            drive_service, target_folder_id, display_name
        )
        if dedup_active and existing_id and cloud_checksum == local_checksum:
            return

        media = MediaFileUpload(filename, mimetype="application/pdf", resumable=True)
        try:
            if existing_id:
                execute_api_call_with_backoff(
                    drive_service.files().update(fileId=existing_id, media_body=media)
                )
            else:
                metadata = {
                    "name": display_name,
                    "mimeType": "application/pdf",
                    "parents": [target_folder_id],
                }
                execute_api_call_with_backoff(
                    drive_service.files().create(body=metadata, media_body=media)
                )
        finally:
            del media
    finally:
        if os.path.exists(filename):
            try:
                os.remove(filename)
            except OSError:
                pass
