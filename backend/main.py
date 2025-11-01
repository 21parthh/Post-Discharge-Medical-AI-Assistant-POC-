from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import sys, os, re
from fastapi.middleware.cors import CORSMiddleware

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.agents.receptionist_agent import receptionist_response
from backend.agents.clinical_agent import generate_medical_response
from backend.utils.web_search import perform_web_search
from backend.utils.logger import log_event
from backend.utils.patient_db import get_patient_data

app = FastAPI(title="Post-Discharge AI Assistant", version="2.1")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # you can restrict later e.g. ["http://127.0.0.1:5500"]
    allow_credentials=True,
    allow_methods=["*"],  # allow POST, OPTIONS etc.
    allow_headers=["*"],
)
# -------------------------
# Input Schema
# -------------------------
class Query(BaseModel):
    patient_name: str | None = None
    message: str

# -------------------------
# Intent Detection
# -------------------------
def detect_intent(user_input: str) -> str:
    medical_keywords = [
        "pain", "fever", "urine", "kidney", "infection", "treatment",
        "edema", "medicine", "dose", "symptom", "disease"
    ]
    if "research" in user_input.lower() or "latest" in user_input.lower():
        return "web"
    if any(re.search(rf"\b{kw}\b", user_input.lower()) for kw in medical_keywords):
        return "medical"
    return "general"

# -------------------------
# GET Endpoint: Retrieve patient info by name
# -------------------------
@app.get("/chat")
async def get_patient_info(name: str):
    try:
        log_event("Reception", f"Retrieving patient info for: {name}")
        patient = get_patient_data(name)

        if not patient:
            log_event("Reception", f"Unknown patient: {name}")
            return {
                "role": "receptionist_agent",
                "response": f"❌ Sorry, no records found for '{name}'. You may register first."
            }

        return {
            "role": "receptionist_agent",
            "response": f"👋 Welcome back, {name}! How are you",
            "patient": patient
        }

    except Exception as e:
        log_event("Error", str(e))
        raise HTTPException(status_code=500, detail=str(e))

# -------------------------
# POST Endpoint: Chat handler
# -------------------------
@app.post("/chat")
async def chat(query: Query):
    try:
        log_event("System", f"Received: {query}")

        # --- Step 1: If no name provided ---
        if not query.patient_name:
            log_event("Reception", "Requesting patient name")
            return {
                "role": "receptionist_agent",
                "response": "👋 Hello! May I know your name, please?"
            }

        # --- Step 2: Retrieve patient data ---
        patient = get_patient_data(query.patient_name)
        if not patient:
            log_event("Reception", f"Unknown patient: {query.patient_name}")
            return {
                "role": "receptionist_agent",
                "response": f"❌ Sorry, I couldn't find records for '{query.patient_name}'."
            }

        # --- Step 3: Detect intent ---
        intent = detect_intent(query.message)
        log_event("Orchestrator", f"Detected intent: {intent}")

        # --- Step 4: Route to agents ---
        if intent == "medical":
            response = generate_medical_response(query.message)
            return {
                "role": "clinical_agent",
                "response": f"🩺 Clinical Agent Response:\n{response}",
                "patient": patient
            }

        elif intent == "web":
            result = perform_web_search(query.message)
            return {
                "role": "web_agent",
                "response": f"🌐 Web Search Result:\n{result}",
                "patient": patient
            }

        else:
            response = receptionist_response(query.message)
            return {
                "role": "receptionist_agent",
                "response": response,
                "patient": patient
            }

    except Exception as e:
        log_event("Error", str(e))
        raise HTTPException(status_code=500, detail=str(e))

# -------------------------
# Health Check
# -------------------------
@app.get("/")
def health_check():
    return {"status": "ok", "message": "Post-Discharge AI Assistant is running 🚀"}
