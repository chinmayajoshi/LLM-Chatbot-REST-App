# LLM Chatbot

A simple chatbot REST App using FastAPI, Streamlit, and Groq’s LLM API; built for Red Team testing.

Streamlit UI            |  Streamlit UI (Reasoning LLM)
:-------------------------:|:-------------------------:
![Streamlit UI](img/Streamlit%20UI%20Screenshot.jpg)    |  ![Streamlit UI](img/Streamlit%20UI%20Screenshot%20(Reasoning%20LLM).jpg)  



## Files  
- `chat_app.py` – Streamlit UI + FastAPI backend  
- `requirements.txt` – Dependencies  
- `/logs/` – Chat session logs  

## Setup & Run

1. install dependencies:  
   ```sh
   pip install -r requirements.txt
   ```

2. Create a `config.json` file in the project root with the following format:
    ```json
    { 
      "GROQ_API_KEY": "your_api_key_here" 
    }
    ``` 

3. Start the FastAPI server: 
    ```sh
    python -m uvicorn chat_app:app --host 127.0.0.1 --port 8000 --reload
    ```  
4. Run the Streamlit app: 
    ```sh
    streamlit run chat_app.py
    ```
5. Open in browser: [http://localhost:8501](http://localhost:8501)

## Built with

- **[FastAPI](https://fastapi.tiangolo.com/)** – Handles backend requests and routes (via [uvicorn](https://www.uvicorn.org/))
- **[Streamlit](https://streamlit.io/)** – Provides the chat UI  
- **[Groq API](https://groq.com/)** – Processes chat completions using LLM  