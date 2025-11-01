import os
import sys
from huggingface_hub import InferenceClient

# ensure backend folder is in path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from backend.utils.patient_db import get_patient_data
from backend.utils.logger import log_event

client = InferenceClient(model="mistralai/Mistral-7B-Instruct-v0.2")


def call_mistral(prompt: str) -> str:
    """Query Mistral model (chat mode)."""
    try:
        completion = client.chat.completions.create(
            model="mistralai/Mistral-7B-Instruct-v0.2",
            messages=[
                {"role": "system", "content": "You are a friendly medical receptionist AI assistant."},
                {"role": "user", "content": prompt},
            ],
            max_tokens=300,
            temperature=0.7,
        )
        return completion.choices[0].message["content"]
    except Exception as e:
        return f"⚠️ Mistral error: {str(e)}"


# Receptionist Agent Logic

def handle_patient_query(patient_name: str):
    """Fetch and greet patient with discharge summary info."""
    patient = get_patient_data(patient_name)
    if not patient:
        print(f"❌ No record found for {patient_name}.")
        return

    log_event("ReceptionistAgent", f"Fetched patient data for {patient_name}")

    prompt = (
        f"The patient {patient_name} was discharged with diagnosis '{patient['primary_diagnosis']}' "
        f"on {patient['discharge_date']}'. Greet the patient warmly, mention their discharge, "
        f"and ask how they are feeling today and if they are following their medication schedule."
    )

    response = call_mistral(prompt)
    print(f"💬 Receptionist: {response}")


def receptionist_response(user_input: str, patient_name: str = "the patient"):
    """Generate receptionist response via Mistral chat model."""
    prompt = (
        f"The patient said: '{user_input}'. "
        f"Generate an empathetic receptionist-style reply. "
        f"If it sounds medical (pain, symptoms, medicine, fever, etc.), "
        f"gently suggest connecting them to the clinical assistant."
    )

    response = call_mistral(prompt)
    log_event("ReceptionistAgent", f"Responded to {patient_name}: {user_input}")
    return response


# Entry Point

if __name__ == "__main__":
    print("🤖 Receptionist Agent (Mistral Chat) Initialized")
    patient_name = input("Enter patient name: ")
    handle_patient_query(patient_name)

    while True:
        user_input = input(f"\n🗣️ {patient_name}: ")
        if user_input.lower() in ["exit", "quit"]:
            print("👋 Goodbye!")
            break

        reply = receptionist_response(user_input, patient_name)
        print(f"💬 Receptionist: {reply}")
