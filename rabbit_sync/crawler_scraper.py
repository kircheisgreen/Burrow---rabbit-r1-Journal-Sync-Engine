import json
import time
import re
import hashlib
import os

def _load_cached_fingerprints():
    dump_file = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "rabbit_journals_dump.json")
    try:
        with open(dump_file, "r", encoding="utf-8") as cache_file:
            cached_journals = json.load(cache_file)
    except (OSError, ValueError):
        return set(), set()

    source_fingerprints = {
        journal.get("sourceFingerprint")
        for journal in cached_journals
        if journal.get("sourceFingerprint")
    }
    legacy_keys = {
        f"{journal.get('createdAt', '')}|{journal.get('summary', '').strip().lower()}"
        for journal in cached_journals
        if journal.get("createdAt") and journal.get("summary")
    }
    return source_fingerprints, legacy_keys

def _load_cached_dates():
    dump_file = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "rabbit_journals_dump.json")
    try:
        with open(dump_file, "r", encoding="utf-8") as cache_file:
            cached_journals = json.load(cache_file)
    except (OSError, ValueError):
        return set()
    return {
        str(journal.get("createdAt", "")).strip()
        for journal in cached_journals
        if journal.get("createdAt")
    }

def run_scrolling_sweep(page, log_callback):
    """Progressively sweeps the sidebar axis down to force dynamic lazy-loaded day containers to render."""
    log_callback("Sweeping sidebar axis to reveal all historical calendar date blocks...")
    time.sleep(2.0)
    try:
        if page.is_closed():
            log_callback("⚠️ Chromium page closed before the journal sweep could begin.")
            return False
        for scroll_step in range(12):
            page.evaluate("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(1.5)
            page.keyboard.press("PageDown")
    except Exception as e:
        log_callback(f"Sidebar pre-scroll check handled: {str(e)}")
        return False
    return True

def extract_state_and_dom_data(page, log_callback, only_unfetched_dates=False):
    """
    Locates parent timeline containers matching 'div.mb-8.w-full', parses their specific date text,
    and programmatically clicks their immediate child 'div.flex-row' journal cards to harvest transcripts.
    """
    journals_list = []
    cached_source_fingerprints, cached_legacy_keys = _load_cached_fingerprints()
    cached_dates = _load_cached_dates() if only_unfetched_dates else set()
    skipped_cached = 0
    skipped_dates = 0
    log_callback("Initializing structural DOM traversal matrix (div.mb-8.w-full -> div.flex-row)...")

    try:
        if page.is_closed():
            log_callback("⚠️ Chromium page closed before DOM traversal could begin.")
            return []
        log_callback(f"Crawler page state: url={page.url} title={page.title()!r}")
        day_containers = page.locator("div.mb-8.w-full").all()
        if not day_containers:
            fallback_selectors = [
                "[class*='mb-8'][class*='w-full']",
                "[class*='journal']",
                "main",
            ]
            for selector in fallback_selectors:
                fallback_containers = page.locator(selector).all()
                log_callback(f"Crawler selector diagnostic: {selector} -> {len(fallback_containers)} matches.")
                if fallback_containers:
                    day_containers = fallback_containers
                    log_callback(f"Using fallback DOM container selector: {selector}")
                    break
        click_targets_queue = []
        seen_card_texts = set()

        for container in day_containers:
            try:
                container_text = container.inner_text().strip()
                if not container_text: continue
                
                lines = [l.strip() for l in container_text.split('\n') if l.strip()]
                if not lines: continue
                    
                header_line = str(lines).lower().strip()
                computed_date = time.strftime('%Y-%m-%d')
                
                date_match = re.search(r'(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*\s*(\d{1,2})', header_line)
                if date_match:
                    day_num = date_match.group(2).zfill(2)
                    computed_date = f"2026-08-{day_num}"
                elif re.search(r'\d{4}-\d{2}-\d{2}', header_line):
                    computed_date = re.search(r'\d{4}-\d{2}-\d{2}', header_line).group(0)
                elif "yesterday" in header_line:
                    yesterday_time = time.time() - 86400
                    computed_date = time.strftime('%Y-%m-%d', time.localtime(yesterday_time))
                elif "today" in header_line:
                    computed_date = time.strftime('%Y-%m-%d')
                else:
                    continue

                if only_unfetched_dates and computed_date in cached_dates:
                    skipped_dates += 1
                    continue

                aria_label_element = container.locator("svg[aria-label]").first
                source_aria_label = ""
                if aria_label_element.count() > 0:
                    source_aria_label = (aria_label_element.get_attribute("aria-label") or "").strip()

                child_cards = container.locator("div.flex-row").all()
                if not child_cards:
                    child_cards = container.locator(
                        "a, button, [role='button'], [class*='flex-row'], [class*='journal']"
                    ).all()
                for card in child_cards:
                    card_text = card.inner_text().strip()
                    if any(marker in card_text.lower() for marker in ["am", "pm"]) and len(card_text) > 5:
                        fingerprint = hashlib.sha256(
                            f"{computed_date}|{card_text}".encode("utf-8")
                        ).hexdigest()
                        card_lines = [line.strip() for line in card_text.split("\n") if line.strip()]
                        legacy_key = f"{computed_date}|{card_lines[0].lower() if card_lines else ''}"
                        if fingerprint in cached_source_fingerprints or legacy_key in cached_legacy_keys:
                            skipped_cached += 1
                            continue
                        if fingerprint not in seen_card_texts:
                            seen_card_texts.add(fingerprint)
                            click_targets_queue.append({
                                "element": card,
                                "raw_text": card_text,
                                "target_date": computed_date,
                                "source_aria_label": source_aria_label,
                            })
            except Exception: pass

        total_targets = len(click_targets_queue)
        log_callback(
            f"Mapped {total_targets} new journal cards; skipped {skipped_cached} already-cached cards and {skipped_dates} cached dates."
        )

        last_scraped_text = ""
        for idx, target in enumerate(click_targets_queue):
            try:
                card_el = target["element"]
                card_date = target["target_date"]
                source_aria_label = target.get("source_aria_label", "")
                
                lines = [l.strip() for l in target["raw_text"].split('\n') if l.strip()]
                
                # FIXED TYPE RESTRUCTURING: Extracts a single flat string value instead of the raw array list container
                raw_title_string = lines[0] if lines else "Scraped Journal Entry"
                summary_title = re.sub(r'[^\w\s\d_.-]', '', raw_title_string).strip()
                if len(summary_title) > 40: 
                    summary_title = summary_title[:37] + "..."
                
                card_el.scroll_into_view_if_needed(timeout=3000)
                card_el.click(timeout=5000)
                log_callback(f"[{idx + 1}/{total_targets}] Clicked Entry -> Target Folder: [{card_date}] Title: [{summary_title}]")
                
                detail_container = page.locator("div.flex.flex-grow.flex-row.justify-center.overflow-y-auto").first
                if detail_container.count() == 0:
                    detail_container = page.locator("div[class*='flex-row'][class*='justify-center'][class*='overflow-y-auto']").first

                start_hydrate_time = time.time()
                while (time.time() - start_hydrate_time) < 4.0:
                    current_raw_peek = detail_container.inner_text().strip()
                    if current_raw_peek and current_raw_peek != last_scraped_text:
                        break
                    time.sleep(0.3)

                journal_html = detail_container.inner_html().strip()
                last_scraped_text = detail_container.inner_text().strip()
                
                if not journal_html or len(journal_html) < 20:
                    journal_html = f"<div><p>{detail_container.inner_text()}</p></div>"
                    
                journals_list.append({
                    "id": f"scraped_click_{idx}_{int(time.time())}",
                    "summary": str(summary_title),
                    "content": journal_html,  
                    "createdAt": card_date,
                    "sourceAriaLabel": source_aria_label,
                    "sourceFingerprint": hashlib.sha256(
                        f"{card_date}|{target['raw_text']}".encode("utf-8")
                    ).hexdigest(),
                })
            except Exception as item_err:
                log_callback(f"⚠️ Skipped processing row item position index {idx}: {str(item_err)}")
                continue

    except Exception as global_err:
        log_callback(f"⚠️ DOM traversal loop breakdown anomaly: {str(global_err)}")

    final_unique_journals = []
    unique_fingerprints = set()
    for j in journals_list:
        content_hash = hashlib.md5(j["content"].encode('utf-8')).hexdigest()
        unique_key = f"{j['createdAt']}_{j['summary']}_{content_hash[:10]}"
        if unique_key not in unique_fingerprints:
            unique_fingerprints.add(unique_key)
            final_unique_journals.append(j)
            
    return final_unique_journals
