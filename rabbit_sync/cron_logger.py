import logging
import json
import os
import sys
import time
from datetime import datetime, timedelta
from logging.handlers import TimedRotatingFileHandler
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile
from rabbit_sync.config import LOG_FILE_PATH

DEFAULT_LOG_RETENTION_DAYS = 7

def get_log_retention_days():
    project_root = Path(LOG_FILE_PATH).parent
    profiles_path = project_root / "rabbit_sync_profiles.json"
    profile_name = "Default Profile"
    if "--profile" in sys.argv:
        profile_index = sys.argv.index("--profile")
        if profile_index + 1 < len(sys.argv):
            profile_name = sys.argv[profile_index + 1]
    try:
        with profiles_path.open("r", encoding="utf-8") as profiles_file:
            profile = json.load(profiles_file).get(profile_name, {})
        retention_days = int(profile.get("log_retention_days", DEFAULT_LOG_RETENTION_DAYS))
        return max(1, retention_days)
    except (OSError, ValueError, TypeError):
        return DEFAULT_LOG_RETENTION_DAYS

class ZipTimedRotatingFileHandler(TimedRotatingFileHandler):
    def __init__(self, filename, retention_days=DEFAULT_LOG_RETENTION_DAYS):
        self.retention_days = max(1, retention_days)
        super().__init__(filename, when="midnight", interval=1, backupCount=0, encoding="utf-8")

    def doRollover(self):
        if self.stream:
            self.stream.close()
            self.stream = None

        log_path = Path(self.baseFilename)
        if log_path.exists() and log_path.stat().st_size:
            archive_name = f"{log_path.stem}.{datetime.now():%Y-%m-%d}.zip"
            archive_path = log_path.with_name(archive_name)
            if archive_path.exists():
                archive_path = log_path.with_name(f"{log_path.stem}.{datetime.now():%Y-%m-%d-%H%M%S}.zip")
            with ZipFile(archive_path, "w", compression=ZIP_DEFLATED) as archive:
                archive.write(log_path, arcname=log_path.name)
            log_path.unlink()

        cutoff = datetime.now() - timedelta(days=self.retention_days)
        for archive_path in log_path.parent.glob(f"{log_path.stem}.*.zip"):
            try:
                if datetime.fromtimestamp(archive_path.stat().st_mtime) < cutoff:
                    archive_path.unlink()
            except OSError:
                continue

        self.rolloverAt = self.computeRollover(time.time())
        if not self.delay:
            self.stream = self._open()

def init_cron_logging():
    """
    Initializes structured file logging configuration matrix using clean append modes.
    Ensures safe, atomic write boundaries across standalone background processes.
    """
    root_logger = logging.getLogger()
    if any(isinstance(handler, ZipTimedRotatingFileHandler) for handler in root_logger.handlers):
        return
    root_logger.setLevel(logging.INFO)
    root_logger.addHandler(ZipTimedRotatingFileHandler(LOG_FILE_PATH, get_log_retention_days()))
    for handler in root_logger.handlers:
        if isinstance(handler, ZipTimedRotatingFileHandler):
            handler.setFormatter(logging.Formatter(
                '%(asctime)s [%(levelname)s] %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S',
            ))
