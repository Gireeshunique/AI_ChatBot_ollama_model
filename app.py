import os
import json
import time
import sys
from flask import Flask, request, jsonify, send_from_directory, session
from flask_cors import CORS
from deep_translator import GoogleTranslator
from PyPDF2 import PdfReader
import whisper
import requests
import threading
from dotenv import load_dotenv

# ----------------- Environment Setup -----------------
load_dotenv()
sys.stdout.reconfigure(encoding="utf-8")
print(">>> USING PYTHON FROM:", sys.executable)

# ----------------- Config -----------------
DATA_DIR = "data"
os.makedirs(DATA_DIR, exist_ok=True)

MODEL_MAP = {
    "llama": "llama3.2",
    "phi": "phi3",
    "mistral": "mistral"
}

# ----------------- Flask Setup -----------------
app = Flask(__name__, static_folder="../frontend/build", static_url_path="/")
app.secret_key = "super_secret_key_change_this"
CORS(app, supports_credentials=True)

# ----------------- Whisper Loading -----------------
whisper_model = None
def load_whisper():
    global whisper_model
    print("🎙️ Loading Whisper model...")
    whisper_model = whisper.load_model("small", device="cpu")
    print("✅ Whisper loaded successfully!")

threading.Thread(target=load_whisper).start()

# ----------------- Translation -----------------
def translate_text(text, target_lang):
    try:
        return GoogleTranslator(source="auto", target=target_lang).translate(text)
    except:
        return text


# ----------------- OLLAMA CHAT (FULLY FIXED) -----------------
def ollama_chat_response(prompt, lang="auto", selected_model="llama"):
    try:
        model_name = MODEL_MAP.get(selected_model, "llama3.2")

        # System instruction
        if lang == "te":
            system = "Reply ONLY in Telugu using natural friendly language."
        elif lang == "en":
            system = "Reply ONLY in English, very clearly."
        else:
            system = "Detect user's language and reply in that language."

        final_prompt = f"{system}\n\n{prompt}"

        payload = {
            "model": model_name,
            "prompt": final_prompt,
            "stream": False    # ❗ REQUIRED TO FIX EMPTY RESPONSE
        }

        response = requests.post(
            "http://localhost:11434/api/generate",
            json=payload,
            timeout=60
        )

        # Debug output to identify any error
        print("\n🔍 RAW OLLAMA RESPONSE:", response.text, "\n")

        # Parse JSON
        data = response.json()

        reply = data.get("response", "")

        if not reply.strip():
            return "⚠️ I couldn't generate a reply. Please try again."

        return reply.strip()

    except Exception as e:
        print("❌ OLLAMA ERROR:", e)
        return "⚠️ Ollama model error."


# ----------------- Helpers -----------------
def get_model_paths(model_key):
    base = os.path.join(DATA_DIR, model_key)
    os.makedirs(base, exist_ok=True)

    return {
        "dir": base,
        "corpus": os.path.join(base, "pdf_corpus.txt"),
        "info": os.path.join(base, "train_info.json")
    }


def log_chat(model, user, question, answer):
    log_path = os.path.join(DATA_DIR, f"chat_logs_{model}.json")

    logs = []
    if os.path.exists(log_path):
        try:
            with open(log_path, "r", encoding="utf-8") as f:
                logs = json.load(f)
        except:
            logs = []

    logs.append({
        "user": user,
        "question": question,
        "answer": answer,
        "ts": time.time()
    })

    with open(log_path, "w", encoding="utf-8") as f:
        json.dump(logs, f, ensure_ascii=False, indent=2)


# ----------------- ROUTES -----------------

@app.route("/")
def serve():
    return send_from_directory(app.static_folder, "index.html")


# ---------- CHAT ----------
@app.route("/api/chat", methods=["POST"])
def chat():
    data = request.get_json()
    message = data.get("message", "").strip()
    lang = data.get("lang", "auto")
    model_key = data.get("model", "llama")

    paths = get_model_paths(model_key)

    if not message:
        return jsonify({"reply": "⚠️ Enter a message."})

    # Translate Telugu → English for model input
    query = message if lang != "te" else translate_text(message, "en")

    # Load corpus context
    context = ""
    if os.path.exists(paths["corpus"]):
        with open(paths["corpus"], "r", encoding="utf-8") as f:
            context = f.read()[:5000]

    prompt = f"Use this context if useful:\n{context}\n\nUser question:\n{query}"

    reply = ollama_chat_response(prompt, lang, model_key)

    log_chat(model_key, "user", message, reply)

    return jsonify({"reply": reply})


# ---------- VOICE ----------
@app.route("/api/transcribe", methods=["POST"])
def transcribe_audio():
    global whisper_model

    if whisper_model is None:
        return jsonify({"error": "Whisper is loading..."}), 503

    if "file" not in request.files:
        return jsonify({"error": "No audio uploaded"}), 400

    file = request.files["file"]
    model_key = request.form.get("model", "llama")
    lang = request.form.get("lang", "auto")

    temp = "temp.wav"
    file.save(temp)

    result = whisper_model.transcribe(temp, language="te" if lang == "te" else None)
    text = result.get("text", "").strip()

    paths = get_model_paths(model_key)

    context = ""
    if os.path.exists(paths["corpus"]):
        with open(paths["corpus"], "r") as f:
            context = f.read()[:5000]

    query = text if lang != "te" else translate_text(text, "en")
    prompt = f"Use this context if useful:\n{context}\n\nUser question:\n{query}"

    reply = ollama_chat_response(prompt, lang, model_key)

    os.remove(temp)
    return jsonify({"text": text, "reply": reply})


# ---------- ADMIN LOGIN ----------
@app.route("/api/admin/login", methods=["POST"])
def admin_login():
    data = request.get_json()
    if data.get("username") == "admin" and data.get("password") == "msme@123":
        session["logged_in"] = True
        return jsonify({"success": True})
    return jsonify({"success": False}), 401


@app.route("/api/admin/check")
def admin_check():
    return jsonify({"logged_in": session.get("logged_in", False)})


# ---------- TRAIN ----------
@app.route("/api/admin/train", methods=["POST"])
def admin_train():
    model_key = request.form.get("model_key", "llama")
    paths = get_model_paths(model_key)

    files = request.files.getlist("files")
    if not files:
        return jsonify({"message": "No PDF uploaded"}), 400

    pdf_texts = []
    filenames = []

    for file in files:
        save_path = os.path.join(paths["dir"], file.filename)
        file.save(save_path)
        filenames.append(file.filename)

        try:
            reader = PdfReader(save_path)
            text = "".join(page.extract_text() or "" for page in reader.pages)
            pdf_texts.append(text)
        except:
            pass

    with open(paths["corpus"], "w", encoding="utf-8") as f:
        f.write("\n\n".join(pdf_texts))

    info = {
        "trained": True,
        "model": MODEL_MAP[model_key],
        "files": filenames,
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
    }

    with open(paths["info"], "w", encoding="utf-8") as f:
        json.dump(info, f, indent=2)

    return jsonify({"message": f"{MODEL_MAP[model_key]} trained successfully!"})


# ---------- GET TRAIN INFO ----------
@app.route("/api/admin/train/info")
def get_train_info():
    model_key = request.args.get("model")
    if not model_key:
        return jsonify({"trained": False})

    paths = get_model_paths(model_key)

    if not os.path.exists(paths["info"]):
        return jsonify({"trained": False})

    with open(paths["info"], "r", encoding="utf-8") as f:
        return jsonify(json.load(f))


# ---------- DELETE MODEL DATA ----------
@app.route("/api/admin/train/delete", methods=["POST"])
def delete_model():
    model_key = request.args.get("model")
    paths = get_model_paths(model_key)

    try:
        if os.path.exists(paths["dir"]):
            for f in os.listdir(paths["dir"]):
                os.remove(os.path.join(paths["dir"], f))
        return jsonify({"success": True})
    except:
        return jsonify({"success": False}), 500


# ----------------- RUN -----------------
if __name__ == "__main__":
    print("🚀 Backend running with multi-model Ollama support")
    app.run(host="0.0.0.0", port=5000, debug=True)
