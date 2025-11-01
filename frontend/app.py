import streamlit as st
import requests

API_BASE = "http://127.0.0.1:8000"

st.set_page_config(page_title="Post-Discharge AI Assistant 💬", layout="centered")

st.title("🏥 Post-Discharge AI Assistant")
st.write("An AI assistant to help patients after hospital discharge.")

if "patient_name" not in st.session_state:
    st.session_state.patient_name = None

if "patient_data" not in st.session_state:
    st.session_state.patient_data = None

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

with st.container():
    st.subheader("Step 1: Enter your name")
    name_input = st.text_input("👤 Patient Name", placeholder="Enter your full name...")

    if st.button("🔍 Fetch Patient Info"):
        if not name_input.strip():
            st.warning("Please enter a name first.")
        else:
            try:
                response = requests.get(f"{API_BASE}/chat", params={"name": name_input})
                data = response.json()

                if response.status_code == 200 and data.get("patient"):
                    st.session_state.patient_name = name_input
                    st.session_state.patient_data = data["patient"]
                    st.session_state.chat_history = [
                        {"role": "assistant", "content": data["response"]}
                    ]
                    st.success(f"✅ Patient data retrieved for {name_input}")
                else:
                    st.error(data.get("response", "❌ No record found."))

            except Exception as e:
                st.error(f"⚠️ Error connecting to backend: {e}")

if st.session_state.patient_data:
    patient = st.session_state.patient_data

    # Extract safely with defaults
    name = patient.get("name") or patient.get("patient_name") or "Patient"
    # condition = patient.get("condition") or patient.get("primary_condition") or "your recent condition"
    diagnosis = patient.get("primary_diagnosis", "your last diagnosis")
    discharge_date = patient.get("discharge_date", "a recent date")

    # Form a friendly receptionist-style message
    greeting_message = (
        f"👋 Hi **{name}**! I found your discharge report from **{discharge_date}** "
        f"for **{diagnosis}**. How are you feeling today? "
        f"Are you following your medication schedule?"
    )

    with st.expander("🩺 Patient Summary", expanded=True):
        st.markdown(greeting_message)

if st.session_state.patient_name:
    st.divider()
    st.subheader("Step 2: Chat with AI Assistant 💬")

    # Role name mapping
    ROLE_LABELS = {
        "receptionist_agent": "💬 Receptionist",
        "clinical_agent": "🩺 Clinical Assistant",
        "web_agent": "🌐 Web Search Agent",
        "system": "⚙️ System",
        "assistant": "🤖 Assistant"
    }

    # Display chat history cleanly
    for chat in st.session_state.chat_history:
        role = chat.get("role", "assistant")
        content = chat.get("content", "")
        label = ROLE_LABELS.get(role, "🤖 Assistant")

        if role == "user":
            st.chat_message("user").markdown(
                f"<div style='font-size: 14px;'>{content}</div>",
                unsafe_allow_html=True
            )
        else:
            st.chat_message("assistant").markdown(
                f"<div style='font-size: 14px;'><b>{label}:</b><br>{content.strip()}</div>",
                unsafe_allow_html=True
            )
    user_message = st.chat_input("💬 Type your message...", key="main_chat_input")

    if user_message:
        # Add user message to chat
        st.session_state.chat_history.append({"role": "user", "content": user_message})

        try:
            payload = {
                "patient_name": st.session_state.patient_name,
                "message": user_message
            }
            response = requests.post(f"{API_BASE}/chat", json=payload)
            data = response.json()

            agent_role = data.get("role", "assistant")
            agent_response = data.get("response", "No response received.").strip()

            # Append AI message to history
            st.session_state.chat_history.append({
                "role": agent_role,
                "content": agent_response
            })

        except Exception as e:
            st.session_state.chat_history.append({
                "role": "system",
                "content": f"⚠️ Backend error: {e}"
            })

        st.rerun()
