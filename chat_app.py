import json
import logging
import os
import time
from datetime import datetime
from fastapi import FastAPI, HTTPException
import requests
import streamlit as st

# load api key from config file
CONFIG_FILE = "config.json"
try:
    with open(CONFIG_FILE, "r") as f:
        config = json.load(f)
        API_KEY = config.get("GROQ_API_KEY")
        if not API_KEY:
            raise ValueError("Missing API key in config.json")
except Exception as e:
    raise RuntimeError(f"Error loading config: {e}")

# setup logging
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
log_filename = f"logs/session_{timestamp}.log"
os.makedirs("logs", exist_ok=True)
logging.basicConfig(filename=log_filename, level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

app = FastAPI()

GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"

@app.post("/chat")
def chat(request: dict):
    user_message = request.get("message")
    chat_history = request.get("history", [])
    if not user_message:
        logging.warning("Received request with missing 'message'")
        raise HTTPException(status_code=400, detail="Missing 'message' in request")

    messages = chat_history + [{"role": "user", "content": user_message}]
    
    payload = {
        "model": "llama-3.1-8b-instant",
        "messages": messages,
        "temperature": 0.7,
    }
    headers = {"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}

    try:
        response = requests.post(GROQ_API_URL, json=payload, headers=headers)
        response.raise_for_status()
        data = response.json()
        reply = data.get("choices", [{}])[0].get("message", {}).get("content", "No response")
        logging.info(f"User: {user_message} | Bot: {reply}")
        return {"response": reply, "history": messages + [{"role": "assistant", "content": reply}]}
    except requests.RequestException as e:
        logging.error(f"API request failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch response from LLM")

# Streamlit UI
def main():
    st.set_page_config(page_title="LLM Chatbot", page_icon="💬", layout="centered")
    st.markdown("""
        <style>
            body { color: white; }
            .user-message {
                background-color: #dcf8c6;
                padding: 10px;
                border-radius: 10px;
                margin-bottom: 5px;
                color: black;
            }
            .bot-message {
                background-color: #f1f0f0;
                padding: 10px;
                border-radius: 10px;
                margin-bottom: 5px;
                color: black;
            }
            .stTextInput, .stTextArea {
                border-radius: 12px;
                border: 1px solid #ccc;
                padding: 10px;
            }
            .stButton>button {
                width: 100%;
                background-color: #4CAF50;
                color: white;
                font-size: 16px;
                border-radius: 8px;
                padding: 10px;
            }
            .stButton>button:hover {
                background-color: #45a049;
            }
        </style>
    """, unsafe_allow_html=True)
    
    st.title("💬 Minimalist LLM Chatbot")
    st.write("Talk to the chatbot below.")
    
    if "chat_history" not in st.session_state:
        st.session_state["chat_history"] = []
    if "user_input" not in st.session_state:
        st.session_state["user_input"] = ""
    if "submit" not in st.session_state:
        st.session_state["submit"] = False
    
    for msg in st.session_state["chat_history"]:
        role = "You" if msg["role"] == "user" else "Bot"
        css_class = "user-message" if msg["role"] == "user" else "bot-message"
        st.markdown(f'<div class="{css_class}"><b>{role}:</b> {msg["content"]}</div>', unsafe_allow_html=True)
    
  # Create a callback that processes the input but doesn't try to clear it
    def submit_message():
        if st.session_state["user_input"].strip():
            user_message = st.session_state["user_input"].strip()
            
            try:
                with st.spinner("Thinking..."):
                    response = requests.post("http://127.0.0.1:8000/chat", json={"message": user_message, "history": st.session_state["chat_history"]})
                    result = response.json()
                    reply = result.get("response", "Error fetching response")
                    st.session_state["chat_history"].append({"role": "user", "content": user_message})
                    st.session_state["chat_history"].append({"role": "assistant", "content": reply})
            except requests.RequestException as e:
                st.error(f"Request failed: {e}")

    # Use a form to handle the input and submission
    with st.form(key="message_form", clear_on_submit=True):
        user_input = st.text_input("Enter your message:", placeholder="Type your message and press Enter...", key="user_input")
        submit_button = st.form_submit_button("Send", on_click=submit_message)
        

if __name__ == "__main__":
    main()

# To start FastAPI server, run:
# python -m uvicorn chat_app:app --host 127.0.0.1 --port 8000 --reload
