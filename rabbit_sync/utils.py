import re

def parse_metadata(text, fallback_date="Unspecified-Date"):
    """Extracts lecturer name and date string from the journal text body."""
    lecturer_match = re.search(r'(?:Lecturer|Speaker|Prof|Instructor):\s*([^\n,]+)', text, re.IGNORECASE)
    date_match = re.search(r'(?:Date):\s*([\d]{4}-[\d]{2}-[\d]{2})', text)
    
    has_meta = bool(lecturer_match or date_match)
    lecturer = lecturer_match.group(1).strip() if lecturer_match else "General Lecturer"
    date_str = date_match.group(1).strip() if date_match else fallback_date
    
    return lecturer, date_str, has_meta

def extract_and_color_speakers(text):
    """
    Scans text paragraph lines sequentially. 
    Activates unique speaker formatting after identifying ANY variant of the Transcript marker,
    handling both flat raw formats and structured bulleted list outlines.
    """
    palette = [
        {"hex": "#0D6EFD", "rgb": {"red": 0.05, "green": 0.43, "blue": 0.99}},  # Blue
        {"hex": "#DC3545", "rgb": {"red": 0.86, "green": 0.21, "blue": 0.27}},  # Red
        {"hex": "#198754", "rgb": {"red": 0.10, "green": 0.53, "blue": 0.33}},  # Green
        {"hex": "#D63384", "rgb": {"red": 0.84, "green": 0.20, "blue": 0.52}},  # Pink
        {"hex": "#FD7E14", "rgb": {"red": 0.99, "green": 0.49, "blue": 0.08}},  # Orange
        {"hex": "#6F42C1", "rgb": {"red": 0.44, "green": 0.26, "blue": 0.76}}   # Purple
    ]
    
    speaker_map = {}
    color_index = 0
    segments = []
    in_transcript_section = False
    
    lines = text.split('\n')
    
    for line in lines:
        cleaned_line = line.strip()
        if not cleaned_line:
            continue
            
        # Flexible Entry Rule: Catches "Transcript", "## I. Transcript", "# Transcript"
        if re.search(r'transcript', cleaned_line.lower()) and len(cleaned_line) < 30:
            in_transcript_section = True
            segments.append((None, None, line, "#212529", {"red": 0.13, "green": 0.15, "blue": 0.16}))
            continue
            
        # Regex Model 1: Flat transcript lines e.g. "[0:03] Speaker 1: text"
        flat_match = re.match(r'^(\[\d{1,2}:\d{2}\])\s*(Speaker\s+\d+|Dr\.\s+[\w\s]+|[\w\s\d_-]+?)(?::|\s|$)(.*)$', cleaned_line, re.IGNORECASE)
        
        # Regex Model 2: Bullet outline structures e.g. "- **Timestamp Audio Marker:** [0:03] Speaker 1: text"
        outline_match = re.match(r'^(\s*-\s*\*\*[^*]+\*\*)\s*(\[\d{1,2}:\d{2}\])\s*(Speaker\s+\d+|Dr\.\s+[\w\s]+|[\w\s\d_-]+?)(?::|\s|$)(.*)$', line, re.IGNORECASE)
        
        if in_transcript_section and outline_match:
            bullet_prefix = outline_match.group(1).strip()
            time_prefix = outline_match.group(2).strip()
            speaker_name = outline_match.group(3).strip()
            dialogue_text = outline_match.group(4).strip()
            
            # Clean trailing punctuation from speaker names safely
            speaker_name = re.sub(r'[:,\s]+$', '', speaker_name)
            
            if speaker_name not in speaker_map:
                speaker_map[speaker_name] = palette[color_index % len(palette)]
                color_index += 1
                
            current_style = speaker_map[speaker_name]
            
            # Reconstruct the line as a colored outline node segment bundle
            rebuilt_text = f"{bullet_prefix} {time_prefix} {speaker_name}: {dialogue_text}"
            segments.append((time_prefix, speaker_name, rebuilt_text, current_style["hex"], current_style["rgb"]))
            
        elif in_transcript_section and flat_match:
            time_prefix = flat_match.group(1).strip()
            speaker_name = flat_match.group(2).strip()
            dialogue_text = flat_match.group(3).strip()
            
            speaker_name = re.sub(r'[:,\s]+$', '', speaker_name)
            
            if speaker_name not in speaker_map:
                speaker_map[speaker_name] = palette[color_index % len(palette)]
                color_index += 1
                
            current_style = speaker_map[speaker_name]
            segments.append((time_prefix, speaker_name, dialogue_text, current_style["hex"], current_style["rgb"]))
        else:
            # Document headers descriptions fallback rows rendering
            segments.append((None, None, line, "#212529", {"red": 0.13, "green": 0.15, "blue": 0.16}))
            
    return segments
