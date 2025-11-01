import os
from datetime import datetime

# Define log file path (auto-create folder if needed)
LOG_DIR = os.path.join(os.path.dirname(__file__), "../../logs")
os.makedirs(LOG_DIR, exist_ok=True)
LOG_FILE = os.path.join(LOG_DIR, "system.log")


def log_event(source, message=None):
    """Log events with or without a source tag."""
    if message is None:
        message = source
        source = "System"
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_message = f"[{timestamp}] [{source}] {message}"
    print("📝 LOGGED:", log_message)
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(log_message + "\n")

