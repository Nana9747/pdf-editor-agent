"""Main entry point for the AI Resume Editor Streamlit application."""

import os
from dotenv import load_dotenv
import streamlit as st

from agent.orchestrator import run_resume_agent
from ui.components import render_comparison_view
from ui.state import (
    init_session_state,
    set_uploaded_pdf,
    update_edited_pdf,
)

# Load local environment variables (.env)
load_dotenv()

st.set_page_config(
    page_title="AI Resume Editor",
    page_icon="📄",
    layout="wide",
)

# Initialize application session state
init_session_state()

# --- Sidebar Configuration ---
with st.sidebar:
  st.title("⚙️ Configuration")

  env_key = os.getenv("GROQ_API_KEY", "")
  user_groq_key = st.text_input(
      "Groq API Key",
      value=env_key,
      type="password",
      help="Get a free API key at console.groq.com",
  )

  available_models = [
        "openai/gpt-oss-120b",
        "qwen/qwen3.8-27b",
        "openai/gpt-oss-20b",
    ]
  selected_model = st.selectbox(
        "Groq Model",
        options=available_models,
        index=0,
        help="Active models on your Groq tier.",
    )

  st.divider()
  st.subheader("📤 Resume Document")
  uploaded_file = st.file_uploader(
      "Upload Resume (PDF)",
      type=["pdf"],
      help="Select a single-page or multi-page resume PDF",
  )

  if uploaded_file is not None:
    file_bytes = uploaded_file.read()
    # Check if a new file was uploaded
    if (
        st.session_state.original_pdf_bytes is None
        or st.session_state.file_name != uploaded_file.name
    ):
      set_uploaded_pdf(file_bytes, uploaded_file.name)
      st.rerun()

  st.markdown("---")
  st.markdown(
      "**Features:**\n"
      "- 🎯 Font, size & weight matching\n"
      "- 📐 Grid & margin preservation\n"
      "- 🔗 Interactive link & URL rebinding\n"
      "- ↩️️ Instant one-click Undo"
  )

# --- Main Interface ---
st.title("📄 Prompt-Driven Resume Editor")
st.caption(
    "Edit dates, job titles, GPA, bullet points, and hyperlinks without"
    " disrupting your resume's layout or ATS formatting."
)

# Render Dual-Pane Document View
render_comparison_view()

# --- User Interaction / Prompt Input ---
st.divider()

# Display chat message history
for msg in st.session_state.chat_messages:
  with st.chat_message(msg["role"]):
    st.write(msg["content"])

user_prompt = st.chat_input(
    "Type an edit (e.g., 'Change GPA to 3.9' or 'Update GitHub link to"
    " https://github.com/myname')..."
)

if user_prompt:
  if not st.session_state.original_pdf_bytes:
    st.warning("⚠️ Please upload a resume PDF from the sidebar first.")
  elif not user_groq_key:
    st.error(
        "⚠️️ Please provide a Groq API Key in the sidebar or in your .env file."
    )
  else:
    # Append user prompt to UI history
    st.session_state.chat_messages.append(
        {"role": "user", "content": user_prompt}
    )
    with st.chat_message("user"):
      st.write(user_prompt)

    # Process prompt through agent
    with st.chat_message("assistant"):
      with st.spinner("Analyzing resume layout, typography, and editing..."):
        agent_reply, updated_bytes = run_resume_agent(
            user_prompt=user_prompt,
            pdf_bytes=st.session_state.edited_pdf_bytes,
            api_key=user_groq_key,
            model_name=selected_model,
            chat_history=st.session_state.chat_messages[:-1],
        )

        # Update in-memory state if changes occurred
        if updated_bytes != st.session_state.edited_pdf_bytes:
          update_edited_pdf(updated_bytes)

        st.write(agent_reply)
        st.session_state.chat_messages.append(
            {"role": "assistant", "content": agent_reply}
        )

    # Refresh canvas preview
    st.rerun()