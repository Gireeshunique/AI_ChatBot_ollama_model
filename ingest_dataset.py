import os
import zipfile
import json
import re
import warnings
import logging
from concurrent.futures import ThreadPoolExecutor
import pdfplumber
import nltk
from nltk.tokenize import sent_tokenize

# ----------------- Setup -----------------
warnings.filterwarnings("ignore", category=UserWarning, module="pdfminer")
logging.getLogger("pdfminer").setLevel(logging.ERROR)

nltk.download("punkt", quiet=True)
nltk.download("punkt_tab", quiet=True)

# ----------------- Config -----------------
ZIP_PATH = r"C:\Users\COMPUTER CENTER\Desktop\chatbot\backend\AI-Powered Chatbot-20251015T144511Z-1-001.zip"

DATA_DIR = "data"
EXTRACTION_DIR = os.path.join(DATA_DIR, "extracted")

MODEL_KEYS = ["llama", "phi", "mistral"]

CHUNK_SIZE = 2000
CHUNK_OVERLAP = 200
MAX_THREADS = 6

# Prepare model folders
for key in MODEL_KEYS:
    os.makedirs(os.path.join(DATA_DIR, key), exist_ok=True)

os.makedirs(EXTRACTION_DIR, exist_ok=True)

# ----------------- Helper Functions -----------------
def extract_zip(zip_path, out_dir):
    if not os.path.exists(zip_path):
        raise FileNotFoundError(f"❌ ZIP not found: {zip_path}")
    with zipfile.ZipFile(zip_path, "r") as z:
        z.extractall(out_dir)
    print(f"✅ Extracted → {out_dir}")


def read_pdf(path):
    try:
        with pdfplumber.open(path) as pdf:
            return "\n".join(page.extract_text() or "" for page in pdf.pages)
    except Exception as e:
        print(f"⚠️ Failed to read PDF {path}: {e}")
        return ""


def clean_text(text):
    text = text.encode("utf-8", "ignore").decode("utf-8", "ignore")
    text = re.sub(r"\s+", " ", text)
    text = re.sub(r"Page \d+ of \d+", "", text)
    text = re.sub(r"[^A-Za-z0-9.,;:?!@()\-\n ]", " ", text)
    text = re.sub(r"•|▪|●|-{2,}", "-", text)
    return text.strip()


def chunk_text(text):
    if not text:
        return []
    sentences = sent_tokenize(text)
    chunks, current = [], ""

    for s in sentences:
        if len(current) + len(s) <= CHUNK_SIZE:
            current += " " + s
        else:
            chunks.append(current.strip())
            current = s
    if current:
        chunks.append(current.strip())

    final_chunks = []
    for i in range(len(chunks)):
        overlap = " ".join(chunks[max(0, i-1): i+1])
        final_chunks.append(overlap.strip())

    return final_chunks


def process_file(path):
    if not path.lower().endswith(".pdf"):
        return [], []

    text = read_pdf(path)
    if not text.strip():
        return [], []

    cleaned = clean_text(text)
    chunks = chunk_text(cleaned)
    meta = [{"source": os.path.basename(path), "text": c} for c in chunks]

    return chunks, meta


# ----------------- Main -----------------
def main():
    print("🚀 Starting multi-model dataset ingestion...\n")

    extract_zip(ZIP_PATH, EXTRACTION_DIR)

    # Collect PDFs
    files = [
        os.path.join(root, f)
        for root, _, fs in os.walk(EXTRACTION_DIR)
        for f in fs if f.lower().endswith(".pdf")
    ]
    print(f"📄 Found {len(files)} PDFs.\n")

    all_chunks, all_meta = [], []

    # Parallel extraction
    with ThreadPoolExecutor(max_workers=MAX_THREADS) as ex:
        for chunks, meta in ex.map(process_file, files):
            if chunks:
                all_chunks.extend(chunks)
                all_meta.extend(meta)

    print(f"✅ Total prepared chunks: {len(all_chunks)}\n")

    # Corpus final output
    combined_text = "\n\n".join(all_chunks)

    # ----------------- SAVE DATA FOR EACH MODEL -----------------
    for model_key in MODEL_KEYS:

        model_dir = os.path.join(DATA_DIR, model_key)

        print(f"📦 Saving dataset for model: {model_key}")

        # Save corpus
        corpus_path = os.path.join(model_dir, "pdf_corpus.txt")
        with open(corpus_path, "w", encoding="utf-8") as f:
            f.write(combined_text)

        # Save metadata
        meta_path = os.path.join(model_dir, "metadata.json")
        with open(meta_path, "w", encoding="utf-8") as f:
            json.dump(all_meta, f, ensure_ascii=False, indent=2)

        print(f"📚 Corpus saved → {corpus_path}")
        print(f"🗂️ Metadata saved → {meta_path}\n")

    print("🎉 Ingestion complete: All 3 models are ready for training!")


# ----------------- Run -----------------
if __name__ == "__main__":
    main()
