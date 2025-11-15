🚀 MSME ONE – AI Support Assistant

An intelligent multilingual chatbot system built using Python Flask, Ollama Local LLMs, React Frontend, and Whisper speech-to-text.
Supports multiple AI models (LLaMA / Phi / Mistral) and PDF-based training per model.

📌 Features
🧠 AI Chat (Local Offline)

Uses Ollama to run LLMs locally

Supports:

llama3.2

phi3

mistral

Replies in Telugu, English, or auto-detects language

Uses trained context from uploaded PDFs

🎙️ Voice Assistant

Whisper converts speech → text

Supports Telugu speech recognition

AI replies back using selected LLM

📄 PDF Training (Per Model)

You can upload PDFs and the bot learns from them:

Extracts text

Saves corpus per model

Used for contextual replies

🔐 Admin Panel

Simple login (admin/msme@123)

Upload PDFs

View training info

Delete training data

💬 Chat Logging

All user messages are saved per model for audit and improvement.

🛠️ Tech Stack
Frontend

React.js

Axios

Custom UI Components

Voice Recorder

Backend

Python Flask

Whisper (small model)

PyPDF2

Deep Translator

Ollama local models

CORS enabled

📦 Project Structure
project/
│
├── backend/
│   ├── app.py
│   ├── data/
│   │   ├── llama/
│   │   ├── phi/
│   │   └── mistral/
│   └── ...
│
└── frontend/
    ├── src/
    ├── build/
    └── ...

⚙️ Installation Guide
1️⃣ Install Python Requirements
pip install flask flask-cors python-dotenv deep-translator PyPDF2 openai-whisper requests

2️⃣ Install Whisper (FFmpeg Required)
pip install openai-whisper


Install FFmpeg:

Windows: download from ffmpeg.org

Linux: sudo apt install ffmpeg

Mac: brew install ffmpeg

🤖 Install Ollama & Models
Install Ollama

Download from:
https://ollama.com/download

Check if running:

ollama list

Pull required models:
ollama pull llama3.2
ollama pull phi3
ollama pull mistral

▶️ Running the Backend

Inside the backend folder:

python app.py


Runs at:

http://localhost:5000

▶️ Running the Frontend

Inside the frontend folder:

npm install
npm start


Runs at:

http://localhost:3000

📡 API Endpoints
Chat
POST /api/chat

Voice Transcription
POST /api/transcribe

Admin Login
POST /api/admin/login

Upload Training PDFs
POST /api/admin/train

Get Training Info
GET /api/admin/train/info?model=llama

Delete Model Data
POST /api/admin/train/delete?model=mistral

🧪 Troubleshooting
❌ No response in frontend?

✔ Ensure backend ollama_chat_response uses:

"stream": False


✔ Check Ollama is running:

curl http://localhost:11434


✔ Verify model exists:

ollama list

📝 License

This project is developed for MSME ONE Support Assistant.
All rights reserved.
