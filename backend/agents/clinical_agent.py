import os
from loguru import logger
from huggingface_hub import InferenceClient
from backend.tools.rag_tool import RAGTool
from backend.utils.patient_db import get_patient_data

# ----------------------------
# 🔑 API Setup
# ----------------------------
HF_API_KEY = os.getenv("HF_TOKEN", "")
if not HF_API_KEY:
    raise ValueError("❌ HF_TOKEN not found in environment. Please set it before running.")

# ----------------------------
# ⚙️ Initialize Components
# ----------------------------
rag = RAGTool()

client = InferenceClient(
    model="mistralai/Mistral-7B-Instruct-v0.2",
    token=HF_API_KEY
)

# ----------------------------
# 🧠 Main Logic
# ----------------------------
def generate_medical_response(query: str, patient_name: str = None):
    """
    Generate a medical response using both patient history and RAG-retrieved context.
    """
    try:
        logger.info(f"🔍 Retrieving medical context for: {query}")

        # 1️⃣ Retrieve domain context from RAG
        rag_result = rag.generate_answer(query)
        context = rag_result.get("context", "")
        retrieved_answer = rag_result.get("answer", "")

        # 2️⃣ Fetch patient-specific history if available
        patient_context = ""
        if patient_name:
            patient = get_patient_data(patient_name)
            if patient:
                patient_context = f"""
                Patient Information:
                - Name: {patient.get('name')}
                - Age: {patient.get('age')}
                - Gender: {patient.get('gender')}
                - Primary Diagnosis: {patient.get('primary_diagnosis')}
                - Discharge Date: {patient.get('discharge_date')}
                - Current Medications: {patient.get('medications')}
                - Recent Symptoms: {patient.get('recent_symptoms')}
                """
            else:
                logger.warning(f"⚠️ No patient history found for {patient_name}")
        else:
            logger.info("No patient name provided — proceeding with general medical context.")

        # 3️⃣ Build combined LLM prompt
        prompt = f"""
        You are a compassionate clinical assistant specializing in nephrology post-discharge care.
        Use the medical context retrieved from research papers and the patient's medical history below 
        to generate a helpful, safe, and empathetic response.

        === Patient Medical History ===
        {patient_context if patient_context else "No personal data available."}

        === Medical Context from Knowledge Base ===
        {context}

        === User Query ===
        {query}

        Now, provide a concise, medically sound answer tailored to the patient’s situation.
        """

        # 4️⃣ Generate final response via Mistral LLM
        logger.info("🧩 Sending combined context to Mistral LLM...")
        completion = client.chat.completions.create(
            messages=[
                {"role": "system", "content": "You are a helpful medical assistant."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=400,
        )

        answer = completion.choices[0].message["content"]
        logger.success("✅ Medical response generated successfully")

        return answer

    except Exception as e:
        logger.error(f"❌ Clinical agent error: {e}")
        return "I'm sorry, I encountered an issue while processing your medical query."
