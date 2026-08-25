import os
import json
import shutil
import threading
from tkinter import messagebox
from rabbit_sync.auth_crawler import run_adaptive_routing_crawler
from rabbit_sync.auth_crawler import PROFILE_DIR
from rabbit_sync.sync_engine import run_headless_sync
# Import decoupled modular helpers
from rabbit_sync.profile_manager import save_profile_to_disk, load_profile_from_disk, get_profiles_path, _decrypt_password
from rabbit_sync.google_folder_loader import async_load_drive_directories
from rabbit_sync.windows_task_registrar import deploy_windows_task_scheduler, remove_windows_task_from_system, TASK_NAME

class GUIEventHandlers:
    def __init__(self, app):
        self.app = app

    def browse_credentials(self):
        from tkinter import filedialog
        filename = filedialog.askopenfilename(filetypes=[("JSON files", "*.json")])
        if filename: 
            self.app.state.client_secret_var.set(filename)

    def trigger_auto_auth(self):
        only_unfetched_dates = self.app.state.only_unfetched_dates_var.get()
        user_str = self.app.state.rabbit_username_var.get().strip()
        pass_str = self.app.state.rabbit_password_var.get().strip()
        if not user_str or not pass_str:
            user_str, pass_str = self._load_saved_rabbit_credentials(user_str, pass_str)
        threading.Thread(
            target=self._auth_loop,
            args=(user_str, pass_str, only_unfetched_dates),
        ).start()

    def _load_saved_rabbit_credentials(self, username, password):
        profile_name = self.app.state.active_profile_var.get().strip()
        try:
            with open(get_profiles_path(), "r", encoding="utf-8") as profiles_file:
                profile_data = json.load(profiles_file).get(profile_name, {})
            username = username or str(profile_data.get("rabbit_username") or "").strip()
            saved_password = str(profile_data.get("rabbit_password") or "")
            if not password and saved_password:
                password = (
                    _decrypt_password(saved_password)
                    if saved_password.startswith("gAAAA")
                    else saved_password
                )
                if saved_password.startswith("gAAAA") and not password:
                    self.app.log(
                        f"⚠️ Saved Rabbit password for profile [{profile_name}] cannot be decrypted. "
                        "Re-enter the password and save the profile again."
                    )
            self.app.log(
                f"Loaded Rabbit login credentials from active profile [{profile_name}] "
                f"(username present={bool(username)}, password present={bool(password)})."
            )
        except (OSError, ValueError) as profile_error:
            self.app.log(f"⚠️ Could not load Rabbit credentials from profile: {profile_error}")
        return username, password

    # FIXED v0.4.1: Nesting block re-aligned perfectly inside the GUIEventHandlers namespace
    def _auth_loop(self, user_str, pass_str, only_unfetched_dates=False):
        token = run_adaptive_routing_crawler(
            username=user_str,
            password=pass_str,
            log_callback=self.app.log,
            only_unfetched_dates=only_unfetched_dates,
        )
        if token:
            self.app.state.access_token_var.set(token)
            self.app.log("🚀 System Progress: Journals retrieved and cached automatically from browser database cookies!")
            
            # Post-Fetch Automation Sub-Routine Chaining Check
            automation_selection = self.app.state.post_fetch_action_var.get()
            
            if automation_selection == "SYNC":
                self.app.log("⚡ Auto-Trigger: Launching 'Start Sync Process' pipeline...")
                self.start_sync_thread(force=False)
            elif automation_selection == "FORCE":
                self.app.log("⚡ Auto-Trigger: Launching 'Force Override Sync All' pipeline...")
                self.start_sync_thread(force=True)
            else:
                self.app.log("💤 Auto-Trigger: Manual Sync mode active. Execution paused pending interaction choice.")
        else:
            self.app.log("⚠️ Auth Failure: Failed to retrieve access token automatically. Verify active browser session.")

    def trigger_load_folders(self):
        self.app.log("Connecting to Google Drive to query file structure directories...")
        threading.Thread(target=lambda: async_load_drive_directories(self.app.state, self.app.log)).start()

    def clear_cache(self):
        if not messagebox.askyesno("Confirm", "Are you sure you want to clear the cache?"):
            return
        self._run_cleanup(
            "Clear Cache",
            [
                os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "rabbit_journals_dump.json"),
                os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "sync_history.json"),
            ],
        )

    def clear_session(self):
        if not messagebox.askyesno("Confirm", "Are you sure you want to clear the session?"):
            return
        self._run_cleanup("Clear Session", [PROFILE_DIR], remove_directory=True)

    def clear_logs(self):
        if not messagebox.askyesno("Confirm", "Are you sure you want to clear the log?"):
            return
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self._run_cleanup("Clear Log", [os.path.join(project_root, "sync_service.log")])

    def _run_cleanup(self, action_name, paths, remove_directory=False):
        threading.Thread(
            target=self._cleanup_paths,
            args=(action_name, paths, remove_directory),
            daemon=True,
        ).start()

    def _cleanup_paths(self, action_name, paths, remove_directory=False):
        deleted = 0
        missing = 0
        failures = []
        for path in paths:
            if not os.path.exists(path):
                missing += 1
                continue
            try:
                if remove_directory:
                    shutil.rmtree(path)
                else:
                    os.remove(path)
                deleted += 1
            except OSError as exc:
                failures.append(f"{os.path.basename(path)}: {exc}")

        if failures:
            self.app.log(f"⚠️ {action_name} could not remove: {'; '.join(failures)}")
        else:
            self.app.log(f"🚀 {action_name} completed: removed {deleted}, already absent {missing}.")

    def get_selected_folder_id(self):
        current_name = self.app.state.selected_folder_name.get()
        for f in self.app.state.drive_folders_cache:
            if f["name"] == current_name: 
                return f["id"]
        return "root"

    def save_current_profile(self):
        success, msg = save_profile_to_disk(self.app.state)
        self.app.log(msg)
        if success: 
            self.refresh_profile_combobox_list()

    def load_selected_profile(self, event=None):
        profile_name = self.app.state.active_profile_var.get()
        success = load_profile_from_disk(self.app.state, profile_name)
        if success:
            if hasattr(self.app, 'pasting_zone') and self.app.pasting_zone:
                if self.app.state.source_mode_var.get() == "Rabbit Hole": 
                    self.app.pasting_zone.pack(fill="x", pady=2)
                else: 
                    self.app.pasting_zone.pack_forget()
            self.toggle_scheduler_ui()
            self.app.log(f"🚀 System Progress: Application configuration parameters synced cleanly to profile setup: [{profile_name}]")

    def refresh_profile_combobox_list(self):
        path = get_profiles_path()
        if os.path.exists(path) and hasattr(self.app.state, 'profile_dropdown') and self.app.state.profile_dropdown:
            try:
                with open(path, "r", encoding="utf-8") as f:
                    profiles_dict = json.load(f)
                names = list(profiles_dict.keys())
                if names: 
                    self.app.state.profile_dropdown['values'] = names
            except Exception: 
                pass

    def modify_windows_scheduler(self):
        folder_id = self.get_selected_folder_id()
        state = self.app.state
        settings = {
            "profile_name": state.active_profile_var.get().strip(),
            "token": state.access_token_var.get(),
            "client_secret": state.client_secret_var.get(),
            "active_workflows": [name for name, var in state.frameworks.items() if var.get()],
            "sync_hour": state.sync_hour_var.get(),
            "sync_minute": state.sync_minute_var.get(),
            "dedup": state.dedup_enabled_var.get(),
            "interval_mode": state.bg_interval_mode_var.get(),
            "interval_value": state.bg_interval_value_var.get(),
            "source_mode": state.source_mode_var.get(),
            "format_mode": state.format_mode_var.get(),
            "image_mode": state.image_mode_var.get(),
        }
        state.btn_register_task.config(state="disabled")
        threading.Thread(
            target=self._modify_windows_scheduler,
            args=(folder_id, settings),
            daemon=True,
        ).start()

    def _modify_windows_scheduler(self, folder_id, settings):
        try:
            success, msg = deploy_windows_task_scheduler(
                self.app.state, TASK_NAME, folder_id, settings=settings
            )
            self.app.log(msg)
        except Exception as exc:
            self.app.log(f"⚠️ Task Scheduler Error: {exc}")
        finally:
            self.app.root.after(0, self._enable_scheduler_button)

    def _enable_scheduler_button(self):
        button = self.app.state.btn_register_task
        if button and button.winfo_exists():
            button.config(state="normal")

    def remove_windows_task(self, quiet=False):
        success = remove_windows_task_from_system(TASK_NAME)
        if success and not quiet: 
            self.app.log("🚀 System Progress: Removed Windows background service task registry.")

    def disable_windows_scheduler(self):
        button = self.app.state.btn_disable_task
        if button:
            button.config(state="disabled")
        threading.Thread(target=self._disable_windows_scheduler, daemon=True).start()

    def _disable_windows_scheduler(self):
        try:
            if remove_windows_task_from_system(TASK_NAME):
                self.app.log("🚀 System Progress: Removed Windows background service task registry.")
            else:
                self.app.log("ℹ️ Background Automation Service is not registered or could not be removed.")
        except Exception as exc:
            self.app.log(f"⚠️ Task Scheduler Error: {exc}")
        finally:
            self.app.root.after(0, self._enable_disable_button)

    def _enable_disable_button(self):
        self.app.state.run_bg_var.set(False)
        for widget_name in ("time_frame", "interval_options_frame", "btn_register_task", "btn_disable_task"):
            widget = getattr(self.app.state, widget_name, None)
            if widget and widget.winfo_exists():
                widget.pack_forget()
        button = self.app.state.btn_disable_task
        if button and button.winfo_exists():
            button.config(state="normal")

    def toggle_scheduler_ui(self):
        if self.app.state.run_bg_var.get():
            if hasattr(self.app.state, 'time_frame') and self.app.state.time_frame: 
                self.app.state.time_frame.pack(side="top", anchor="w", padx=5, pady=2)
            if hasattr(self.app.state, 'interval_options_frame') and self.app.state.interval_options_frame: 
                self.app.state.interval_options_frame.pack(side="top", anchor="w", padx=5, pady=2)
            if hasattr(self.app.state, 'btn_register_task') and self.app.state.btn_register_task: 
                self.app.state.btn_register_task.pack(anchor="w", padx=10, pady=5)
            if hasattr(self.app.state, 'btn_disable_task') and self.app.state.btn_disable_task:
                self.app.state.btn_disable_task.pack(anchor="w", padx=10, pady=5)
        else:
            if hasattr(self.app.state, 'time_frame') and self.app.state.time_frame: 
                self.app.state.time_frame.pack_forget()
            if hasattr(self.app.state, 'interval_options_frame') and self.app.state.interval_options_frame: 
                self.app.state.interval_options_frame.pack_forget()
            if hasattr(self.app.state, 'btn_register_task') and self.app.state.btn_register_task: 
                self.app.state.btn_register_task.pack_forget()
            if hasattr(self.app.state, 'btn_disable_task') and self.app.state.btn_disable_task:
                self.app.state.btn_disable_task.pack_forget()
            self.remove_windows_task()

    def start_sync_thread(self, force=False):
        if not self.app.state.access_token_var.get().strip():
            self.app.log("⚠️ Error: Please enter your Rabbit Access Token first.")
            return
        self.app.state.btn_start.config(state="disabled")
        self.app.state.btn_force.config(state="disabled")
        threading.Thread(target=self._sync_loop, args=(force,)).start()

    def _sync_loop(self, force):
        active_workflows = [name for name, var in self.app.state.frameworks.items() if var.get()]
        token = self.app.state.access_token_var.get().strip()
        secret = self.app.state.client_secret_var.get()
        folder_id = self.get_selected_folder_id()
        
        src_mode = self.app.state.source_mode_var.get()
        fmt_mode = self.app.state.format_mode_var.get()
        img_mode = self.app.state.image_mode_var.get()
        dedup_active = self.app.state.dedup_enabled_var.get()
        
        run_headless_sync(
            token, secret, active_workflows, 
            log_callback=self.app.log, 
            force_sync=force, 
            master_parent_id=folder_id,
            source_mode=src_mode,
            format_mode=fmt_mode,
            image_mode=img_mode,
            dedup_mode=dedup_active
        )
        self.app.state.btn_start.config(state="normal")
        self.app.state.btn_force.config(state="normal")
