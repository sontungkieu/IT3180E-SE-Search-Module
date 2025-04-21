import fitz  # PyMuPDF
import json
import os
import re
from typing import Dict, List, Any, Tuple
from sentence_transformers import SentenceTransformer

# Load a pre-trained embedding model once
embedder = SentenceTransformer('all-MiniLM-L6-v2')

def extract_text_from_pdf(pdf_path: str) -> List[Tuple[str, int]]:
    """Extract text from PDF with page numbers"""
    doc = fitz.open(pdf_path)
    text_with_pages = []
    
    for page_num in range(len(doc)):
        page = doc[page_num]
        text = page.get_text("text").strip()
        if text:
            text_with_pages.append((text, page_num + 1))  # (text, page number starting from 1)
    
    doc.close()
    return text_with_pages

def split_into_chunks(text_with_pages: List[Tuple[str, int]], chunk_size: int = 250) -> List[Dict[str, Any]]:
    """Split text into chunks of approximately 250 words with page metadata"""
    chunks = []
    current_chunk = []
    word_count = 0
    current_page = 1

    all_words = []
    for text, page in text_with_pages:
        words = text.split()
        all_words.extend([(word, page) for word in words])

    for word, page in all_words:
        current_chunk.append(word)
        word_count += 1
        current_page = page

        if word_count >= chunk_size:
            chunk_text = " ".join(current_chunk)
            chunks.append({
                "text": chunk_text,
                "timestamp": f"page_{current_page}"
            })
            current_chunk = []
            word_count = 0

    if current_chunk:
        chunk_text = " ".join(current_chunk)
        chunks.append({
            "text": chunk_text,
            "timestamp": f"page_{current_page}"
        })

    return chunks

def sanitize_filename(name: str) -> str:
    name = os.path.splitext(os.path.basename(name))[0]
    safe_name = re.sub(r"[^\w\s-]", "", name).strip().replace(" ", "_")
    return safe_name

def create_json_file(pdf_path: str, output_dir: str = "./json_output") -> str:
    """Create a JSON file from PDF content with embeddings in YouTube-style format"""
    os.makedirs(output_dir, exist_ok=True)

    # Extract text and chunk it
    text_with_pages = extract_text_from_pdf(pdf_path)
    extracted_text = " ".join(text for text, _ in text_with_pages)
    chunks = split_into_chunks(text_with_pages)

    # Generate embeddings
    chunk_texts = [chunk["text"] for chunk in chunks]
    embeddings = embedder.encode(chunk_texts, convert_to_tensor=False).tolist()

    for chunk, embedding in zip(chunks, embeddings):
        chunk["embedding"] = embedding

    # Build final JSON structure (no language_used key)
    json_data = {
        "type": "pdf",
        "scope": sanitize_filename(pdf_path),
        "original_data": pdf_path,
        "extracted_text": extracted_text,
        "chunks": chunks
    }

    # Save file using YouTube-style title
    safe_title = sanitize_filename(pdf_path)
    output_path = os.path.join(output_dir, f"{safe_title}.json")

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(json_data, f, indent=4, ensure_ascii=False)

    print(f"JSON file created at: {output_path}")
    return output_path


def main():
    pdf_path = "Computational Intelligence and Neuroscience - 2018 - Voulodimos - Deep Learning for Computer Vision A Brief Review.pdf"
    try:
        json_file = create_json_file(pdf_path)
        print(f"Generated JSON file: {json_file}")
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    main()
