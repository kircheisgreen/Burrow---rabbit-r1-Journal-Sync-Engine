import re

def _clean_journal(content):
    return re.sub(r'<[^>]+>', '', content).strip()


def transform_to_cornell(base_name, content):
    """Apply the Cornell Method to a journal."""
    clean_text = _clean_journal(content)
    return (
        f"# Cornell Method: {base_name}\n\n"
        "Divide your page into a narrow left column for cues/questions, "
        "a wide right column for main notes, and a bottom section for a short summary.\n\n"
        "## CUES / QUESTIONS\n\n"
        "## MAIN NOTES\n"
        f"{clean_text}\n\n"
        "## SUMMARY\n"
    )

def transform_to_outlining(base_name, content):
    """Apply Outlining to a journal."""
    clean_text = _clean_journal(content)
    lines = [line.strip() for line in clean_text.split('\n') if line.strip()]
    outline = [
        f"# Outlining: {base_name}",
        "",
        "Use main headings for major topics with indented sub-points and details underneath for clear, hierarchical tracking.",
        "",
    ]
    outline.extend(f"- {line}" for line in lines)
    return "\n".join(outline) + "\n"

def transform_to_boxing(base_name, content):
    """Apply Boxing to a journal."""
    clean_text = _clean_journal(content)
    return (
        f"# Boxing: {base_name}\n\n"
        "Group related sub-points into distinct visual boxes or grids on the page to separate different ideas clearly.\n\n"
        "[ BOX 1: JOURNAL ]\n"
        f"{clean_text}\n\n"
        "[ BOX 2: RELATED SUB-POINTS ]\n"
    )

def transform_to_mindmap_text(base_name, content):
    """Apply Mind Mapping to a journal."""
    clean_text = _clean_journal(content)
    raw_lines = [line.strip() for line in clean_text.split('\n') if line.strip()]

    title_label = (base_name or 'Journal Overview').strip()

    topics = []
    for line in raw_lines:
        clean_line = re.sub(r'^\[\d+:\d+\]\s*(Speaker\s*\d+:)?', '', line).strip()
        clean_line = re.sub(r'^(Speaker\s*\d+:|Presenter\s*:|Host\s*:)', '', clean_line, flags=re.I)
        clean_line = clean_line.strip('"\'')
        if not clean_line or len(clean_line) <= 10:
            continue
        if clean_line.lower() in {'summary', 'notes'}:
            continue
        if clean_line not in topics:
            topics.append(clean_line)
        if len(topics) >= 8:
            break

    if not topics:
        topics = [
            "Big picture themes",
            "Evidence and examples",
            "Key takeaways",
            "Action steps",
            "Questions to revisit"
        ]

    branch_one = topics[0]
    branch_two = topics[1] if len(topics) > 1 else "Supporting ideas"
    branch_three = topics[2] if len(topics) > 2 else "Connections"
    detail_nodes = topics[3:] if len(topics) > 3 else []

    mindmap_outline = f"# Mind Mapping: {title_label}\n\n"
    mindmap_outline += "Draw a central topic in the middle of the page and branch out with connecting bubbles for subtopics and associated concepts.\n\n"

    mindmap_outline += "                    +---------------------------------------------+\n"
    mindmap_outline += f"                    |            CENTRAL TOPIC: {title_label[:27].ljust(27)} |\n"
    mindmap_outline += "                    +---------------------------------------------+\n"
    mindmap_outline += "                                      │\n"
    mindmap_outline += f"                                      ├── Main Branch: {branch_one}\n"
    mindmap_outline += f"                                      │      ├── Detail: {topics[3] if len(topics) > 3 else 'Supporting evidence'}\n"
    mindmap_outline += f"                                      │      └── Detail: {topics[4] if len(topics) > 4 else 'Link to broader context'}\n"
    mindmap_outline += f"                                      │\n"
    mindmap_outline += f"                                      ├── Main Branch: {branch_two}\n"
    mindmap_outline += f"                                      │      ├── Detail: {topics[5] if len(topics) > 5 else 'Connection to other ideas'}\n"
    mindmap_outline += f"                                      │      └── Detail: {topics[6] if len(topics) > 6 else 'Implications or examples'}\n"
    mindmap_outline += f"                                      │\n"
    mindmap_outline += f"                                      └── Main Branch: {branch_three}\n"

    if detail_nodes:
        for idx, node in enumerate(detail_nodes[:4], start=1):
            mindmap_outline += f"                                             ├── Detail {idx}: {node}\n"

    mindmap_outline += f"\nJournal source:\n{clean_text}\n"
    return mindmap_outline
