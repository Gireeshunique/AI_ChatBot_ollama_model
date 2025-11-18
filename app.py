# app.py
import os
import json
import time
import sys
import subprocess
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from deep_translator import GoogleTranslator
from dotenv import load_dotenv
import requests
import numpy as np
import faiss
from sentence_transformers import SentenceTransformer
import threading
import whisper
import shutil
import tempfile
import zipfile

# ----------------- Env & Paths -----------------
load_dotenv()
BACKEND_ROOT = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BACKEND_ROOT, "data")
UPLOADS_DIR = os.path.join(DATA_DIR, "uploads")
CORPUS_PATH = os.path.join(DATA_DIR, "pdf_corpus.txt")
METADATA_PATH = os.path.join(DATA_DIR, "metadata.json")
EMBEDDINGS_PATH = os.path.join(DATA_DIR, "embeddings.npy")
INDEX_PATH = os.path.join(DATA_DIR, "faiss.index")
CHAT_LOG = os.path.join(DATA_DIR, "chat_logs.json")
TRAIN_INFO_PATH = os.path.join(DATA_DIR, "train_info_versions.json")

os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(UPLOADS_DIR, exist_ok=True)

# ----------------- Flask app -----------------
app = Flask(__name__, static_folder="../frontend/build", static_url_path="/")
CORS(app, supports_credentials=True)
app.secret_key = os.getenv("FLASK_SECRET", "change_this_secret")

# ----------------- Load sentence-transformer for queries ----------- 
embed_model = None
index = None
metadata = None

def load_index_and_models():
    global embed_model, index, metadata
    try:
        print("Loading embed model...")
        embed_model = SentenceTransformer("all-MiniLM-L6-v2")
    except Exception as e:
        print("Failed to load sentence-transformer:", e)
        embed_model = None

    if os.path.exists(INDEX_PATH) and os.path.exists(METADATA_PATH) and os.path.exists(EMBEDDINGS_PATH):
        try:
            print("Loading FAISS index and metadata...")
            index = faiss.read_index(INDEX_PATH)
            metadata = json.load(open(METADATA_PATH, "r", encoding="utf-8"))
            print("Index & metadata loaded.")
        except Exception as e:
            print("Error loading index/metadata:", e)
            index = None
            metadata = None
    else:
        print("Index or metadata missing — run ingestion first.")

load_index_and_models()

# ----------------- Whisper (optional) -----------------
whisper_model = None
def load_whisper():
    global whisper_model
    try:
        print("Loading Whisper model (background)...")
        whisper_model = whisper.load_model("small", device="cpu")
        print("Whisper loaded.")
    except Exception as e:
        print("Whisper load error:", e)
        whisper_model = None

threading.Thread(target=load_whisper, daemon=True).start()

# ----------------- Utilities -----------------
def translate_text(text, target_lang):
    if not text or not text.strip():
        return text
    try:
        return GoogleTranslator(source="auto", target=target_lang).translate(text)
    except Exception as e:
        print("Translate error:", e)
        return text

def retrieve_chunks(query, top_k=4):
    global embed_model, index, metadata
    if embed_model is None or index is None or metadata is None:
        return []
    try:
        q_emb = embed_model.encode([query], convert_to_numpy=True)
        try:
            faiss.normalize_L2(q_emb)
        except Exception:
            q_emb = q_emb / (np.linalg.norm(q_emb, axis=1, keepdims=True) + 1e-10)
        D, I = index.search(q_emb.astype("float32"), top_k)
        results = []
        for idx in I[0]:
            if idx < 0 or idx >= len(metadata):
                continue
            results.append(metadata[idx].get("text", ""))
        return results
    except Exception as e:
        print("retrieve_chunks error:", e)
        return []

def make_context_text(chunks):
    joined = "\n\n".join(chunks)
    return joined[:3500]

# ----------------- Ollama generic call -----------------
def call_ollama_generic(model_name, context_text, question, timeout=40):
    endpoint = "http://localhost:11434/api/generate"
    full_prompt = (
        "Use the context below to answer the question. If the answer is not in the context, answer concisely.\n\n"
        f"CONTEXT:\n{context_text}\n\nQUESTION:\n{question}\n\nAnswer:"
    )
    try:
        r = requests.post(endpoint, json={"model": model_name, "prompt": full_prompt, "stream": False}, timeout=timeout)
        print(f"[Ollama] status={r.status_code}")
        print("[Ollama] resp preview:", (r.text or "")[:500])
        if r.status_code != 200:
            return f"⚠️ Ollama error {r.status_code}: {r.text}"
        try:
            j = r.json()
        except ValueError:
            return r.text or "⚠️ Ollama returned non-JSON response."
        if isinstance(j, dict):
            if "response" in j and isinstance(j["response"], str):
                return j["response"].strip()
            if "choices" in j and isinstance(j["choices"], list) and len(j["choices"]) > 0:
                first = j["choices"][0]
                for key in ("text", "content", "message", "output"):
                    if key in first and isinstance(first[key], str):
                        return first[key].strip()
        return str(j)[:2000]
    except requests.exceptions.ConnectionError:
        return "⚠️ Ollama is not running on localhost:11434. Start it with: ollama serve"
    except requests.Timeout:
        return "⚠️ Ollama request timed out."
    except Exception as e:
        print("Ollama call error:", e)
        return f"⚠️ Ollama call error: {e}"

# ----------------- Chat logging -----------------
def log_chat(model, question, answer):
    logs = []
    if os.path.exists(CHAT_LOG):
        try:
            with open(CHAT_LOG, "r", encoding="utf-8") as f:
                logs = json.load(f)
        except Exception:
            logs = []
    logs.append({"model": model, "question": question, "answer": answer, "ts": time.time()})
    try:
        with open(CHAT_LOG, "w", encoding="utf-8") as f:
            json.dump(logs, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print("Failed to write chat log:", e)

# ----------------- Train info helpers -----------------
def read_train_history():
    if not os.path.exists(TRAIN_INFO_PATH):
        return []
    try:
        return json.load(open(TRAIN_INFO_PATH, "r", encoding="utf-8"))
    except Exception:
        return []

def write_train_history(history):
    try:
        with open(TRAIN_INFO_PATH, "w", encoding="utf-8") as f:
            json.dump(history, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print("Failed to write train history:", e)

# ----------------- Routes -----------------
@app.route("/api/chat", methods=["POST"])
def chat():
    data = request.get_json(force=True)
    message = data.get("message", "").strip()
    lang = data.get("lang", "auto")
    model_choice = data.get("model", "ollama:gemma2")  
    top_k = int(data.get("top_k", 4))

    if not message:
        return jsonify({"reply": "⚠️ Please enter a message."}), 400

    query_for_search = message if lang != "te" else translate_text(message, "en")
    chunks = retrieve_chunks(query_for_search, top_k=top_k)
    context_text = make_context_text(chunks)

    answer = "⚠️ Unknown model selection."
    if model_choice.startswith("ollama"):
        parts = model_choice.split(":", 1)
        if len(parts) == 2:
            alias = parts[1]
            if alias == "gemma2":
                answer = call_ollama_generic("gemma2:2b", context_text, message)
            elif alias == "phi3":
                answer = call_ollama_generic("phi3:3.8b", context_text, message)
            else:
                answer = f"⚠️ Unknown Ollama model alias: {alias}"
        else:
            answer = "⚠️ Invalid model format."
    else:
        answer = "⚠️ Unsupported model."

    log_chat(model_choice, message, answer)
    return jsonify({"reply": answer, "used_context": chunks})

# ---------- Transcription endpoint (Whisper) ----------
@app.route("/api/transcribe", methods=["POST"])
def transcribe_audio():
    file = request.files.get("file")
    lang = request.form.get("lang", "en")
    model_choice = request.form.get("model", "ollama:gemma2")

    if file is None:
        return jsonify({"error": "No audio file uploaded."}), 400

    tmpdir = tempfile.mkdtemp()
    try:
        tmp_path = os.path.join(tmpdir, "upload.wav")
        file.save(tmp_path)

        text = ""
        if whisper_model is not None:
            try:
                res = whisper_model.transcribe(tmp_path, language=None)
                text = res.get("text", "").strip()
            except Exception as e:
                print("Whisper transcription error:", e)
                text = ""
        else:
            return jsonify({"error": "Transcription model not available."}), 503

        query_for_search = text if lang != "te" else translate_text(text, "en")
        chunks = retrieve_chunks(query_for_search, top_k=4)
        context_text = make_context_text(chunks)

        reply = "⚠️ Unknown model selection."
        if model_choice.startswith("ollama"):
            parts = model_choice.split(":", 1)
            alias = parts[1] if len(parts) > 1 else ""
            if alias == "gemma2":
                reply = call_ollama_generic("gemma2:2b", context_text, text)
            elif alias == "phi3":
                reply = call_ollama_generic("phi3:3.8b", context_text, text)
            else:
                reply = f"⚠️ Unknown Ollama model alias: {alias}"
        else:
            reply = "⚠️ Unsupported model."

        log_chat(model_choice, text, reply)
        return jsonify({"text": text, "reply": reply, "used_context": chunks})
    finally:
        try:
            shutil.rmtree(tmpdir)
        except Exception:
            pass

# ---------- Admin routes ----------
@app.route("/api/admin/train", methods=["POST"])
def admin_train():
    files = request.files.getlist("files")
    version = request.form.get("version", f"v{int(time.time())}")
    description = request.form.get("description", "")
    model_key = request.form.get("model_key", "ollama")
    train_rag = request.form.get("train_rag", "true").lower() == "true"

    if not files:
        return jsonify({"message": "No PDF files uploaded."}), 400

    model_upload_dir = os.path.join(UPLOADS_DIR, model_key, version)
    os.makedirs(model_upload_dir, exist_ok=True)

    saved_files = []
    for f in files:
        fname = f.filename
        dest = os.path.join(model_upload_dir, fname)
        f.save(dest)
        saved_files.append(fname)

    train_info = {
        "model": model_key,
        "version": version,
        "description": description,
        "files": saved_files,
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "active": True
    }
    history = read_train_history()
    for entry in history:
        if entry.get("model") == model_key:
            entry["active"] = False
    history.insert(0, train_info)
    write_train_history(history)

    if train_rag:
        try:
            tmp_zip = os.path.join(DATA_DIR, f"tmp_uploads_{int(time.time())}.zip")
            with zipfile.ZipFile(tmp_zip, "w") as z:
                for root, _, files_walk in os.walk(UPLOADS_DIR):
                    for fname in files_walk:
                        if fname.lower().endswith(".pdf"):
                            z.write(os.path.join(root, fname), arcname=fname)
            env = os.environ.copy()
            env["ZIP_PATH_OVERRIDE"] = tmp_zip
            subprocess.run([sys.executable, os.path.join(BACKEND_ROOT, "ingest_build_index.py")], env=env, check=False)
            load_index_and_models()
            try:
                os.remove(tmp_zip)
            except Exception:
                pass
        except Exception as e:
            print("Failed to run ingestion:", e)
            return jsonify({"message": "Uploaded but ingestion failed", "error": str(e)}), 500

    return jsonify({"message": f"Trained on {len(saved_files)} PDFs.", "train_info": train_info})

@app.route("/api/admin/activate", methods=["POST"])
def activate_version():
    data = request.get_json(force=True)
    model_key = data.get("model")
    version = data.get("version")

    if not model_key or not version:
        return jsonify({"success": False, "message": "Model and version required."}), 400

    history = read_train_history()
    found = False
    for entry in history:
        if entry.get("model") == model_key and entry.get("version") == version:
            entry["active"] = True
            found = True
        elif entry.get("model") == model_key:
            entry["active"] = False

    if not found:
        return jsonify({"success": False, "message": "Version not found."}), 404

    write_train_history(history)
    return jsonify({"success": True, "message": "Activated", "version": version})

@app.route("/api/admin/delete-version", methods=["POST"])
def delete_version():
    data = request.get_json(force=True)
    model_key = data.get("model")
    version = data.get("version")

    if not model_key or not version:
        return jsonify({"success": False, "message": "Model and version required."}), 400

    history = read_train_history()
    removed = None
    new_history = []
    for entry in history:
        if entry.get("model") == model_key and entry.get("version") == version:
            removed = entry
            continue
        new_history.append(entry)

    if not removed:
        return jsonify({"success": False, "message": "Version not found."}), 404

    folder_to_remove = os.path.join(UPLOADS_DIR, model_key, version)
    try:
        if os.path.exists(folder_to_remove):
            shutil.rmtree(folder_to_remove)
    except Exception as e:
        print("Failed to remove uploaded files:", e)

    if removed.get("active", False):
        promoted = None
        for entry in new_history:
            if entry.get("model") == model_key:
                promoted = entry
                break
        if promoted:
            promoted["active"] = True

    write_train_history(new_history)
    resp = {"success": True, "message": "Deleted", "deleted": removed}
    return jsonify(resp)

@app.route("/api/admin/train/info", methods=["GET"])
def get_training_info():
    model = request.args.get("model", "ollama")
    history = read_train_history()
    for h in history:
        if h.get("model") == model:
            return jsonify(h)
    return jsonify({"trained": False})

@app.route("/api/admin/train/history", methods=["GET"])
def train_history():
    return jsonify({"versions": read_train_history()})

@app.route("/api/admin/check", methods=["GET"])
def admin_check():
    return jsonify({"logged_in": True})

@app.route("/api/admin/login", methods=["POST"])
def admin_login():
    data = request.get_json(force=True)
    username = data.get("username", "").strip()
    password = data.get("password", "").strip()

    ADMIN_USER = os.getenv("ADMIN_USER", "admin")
    ADMIN_PASS = os.getenv("ADMIN_PASS", "msme@123")

    if username == ADMIN_USER and password == ADMIN_PASS:
        return jsonify({"success": True, "message": "Login successful"})
    return jsonify({"success": False, "message": "Invalid username or password"}), 401

@app.route("/")
def serve_frontend():
    if os.path.exists(app.static_folder):
        return send_from_directory(app.static_folder, "index.html")
    return "Chat backend running."

# ----------------- Run -----------------
if __name__ == "__main__":
    print("Starting RAG backend (Ollama) with gemma2 and phi3 models...")
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 5000)), debug=os.getenv("FLASK_DEBUG", "True") == "True")
