import json
import logging
import os
import time
import re
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
logging.basicConfig(
    filename=log_filename, 
    level=logging.INFO, 
    format="%(asctime)s - %(levelname)s - %(message)s"
    )

app = FastAPI()

GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"
# Define available models
AVAILABLE_MODELS = {
    "Llama 3.3 70B": "llama-3.3-70b-versatile",
    "Llama 3.1 8B": "llama-3.1-8b-instant",
    "DeepSeek R1 Distill Qwen 32B": "deepseek-r1-distill-qwen-32b",
    "Llama Guard 3 8B": "llama-guard-3-8b"
}
# Define thinking/reasoning models
THINKING_MODELS = ["deepseek-r1-distill-qwen-32b"]

@app.post("/chat")
def chat(request: dict):
    user_message = request.get("message")
    chat_history = request.get("history", [])
    model_name = request.get("model", "llama-3.3-70b-versatile")
    
    if not user_message:
        logging.warning("Received request with missing 'message'")
        raise HTTPException(status_code=400, detail="Missing 'message' in request")

    messages = chat_history + [{"role": "user", "content": user_message}]
    
    payload = {
        "model": model_name,
        "messages": messages,
        "temperature": 0.7,
    }
    headers = {"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}

    try:
        response = requests.post(GROQ_API_URL, json=payload, headers=headers)
        response.raise_for_status()
        data = response.json()
        reply = data.get("choices", [{}])[0].get("message", {}).get("content", "No response")
        logging.info(f"Model: {model_name} | User: {user_message} | Bot: {reply}")
        return {"response": reply, "history": messages + [{"role": "assistant", "content": reply}]}
    except requests.RequestException as e:
        logging.error(f"API request failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch response from LLM")

# Function to process thinking model output
def process_thinking_response(response):
    think_pattern = r'<think>(.*?)</think>'
    match = re.search(think_pattern, response, re.DOTALL)
    
    if match:
        thinking = match.group(1).strip()
        main_response = re.sub(think_pattern, '', response, flags=re.DOTALL).strip()
        return thinking, main_response
    
    return None, response

# Toggle thinking section
def toggle_thinking(key):
    st.session_state["thinking_expanded"][key] = not st.session_state["thinking_expanded"].get(key, False)

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
            .thinking-section {
                background-color: rgba(60, 60, 60, 0.2);
                padding: 10px;
                border-radius: 10px;
                margin-bottom: 10px;
                border-left: 3px solid #aaa;
                color: #cccccc;
                font-size: 0.9em;
            }
            .toggle-button {
                background-color: transparent;
                border: none;
                color: #aaaaaa;
                padding: 2px 8px;
                text-align: left;
                text-decoration: none;
                display: inline-block;
                font-size: 0.8em;
                margin: 2px 0;
                cursor: pointer;
                border-radius: 4px;
            }
            .toggle-button:hover {
                background-color: rgba(100, 100, 100, 0.2);
                color: #ffffff;
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
    
    # Initialize session state variables
    if "chat_history" not in st.session_state:
        st.session_state["chat_history"] = []
    if "user_input" not in st.session_state:
        st.session_state["user_input"] = ""
    if "selected_model" not in st.session_state:
        st.session_state["selected_model"] = "Llama 3.3 70B"
    if "thinking_expanded" not in st.session_state:
        st.session_state["thinking_expanded"] = {}
    
    # Model selection dropdown in sidebar
    with st.sidebar:
        st.header("Model Selection")
        selected_model_display = st.selectbox(
            "Choose a model:",
            options=list(AVAILABLE_MODELS.keys()),
            index=0,
            key="model_selector"
        )
        st.session_state["selected_model"] = selected_model_display
        
        # Show indicator for thinking models
        if AVAILABLE_MODELS[selected_model_display] in THINKING_MODELS:
            st.info("This is a thinking/reasoning model with chain-of-thought capabilities.")
    
    # Display chat history
    chat_container = st.container()
    with chat_container:
        # Group messages by conversation pairs
        i = 0
        while i < len(st.session_state["chat_history"]):
            # Display user message
            if i < len(st.session_state["chat_history"]):
                user_msg = st.session_state["chat_history"][i]
                st.markdown(f'<div class="user-message"><b>You:</b> {user_msg["content"]}</div>', unsafe_allow_html=True)
                i += 1
            
            # Display assistant message if available
            if i < len(st.session_state["chat_history"]):
                assistant_msg = st.session_state["chat_history"][i]
                model_key = st.session_state.get(f"model_used_{i//2}", "Llama 3.3 70B")
                
                # Check if this is from a thinking model
                if AVAILABLE_MODELS[model_key] in THINKING_MODELS:
                    thinking, main_response = process_thinking_response(assistant_msg["content"])
                    
                    if thinking:
                        thinking_id = f"thinking_{i}"
                        
                        # Use a proper button for toggle
                        expanded = st.session_state["thinking_expanded"].get(thinking_id, False)
                        toggle_text = "▶ Show thinking" if not expanded else "▼ Hide thinking"
                        
                        # Create a proper button with unique key
                        if st.button(toggle_text, key=f"toggle_btn_{thinking_id}", on_click=toggle_thinking, args=(thinking_id,), type="secondary", help="Toggle thinking process"):
                            pass  # The on_click handler takes care of the state change
                        
                        # Show thinking section if expanded
                        if st.session_state["thinking_expanded"].get(thinking_id, False):
                            st.markdown(f'<div class="thinking-section"><pre>{thinking}</pre></div>', unsafe_allow_html=True)
                        
                        # Show the main response
                        st.markdown(f'<div class="bot-message"><b>Bot:</b> {main_response}</div>', unsafe_allow_html=True)
                    else:
                        st.markdown(f'<div class="bot-message"><b>Bot:</b> {assistant_msg["content"]}</div>', unsafe_allow_html=True)
                else:
                    st.markdown(f'<div class="bot-message"><b>Bot:</b> {assistant_msg["content"]}</div>', unsafe_allow_html=True)
                i += 1
    
    # Create a callback that processes the input
    def submit_message():
        if st.session_state["user_input"].strip():
            user_message = st.session_state["user_input"].strip()
            model_key = st.session_state["selected_model"]
            model_name = AVAILABLE_MODELS[model_key]
            
            try:
                with st.spinner("Thinking..."):
                    response = requests.post(
                        "http://127.0.0.1:8000/chat", 
                        json={
                            "message": user_message, 
                            "history": st.session_state["chat_history"],
                            "model": model_name
                        }
                    )
                    result = response.json()
                    reply = result.get("response", "Error fetching response")
                    
                    # Store which model was used for this exchange
                    conversation_index = len(st.session_state["chat_history"]) // 2
                    st.session_state[f"model_used_{conversation_index}"] = model_key
                    
                    st.session_state["chat_history"].append({"role": "user", "content": user_message})
                    st.session_state["chat_history"].append({"role": "assistant", "content": reply})
            except requests.RequestException as e:
                st.error(f"Request failed: {e}")

    # Use a form to handle the input and submission
    with st.form(key="message_form", clear_on_submit=True):
        user_input = st.text_input("Enter your message:", placeholder="Type your message and press Enter...", key="user_input")
        submit_button = st.form_submit_button("Send", on_click=submit_message)
        
    model_name = AVAILABLE_MODELS[st.session_state["selected_model"]]
    st.write(f"Using model: {model_name}")

if __name__ == "__main__":
    main()

# To start FastAPI server, run:
# python -m uvicorn chat_app:app --host 127.0.0.1 --port 8000 --reload