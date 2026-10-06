"""Session state management for the AI Resume Editor."""

import streamlit as st


def init_session_state():
  """Initializes session state variables required for the PDF editor."""
  if "original_pdf_bytes" not in st.session_state:
    st.session_state.original_pdf_bytes = None

  if "edited_pdf_bytes" not in st.session_state:
    st.session_state.edited_pdf_bytes = None

  if "current_page" not in st.session_state:
    st.session_state.current_page = 0

  if "history" not in st.session_state:
    # Stack of previous PDF byte states to allow undo functionality
    st.session_state.history = []

  if "chat_messages" not in st.session_state:
    # Track prompt and agent response history
    st.session_state.chat_messages = []

  if "file_name" not in st.session_state:
    st.session_state.file_name = "resume.pdf"


def set_uploaded_pdf(file_bytes: bytes, file_name: str):
  """Sets a newly uploaded PDF into session state and resets history."""
  st.session_state.original_pdf_bytes = file_bytes
  st.session_state.edited_pdf_bytes = file_bytes
  st.session_state.current_page = 0
  st.session_state.history = []
  st.session_state.file_name = file_name
  st.session_state.chat_messages = []


def update_edited_pdf(new_pdf_bytes: bytes):
  """Appends current state to history and updates edited PDF bytes."""
  if st.session_state.edited_pdf_bytes is not None:
    st.session_state.history.append(st.session_state.edited_pdf_bytes)
  st.session_state.edited_pdf_bytes = new_pdf_bytes


def undo_last_edit():
  """Reverts the last edit operation from history."""
  if st.session_state.history:
    st.session_state.edited_pdf_bytes = st.session_state.history.pop()
    return True
  return False