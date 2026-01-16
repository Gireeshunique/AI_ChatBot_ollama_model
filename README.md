# 👉🧩 MSME ONE Assistant

A full‑stack AI assistant for MSMEs — React frontend + Flask backend — that supports English & Telugu, Whisper-based speech-to-text, semantic search (FAISS + SentenceTransformers), and integration with local LLMs via Ollama (e.g. `gemma2:2b`, `phi3.3:8b`).

![MSME Logo](https://github.com/Gireeshunique/AI_ChatBot_ollama_model/blob/c1226392c8d5f88d7adb98aa65b7f8bde0fe7e0e/Screenshot%202025-11-20%20234643.png)
![Project Diagram](images/diagram.png)

---

## 🚀 Features

* Bilingual chat (English ↔ Telugu) using Deep Translator
* Voice-to-text using OpenAI Whisper (local)
* Semantic search over uploaded docs (FAISS + SentenceTransformer)
* Pluggable LLM backend via Ollama (local models like `gemma2:2b`, `phi3.3:8b`)
* REST API backend (Flask) and modern React (Vite) frontend
* Embeddings stored as `embeddings.npy` + `metadata.json`
* Chat logging and basic admin routes

---

## 🗂️ Project Structure

```
project/
├── backend/
│   ├── app.py               # Flask backend (chat, upload, transcribe endpoints)
│   ├── ingest_dataset.py    # Prepare embeddings & FAISS index
│   ├── requirements.txt
│   └── data/
│       ├── embeddings.npy
│       ├── metadata.json
│       └── chat_logs.json
├── frontend/
│   ├── public/
│   │   └── index.html
│   ├── src/
│   │   ├── App.jsx
│   │   ├── ChatApp.jsx
│   │   ├── ChatMessage.jsx
│   │   └── index.js
│   ├── package.json
│   └── vite.config.js
└── README.md
```

---

## ⚙️ Prerequisites

* Node.js 18+ and npm
* Python 3.10+
* (Optional) Ollama installed and running locally for LLM-based responses
* (Optional) GPU / CUDA if you want faster Whisper or SentenceTransformer inference

---

## 🔧 Backend Setup (Flask)

1. Create & activate virtual environment

```bash
cd backend
python -m venv myenv
# Windows
myenv\Scripts\activate
# mac / linux
source myenv/bin/activate
```

2. Install dependencies

```bash
pip install -r requirements.txt
# if you don't have a requirements file, the main packages are:
# flask flask-cors faiss-cpu sentence-transformers openai-whisper deep-translator PyPDF2 torch numpy
```

3. Prepare embeddings (data ingestion)

```bash
python ingest_dataset.py
```

This script should:

* Read training documents (PDF/TXT) from a `data/raw/` folder
* Use a SentenceTransformer model (e.g. `all-MiniLM-L6-v2`) to compute embeddings
* Save `embeddings.npy` and `metadata.json` and build a FAISS index file

4. Run the Flask server

```bash
python app.py
```

Default: `http://localhost:5000`

---

## 🧭 Frontend Setup (React + Vite)

1. Install dependencies

```bash
cd frontend
npm install
```

2. Start the dev server

```bash
npm run dev
```

Default: `http://localhost:5173`

The frontend should call backend endpoints like `/api/chat`, `/api/transcribe`, `/api/search`, etc., via Axios.

---

## 🧠 LLM Integration (Ollama)

This project supports sending prompts to a local Ollama server (recommended for offline/local deployments). Example models we reference:

* `gemma2:2b` — fast, smaller model for chat & semantic tasks
* `phi3.3:8b` — larger, higher-quality model for complex responses

### Example usage (backend)

```python
import requests

def call_ollama(prompt, model="gemma2:2b"):
    url = f"http://localhost:11434/api/generate"
    payload = {"model": model, "prompt": prompt, "max_tokens": 512}
    r = requests.post(url, json=payload)
    r.raise_for_status()
    return r.json()
```

> Ensure your Ollama server is running and the models are installed locally:
>
> ```bash
> ollama run gemma2:2b
> ollama run phi3.3:8b
> ```

---

## 🔁 Translation & Bilingual Flow

* Incoming Telugu messages are translated to English for model processing using `deep-translator`.
* Model responses are translated back to Telugu when requested.

Example flow in `app.py`:

1. detect language (or rely on user selection)
2. if telugu -> translate to english
3. call retriever + LLM
4. translate response back if needed

---

## 🔎 Semantic Search

* `ingest_dataset.py` should produce a FAISS index and a parallel `metadata.json`.
* At query time, compute embedding for the user question and perform FAISS `search` to retrieve top-K docs.
* Construct a context prompt that includes retrieved snippets before calling the LLM.

---

## Environment & Configuration

Create a `.env` in `backend/` containing settings such as:

```
FLASK_ENV=development
OLLAMA_URL=http://localhost:11434
SENTENCE_TRANSFORMER_MODEL=all-MiniLM-L6-v2
FAISS_INDEX_PATH=data/faiss.index
EMBEDDINGS_PATH=data/embeddings.npy
METADATA_PATH=data/metadata.json
WHISPER_MODEL=small
```

Load with `python-dotenv` or `os.environ` in `app.py`.

---

## Example Endpoints (suggested)

* `POST /api/chat` — { message, user_id, language, model } → chat response
* `POST /api/transcribe` — multipart form audio file → transcript
* `POST /api/upload` — upload PDF/TXT to be added to dataset
* `GET /api/logs` — return saved `chat_logs.json` for admin

---

## Troubleshooting

* **Ollama 404 / connection errors:** confirm Ollama is running, `ollama ps` shows model, and `OLLAMA_URL` is correct.
* **FAISS errors on Windows:** prefer `faiss-cpu` and match the compiled wheel for your Python version.
* **Whisper slow / errors:** check that `torch` is installed and GPU/CUDA drivers are available if using GPU models.

---

## Security & Production Notes

* Add auth (JWT) for admin endpoints and rate-limit model calls.
* Store embeddings and metadata in a proper vector DB (e.g. Milvus, Pinecone, or Weaviate) for scaling.
* Sanitize and limit file upload sizes.

---

## Contribution

1. Fork the repo
2. Create a feature branch
3. Open a pull request describing changes

---

## License

This project is licensed under the **MSME** license. See `LICENSE` for details.

---
**Author:** Gireesh Boggala

**License:** MSME
