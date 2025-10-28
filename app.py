import streamlit as st
import requests
import time

# --- Configuration ---
BACKEND_URL = "http://127.0.0.1:8000"

# --- Streamlit UI ---
st.set_page_config(page_title="Financial Chatbot", layout="wide")
st.title("Financial Reports Analyzer 📈")
st.write("Upload a financial report (PDF) and ask questions about its content.")

# --- Session State Initialization ---
if "messages" not in st.session_state:
    st.session_state.messages = []
if "pdf_processed" not in st.session_state:
    st.session_state.pdf_processed = False

# --- Sidebar for PDF Upload ---
with st.sidebar:
    st.header("1. Upload PDF")
    uploaded_file = st.file_uploader("Choose a PDF file", type="pdf")

    if uploaded_file is not None:
        if st.button("Process Document"):
            with st.spinner("Processing document... This may take a moment."):
                files = {"file": (uploaded_file.name, uploaded_file.getvalue(), "application/pdf")}
                try:
                    response = requests.post(f"{BACKEND_URL}/upload/", files=files, timeout=600)
                    if response.status_code == 200:
                        st.session_state.pdf_processed = True
                        st.session_state.messages = [] # Clear previous chat
                        st.success("Document processed successfully! You can now ask questions.")
                    else:
                        st.error(f"Error processing document: {response.text}")
                except requests.exceptions.RequestException as e:
                    st.error(f"Connection error: {e}")

# --- Main Chat Interface ---
st.header("2. Chat with the Document")

if not st.session_state.pdf_processed:
    st.warning("Please upload and process a document in the sidebar to begin.")
else:
    # Display existing messages
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # Chat input
    if prompt := st.chat_input("Ask a question about the document..."):
        # Add user message to chat history
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        # Get assistant response
        with st.chat_message("assistant"):
            message_placeholder = st.empty()
            with st.spinner("Thinking..."):
                try:
                    # Prepare chat history for the API
                    api_chat_history = [
                        {"type": msg["role"], "content": msg["content"]}
                        for msg in st.session_state.messages
                    ]
                    
                    response = requests.post(
                        f"{BACKEND_URL}/chat/",
                        json={"question": prompt, "chat_history": api_chat_history[:-1]}, # Send history *before* the new question
                        timeout=600
                    )
                    
                    if response.status_code == 200:
                        full_response = response.json()["answer"]
                        message_placeholder.markdown(full_response)
                        st.session_state.messages.append({"role": "assistant", "content": full_response})
                    else:
                        st.error(f"Error from API: {response.text}")

                except requests.exceptions.RequestException as e:
                    st.error(f"Connection error: {e}")