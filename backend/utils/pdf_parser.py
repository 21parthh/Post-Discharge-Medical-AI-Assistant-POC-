# backend/utils/pdf_parser.py

import fitz  # PyMuPDF
import re
from tqdm import tqdm
import json
from pathlib import Path

def extract_text_from_pdf(pdf_path: str) -> str:
    """Extract raw text from PDF using PyMuPDF"""
    doc = fitz.open(pdf_path)
    text = ""
    for page in tqdm(doc, desc="Extracting PDF text"):
        text += page.get_text("text")
    doc.close()
    return text


def clean_text(text: str) -> str:
    """Basic cleanup to remove multiple spaces, headers, etc."""
    text = re.sub(r'\n+', '\n', text)               # normalize newlines
    text = re.sub(r'\s{2,}', ' ', text)             # remove extra spaces
    text = re.sub(r'Page \d+ of \d+', '', text)     # remove page numbers
    return text.strip()


def chunk_text(text: str, chunk_size: int = 800, overlap: int = 100):
    """Split text into overlapping chunks for embeddings"""
    sentences = re.split(r'(?<=[.!?]) +', text)
    chunks, current_chunk = [], ""

    for sentence in sentences:
        if len(current_chunk) + len(sentence) < chunk_size:
            current_chunk += " " + sentence
        else:
            chunks.append(current_chunk.strip())
            current_chunk = sentence

    if current_chunk:
        chunks.append(current_chunk.strip())

    # Add overlap
    final_chunks = []
    for i in range(0, len(chunks)):
        start = max(0, i - 1)
        merged = " ".join(chunks[start:i+1])
        final_chunks.append(merged)

    return final_chunks


def process_pdf(pdf_path: str, output_path: str):
    """Extract, clean, chunk, and save PDF text"""
    raw_text = extract_text_from_pdf(pdf_path)
    clean = clean_text(raw_text)
    chunks = chunk_text(clean)

    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(chunks, f, indent=2, ensure_ascii=False)

    print(f"✅ Processed {len(chunks)} chunks saved to {output_path}")


if __name__ == "__main__":
    pdf_path = "E:\\assi\\backend\data\comprehensive-clinical-nephrology.pdf"
    output_path = "backend/data/chunks/nephrology_chunks.json"
    process_pdf(pdf_path, output_path)
