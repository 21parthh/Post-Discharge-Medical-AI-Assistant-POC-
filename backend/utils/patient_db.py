import json
from pathlib import Path
from datetime import datetime
from backend.utils.logger import log_event

# Path to the patient database JSON file
DB_PATH = Path(__file__).resolve().parent.parent / "data" / "patients.json"

def load_db():
    """Load the JSON database safely."""
    if not DB_PATH.exists():
        log_event.warning(f"⚠️ No patient DB found at {DB_PATH}, creating a new one.")
        DB_PATH.parent.mkdir(parents=True, exist_ok=True)
        with open(DB_PATH, "w") as f:
            json.dump([], f)
        return []

    with open(DB_PATH, "r") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            log_event.error("❌ Corrupted patient database — resetting file.")
            return []

def save_db(data):
    """Save updated patient data."""
    with open(DB_PATH, "w") as f:
        json.dump(data, f, indent=4)

def get_patient_data(name: str):
    """Retrieve patient data by name."""
    db = load_db()
    matches = [p for p in db if p["patient_name"].lower() == name.lower()]
    
    if not matches:
        log_event.info(f"No record found for {name}")
        return None
    if len(matches) > 1:
        log_event.warning(f"⚠️ Multiple records found for {name}, returning the latest.")
        matches = sorted(matches, key=lambda x: x.get("discharge_date", ""), reverse=True)
    
    log_event("PatientDB", f"✅ Retrieved record for {name}")

    return matches[0]

def add_patient_record(record: dict):
    """Add a new patient record."""
    db = load_db()
    record["created_at"] = datetime.now().isoformat()
    db.append(record)
    save_db(db)
    log_event.info(f"🩺 Added record for {record['patient_name']}")
