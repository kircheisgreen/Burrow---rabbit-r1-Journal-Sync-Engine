# SEMANTIC VERSION v0.5.0
import tkinter as tk

class AppState:
    def __init__(self):
        self.active_profile_var = tk.StringVar(value="Default Profile")
        self.access_token_var = tk.StringVar()
        self.client_secret_var = tk.StringVar(value="credentials.json")
        self.run_bg_var = tk.BooleanVar(value=False)
        self.sync_hour_var = tk.StringVar(value="12")
        self.sync_minute_var = tk.StringVar(value="00")
        
        self.rabbit_username_var = tk.StringVar()
        self.rabbit_password_var = tk.StringVar()
        
        # Asynchronous Post-Fetch Automation Chaining Variables: "NONE", "SYNC", "FORCE"
        self.post_fetch_action_var = tk.StringVar(value="NONE")
        self.only_unfetched_dates_var = tk.BooleanVar(value=False)
        self.frameworks_expanded_var = tk.BooleanVar(value=True)
        self.google_expanded_var = tk.BooleanVar(value=False)
        self.scheduler_expanded_var = tk.BooleanVar(value=False)
        self.log_retention_days_var = tk.StringVar(value="7")
        
        self.dedup_enabled_var = tk.BooleanVar(value=False)
        self.bg_interval_mode_var = tk.StringVar(value="Daily")
        self.bg_interval_value_var = tk.StringVar(value="1")
        
        self.source_mode_var = tk.StringVar(value="Google Mail")
        self.format_mode_var = tk.StringVar(value="Google Doc")
        self.image_mode_var = tk.StringVar(value="PNG")
        
        self.drive_folders_cache = [{"name": "My Drive (Root)", "id": "root"}]
        self.selected_folder_name = tk.StringVar(value="My Drive (Root)")
        
        self.frameworks = {
            "Cornell Method": tk.BooleanVar(value=False),
            "Outlining": tk.BooleanVar(value=False),
            "Mind Mapping": tk.BooleanVar(value=False),
            "Boxing": tk.BooleanVar(value=False)
        }
        
        self.profile_dropdown = None
        self.folder_dropdown = None
        self.time_frame = None
        self.interval_options_frame = None
        self.btn_register_task = None
        self.btn_disable_task = None
        self.btn_start = None
        self.btn_force = None
        self.log_area = None
