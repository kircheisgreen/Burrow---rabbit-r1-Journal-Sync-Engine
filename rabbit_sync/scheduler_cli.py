import sys
import os
import json
import logging
import time

# Ensure parent scope context tracks system environment dependencies seamlessly
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from rabbit_sync.cron_logger import init_cron_logging
from rabbit_sync.auth_crawler import run_adaptive_routing_crawler
from rabbit_sync.sync_engine import run_headless_sync
from rabbit_sync.profile_manager import get_profiles_path, _decrypt_password

# Unpack structural file append boundaries instantly upon script awakening
init_cron_logging()

if __name__ == "__main__":
    # Handle direct execution parameter arrays parsing from windows background task vectors
    if len(sys.argv) >= 4:
        r_token = sys.argv[1]
        c_secret = sys.argv[2]
        
        try:
            active_wf = json.loads(sys.argv[3])
        except Exception:
            active_wf = []
            
        # Parse trailing named CLI string arguments dynamically 
        src = "Google Mail"
        fmt = "Google Doc"
        img = "PNG"
        dedup = False
        f_id = "root"
        profile_name = ""
        
        for i in range(len(sys.argv)):
            if sys.argv[i] == "--source" and i+1 < len(sys.argv): src = sys.argv[i+1]
            if sys.argv[i] == "--format" and i+1 < len(sys.argv): fmt = sys.argv[i+1]
            if sys.argv[i] == "--image" and i+1 < len(sys.argv): img = sys.argv[i+1]
            if sys.argv[i] == "--folder" and i+1 < len(sys.argv): f_id = sys.argv[i+1]
            if sys.argv[i] == "--profile" and i+1 < len(sys.argv): profile_name = sys.argv[i+1]

        crawler_username = None
        crawler_password = None
        if profile_name:
            try:
                with open(get_profiles_path(), "r", encoding="utf-8") as profiles_file:
                    profile_data = json.load(profiles_file).get(profile_name, {})
                crawler_username = profile_data.get("rabbit_username") or None
                encrypted_password = profile_data.get("rabbit_password") or ""
                if encrypted_password.startswith("gAAAA"):
                    crawler_password = _decrypt_password(encrypted_password) or None
                else:
                    crawler_password = encrypted_password or None
                logging.info(
                    "Loaded scheduled crawler credentials from profile '%s' (username present=%s, password present=%s, password decrypted=%s).",
                    profile_name,
                    bool(crawler_username),
                    bool(crawler_password),
                    bool(encrypted_password) and encrypted_password != crawler_password,
                )
                if encrypted_password.startswith("gAAAA") and not crawler_password:
                    logging.error("Saved Rabbit password could not be decrypted; re-enter it in the GUI and save the profile again.")
            except (OSError, ValueError) as profile_error:
                logging.warning("Could not load scheduled crawler profile '%s': %s", profile_name, profile_error)
            if sys.argv[i] == "--dedup": dedup = True
            
        fetch_started = time.monotonic()
        logging.info("BACKGROUND PHASE 1/2 START: Programmatic Auto-Fetch Journals (Visible Routing). Chromium should open in the interactive desktop session.")
        try:
            fetched_token = run_adaptive_routing_crawler(
                username=crawler_username,
                password=crawler_password,
                log_callback=logging.info,
                headless=False,
            )
        except Exception:
            logging.exception("Headless journal auto-fetch failed; continuing with the existing journal cache.")
            fetched_token = None
        sync_token = fetched_token or r_token
        if not fetched_token:
            logging.warning("Headless journal auto-fetch did not return a token; syncing the existing journal cache.")
        logging.info("BACKGROUND PHASE 1/2 END: Auto-fetch returned %s in %.1f seconds.", "fresh token" if fetched_token else "no token", time.monotonic() - fetch_started)

        sync_started = time.monotonic()
        logging.info("BACKGROUND PHASE 2/2 START: Start Sync Process.")
        sync_succeeded = run_headless_sync(
            token=sync_token,
            client_secret=c_secret, 
            active_workflows=active_wf, 
            log_callback=None, 
            force_sync=False, 
            master_parent_id=f_id, 
            source_mode=src, 
            format_mode=fmt, 
            image_mode=img, 
            dedup_mode=dedup
        )
        if sync_succeeded:
            logging.info("BACKGROUND PHASE 2/2 END: Start Sync Process completed successfully in %.1f seconds.", time.monotonic() - sync_started)
        else:
            logging.error("BACKGROUND PHASE 2/2 END: Start Sync Process reported failure after %.1f seconds.", time.monotonic() - sync_started)
