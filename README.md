# MSME ONE — AI Support Assistant

An intelligent multilingual chatbot system built with a Python Flask backend, Ollama local LLMs, React frontend, and Whisper speech-to-text. Designed to run locally (offline-capable) and allow per-model PDF-based training to improve contextual replies.

---

## Table of contents

* [Project overview](#project-overview)
* [Features](#features)
* [Tech stack](#tech-stack)
* [Repository structure](#repository-structure)
* [Requirements](#requirements)
* [Installation](#installation)
* [Configuration](#configuration)
* [Running the app](#running-the-app)
* [API Endpoints](#api-endpoints)
* [How PDF training works](#how-pdf-training-works)
* [Voice assistant flow](#voice-assistant-flow)
* [Admin panel](#admin-panel)
* [Troubleshooting](#troubleshooting)
* [Security & notes](#security--notes)
* [Contributing](#contributing)
* [License](#license)

---

## Project overview

MSME ONE is a local-first multilingual AI support assistant that:

* Runs LLMs locally with Ollama (or other LLM runtimes you choose).
* Supports multiple model families per deployment (e.g. `llama3.1:8b`, `gemma2:2b`, `phi3`, `mistral`).
* Accepts PDFs and converts them to a training corpus per model for RAG-like contextual replies.
* Uses Whisper for speech-to-text and accepts Telugu / English voice input.
* Provides a simple Admin UI for uploading training PDFs and managing model-specific data.

## Features

* Local/offline LLM chat using Ollama.
* Per-model PDF ingestion and storage (corpus saved under `backend/data/<model>`).
* Multilingual responses: English, Telugu, or auto-detected by the backend.
* Whisper-based voice transcription + chat reply audio (if you integrate TTS).
* Admin login (default demo creds) and training data management.
* Chat logging per model for audit and future improvement.

## Tech stack

**Frontend**: React.js, Axios, custom UI components, voice recorder

**Backend**: Python Flask, Whisper, PyPDF2 (or pdfplumber), Ollama local models, deep-translator

**Models**: Ollama models (e.g. `llama3.1:8b`, `gemma2:2b`, `phi3`, `mistral`)

## Repository structure

```
project/
├── backend/
│   ├── app.py
│   ├── requirements.txt
│   ├── data/
│   │   ├── llama/
│   │   ├── phi/
│   │   └── mistral/
│   └── ...
└── frontend/
    ├── package.json
    ├── src/
    └── build/
```

## Requirements

* Python 3.9+ (3.10+ recommended)
* Node.js 18+ / npm
* FFmpeg (required for Whisper voice processing)
* Ollama installed and running locally

## Installation

### 1. Backend (Python)

```bash
# create & activate venv
python -m venv venv
source venv/bin/activate    # macOS / Linux
venv\Scripts\activate      # Windows

pip install -r backend/requirements.txt
# if you don't have requirements.txt, the main packages are:
# pip install flask flask-cors python-dotenv deep-translator PyPDF2 openai-whisper requests
```

Install or verify ffmpeg is available on PATH:

* macOS: `brew install ffmpeg`
* Ubuntu/Debian: `sudo apt install ffmpeg`
* Windows: download from [https://ffmpeg.org](https://ffmpeg.org) and add to PATH

### 2. Ollama and Models

1. Install Ollama from [https://ollama.com/download](https://ollama.com/download) and follow platform instructions.
2. Start Ollama (if the service requires it on your platform).
3. Pull models you plan to use locally with Ollama, for example:

```bash
ollama pull llama3.1:8b
ollama pull gemma2:2b
ollama pull phi3
ollama pull mistral
```

4. Confirm models are available:

```bash
ollama list
```

> **Important**: Confirm Ollama's HTTP endpoint (default `http://localhost:11434`) and change backend config if different.

### 3. Frontend (React)

```bash
cd frontend
npm install
npm start
```

## Configuration

Create a `.env` file in `backend/` if needed. Example:

```
FLASK_ENV=development
OLLAMA_URL=http://localhost:11434
ADMIN_USER=admin
ADMIN_PASS=msme@123
PORT=5000
```

## Running the app

1. Start Ollama and ensure the models you need are pulled and listed.
2. Start the backend:

```bash
cd backend
python app.py
```

By default the Flask server runs on `http://localhost:5000`.

3. Start the frontend:

```bash
cd frontend
npm start
```

Open `http://localhost:3000` in the browser.

## API Endpoints

Below are the primary endpoints implemented by the project.

* `POST /api/chat`

  * Send: `{ model: "llama", message: "...", lang: "te" }`
  * Response: JSON with `reply`, `metadata` etc.

* `POST /api/transcribe`

  * Accepts multipart audio (wav/m4a). Returns transcription by Whisper.

* `POST /api/admin/login`

  * Accepts `{ username, password }`. Returns session/cookie.

* `POST /api/admin/train`

  * Upload PDF(s) to be processed for a specific model. Example form fields: `model=llama`, `file=@/path/to/doc.pdf`.

* `GET /api/admin/train/info?model=llama`

  * Returns training metadata for the model (list of files, sizes, ingestion date).

* `POST /api/admin/train/delete?model=mistral`

  * Deletes the stored training corpus for the specified model.

## How PDF training works

1. Admin uploads PDF(s) via the Admin UI.
2. Backend extracts text (via `PyPDF2` / `pdfplumber`) and optionally splits it into chunks / sentences.
3. Plain text is saved under `backend/data/<model>/` (organized by filename and timestamp).
4. On chat requests, backend looks up the `data/<model>` corpus and constructs context (simple retrieval or basic RAG) to pass along with the user prompt to the LLM.

Implementation notes:

* Keep an eye on chunk sizes to avoid exceeding model context window.
* Consider using embeddings + vector DB (faiss / milvus) for better retrieval if corpus grows.

## Voice assistant flow

* Client records audio and sends it to `/api/transcribe`.
* Backend runs Whisper transcription, returns text.
* The frontend sends the transcription to `/api/chat` to get a model response.
* Optionally play TTS audio of the reply in the client.

## Admin panel

* Default demo credentials in `.env` or `app.py`: `admin / msme@123`.
* Admin features:

  * Upload PDFs per model
  * See uploaded files & ingestion timestamps
  * Delete training data for a model

## Troubleshooting

* **No response in frontend**

  * Ensure Ollama is running and `ollama list` shows the model. The backend should call Ollama with `"stream": False` (some LLM runtimes may expect streaming disabled for synchronous replies).
  * Test Ollama HTTP health: `curl http://localhost:11434`.
  * Check Flask logs for errors or stack traces.

* **Ollama model not found**

  * `ollama list` to check installed models.
  * Pull the model again: `ollama pull gemma2:2b` (or correct model name/version).

* **Whisper audio issues**

  * Ensure `ffmpeg` is installed and accessible in PATH.
  * Use WAV or M4A input; confirm MIME-type and file encoding.

## Example cURL requests

**Chat**

```bash
curl -X POST http://localhost:5000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"model":"llama", "message":"Hello, how can I get a loan?", "lang":"en"}'
```

**Transcribe**

```bash
curl -X POST http://localhost:5000/api/transcribe \
  -F "file=@/path/to/audio.wav"
```

**Upload training PDF**

```bash
curl -X POST "http://localhost:5000/api/admin/train?model=llama" \
  -F "file=@/path/to/manual.pdf" \
  -u admin:msme@123
```

## Security & notes

* This project is intended for local, internal, or demo usage. If you deploy in a production environment consider:

  * Securing endpoints with stronger auth (JWT, OAuth).
  * Rate limiting and request validation for uploads.
  * Storing secrets / credentials outside the repo (use environment variables or a secrets manager).
  * Sanitizing/validating uploaded PDFs to avoid malicious payloads.

## Contributing

Contributions are welcome. Recommended workflow:

1. Fork this repository.
2. Create a feature branch.
3. Open a PR with a clear description & testing notes.

## License

This project was developed for MSME ONE Support Assistant. All rights reserved — modify this section to reflect the desired open source license if you plan to publish.

---

If you want, I can also:

* Generate a `.env.example` file.
* Produce an `install.sh` script for dev setup.
* Add sample `curl` commands directly to the admin UI.
