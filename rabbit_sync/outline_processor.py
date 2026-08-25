import re
from rabbit_sync.utils import extract_and_color_speakers

def process_colored_markdown_outline(raw_outline):
    """Parses an outline string line-by-line to inject HTML font tags inside transcript nodes."""
    colored_outline_lines = []
    for line in raw_outline.split('\n'):
        # Strip out leading tab spaces to allow regex evaluations to run safely
        stripped_line = line.strip()
        outline_segment = extract_and_color_speakers(stripped_line)
        
        # Verify the segment contains an explicit speaker match (5-item tuple with a valid timestamp)
        if outline_segment and len(outline_segment) == 5 and outline_segment[0] is not None:
            ts, spk, text_body, hex_c, rgb_d = outline_segment
            
            # Isolate the structural leading tab prefix (e.g., '    - **Timestamp Audio Marker:** ')
            match = re.match(r'^(\s*-\s*\*\*[^*]+\*\*)\s*(.*)$', line)
            if match:
                prefix = match.group(1)
                colored_outline_lines.append(f'{prefix} <font color="{hex_c}"><b>{ts} {spk}:</b> {text_body}</font>')
            else:
                colored_outline_lines.append(f'<font color="{hex_c}">{line}</font>')
        else:
            colored_outline_lines.append(line)
            
    return "\n".join(colored_outline_lines)

def process_colored_docs_outline(raw_outline):
    """Tokenizes an outline string into an array of styled segments for native Google Docs uploads."""
    docs_outline_segments = []
    for line in raw_outline.split('\n'):
        stripped_line = line.strip()
        segment = extract_and_color_speakers(stripped_line)
        
        # FIXED: Added safe length tracking to handle both 5-item speaker rows and 5-item fallback metadata text rows
        if segment and len(segment) == 5 and segment[0] is not None:
            ts, spk, text_body, hex_c, rgb_d = segment
            match = re.match(r'^(\s*-\s*\*\*[^*]+\*\*)\s*(.*)$', line)
            full_txt = f"{match.group(1)} {ts} {spk}: {text_body}" if match else line
            docs_outline_segments.append((ts, spk, full_txt, hex_c, rgb_d))
        else:
            # Fallback for plain structural lines or rows that returned standard formats
            docs_outline_segments.append((None, None, line, "#212529", {"red": 0.13, "green": 0.15, "blue": 0.16}))
            
    return docs_outline_segments
