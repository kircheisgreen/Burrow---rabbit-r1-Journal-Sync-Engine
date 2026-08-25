import time
from rabbit_sync.crawler_typing import human_type_string

def click_human_verification(page, log_callback, timeout_seconds=30):
    selectors = [
        "input[type='checkbox'][aria-label='Verify you are human']",
        "input[type='checkbox']",
        "[role='checkbox']",
        "label:has-text('Verify you are human')",
        "text=Verify you are human",
        "[aria-label*='human' i]",
    ]
    deadline = time.time() + timeout_seconds
    diagnostic_logged = False
    while time.time() < deadline:
        if not diagnostic_logged:
            frame_urls = [frame.url for frame in page.frames]
            log_callback(f"Human-verification scan: {len(frame_urls)} browser frame(s): {frame_urls}")
            diagnostic_logged = True
        for frame in page.frames:
            for selector in selectors:
                try:
                    candidate = frame.locator(selector).first
                    if candidate.count() > 0:
                        if selector == "input[type='checkbox'][aria-label='Verify you are human']":
                            log_callback(f"Found exact human-verification checkbox in frame: {frame.url!r}")
                            if not candidate.is_checked():
                                try:
                                    candidate.check(timeout=3000, force=True)
                                except Exception:
                                    candidate.click(timeout=3000, force=True)
                        else:
                            try:
                                candidate.click(timeout=3000)
                            except Exception:
                                candidate.click(timeout=3000, force=True)
                        if selector.startswith("input[type='checkbox']") and not candidate.is_checked():
                            log_callback("⚠️ Human-verification checkbox click did not change its checked state.")
                            continue
                        log_callback("Human-verification checkbox clicked; waiting for challenge validation...")
                        time.sleep(2.0)
                        return True
                except Exception:
                    continue
        time.sleep(0.5)

    log_callback(
        f"⚠️ Human-verification control was not rendered after {timeout_seconds} seconds; "
        f"current page={page.url!r}."
    )
    return False

def execute_multi_hop_navigation(page, username, password, log_callback, headless=False):
    """
    Drives the browser window sequentially across URLs while routing past security login gates.
    FIXED: Pauses for 5 seconds upon detecting /rabbitos redirection, then forces navigation 
    straight to the final journal details matrix layout.
    """
    
    # HOP 1: Navigate directly to the split-pane database catalog path to initiate auth checks
    target_url = "https://hole.rabbit.tech/journal/details"
    log_callback(f"Routing directly to data target split-pane details matrix: {target_url}...")
    try:
        page.goto(target_url, wait_until="commit")
        
        # Allow the server-side NextAuth engine to process client telemetry and determine login state
        log_callback("Monitoring secure directory authorization routing context...")
        time.sleep(4.0)
    except Exception as e:
        log_callback(f"⚠️ Initial routing connection glitch: {str(e)}")
        
    # Evaluate the address bar state now that the dynamic redirect has stabilized
    current_url = page.url.lower().strip()
    is_login_page = (
        "login.rabbit.tech" in current_url or 
        "auth" in current_url or 
        page.locator("input[type='password']").count() > 0 or 
        page.locator("input[name='username']").count() > 0 or 
        page.locator("input[type='email']").count() > 0
    )
    
    if is_login_page:
        log_callback("🔒 Secure Login Gateway Intercepted (https://rabbit.tech)!")
        
        if username and password:
            try:
                user_box = page.locator("input[type='email'], input[name='username'], input[id='username'], input[type='text']").first
                log_callback("Waiting for form elements to hydrate into view...")
                user_box.wait_for(state="visible", timeout=15000)
                
                log_callback("Auto-populating email account parameters...")
                human_type_string(user_box, username)
                time.sleep(0.8)
                
                btn_next = page.locator("button[type='submit'], button[name='action'], button:has-text('Continue')").first
                if btn_next.count() > 0:
                    btn_next.click()
                    time.sleep(1.5)
                    
                pass_box = page.locator("input[type='password'], input[name='password'], input[id='password']").first
                pass_box.wait_for(state="visible", timeout=15000)
                
                log_callback("Auto-populating profile account password credentials...")
                human_type_string(pass_box, password)
                time.sleep(0.8)

                click_human_verification(page, log_callback)
                
                btn_submit = page.locator("button[type='submit'], button[name='action']").first
                btn_submit.click()
                log_callback("Form parameters submitted. Awaiting redirection token hydration...")
                
                # FIXED DELAY HANDSHAKE: Wait for the browser to transit onto the dynamic redirect layout
                page.wait_for_url("https://hole.rabbit.tech/**", timeout=45000)
                
                # OPTIMIZATION ACTION GATING: If landed on the intermediate endpoint branch, freeze and push
                if "rabbitos" in page.url.lower():
                    log_callback("🕒 Intermediate redirect branch (/rabbitos) identified. Freezing loop execution for 5 seconds...")
                    time.sleep(5.0)
                    
                    log_callback(f"Redirection pause complete. Enforcing hard navigation straight to final data matrix: {target_url}...")
                    page.goto(target_url, wait_until="load")
                
                # Verify that the final target session settles cleanly
                page.wait_for_url(f"{target_url}**", timeout=30000)
                log_callback("Redirection pipeline cleared! Session token handshakes successfully completed.")
                time.sleep(4.0)
                
            except Exception as e:
                log_callback(f"⚠️ Form Auto-Population bypassed by security filters: {str(e)}")
                log_callback("🕒 Extended Manual Gateway Active: Please enter credentials manually inside the window canvas...")
                try:
                    page.wait_for_url("https://hole.rabbit.tech/**", timeout=300000)
                    if "rabbitos" in page.url.lower():
                        log_callback("🕒 Manual sync hit /rabbitos branch. Pausing 5 seconds before routing...")
                        time.sleep(5.0)
                        page.goto(target_url, wait_until="load")
                    page.wait_for_url(f"{target_url}**", timeout=30000)
                    log_callback("Manual authentication successful! Context cleared.")
                    time.sleep(3.0)
                except Exception:
                    return False
        else:
            if headless:
                log_callback("⚠️ Headless auto-fetch requires an active authenticated browser session.")
                return False
            log_callback("🕒 GUI Username/Password fields are empty. Initializing manual login verification window...")
            try:
                page.wait_for_url("https://hole.rabbit.tech/**", timeout=300000)
                if "rabbitos" in page.url.lower():
                    time.sleep(5.0)
                    page.goto(target_url, wait_until="load")
                page.wait_for_url(f"{target_url}**", timeout=30000)
                time.sleep(3.0)
            except Exception:
                return False

    return True
