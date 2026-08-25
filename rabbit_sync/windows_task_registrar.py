import os
import sys
import json
import getpass
import subprocess

# FIXED: Explicitly declared the operational constant in the module namespace bounds
TASK_NAME = "RabbitR1_GoogleDocs_Sync"

def deploy_windows_task_scheduler(state, task_name, selected_folder_id, settings=None):
    """Assembles a proxied batch layer to bypass character limit bottlenecks and hooks it to Windows."""
    if settings is None:
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

    token = str(settings["token"]).strip()
    secret = os.path.abspath(str(settings["client_secret"]))
    if not token:
        token = "BROWSER_COOKIE_AUTHENTICATED_SESSION_OK"

    active_workflows = settings["active_workflows"]
    workflows_json = json.dumps(active_workflows).replace('"', '\\"')
    
    target_script = os.path.abspath(os.path.join(os.path.dirname(__file__), "scheduler_cli.py"))
    python_exe = sys.executable
    sync_time = f"{str(settings['sync_hour']).zfill(2)}:{str(settings['sync_minute']).zfill(2)}"
    
    dedup_flag = "--dedup" if settings["dedup"] else ""
    src_mode = str(settings["source_mode"])
    fmt_mode = str(settings["format_mode"])
    img_mode = str(settings["image_mode"])
    
    profile_name = str(settings.get("profile_name", ""))
    long_python_cmd = f'"{python_exe}" "{target_script}" "{token}" "{secret}" "{workflows_json}" --profile "{profile_name}" --folder "{selected_folder_id}" --source "{src_mode}" --format "{fmt_mode}" --image "{img_mode}" {dedup_flag}'
    
    project_root = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
    bat_file_path = os.path.join(project_root, "run_background_sync.bat")
    log_file_path = os.path.join(project_root, "sync_service.log")
    
    try:
        with open(bat_file_path, "w", encoding="utf-8", errors="ignore") as bat_file:
            bat_file.write("@echo off\n")
            bat_file.write(f'echo %date% %time% [BAT CRON] 🔔 Windows Task Scheduler successfully executed batch script proxy launcher! >> "{log_file_path}"\n')
            bat_file.write(f'cd /d "{project_root}"\n')
            bat_file.write(f"{long_python_cmd} >> background_crash.log 2>&1\n")
            bat_file.write(f'echo %date% %time% [BAT CRON] ✅ Batch wrapper completed processing sequence. >> "{log_file_path}"\n')
    except Exception as e:
        return False, f"⚠️ IO Write Error: Could not generate batch background launcher: {str(e)}"

    # Clear previous instances safely before re-registering
    subprocess.run(
        ["schtasks.exe", "/Delete", "/TN", task_name, "/F"],
        capture_output=True,
        text=True,
        timeout=15,
        check=False,
    )
    
    mode = settings["interval_mode"]
    val = str(settings["interval_value"])
    
    current_user = getpass.getuser()
    task_action = f'cmd.exe /d /c ""{os.path.abspath(bat_file_path)}""'
    base_args = ["schtasks.exe", "/Create", "/TN", task_name, "/TR", task_action, "/F"]
    
    if mode == "Daily":
        create_args = base_args + ["/SC", "DAILY", "/ST", sync_time]
    elif mode == "Hourly":
        create_args = base_args + ["/SC", "HOURLY", "/MO", val, "/ST", sync_time]
    else:
        create_args = base_args + ["/SC", "MINUTE", "/MO", val, "/ST", sync_time]
        
    try:
        res = subprocess.run(create_args, capture_output=True, text=True, timeout=15, check=False)
    except (OSError, subprocess.TimeoutExpired) as exc:
        return False, f"⚠️ Task Scheduler Error: {exc}"

    if res.returncode == 0:
        return True, f"🚀 System Progress: Background Service Task Registered Successfully under profile: {current_user}!"
    return False, f"⚠️ Task Scheduler Error: {res.stderr.strip() or 'Task registration failed.'}"

def remove_windows_task_from_system(task_name):
    """Deletes task entries and removes the proxy batch script."""
    res = subprocess.run(
        ["schtasks.exe", "/Delete", "/TN", task_name, "/F"],
        capture_output=True,
        text=True,
        timeout=15,
        check=False,
    )
    
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    bat_file_path = os.path.join(project_root, "run_background_sync.bat")
    if os.path.exists(bat_file_path):
        try: os.remove(bat_file_path)
        except Exception: pass
    return res.returncode == 0
