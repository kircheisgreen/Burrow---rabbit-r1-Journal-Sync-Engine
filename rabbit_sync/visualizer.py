import math
import io
import re
import logging
from reportlab.lib import colors
from reportlab.pdfgen import canvas
from xml.sax.saxutils import escape
from rabbit_sync.pdf_fonts import register_unicode_fonts

# CRITICAL FIX: Force Matplotlib to use the headless, thread-safe Agg backend.
# This prevents thread context resource locks and fixes blank/empty image files on Windows.
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import xml.etree.ElementTree as ET


def clean_transcript_to_keywords(content):
    """Extract meaningful branches from either raw transcript text or a structured Mind Mapping outline."""
    if not content:
        return ["Journal Summary", "Key Discussion Points"]

    content = re.sub(r'<[^>]+>', '', content)
    lines = [line.strip() for line in content.split('\n') if line.strip()]
    keywords = []

    # Prefer the generated Mind Mapping outline structure when it exists.
    # Parse the whole content so connector characters and line formatting do not hide the [Node n] branches.
    for match in re.finditer(r'\[Node\s*\d+\]\s*:\s*(.+)', content, flags=re.MULTILINE):
        cleaned = match.group(1).strip()
        if cleaned and cleaned not in keywords:
            keywords.append(cleaned)
            if len(keywords) >= 6:
                break

    if not keywords:
        for line in lines:
            cleaned = line.strip("-*\u2022 # \t")
            if not cleaned:
                continue

            cleaned = re.sub(r'^\[\d{1,2}:\d{2}\]\s*', '', cleaned)
            cleaned = re.sub(r'^(speaker\s*\d+\s*[:\-]|presenter\s*[:\-]|host\s*[:\-])', '', cleaned, flags=re.I)
            cleaned = cleaned.strip('"\'"')
            if not cleaned or len(cleaned) < 5:
                continue

            if re.match(r'^(speaker|presenter|host)\b', cleaned, flags=re.I):
                continue

            if ':' in cleaned:
                _, remainder = cleaned.split(':', 1)
                cleaned = remainder.strip()

            cleaned = re.sub(r'\s*[-–—]\s*\S.*$', '', cleaned)
            cleaned = re.sub(r'\s{2,}', ' ', cleaned).strip(' .;:!?')

            if not cleaned or len(cleaned) < 6:
                continue

            if cleaned.lower() in {'speaker 1', 'speaker 2', 'speaker 3', 'summary', 'notes'}:
                continue

            if cleaned not in keywords:
                keywords.append(cleaned)

            if len(keywords) >= 6:
                break

    if not keywords:
        keywords = [
            "Core discussion themes",
            "Key takeaways",
            "Action items",
            "Decision points",
            "Open questions",
        ]

    return keywords[:6]


def generate_mindmap_svg(central_topic, content):
    """Render the visualization from the structured Mind Mapping document text, falling back to transcript parsing only when needed."""
    subtopics = clean_transcript_to_keywords(content)

    width, height = 800, 600
    cx, cy = width // 2, height // 2
    radius = 220
    visible_central = (central_topic or 'Journal Overview').strip() or 'Journal Overview'
    central_label = visible_central

    svg_lines = [
        f'<svg xmlns="http://w3.org" viewBox="0 0 {width} {height}" width="{width}" height="{height}">',
        '  <rect width="100%" height="100%" fill="#F8F9FA"/>',
        '  <!-- Connection Vector Paths -->'
    ]

    nodes_svg = []
    num_nodes = len(subtopics)
    if num_nodes == 0:
        subtopics = ["Journal Summary"]
        num_nodes = 1

    for i, topic in enumerate(subtopics):
        angle = (2 * math.pi / num_nodes) * i
        nx = int(cx + radius * math.cos(angle))
        ny = int(cy + radius * math.sin(angle))

        safe_topic = escape(topic)
        svg_lines.append(f'  <line x1="{cx}" y1="{cy}" x2="{nx}" y2="{ny}" stroke="#0D6EFD" stroke-width="2.5" stroke-dasharray="5,5" />')
        nodes_svg.append(f'  <circle cx="{nx}" cy="{ny}" r="65" fill="#FFFFFF" stroke="#495057" stroke-width="2"/>')
        nodes_svg.append(f'  <text x="{nx}" y="{ny + 4}" font-family="Arial, sans-serif" font-size="11" font-weight="bold" fill="#212529" text-anchor="middle">{safe_topic}</text>')

    svg_lines.extend(nodes_svg)
    svg_lines.append('  <!-- Central Core Master Node -->')

    svg_lines.append(f'  <rect x="{cx - 120}" y="{cy - 40}" width="240" height="80" rx="15" fill="#212529" stroke="#495057" stroke-width="3"/>')
    svg_lines.append(f'  <text x="{cx}" y="{cy + 6}" font-family="Arial, sans-serif" font-size="12" font-weight="bold" fill="#FFFFFF" text-anchor="middle">{escape(central_label)}</text>')
    svg_lines.append('</svg>')

    return "\n".join(svg_lines)

def convert_svg_to_png_bytes(svg_string):
    """Converts the clean semantic keyword SVG model into a high-quality rasterized PNG file utilizing a headless canvas context."""
    try:
        root = ET.fromstring(svg_string)
        
        # Explicitly declare and clean figure boundaries
        fig, ax = plt.subplots(figsize=(8, 6), dpi=150)
        ax.set_facecolor('#F8F9FA')
        fig.patch.set_facecolor('#F8F9FA')
        
        # Draw dotted connectors
        for line in root.findall('{http://w3.org}line'):
            x1, y1 = float(line.get('x1')), 600 - float(line.get('y1'))
            x2, y2 = float(line.get('x2')), 600 - float(line.get('y2'))
            ax.plot([x1, x2], [y1, y2], color='#0D6EFD', linestyle=':', linewidth=2, zorder=1)
            
        # Draw node circles
        for circle in root.findall('{http://w3.org}circle'):
            cx, cy = float(circle.get('cx')), 600 - float(circle.get('cy'))
            ax.add_patch(plt.Circle((cx, cy), 65, color='#FFFFFF', ec='#495057', lw=1.5, zorder=2))
            
        # Draw center rectangle bounding block
        for rect in root.findall('{http://w3.org}rect'):
            if rect.get('x'):
                x, y = float(rect.get('x')), 600 - float(rect.get('y')) - float(rect.get('height'))
                w, h = float(rect.get('width')), float(rect.get('height'))
                ax.add_patch(plt.Rectangle((x, y), w, h, color='#212529', ec='#495057', lw=2, zorder=3))
                
        # Inject matching text labels onto layout anchors
        for text in root.findall('{http://w3.org}text'):
            tx, ty = float(text.get('x')), 600 - float(text.get('y'))
            val = text.text
            
            is_center = ty > 250 and ty < 350 and tx > 350 and tx < 450
            color = '#FFFFFF' if is_center else '#212529'
            fontsize = 11 if is_center else 9
            
            ax.text(tx, ty, val, horizontalalignment='center', verticalalignment='center', fontname='Arial', fontsize=fontsize, fontweight='bold', color=color, zorder=4)
            
        ax.set_xlim(0, 800)
        ax.set_ylim(0, 600)
        plt.axis('off')
        
        buf = io.BytesIO()
        plt.savefig(buf, format='png', bbox_inches='tight', pad_inches=0.1)
        buf.seek(0)
        plt.close(fig)
        return buf.read()
    except Exception as e:
        logging.error(f"Matplotlib background image drawing fault: {str(e)}")
        # Ultimate basic pixel stream fallback if initialization fails
        return b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x02\x00\x00\x00\x90wS\xde\x00\x00\x00\x0cIDATx\x9cc\x00\x01\x00\x00\x05\x00\x01\r\n-\xb4\x00\x00\x00\x00IEND\xaeB`\x82'

def convert_svg_to_pdf_bytes(svg_string):
    """Convert the generated SVG visualization primitives into a vector PDF."""
    try:
        root = ET.fromstring(svg_string)
        width, height = 800, 600
        output = io.BytesIO()
        pdf = canvas.Canvas(output, pagesize=(width, height))
        regular_font, bold_font = register_unicode_fonts()
        pdf.setFillColorRGB(248 / 255, 249 / 255, 250 / 255)
        pdf.rect(0, 0, width, height, stroke=0, fill=1)

        svg_namespace = "{http://www.w3.org/2000/svg}"
        for line in root.findall(f"{svg_namespace}line"):
            pdf.setStrokeColorRGB(13 / 255, 110 / 255, 253 / 255)
            pdf.setLineWidth(float(line.get("stroke-width", 2.5)))
            pdf.setDash(5, 5)
            pdf.line(
                float(line.get("x1")), height - float(line.get("y1")),
                float(line.get("x2")), height - float(line.get("y2")),
            )
        pdf.setDash()

        for circle in root.findall(f"{svg_namespace}circle"):
            center_x = float(circle.get("cx"))
            center_y = height - float(circle.get("cy"))
            radius = float(circle.get("r", 65))
            pdf.setFillColor(colors.white)
            pdf.setStrokeColorRGB(73 / 255, 80 / 255, 87 / 255)
            pdf.setLineWidth(float(circle.get("stroke-width", 2)))
            pdf.circle(center_x, center_y, radius, stroke=1, fill=1)

        for rect in root.findall(f"{svg_namespace}rect"):
            if rect.get("x") is None:
                continue
            x = float(rect.get("x"))
            y = height - float(rect.get("y")) - float(rect.get("height"))
            rect_width = float(rect.get("width"))
            rect_height = float(rect.get("height"))
            pdf.setFillColorRGB(33 / 255, 37 / 255, 41 / 255)
            pdf.setStrokeColorRGB(73 / 255, 80 / 255, 87 / 255)
            pdf.setLineWidth(float(rect.get("stroke-width", 2)))
            pdf.roundRect(x, y, rect_width, rect_height, 15, stroke=1, fill=1)

        for text in root.findall(f"{svg_namespace}text"):
            value = text.text or ""
            center_x = float(text.get("x"))
            center_y = height - float(text.get("y"))
            is_center = 350 < center_x < 450 and 250 < center_y < 350
            pdf.setFillColor(colors.white if is_center else colors.HexColor("#212529"))
            pdf.setFont(bold_font, 12 if is_center else 11)
            pdf.drawCentredString(center_x, center_y, value)

        pdf.showPage()
        pdf.save()
        return output.getvalue()
    except Exception as error:
        logging.error(f"PDF visualization conversion fault: {error}")
        return b"%PDF-1.4\n%%EOF\n"
