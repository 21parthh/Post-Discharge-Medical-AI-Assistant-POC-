import sys
import os
import re

# ✅ Ensure backend package is importable
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from backend.agents.receptionist_agent import receptionist_response
from backend.agents.clinical_agent import generate_medical_response
from backend.utils.web_search import perform_web_search
from backend.utils.logger import log_event


# 🔍 Intent detection
import re

def detect_intent(user_input: str) -> str:
    """
    Detect if the user's input is medical, web/research, or general conversation.
    Returns one of: 'medical', 'web', or 'general'
    """

    text = user_input.lower().strip()

    # -------------------------------
    # 1️⃣ Web / Research / Information intent
    # -------------------------------
    web_keywords = [
        "latest", "update", "research", "news", "recent", "current treatment",
        "new treatment", "recent study", "findings", "breakthrough",
        "paper", "publication", "guidelines", "discovery"
    ]
    if any(kw in text for kw in web_keywords):
        return "web"

    # -------------------------------
    # 2️⃣ Medical / Symptom / Treatment intent
    # -------------------------------
    medical_patterns = [
        r"\b(pain|ache|cramp|swelling|fever|cough|infection|vomit|nausea|edema)\b",
        r"\b(kidney|urine|dialysis|bp|blood pressure|creatinine|urea|glucose)\b",
        r"\b(medicine|tablet|drug|dose|mg|prescription|treatment|therapy)\b",
        r"\b(symptom|diagnosis|disease|condition|disorder)\b",
        r"\b(follow[- ]?up|appointment|check[- ]?up)\b",
        r"\b(report|scan|test|result|x-ray|ultrasound|blood test)\b",
        r"\b(shortness of breath|dizziness|fatigue|numbness|itching)\b"
    ]
    for pattern in medical_patterns:
        if re.search(pattern, text):
            return "medical"

    # -------------------------------
    # 3️⃣ Contextual cues (sentence structure / tone)
    # -------------------------------
    if re.search(r"(should i|can i|do i need|is it okay if)", text):
        # Often implies a health-related question
        return "medical"

    # -------------------------------
    # 4️⃣ Default fallback: general / small talk
    # -------------------------------
    return "general"



# 🧩 Orchestrator
def orchestrate_conversation():
    print("🧩 Orchestrator Started — Managing Reception & Clinical Agents")
    log_event("System", "🧠 Orchestrator initialized.")

    patient_name = input("Enter patient name: ").strip()
    log_event("System", f"Patient identified: {patient_name}")

    print(f"\n🤖 Receptionist: Hello {patient_name}! How are you feeling today?")

    while True:
        user_input = input("\n💬 You: ").strip()
        if user_input.lower() in ["exit", "quit", "bye"]:
            print("👋 Goodbye! Take care of your health.")
            log_event("System", "Session ended by user.")
            break

        # Detect intent
        intent = detect_intent(user_input)
        log_event("System", f"Detected intent: {intent}")

        # Route based on intent
        if intent == "medical":
            print("\n🤖 Receptionist: This sounds medical, connecting you to the Clinical AI Agent...")
            log_event("System", "Routing to Clinical Agent.")
            response = generate_medical_response(user_input)
            print("\n🩺 Clinical Agent Response:\n", response)

        elif intent == "web":
            print("\n🌐 Web Search Agent: Fetching latest research data...")
            log_event("System", "Routing to Web Search Agent.")
            try:
                result = perform_web_search(user_input)
                print("\n🧠 Web Search Result:\n", result)
            except Exception as e:
                print(f"❌ Web Search Error: {e}")
                log_event("WebSearch", f"Error: {e}")

        else:
            response = receptionist_response(user_input)
            print(f"\n🤖 Receptionist: {response}")
            log_event("System", "Receptionist handled general query.")


if __name__ == "__main__":
    orchestrate_conversation()
