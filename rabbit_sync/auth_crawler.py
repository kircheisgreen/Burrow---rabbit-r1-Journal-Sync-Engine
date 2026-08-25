import os
import json
import time
from playwright.sync_api import sync_playwright

from rabbit_sync.crawler_navigation import execute_multi_hop_navigation
from rabbit_sync.crawler_scraper import run_scrolling_sweep, extract_state_and_dom_data

PROFILE_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "browser_session")
DUMP_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "rabbit_journals_dump.json")

def get_automatic_token(log_callback=print, headless=False, only_unfetched_dates=False):
    return run_adaptive_routing_crawler(
        username=None,
        password=None,
        log_callback=log_callback,
        headless=headless,
        only_unfetched_dates=only_unfetched_dates,
    )

def run_adaptive_routing_crawler(username=None, password=None, log_callback=print, headless=False, only_unfetched_dates=False):
    """Coordinates the browser window workflow, executing direct target DOM parsing on the target details view."""
    log_callback(f"Crawler browser launch requested: mode={'HEADLESS' if headless else 'VISIBLE'}.")
    with sync_playwright() as p:
        context = p.chromium.launch_persistent_context(
            user_data_dir=PROFILE_DIR,
            headless=headless,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--disable-gpu",
                "--disable-dev-shm-usage",
                "--window-size=1920,1080",
            ]
        )
        page = context.new_page()
        page.on("crash", lambda: log_callback("⚠️ Chromium page crashed during headless journal routing."))
        
        # Drive browser immediately onto hole.rabbit.tech/journal/details
        nav_success = execute_multi_hop_navigation(
            page, username, password, log_callback, headless=headless
        )
        if not nav_success:
            context.close()
            return None
            
        if not run_scrolling_sweep(page, log_callback):
            context.close()
            return None
        
        # Gather text items from your screen interface grouped precisely by parent containers
        final_unique_journals = extract_state_and_dom_data(
            page,
            log_callback,
            only_unfetched_dates=only_unfetched_dates,
        )
        context.close()

    if final_unique_journals:
        with open(DUMP_FILE, "w", encoding="utf-8") as f:
            json.dump(final_unique_journals, f, indent=4)
        log_callback(f"Successfully scraped and cached {len(final_unique_journals)} total journal logs from the long-form details sub-page!")
        log_callback(f"Programmatic Auto-Fetch Journals completed successfully: {len(final_unique_journals)} journals cached.")
        return "BROWSER_COOKIE_AUTHENTICATED_SESSION_OK"
        
    log_callback("⚠️ Scraper completed loop pass. No new layout containers found.")
    log_callback("Programmatic Auto-Fetch Journals completed without new journals.")
    return None
