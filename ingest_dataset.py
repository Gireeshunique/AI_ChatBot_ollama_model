# ingest_build_index.py
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
from sentence_transformers import SentenceTransformer
import numpy as np
import faiss

# ----------------- Setup -----------------
warnings.filterwarnings("ignore")
logging.getLogger("pdfminer").setLevel(logging.ERROR)
nltk.download("punkt", quiet=True)

# ----------------- Config -----------------

ZIP_PATH = os.environ.get("ZIP_PATH_OVERRIDE") or r"D:\project1\backend\AI-Powered Chatbot-20251015T144511Z-1-001.zip"
 # change to your zip path
EXTRACTION_DIR = "data/extracted"
CORPUS_PATH = "data/pdf_corpus.txt"
METADATA_PATH = "data/metadata.json"
EMBEDDINGS_PATH = "data/embeddings.npy"
INDEX_PATH = "data/faiss.index"

CHUNK_SIZE = 1000   # characters per chunk (smaller is safer on low RAM)
CHUNK_OVERLAP = 200
MAX_THREADS = 4

os.makedirs("data", exist_ok=True)
os.makedirs(EXTRACTION_DIR, exist_ok=True)

# ----------------- Helpers -----------------
def extract_zip(zip_path, out_dir):
    if not os.path.exists(zip_path):
        raise FileNotFoundError(f"ZIP not found: {zip_path}")
    with zipfile.ZipFile(zip_path, "r") as z:
        z.extractall(out_dir)
    print(f"Extracted to {out_dir}")

def read_pdf(path):
    try:
        with pdfplumber.open(path) as pdf:
            return "\n".join(page.extract_text() or "" for page in pdf.pages)
    except Exception as e:
        print(f"PDF read error {path}: {e}")
        return ""

def clean_text(text):
    text = text.encode("utf-8", "ignore").decode("utf-8", "ignore")
    text = re.sub(r"\s+", " ", text)
    text = re.sub(r"Page \d+ of \d+", "", text, flags=re.IGNORECASE)
    text = re.sub(r"[^A-Za-z0-9.,;:?!@()\-\n ]", " ", text)
    return text.strip()

def chunk_text(text):
    if not text:
        return []
    sentences = sent_tokenize(text)
    chunks = []
    cur = ""
    for s in sentences:
        if len(cur) + len(s) <= CHUNK_SIZE:
            cur += " " + s
        else:
            chunks.append(cur.strip())
            # start new chunk with overlap of last sentences (simple)
            cur = s
    if cur:
        chunks.append(cur.strip())

    # optionally add overlaps
    final = []
    for i, c in enumerate(chunks):
        start = max(0, i - 1)
        ov = " ".join(chunks[start:i+1])
        final.append(ov.strip())
    return final

def process_file(path):
    if not path.lower().endswith(".pdf"):
        return []
    text = read_pdf(path)
    if not text.strip():
        return []
    text = clean_text(text)
    return chunk_text(text)

# ----------------- Main building -----------------
def main():
    print("Starting ingestion and index build...")
    extract_zip(ZIP_PATH, EXTRACTION_DIR)

    # find pdfs
    files = [os.path.join(r, f) for r, _, fs in os.walk(EXTRACTION_DIR) for f in fs if f.lower().endswith(".pdf")]
    print(f"Found {len(files)} PDFs")

    all_chunks = []
    metadata = []

    with ThreadPoolExecutor(max_workers=MAX_THREADS) as ex:
        for i, chunks in enumerate(ex.map(process_file, files)):
            if not chunks:
                continue
            for c in chunks:
                all_chunks.append(c)
                metadata.append({"source": os.path.basename(files[i]), "text": c})

    print(f"Total chunks: {len(all_chunks)}")

    # save corpus
    with open(CORPUS_PATH, "w", encoding="utf-8") as f:
        f.write("\n\n".join(all_chunks))

    with open(METADATA_PATH, "w", encoding="utf-8") as f:
        json.dump(metadata, f, ensure_ascii=False, indent=2)

    # ----------------- Embeddings -----------------
    print("Loading embedding model (sentence-transformers/all-MiniLM-L6-v2)...")
    model = SentenceTransformer("all-MiniLM-L6-v2")  # small and fast on CPU
    batch_size = 64
    embeddings = []
    for i in range(0, len(all_chunks), batch_size):
        batch = all_chunks[i:i+batch_size]
        emb = model.encode(batch, show_progress_bar=False, convert_to_numpy=True)
        embeddings.append(emb)
    embeddings = np.vstack(embeddings).astype("float32")
    np.save(EMBEDDINGS_PATH, embeddings)
    print(f"Saved embeddings → {EMBEDDINGS_PATH}")

    # ----------------- FAISS index -----------------
    dim = embeddings.shape[1]
    index = faiss.IndexFlatIP(dim)  # inner product (use normalized vectors for cosine)
    faiss.normalize_L2(embeddings)
    index.add(embeddings)
    faiss.write_index(index, INDEX_PATH)
    print(f"Saved FAISS index → {INDEX_PATH}")

    print("Done. You can now run the backend server (app.py).")

if __name__ == "__main__":
    main()
