import os

from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont


FONT_CANDIDATES = (
    ("ArialUnicode", "arial.ttf", "ArialUnicode-Bold", "arialbd.ttf"),
    ("SegoeUI", "segoeui.ttf", "SegoeUI-Bold", "segoeuib.ttf"),
    ("DejaVuSans", "DejaVuSans.ttf", "DejaVuSans-Bold", "DejaVuSans-Bold.ttf"),
)


def _font_path(filename):
    windows_path = os.path.join(os.environ.get("WINDIR", "C:\\Windows"), "Fonts", filename)
    if os.path.exists(windows_path):
        return windows_path
    return filename


def register_unicode_fonts():
    for regular_name, regular_file, bold_name, bold_file in FONT_CANDIDATES:
        regular_path = _font_path(regular_file)
        bold_path = _font_path(bold_file)
        if not (os.path.exists(regular_path) and os.path.exists(bold_path)):
            continue
        try:
            if regular_name not in pdfmetrics.getRegisteredFontNames():
                pdfmetrics.registerFont(TTFont(regular_name, regular_path))
            if bold_name not in pdfmetrics.getRegisteredFontNames():
                pdfmetrics.registerFont(TTFont(bold_name, bold_path))
            pdfmetrics.registerFontFamily(
                regular_name,
                normal=regular_name,
                bold=bold_name,
                italic=regular_name,
                boldItalic=bold_name,
            )
            return regular_name, bold_name
        except (OSError, ValueError):
            continue
    return "Helvetica", "Helvetica-Bold"
