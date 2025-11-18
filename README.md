# 🚀 Full-Stack Project: React + Flask (MSME ONE Assistant)

This project is a full-stack web application built with a React.js frontend and a Flask (Python) backend.
It supports English and Telugu languages, voice-to-text queries using Whisper, and semantic search over uploaded documents using FAISS and Sentence Transformers.


## 🧩 Tech Stack
Layer	Technology	Purpose
Frontend	React.js, Axios, Vite	Chat UI, voice recording, multilingual support
Backend	Flask, Flask-CORS	REST APIs for chat, file upload, and transcription
ML Models	SentenceTransformer, Whisper, FAISS	Text embeddings, speech-to-text, semantic search
Translation	Deep Translator	Telugu ↔ English conversion
Data Format	JSON, NumPy, PDF (training files)	Store embeddings, metadata, logs


## 📂 Folder Structure
project/
├── backend/
│  
├── app.py               # Flask backend with chat + voice endpoints
│ 
├── ingest_dataset.py    # Embedding + dataset preparation
│ 
├── data/
│ 
│   ├── embeddings.npy
│ 
│   ├── metadata.json
│ 
│   └── chat_logs.json
│ 
└── requirements.txt
│

├── frontend/
│ 
├── src/
│  
│   ├── App.jsx
│  
│   ├── ChatApp.jsx
│ 
│   ├── ChatMessage.jsx
│  
│   └── index.js
│ 
├── public/
│ 
│   └── index.html
│ 
├── package.json
│ 
└── vite.config.js
│

└── README.md


## ⚙️Backend Setup (Flask + Python)
1. Create a virtual environment
cd backend
python -m venv myenv
myenv\Scripts\activate  # Windows

2. Install dependencies
pip install flask flask-cors faiss-cpu sentence-transformers openai-whisper deep-translator PyPDF2 torch numpy

3. Prepare data embeddings

⚙️Before starting the app, run the dataset ingestion script:

python ingest_dataset.py

4. Run Flask server
python app.py


The backend runs at http://localhost:5000

## 💻 Frontend Setup (React + Vite)
1. Install Node modules
cd frontend
npm install

2. Run the development server
npm run dev


Frontend runs at http://localhost:5173
