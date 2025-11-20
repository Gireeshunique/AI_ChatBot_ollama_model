# app.py — Full backend (Chat + Whisper + Ollama + Admin version management)
import os
import json
import time
import sys
import threading
from flask import Flask, request, jsonify, send_from_directory, session
from flask_cors import CORS
from werkzeug.utils import secure_filename
from PyPDF2 import PdfReader
import whisper
import requests
from deep_translator import GoogleTranslator
from dotenv import load_dotenv

# ----------------------------
# Environment & prints
# ----------------------------
load_dotenv()
sys.stdout.reconfigure(encoding="utf-8")
print(">>> USING PYTHON FROM:", sys.executable)

# ----------------------------
# Config / Paths
# ----------------------------
BASE_DIR = os.getcwd()
DATA_DIR = os.path.join(BASE_DIR, "data")
PDF_STORE = os.path.join(DATA_DIR, "pdfs")
VERSIONS_PATH = os.path.join(DATA_DIR, "versions.json")
CHAT_LOG = os.path.join(DATA_DIR, "chat_logs.json")

os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(PDF_STORE, exist_ok=True)

# Ollama / model config
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434/api/generate")
MODEL_NAME = os.getenv("DEFAULT_MODEL", "gemma2:2b")

# Admin debug + delete behavior
DEBUG_ADMIN = True
DELETE_PDFS_ON_DELETE = False  # set True to remove PDF files when a version is deleted

# ----------------------------
# Flask app
# ----------------------------
app = Flask(__name__, static_folder="../frontend/build", static_url_path="/")
app.secret_key = os.getenv("FLASK_SECRET", "super_secret_key_change_this")
CORS(app, supports_credentials=True)

# ----------------------------
# Whisper model (load in background)
# ----------------------------
whisper_model = None

def load_whisper_model():
    global whisper_model
    try:
        print("🎙️ Loading Whisper model (small)...")
        whisper_model = whisper.load_model("small", device="cpu")
        print("✅ Whisper loaded.")
    except Exception as e:
        print("❌ Whisper load error:", e)
        whisper_model = None

threading.Thread(target=load_whisper_model).start()

# ----------------------------
# Utils: debug log
# ----------------------------
def dlog(*args, **kwargs):
    if DEBUG_ADMIN:
        print("[DEBUG]", *args, **kwargs)

# ----------------------------
# Utils: versions storage
# versions.json structure: list of {model, version, description, timestamp, files[], active}
# ----------------------------
def load_versions():
    if not os.path.exists(VERSIONS_PATH):
        return []
    try:
        with open(VERSIONS_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        dlog("load_versions error:", e)
        return []

def save_versions(versions):
    try:
        with open(VERSIONS_PATH, "w", encoding="utf-8") as f:
            json.dump(versions, f, indent=2, ensure_ascii=False)
    except Exception as e:
        dlog("save_versions error:", e)

# ----------------------------
# Utils: extract text from PDF
# ----------------------------
def extract_pdf_text(path):
    text = ""
    try:
        reader = PdfReader(path)
        for page in reader.pages:
            text += page.extract_text() or ""
    except Exception as e:
        dlog("PDF extract error:", path, e)
    return text

# ----------------------------
# Utils: Ollama call
# ----------------------------
def ollama_generate(prompt, model=MODEL_NAME, timeout=60):
    try:
        payload = {"model": model, "prompt": prompt, "stream": False}
        res = requests.post(OLLAMA_URL, json=payload, timeout=timeout)
        res.raise_for_status()
        data = res.json()
        # Ollama response shape may differ; try common keys:
        if isinstance(data, dict):
            # try a few keys
            for k in ("response", "text", "content", "output"):
                if k in data:
                    return data[k]
            # if nested
            if "choices" in data and isinstance(data["choices"], list) and data["choices"]:
                ch = data["choices"][0]
                return ch.get("message", ch.get("text", "")) if isinstance(ch, dict) else str(ch)
        return str(data)
    except Exception as e:
        dlog("Ollama generate error:", e)
        return "⚠️ Ollama not responding."

# ----------------------------
# Chat logging
# ----------------------------
def log_chat(user, question, answer, model=MODEL_NAME, feedback=None):
    logs = []
    if os.path.exists(CHAT_LOG):
        try:
            with open(CHAT_LOG, "r", encoding="utf-8") as f:
                logs = json.load(f)
        except Exception:
            logs = []
    entry = {"user": user, "question": question, "answer": answer, "model": model, "feedback": feedback, "ts": int(time.time())}
    logs.append(entry)
    try:
        with open(CHAT_LOG, "w", encoding="utf-8") as f:
            json.dump(logs, f, ensure_ascii=False, indent=2)
    except Exception as e:
        dlog("log_chat error:", e)

# ----------------------------
# Translation helper
# ----------------------------
def translate_text(text, target_lang):
    if not text or not text.strip():
        return text
    try:
        return GoogleTranslator(source="auto", target=target_lang).translate(text)
    except Exception as e:
        dlog("translate error:", e)
        return text

# ----------------------------
# Serve frontend
# ----------------------------
@app.route("/")
def serve_frontend():
    return send_from_directory(app.static_folder, "index.html")

# ----------------------------
# Chat endpoint — uses active version context if available
# ----------------------------
@app.route("/api/chat", methods=["POST"])
def api_chat():
    data = request.get_json(force=True)
    message = data.get("message", "").strip()
    lang = data.get("lang", "auto")
    model = data.get("model", MODEL_NAME)

    if not message:
        return jsonify({"reply": "⚠️ Please enter a message."}), 400

    # Load active version's context for the requested model (if any)
    versions = load_versions()
    active = None
    for v in versions:
        # match model key by prefix (e.g., "gemma2" in "gemma2:2b") or exact
        if (v.get("model") and v.get("model") in model) or (v.get("model") == model):
            if v.get("active"):
                active = v
                break

    context = ""
    if active:
        ctx_path = os.path.join(PDF_STORE, active["model"], active["version"], "context.txt")
        if os.path.exists(ctx_path):
            try:
                with open(ctx_path, "r", encoding="utf-8") as f:
                    context = f.read()[:4000]
            except Exception as e:
                dlog("read context error:", e)

    # translate if telugu requested
    query = message
    if lang == "te":
        query = translate_text(message, "en")

    prompt = f"Use this context if relevant:\n{context}\n\nUser question:\n{query}"
    reply = ollama_generate(prompt, model=model)

    if lang == "te":
        # translate back to Telugu if needed (optional, here assume Ollama responded in english)
        try:
            reply = translate_text(reply, "te")
        except Exception:
            pass

    log_chat("user", message, reply, model=model)
    return jsonify({"reply": reply, "ts": int(time.time())})

# ----------------------------
# Transcription endpoint
# ----------------------------
@app.route("/api/transcribe", methods=["POST"])
def api_transcribe():
    global whisper_model
    if whisper_model is None:
        return jsonify({"error": "⚠️ Whisper model is loading. Try again shortly."}), 503

    if "file" not in request.files:
        return jsonify({"error": "❌ No audio file uploaded."}), 400

    file = request.files["file"]
    lang = request.form.get("lang", "auto")
    temp_path = os.path.join(DATA_DIR, f"temp_{int(time.time())}.wav")
    file.save(temp_path)

    try:
        result = whisper_model.transcribe(temp_path, language="te" if lang == "te" else None)
        text = result.get("text", "").strip()
        if not text:
            return jsonify({"text": "", "reply": "⚠️ Couldn't understand the audio clearly."})
        query = text if lang != "te" else translate_text(text, "en")
        # Get context from active version for default model
        versions = load_versions()
        active = next((v for v in versions if v.get("model") == "gemma2" and v.get("active")), None)
        context = ""
        if active:
            ctx_path = os.path.join(PDF_STORE, active["model"], active["version"], "context.txt")
            if os.path.exists(ctx_path):
                with open(ctx_path, "r", encoding="utf-8") as f:
                    context = f.read()[:4000]
        prompt = f"Use this context if relevant:\n{context}\n\nUser question:\n{query}"
        reply = ollama_generate(prompt, model=MODEL_NAME)
        log_chat("voice", text, reply, model=MODEL_NAME)
        return jsonify({"text": text, "reply": reply})
    except Exception as e:
        dlog("transcribe error:", e)
        return jsonify({"error": str(e)}), 500
    finally:
        try:
            if os.path.exists(temp_path):
                os.remove(temp_path)
        except:
            pass

# ----------------------------
# Admin: login / check / logout
# ----------------------------
@app.route("/api/admin/login", methods=["POST"])
def admin_login():
    data = request.get_json(silent=True) or {}
    username = data.get("username")
    password = data.get("password")
    ADMIN_USERNAME = os.getenv("ADMIN_USERNAME", "admin")
    ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "msme@123")
    if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
        session["logged_in"] = True
        dlog("Admin logged in")
        return jsonify({"success": True, "message": "Login successful"})
    return jsonify({"success": False, "message": "Invalid credentials"}), 401

@app.route("/api/admin/check", methods=["GET"])
def admin_check():
    return jsonify({"logged_in": bool(session.get("logged_in", False))})

@app.route("/api/admin/logout", methods=["POST"])
def admin_logout():
    session.clear()
    dlog("Admin logged out")
    return jsonify({"success": True, "message": "Logged out"})

# ----------------------------
# Admin: Train (upload PDFs, create version)
# POST /api/admin/train
# form fields: model_key, version, description (optional), files[]
# ----------------------------
@app.route("/api/admin/train", methods=["POST"])
def admin_train():
    if not session.get("logged_in"):
        return jsonify({"message": "Unauthorized"}), 401

    model_key = request.form.get("model_key")
    version = request.form.get("version")
    description = request.form.get("description", "")
    if not model_key or not version:
        return jsonify({"message": "Missing model or version"}), 400

    # Save PDFs under data/pdfs/<model>/<version>/
    model_version_dir = os.path.join(PDF_STORE, model_key, version)
    os.makedirs(model_version_dir, exist_ok=True)

    files = request.files.getlist("files")
    if not files:
        return jsonify({"message": "No PDF files uploaded."}), 400

    saved_files = []
    combined_text = ""
    for f in files:
        filename = secure_filename(f.filename)
        save_path = os.path.join(model_version_dir, filename)
        f.save(save_path)
        saved_files.append(filename)
        # extract text
        try:
            text = extract_pdf_text(save_path)
            combined_text += text + "\n\n"
        except Exception as e:
            dlog("pdf extract error:", e)

    # Save context.txt for RAG usage
    ctx_path = os.path.join(model_version_dir, "context.txt")
    try:
        with open(ctx_path, "w", encoding="utf-8") as cf:
            cf.write(combined_text)
    except Exception as e:
        dlog("write context error:", e)

    # Update versions.json
    versions = load_versions()
    # deactivate existing actives for this model
    for v in versions:
        if v.get("model") == model_key:
            v["active"] = False

    new_entry = {
        "model": model_key,
        "version": version,
        "description": description,
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "files": saved_files,
        "active": True
    }
    versions.append(new_entry)
    save_versions(versions)

    dlog("Trained new version:", new_entry)
    return jsonify({"success": True, "message": f"Trained {model_key}:{version}."})

# ----------------------------
# Admin: get active version info for a model
# GET /api/admin/train/info?model=<model_key>
# ----------------------------
@app.route("/api/admin/train/info", methods=["GET"])
def admin_train_info():
    model_key = request.args.get("model")
    versions = load_versions()
    info = next((v for v in versions if v.get("model") == model_key and v.get("active")), None)
    if not info:
        return jsonify({"trained": False})
    return jsonify(info)

# ----------------------------
# Admin: version history
# GET /api/admin/train/history
# ----------------------------
@app.route("/api/admin/train/history", methods=["GET"])
def admin_train_history():
    versions = load_versions()
    # return newest first
    versions_sorted = sorted(versions, key=lambda x: x.get("timestamp", ""), reverse=True)
    return jsonify({"versions": versions_sorted})

# ----------------------------
# Admin: activate version
# POST /api/admin/activate  {model, version}
# ----------------------------
@app.route("/api/admin/activate", methods=["POST"])
def admin_activate():
    if not session.get("logged_in"):
        return jsonify({"message": "Unauthorized"}), 401

    data = request.get_json(silent=True) or {}
    model_key = data.get("model")
    version = data.get("version")
    if not model_key or not version:
        return jsonify({"success": False, "message": "model/version missing"}), 400

    versions = load_versions()
    found = False
    for v in versions:
        if v.get("model") == model_key:
            v["active"] = (v.get("version") == version)
        if v.get("model") == model_key and v.get("version") == version:
            found = True

    if not found:
        return jsonify({"success": False, "message": "Version not found"}), 404

    save_versions(versions)
    dlog("Activated version", model_key, version)
    return jsonify({"success": True})

# ----------------------------
# Admin: delete a version (history or active)
# POST /api/admin/delete-version  {model, version}
# ----------------------------
@app.route("/api/admin/delete-version", methods=["POST"])
def admin_delete_version():
    if not session.get("logged_in"):
        return jsonify({"message": "Unauthorized"}), 401

    data = request.get_json(silent=True) or {}
    model_key = data.get("model")
    version = data.get("version")
    if not model_key or not version:
        return jsonify({"success": False, "message": "model/version missing"}), 400

    versions = load_versions()
    entry = next((v for v in versions if v.get("model") == model_key and v.get("version") == version), None)
    if not entry:
        return jsonify({"success": False, "message": "Version not found"}), 404

    # remove context file
    ctx_path = os.path.join(PDF_STORE, model_key, version, "context.txt")
    try:
        if os.path.exists(ctx_path):
            os.remove(ctx_path)
    except Exception as e:
        dlog("remove context error:", e)

    # optionally delete PDFs
    if DELETE_PDFS_ON_DELETE:
        try:
            folder = os.path.join(PDF_STORE, model_key, version)
            if os.path.exists(folder):
                # remove all files and the folder
                for fn in os.listdir(folder):
                    p = os.path.join(folder, fn)
                    try:
                        os.remove(p)
                    except:
                        pass
                try:
                    os.rmdir(folder)
                except:
                    pass
        except Exception as e:
            dlog("delete pdfs error:", e)

    # remove entry from versions list
    versions = [v for v in versions if not (v.get("model") == model_key and v.get("version") == version)]
    save_versions(versions)
    dlog("Deleted version", model_key, version)
    return jsonify({"success": True})

# ----------------------------
# Admin: delete active (convenience)
# POST /api/admin/delete-active {model, version}
# (same behavior as delete-version; requires version param to avoid `undefined`)
# ----------------------------
@app.route("/api/admin/delete-active", methods=["POST"])
def admin_delete_active():
    if not session.get("logged_in"):
        return jsonify({"message": "Unauthorized"}), 401

    data = request.get_json(silent=True) or {}
    model_key = data.get("model")
    version = data.get("version")
    if not model_key or not version:
        return jsonify({"success": False, "message": "model/version missing"}), 400

    # delegate to delete-version handler logic by duplicating behavior
    versions = load_versions()
    entry = next((v for v in versions if v.get("model") == model_key and v.get("version") == version), None)
    if not entry:
        return jsonify({"success": False, "message": "Version not found"}), 404

    ctx_path = os.path.join(PDF_STORE, model_key, version, "context.txt")
    try:
        if os.path.exists(ctx_path):
            os.remove(ctx_path)
    except Exception as e:
        dlog("remove context error:", e)

    if DELETE_PDFS_ON_DELETE:
        try:
            folder = os.path.join(PDF_STORE, model_key, version)
            if os.path.exists(folder):
                for fn in os.listdir(folder):
                    p = os.path.join(folder, fn)
                    try:
                        os.remove(p)
                    except:
                        pass
                try:
                    os.rmdir(folder)
                except:
                    pass
        except Exception as e:
            dlog("delete pdfs error:", e)

    versions = [v for v in versions if not (v.get("model") == model_key and v.get("version") == version)]
    save_versions(versions)
    dlog("Deleted active version", model_key, version)
    return jsonify({"success": True})

# ----------------------------
# Admin: get all chat logs (protected)
# GET /api/admin/chat/logs
# ----------------------------
@app.route("/api/admin/chat/logs", methods=["GET"])
def admin_get_logs():
    if not session.get("logged_in"):
        return jsonify({"error": "Unauthorized"}), 401

    if not os.path.exists(CHAT_LOG):
        return jsonify({"logs": []})
    try:
        with open(CHAT_LOG, "r", encoding="utf-8") as f:
            logs = json.load(f)
    except Exception:
        logs = []
    return jsonify({"logs": logs})

# ----------------------------
# Admin: get log details
# GET /api/admin/chat/logs/<ts>
# ----------------------------
@app.route("/api/admin/chat/logs/<ts>", methods=["GET"])
def admin_get_log_details(ts):
    if not session.get("logged_in"):
        return jsonify({"error": "Unauthorized"}), 401
    if not os.path.exists(CHAT_LOG):
        return jsonify({"error": "No logs found"}), 404
    try:
        with open(CHAT_LOG, "r", encoding="utf-8") as f:
            logs = json.load(f)
    except Exception:
        logs = []
    for entry in logs:
        if str(entry.get("ts")) == str(ts):
            return jsonify({"log": entry})
    return jsonify({"error": "Log not found"}), 404

# ----------------------------
# Chat feedback endpoint
# POST /api/chat/feedback {ts, feedback}
# ----------------------------
# ----------------------------------------
# Chat Feedback API
# POST /api/chat/feedback
# Body: { "ts": 1234567890, "feedback": "positive" | "negative" | "none" }
# ----------------------------------------
@app.route("/api/chat/feedback", methods=["POST"])
def chat_feedback():
    data = request.get_json(silent=True) or {}

    ts = data.get("ts")
    feedback = data.get("feedback")  # "positive", "negative", "none"

    if ts is None:
        return jsonify({"error": "ts missing"}), 400

    # Ensure log file exists
    if not os.path.exists(CHAT_LOG):
        # Create empty log file automatically
        with open(CHAT_LOG, "w", encoding="utf-8") as f:
            json.dump([], f, indent=2, ensure_ascii=False)

    # Load logs
    try:
        with open(CHAT_LOG, "r", encoding="utf-8") as f:
            logs = json.load(f)
    except Exception as e:
        print("❌ Failed to read chat logs:", e)
        return jsonify({"error": "Failed to read chat logs"}), 500

    updated = False

    # Update the right log entry
    for entry in logs:
        if str(entry.get("ts")) == str(ts):
            # Convert "none" → remove feedback
            entry["feedback"] = None if feedback == "none" else feedback
            updated = True
            break

    if not updated:
        return jsonify({"error": "Timestamp not found"}), 404

    # Save updates back to file
    try:
        with open(CHAT_LOG, "w", encoding="utf-8") as f:
            json.dump(logs, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print("❌ Failed to save feedback:", e)
        return jsonify({"error": "Failed to save"}), 500

    return jsonify({"success": True})


# ------------------------------------------------
# Ensure JSON storage files exist
# ------------------------------------------------

# versions.json (model training versions)
if not os.path.exists(VERSIONS_PATH):
    with open(VERSIONS_PATH, "w", encoding="utf-8") as f:
        json.dump([], f, indent=2, ensure_ascii=False)

# chat_logs.json (chat history)
if not os.path.exists(CHAT_LOG):
    with open(CHAT_LOG, "w", encoding="utf-8") as f:
        json.dump([], f, indent=2, ensure_ascii=False)

# Ensure PDF directory structure exists
if not os.path.exists(PDF_STORE):
    os.makedirs(PDF_STORE, exist_ok=True)


# ----------------------------
# Health / ping
# ----------------------------
@app.route("/ping")
def ping():
    return "pong"

# ----------------------------
# Run
# ----------------------------
if __name__ == "__main__":
    print(f"🚀 Backend starting — Ollama model: {MODEL_NAME}")
    app.run(host="0.0.0.0", port=5000, debug=True)
