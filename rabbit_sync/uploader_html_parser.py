import re
from html.parser import HTMLParser

CSS_COLOR_HEX = {
    "black": "#000000", "white": "#ffffff", "red": "#ff0000", "blue": "#0000ff",
    "green": "#008000", "yellow": "#ffff00", "orange": "#ffa500", "purple": "#800080",
    "pink": "#ffc0cb", "gray": "#808080", "grey": "#808080", "brown": "#a52a2a",
    "cyan": "#00ffff", "teal": "#008080", "indigo": "#4b0082", "violet": "#ee82ee",
    "lime": "#00ff00", "navy": "#000080", "maroon": "#800000", "olive": "#808000",
    "darkgrey": "#666666", "magenta": "#ff00ff"
}

TAILWIND_COLOR_HEX = {
    "red": {"500": "#ef4444", "400": "#ef4444"}, 
    "blue": {"500": "#3b82f6", "400": "#3b82f6"}, 
    "green": {"500": "#22c55e", "400": "#22c55e"},
    "yellow": {"500": "#eab308", "400": "#eab308"}, 
    "orange": {"500": "#f97316", "400": "#f97316"}, 
    "purple": {"500": "#a855f7", "400": "#a855f7"},
    "pink": {"500": "#ec4899", "400": "#ec4899"}, 
    "gray": {"500": "#6b7280", "400": "#6b7280"}, 
    "grey": {"500": "#6b7280", "400": "#6b7280"}, 
    "slate": {"500": "#64748b","400": "#64748b"}, 
    "indigo": {"500": "#6366f1", "400": "#6366f1"}, 
    "teal": {"500": "#14b8a6", "400": "#14b8a6"}, 
    "cyan": {"500": "#06b6d4", "400": "#06b6d4"}, 
    "lime": {"500": "#84cc16", "400": "#84cc16"},
}

def _normalize_font_color(color):
    if color and color.lower() in {"#fff", "#ffffff", "white"}:
        return "#000000"
    return color

SPEAKER_COLOR_KEYS = (
    "blue", "orange", "green", "purple", "red", "teal", "yellow", "indigo",
    "pink", "cyan", "lime", "navy", "maroon", "olive", "brown", "violet",
    "darkgrey", "gray", "black", "magenta",
)

# Keep the twentieth speaker distinct from the base palette where possible.
CSS_COLOR_HEX["magenta"] = "#ff00ff"

def _class_styles(attributes):
    class_match = re.search(r"\bclass\s*=\s*['\"]([^'\"]*)['\"]", attributes, flags=re.IGNORECASE)
    if not class_match:
        return False, None

    class_tokens = class_match.group(1).split()
    is_bold = any(token == "font-bold" or ("font" in token and "bold" in token) for token in class_tokens)
    class_color = None
    for token in class_tokens:
        color_match = re.fullmatch(r"text-([a-zA-Z]+)(?:-(\d{2,3}))?", token)
        if not color_match:
            continue
        color_name, shade = color_match.groups()
        color_name = color_name.lower()
        if shade and color_name in TAILWIND_COLOR_HEX and shade in TAILWIND_COLOR_HEX[color_name]:
            class_color = TAILWIND_COLOR_HEX[color_name][shade]
        elif not shade and color_name in CSS_COLOR_HEX:
            class_color = CSS_COLOR_HEX[color_name]
        if class_color:
            break
    return is_bold, _normalize_font_color(class_color)

def hex_to_rgb(hex_str):
    """Helper to convert hex strings (#RRGGBB) to Google Docs RGB dictionary ratios."""
    hex_str = hex_str.lstrip('#')
    if len(hex_str) == 3: 
        hex_str = ''.join([c*2 for c in hex_str])
    try:
        return {
            "red": int(hex_str[0:2], 16) / 255.0,
            "green": int(hex_str[2:4], 16) / 255.0,
            "blue": int(hex_str[4:6], 16) / 255.0
        }
    except Exception: 
        return {"red": 0.13, "green": 0.15, "blue": 0.16}

def create_space_segment():
    return {
        "text": " ",
        "hex": "#212529",
        "rgb": hex_to_rgb("#212529"),
        "bold": False,
        "is_header": False,
        "list_style": None,
        "list_prefix": ""
    }

def parse_block_attributes_and_content(tag, attributes, inner_content, active_list_type, current_index=1):
    """Processes an individual block element node to map layout styles and colors cleanly."""

    # FIXED COMPILER BLOCK FILTER: Ignore any button tags immediately inside block parsing sequences
    if tag == "button":
        return None

    text_line = re.sub(r'<[^>]+>', '', inner_content).strip()
    if not text_line or text_line == "undefined":
        return None
        
    # Unescape HTML formatting entities back to clean raw text symbols
    text_line = text_line.replace("&amp;", "&").replace("&lt;", "<").replace("&gt;", ">").replace("&quot;", '"').replace("back to journal", "")
        
    color_match = re.search(r'color:\s*(#[0-9a-fA-F]{3,6}|rgb\([^)]+\))', attributes + inner_content)
    hex_color = "#212529"
    if color_match:
        raw_color = color_match.group(1)
        if raw_color.startswith("#"): 
            hex_color = _normalize_font_color(raw_color)
        
    class_bold, class_color = _class_styles(attributes)
    if class_color:
        hex_color = class_color
    is_bold = class_bold or "font-weight: bold" in inner_content or "font-weight:700" in inner_content or "<b>" in inner_content or "<strong>" in inner_content
    is_header = tag.startswith("h") or "font-size: 2" in inner_content
    
    speaker_match = re.search(r'\bspeaker\s*(\d+)\b', text_line, flags=re.IGNORECASE)
    if speaker_match or re.match(r'^\[\d+:\d+\]', text_line):
        is_bold = True
        speaker_number = int(speaker_match.group(1)) if speaker_match else 1
        speaker_number = min(max(speaker_number, 1), len(SPEAKER_COLOR_KEYS))
        hex_color = CSS_COLOR_HEX[SPEAKER_COLOR_KEYS[speaker_number - 1]]

    list_style = None
    list_prefix = ""
    
    if tag == "li" or active_list_type is not None:
        if active_list_type == "NUMBERED":
            list_style = "NUMBERED"
            list_prefix = f"{current_index}. "
        else:
            list_style = "BULLET"
            list_prefix = "- "

    return {
        "text": text_line,
        "hex": hex_color,
        "rgb": hex_to_rgb(hex_color),
        "bold": is_bold,
        "is_header": is_header,
        "list_style": list_style,
        "list_prefix": list_prefix
    }

SPEAKER_COLOR_KEYS = (
    "blue", "orange", "green", "purple", "red", "teal", "yellow", "indigo",
    "pink", "cyan", "lime", "navy", "maroon", "olive", "brown", "violet",
    "darkgrey", "gray", "black", "magenta",
)

class _JournalHTMLParser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.segments = []
        self.styles = [{"bold": False, "hex": "#212529", "is_header": False, "list_style": None, "list_prefix": ""}]
        self.lists = []
        self.skip_depth = 0

    def handle_starttag(self, tag, attrs):
        attributes = " ".join(f'{name}="{value or ""}"' for name, value in attrs)
        if self.skip_depth:
            self.skip_depth += 1
            return
        if tag in {"aside", "button"} or "button" in attributes.lower():
            self.skip_depth = 1
            return
        if "ml:hidden" in attributes.lower():
            self.segments.append(create_space_segment())
            self.skip_depth = 1
            return
        style = self.styles[-1].copy()
        class_bold, class_color = _class_styles(attributes)
        inline_color = re.search(r'color:\s*(#[0-9a-fA-F]{3,6})', attributes)
        style["bold"] |= class_bold or tag in {"b", "strong"}
        style["hex"] = _normalize_font_color(class_color or (inline_color.group(1) if inline_color else style["hex"]))
        style["is_header"] |= tag.startswith("h")
        if tag in {"ul", "ol"}:
            self.lists.append(["NUMBERED" if tag == "ol" else "BULLET", 1])
        if tag == "li" and self.lists:
            style["list_style"] = self.lists[-1][0]
            style["list_prefix"] = f"{self.lists[-1][1]}. " if self.lists[-1][0] == "NUMBERED" else "- "
        self.styles.append(style)

    def handle_endtag(self, tag):
        if self.skip_depth:
            self.skip_depth -= 1
            return
        if len(self.styles) > 1:
            self.styles.pop()
        if tag == "li" and self.lists and self.lists[-1][0] == "NUMBERED":
            self.lists[-1][1] += 1
        if tag in {"ul", "ol"} and self.lists:
            self.lists.pop()

    def handle_data(self, data):
        text = data.replace("back to journal", "").strip()
        if not text or self.skip_depth:
            return
        style = self.styles[-1].copy()
        speaker = re.search(r"\bspeaker\s*(\d+)\b", text, re.IGNORECASE)
        if speaker or re.match(r"^\[?\d+:\d+\]?", text):
            number = int(speaker.group(1)) if speaker else 1
            style["bold"] = True
            style["hex"] = _normalize_font_color(CSS_COLOR_HEX[SPEAKER_COLOR_KEYS[min(max(number, 1), 20) - 1]])
        self.segments.append({"text": text, "hex": style["hex"], "rgb": hex_to_rgb(style["hex"]), "bold": style["bold"], "is_header": style["is_header"], "list_style": style["list_style"], "list_prefix": style["list_prefix"]})

def convert_html_to_styled_segments(html_body):
    """Recursively convert journal HTML while inheriting styles through child elements."""
    parser = _JournalHTMLParser()
    parser.feed(html_body)
    parser.close()
    if parser.segments:
        return parser.segments
    plain_text = re.sub(r'<[^>]+>', '', html_body).strip()
    return [{"text": line.strip(), "hex": "#212529", "rgb": hex_to_rgb("#212529"), "bold": False, "is_header": False, "list_style": None, "list_prefix": ""} for line in plain_text.split("\n") if line.strip()]
