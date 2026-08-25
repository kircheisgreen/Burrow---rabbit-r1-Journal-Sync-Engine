# SEMANTIC VERSION v0.13.3
import os
import json
import base64
import hashlib
from cryptography.fernet import Fernet
from pathlib import Path

def get_profiles_path():
    return os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "rabbit_sync_profiles.json")

def _get_encryption_key_path():
    return Path(os.path.dirname(get_profiles_path())) / "profile_encryption.key"

def _get_legacy_fernet():
    """Build the pre-v0.13.11 token-derived key for one-time migration support."""
    token_path = Path(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "token.json"))
    if not token_path.exists():
        raise FileNotFoundError("token.json not found. Cannot derive legacy encryption key.")
    with open(token_path, "r") as token_file:
        token_value = json.load(token_file).get("token", "")
    if not token_value:
        raise ValueError("Token value is empty in token.json.")
    return Fernet(base64.urlsafe_b64encode(hashlib.sha256(token_value.encode()).digest()))

def _get_fernet():
    """
    Derives a Fernet key from the token in token.json.
    Uses SHA-256 to hash the token, then takes the first 32 bytes
    and base64 encodes them to meet Fernet's key requirements.
    """
    key_path = _get_encryption_key_path()
    if not key_path.exists():
        key_path.write_bytes(Fernet.generate_key())
    return Fernet(key_path.read_bytes())

def _encrypt_password(password):
    """Encrypts a password string using the derived Fernet key."""
    if not password:
        return ""
    fernet = _get_fernet()
    return fernet.encrypt(password.encode()).decode()

def _decrypt_password(encrypted_password):
    """Decrypts an encrypted password string using the derived Fernet key."""
    if not encrypted_password:
        return ""
    for fernet_loader in (_get_fernet, _get_legacy_fernet):
        try:
            return fernet_loader().decrypt(encrypted_password.encode()).decode()
        except Exception:
            continue
    return ""

def _is_encrypted(password_str):
    """
    Checks if a password string is already encrypted.
    Fernet tokens are base64url encoded and typically start with specific patterns.
    A simple heuristic: try to decrypt it; if it fails, it's plain text.
    """
    if not password_str:
        return False
    return bool(_decrypt_password(password_str))

def migrate_existing_profiles():
    """
    Scans rabbit_sync_profiles.json and encrypts any plain-text rabbit_password values.
    """
    path = get_profiles_path()
    if not os.path.exists(path):
        return

    try:
        with open(path, "r", encoding="utf-8") as f:
            profiles_dict = json.load(f)
    except Exception:
        return

    migrated = False
    for profile_name, data in profiles_dict.items():
        pwd = data.get("rabbit_password", "")
        if pwd and not _is_encrypted(pwd):
            data["rabbit_password"] = _encrypt_password(pwd)
            migrated = True
            print(f"Migrated plain-text password for profile: {profile_name}")

    if migrated:
        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(profiles_dict, f, indent=4)
            print("Migration complete. Passwords are now encrypted.")
        except Exception as e:
            print(f"Failed to save migrated profiles: {e}")

def save_profile_to_disk(state):
    path = get_profiles_path()
    profile_name = state.active_profile_var.get().strip()
    if not profile_name:
        return False, "⚠️ Error: Profile name cannot be blank."

    profiles_dict = {}
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                profiles_dict = json.load(f)
        except Exception: pass

    # Migrate any existing plain-text passwords before saving
    migrate_existing_profiles()

    # Encrypt password before saving
    raw_password = state.rabbit_password_var.get()
    encrypted_password = _encrypt_password(raw_password)

    profiles_dict[profile_name] = {
        "source_mode": state.source_mode_var.get(),
        "format_mode": state.format_mode_var.get(),
        "image_mode": state.image_mode_var.get(),
        "rabbit_username": state.rabbit_username_var.get(),
        "rabbit_password": encrypted_password,
        "post_fetch_action": state.post_fetch_action_var.get(),
        "client_secret": state.client_secret_var.get(),
        "selected_folder": state.selected_folder_name.get(),
        "dedup_enabled": state.dedup_enabled_var.get(),
        "run_background": state.run_bg_var.get(),
        "sync_hour": state.sync_hour_var.get(),
        "sync_minute": state.sync_minute_var.get(),
        "bg_interval_mode": state.bg_interval_mode_var.get(),
        "bg_interval_value": state.bg_interval_value_var.get(),
        "frameworks": {name: var.get() for name, var in state.frameworks.items()},
        "frameworks_expanded": state.frameworks_expanded_var.get(),
        "google_expanded": state.google_expanded_var.get(),
        "scheduler_expanded": state.scheduler_expanded_var.get(),
        "log_retention_days": int(state.log_retention_days_var.get() or 7)
    }

    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(profiles_dict, f, indent=4)
        return True, f"🚀 System Progress: Profile configuration details saved to profile memory: [{profile_name}]"
    except Exception as e:
        return False, f"⚠️ IO Save Fault: Could not update profile cache file: {str(e)}"

def load_profile_from_disk(state, profile_name):
    path = get_profiles_path()
    if not os.path.exists(path):
        return None

    try:
        with open(path, "r", encoding="utf-8") as f:
            profiles_dict = json.load(f)
        
        p_data = profiles_dict.get(profile_name)
        if not p_data:
            return None
            
        state.source_mode_var.set(p_data.get("source_mode", "Google Mail"))
        state.format_mode_var.set(p_data.get("format_mode", "Google Doc"))
        state.image_mode_var.set(p_data.get("image_mode", "PNG"))
        
        state.rabbit_username_var.set(p_data.get("rabbit_username", ""))
        
        # Decrypt password after loading
        encrypted_password = p_data.get("rabbit_password", "")
        decrypted_password = _decrypt_password(encrypted_password)
        state.rabbit_password_var.set(decrypted_password)
        
        state.post_fetch_action_var.set(p_data.get("post_fetch_action", "NONE"))
        
        state.client_secret_var.set(p_data.get("client_secret", "credentials.json"))
        state.selected_folder_name.set(p_data.get("selected_folder", "My Drive (Root)"))
        state.dedup_enabled_var.set(p_data.get("dedup_enabled", False))
        
        # Handle background run variable naming inconsistency
        if hasattr(state, 'run_background_var'):
            state.run_background_var.set(p_data.get("run_background", False))
        elif hasattr(state, 'run_bg_var'):
            state.run_bg_var.set(p_data.get("run_background", False))
            
        state.sync_hour_var.set(p_data.get("sync_hour", "12"))
        state.sync_minute_var.set(p_data.get("sync_minute", "00"))
        state.bg_interval_mode_var.set(p_data.get("bg_interval_mode", "Daily"))
        state.bg_interval_value_var.set(p_data.get("bg_interval_value", "1"))
        state.frameworks_expanded_var.set(p_data.get("frameworks_expanded", True))
        state.google_expanded_var.set(p_data.get("google_expanded", False))
        state.scheduler_expanded_var.set(p_data.get("scheduler_expanded", False))
        state.log_retention_days_var.set(str(p_data.get("log_retention_days", 7)))

        saved_wf = p_data.get("frameworks", {})
        for name, val in saved_wf.items():
            if name in state.frameworks:
                state.frameworks[name].set(val)
        return True
    except Exception:
        return False