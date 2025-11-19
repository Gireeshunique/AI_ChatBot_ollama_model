# app.py
"""
Backend for Ollama (new API) + JSON chatlogs + JWT admin + optional Whisper.
Calls Ollama at /api/chat with messages format.
"""

import os
import json
import time
import tempfile
import threading
from functools import wraps
from io import StringIO
from dotenv import load_dotenv
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import requests
import jwt
from werkzeug.utils import secure_filename

# Optional whisper
try:
    import whisper
    WHISPER_AVAILABLE = True
except Exception:
    WHISPER_AVAILABLE = False

load_dotenv()

# --------------- CONFIG ---------------
JWT_SECRET = os.getenv("JWT_SECRET", "supersecretjwt")
ADMIN_USER = os.getenv("ADMIN_USER", "admin")
ADMIN_PASS = os.getenv("ADMIN_PASS", "adminpass")

OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost")
OLLAMA_PORT = os.getenv("OLLAMA_PORT", "11434")
OLLAMA_CHAT_API = f"{OLLAMA_HOST}:{OLLAMA_PORT}/api/chat"

CHATLOG_FILE = os.getenv("CHATLOG_FILE", "chatlogs.json")
WHISPER_MODEL = os.getenv("WHISPER_MODEL", "base")
FLASK_DEBUG = os.getenv("FLASK_DEBUG", "true").lower() in ("1", "true")
PORT = int(os.getenv("PORT", 5000))

# --------------- APP INIT ---------------
app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}}, supports_credentials=True)

_file_lock = threading.Lock()

# --------------- LOG FILE HELPERS ---------------
def ensure_logfile():
    if not os.path.exists(CHATLOG_FILE):
        with _file_lock:
            if not os.path.exists(CHATLOG_FILE):
                with open(CHATLOG_FILE, "w", encoding="utf-8") as f:
                    json.dump({"seq": 0, "logs": []}, f, indent=2, ensure_ascii=False)

def load_logs():
    ensure_logfile()
    with open(CHATLOG_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_logs(data):
    with _file_lock:
        tmp = tempfile.NamedTemporaryFile("w", delete=False, encoding="utf-8", suffix=".tmp")
        tmp.write(json.dumps(data, indent=2, ensure_ascii=False))
        tmp.flush()
        tmp.close()
        os.replace(tmp.name, CHATLOG_FILE)

def next_id():
    data = load_logs()
    data["seq"] = int(data.get("seq", 0)) + 1
    save_logs(data)
    return data["seq"]

def add_log(entry):
    data = load_logs()
    data.setdefault("logs", []).append(entry)
    save_logs(data)

def now_ts():
    return int(time.time())

# --------------- JWT HELPERS ---------------
def create_jwt(payload: dict):
    p = dict(payload)
    p["exp"] = now_ts() + 60 * 60 * 12  # 12 hours
    token = jwt.encode(p, JWT_SECRET, algorithm="HS256")
    return token.decode() if isinstance(token, bytes) else token

def decode_jwt(token: str):
    return jwt.decode(token, JWT_SECRET, algorithms=["HS256"])

def admin_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        auth = request.headers.get("Authorization", "")
        if not auth.startswith("Bearer "):
            return jsonify({"error": "Missing token"}), 401
        token = auth.split(" ", 1)[1]
        try:
            payload = decode_jwt(token)
            if payload.get("sub") != "admin":
                return jsonify({"error": "Forbidden"}), 403
            return fn(*args, **kwargs)
        except jwt.ExpiredSignatureError:
            return jsonify({"error": "Token expired"}), 401
        except Exception as e:
            return jsonify({"error": "Invalid token", "msg": str(e)}), 401
    return wrapper

# --------------- Ollama (new API) ---------------
def generate_reply_ollama(model: str, messages: list, timeout: int = 60):
    """
    Calls Ollama v0.4+ /api/chat endpoint.
    messages: list of {"role": "user"|"system"|"assistant", "content": "..."}
    model: e.g. "gemma2:2b" or "phi3:3.8b"
    """
    try:
        payload = {
            "model": model,
            "messages": messages,
            "stream": False
        }
        r = requests.post(OLLAMA_CHAT_API, json=payload, timeout=timeout)
        r.raise_for_status()
        data = r.json()

        # Defensive parsing for different possible shapes:
        # - {"message": {"content": "..."}} OR
        # - {"choices": [{"message": {"content": "..."}}], ...}
        if isinstance(data, dict):
            # check .message.content
            msg = data.get("message")
            if isinstance(msg, dict):
                content = msg.get("content")
                if isinstance(content, str):
                    return content

            # check .choices[0].message.content
            choices = data.get("choices")
            if isinstance(choices, list) and len(choices) > 0:
                first = choices[0]
                if isinstance(first, dict):
                    m = first.get("message") or first.get("content") or first.get("text")
                    if isinstance(m, dict):
                        c = m.get("content") or m.get("text")
                        if isinstance(c, str):
                            return c
                    if isinstance(m, str):
                        return m

            # as fallback: try 'response' or 'text'
            if "response" in data and isinstance(data["response"], str):
                return data["response"]
            if "text" in data and isinstance(data["text"], str):
                return data["text"]
        # fallback to stringifying response
        return str(data)
    except requests.exceptions.HTTPError as he:
        return f"[Ollama HTTP Error: {he} - {getattr(he.response, 'text', '')}]"
    except Exception as e:
        return f"[Ollama Error: {str(e)}]"

# --------------- ROUTES ---------------

@app.post("/api/admin/login")
def admin_login():
    body = request.json or {}
    username = (body.get("username") or "").strip()
    password = (body.get("password") or "").strip()
    if username == ADMIN_USER and password == ADMIN_PASS:
        token = create_jwt({"sub": "admin"})
        return jsonify({"token": token})
    return jsonify({"error": "Invalid credentials"}), 401

@app.post("/api/chat")
def chat():
    try:
        d = request.json or {}
        message = (d.get("message") or "").strip()
        if not message:
            return jsonify({"error": "Empty message"}), 400

        model = (d.get("model") or "gemma2:2b").strip()
        feature = (d.get("feature") or "rag").strip()
        version = (d.get("version") or "default").strip()
        user_id = (d.get("user_id") or d.get("user") or "anonymous")

        # Build messages list: include optional system message based on feature/version
        messages = []
        system_lines = []
        if feature == "rag":
            system_lines.append("You are a precise RAG assistant.")
        elif feature == "lora":
            system_lines.append("You are a LoRA fine-tuned assistant.")
        if version and version != "default":
            system_lines.append(f"[Version: {version}]")
        if system_lines:
            messages.append({"role": "system", "content": "\n".join(system_lines)})

        messages.append({"role": "user", "content": message})

        reply = generate_reply_ollama(model=model, messages=messages)

        entry = {
            "id": next_id(),
            "ts": now_ts(),
            "user_id": user_id,
            "question": message,
            "reply": reply,
            "model": model,
            "feature": feature,
            "version": version,
            "feedback": None
        }
        add_log(entry)

        return jsonify({"reply": reply, "ts": entry["ts"], "id": entry["id"]})
    except Exception as e:
        return jsonify({"error": "Server error", "msg": str(e)}), 500

@app.post("/api/transcribe")
def transcribe():
    try:
        if "file" not in request.files:
            return jsonify({"error": "No file uploaded"}), 400
        f = request.files["file"]
        filename = secure_filename(f.filename or "upload.wav")
        tmpdir = tempfile.mkdtemp(prefix="msme_trans_")
        filepath = os.path.join(tmpdir, filename)
        f.save(filepath)

        lang = request.form.get("lang") or request.form.get("language") or "en"
        model = (request.form.get("model") or "gemma2:2b").strip()
        feature = (request.form.get("feature") or "rag").strip()
        version = (request.form.get("version") or "default").strip()
        user_id = request.form.get("user_id") or "anonymous"

        text = ""
        if WHISPER_AVAILABLE:
            w = whisper.load_model(WHISPER_MODEL)
            res = w.transcribe(filepath, language=None if lang == "auto" else lang)
            text = res.get("text", "") or ""
        else:
            # no whisper available; return uploaded filename info
            text = ""

        # assemble messages
        messages = []
        system_lines = []
        if feature == "rag":
            system_lines.append("You are a precise RAG assistant.")
        elif feature == "lora":
            system_lines.append("You are a LoRA fine-tuned assistant.")
        if version and version != "default":
            system_lines.append(f"[Version: {version}]")
        if system_lines:
            messages.append({"role": "system", "content": "\n".join(system_lines)})
        messages.append({"role": "user", "content": text or "(no transcript)"} )

        reply = generate_reply_ollama(model=model, messages=messages)

        entry = {
            "id": next_id(),
            "ts": now_ts(),
            "user_id": user_id,
            "question": text,
            "reply": reply,
            "model": model,
            "feature": feature,
            "version": version,
            "feedback": None
        }
        add_log(entry)

        # cleanup
        try:
            if os.path.exists(filepath):
                os.remove(filepath)
            os.rmdir(tmpdir)
        except Exception:
            pass

        return jsonify({"text": text, "reply": reply, "ts": entry["ts"], "id": entry["id"]})
    except Exception as e:
        return jsonify({"error": "Server error", "msg": str(e)}), 500

@app.get("/api/admin/chat/logs")
@admin_required
def admin_get_logs():
    try:
        data = load_logs()
        logs = data.get("logs", [])[:]
        model_q = request.args.get("model")
        fb_q = request.args.get("feedback")
        user_q = request.args.get("user_id")

        if model_q:
            logs = [l for l in logs if (l.get("model") or "").lower() == model_q.lower()]
        if fb_q:
            if fb_q == "none":
                logs = [l for l in logs if not l.get("feedback")]
            else:
                logs = [l for l in logs if l.get("feedback") == fb_q]
        if user_q:
            logs = [l for l in logs if l.get("user_id") == user_q]

        logs = sorted(logs, key=lambda x: x.get("ts", 0), reverse=True)
        limit = int(request.args.get("limit") or 1000)
        skip = int(request.args.get("skip") or 0)
        return jsonify({"logs": logs[skip: skip + limit]})
    except Exception as e:
        return jsonify({"error": "Server error", "msg": str(e)}), 500

@app.get("/api/admin/chat/logs/<int:ts>")
@admin_required
def admin_get_single(ts: int):
    try:
        logs = load_logs().get("logs", [])
        for l in logs:
            if int(l.get("ts", 0)) == int(ts):
                return jsonify(l)
        return jsonify({"error": "Not found"}), 404
    except Exception as e:
        return jsonify({"error": "Server error", "msg": str(e)}), 500

@app.post("/api/chat/feedback")
@admin_required
def admin_feedback():
    try:
        d = request.json or {}
        ts = d.get("ts")
        fb = d.get("feedback")
        if ts is None or fb is None:
            return jsonify({"error": "Missing ts or feedback"}), 400
        data = load_logs()
        modified = False
        for entry in data.get("logs", []):
            if int(entry.get("ts", 0)) == int(ts):
                entry["feedback"] = None if fb == "none" else fb
                modified = True
                break
        if modified:
            save_logs(data)
            return jsonify({"status": "ok"})
        else:
            return jsonify({"error": "Not found"}), 404
    except Exception as e:
        return jsonify({"error": "Server error", "msg": str(e)}), 500

@app.get("/api/admin/chat/export.csv")
@admin_required
def admin_export_csv():
    try:
        data = load_logs()
        logs = sorted(data.get("logs", []), key=lambda x: x.get("ts", 0), reverse=True)
        # build CSV in memory
        si = StringIO()
        import csv
        writer = csv.writer(si)
        writer.writerow(["id", "ts", "user_id", "question", "reply", "model", "feature", "version", "feedback"])
        for l in logs:
            writer.writerow([
                l.get("id"),
                l.get("ts"),
                l.get("user_id"),
                (l.get("question") or "").replace("\n", " "),
                (l.get("reply") or "").replace("\n", " "),
                l.get("model"),
                l.get("feature"),
                l.get("version"),
                l.get("feedback")
            ])
        si.seek(0)
        tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".csv")
        tmp.write(si.getvalue().encode("utf-8"))
        tmp.close()
        return send_file(tmp.name, as_attachment=True, download_name="chatlogs.csv", mimetype="text/csv")
    except Exception as e:
        return jsonify({"error": "Server error", "msg": str(e)}), 500

@app.get("/healthz")
def healthz():
    return jsonify({"status": "ok", "time": now_ts()})

# --------------- START ---------------
if __name__ == "__main__":
    print("Starting backend (Ollama chat API) ->", OLLAMA_CHAT_API)
    app.run(host="0.0.0.0", port=PORT, debug=FLASK_DEBUG)
