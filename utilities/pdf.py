import os
import json
import re
import PyPDF2

def extract_text_from_pdf(pdf_path):
    try:
        with open(pdf_path, "rb") as file:
            reader = PyPDF2.PdfReader(file)
            full_text = ""
            for page in reader.pages:
                text = page.extract_text()
                if text:
                    full_text += text + "\n"
            return full_text.strip()
    except Exception as e:
        print(f"Error reading PDF: {e}")
        return None

def chunk_text(text, chunk_size=250):
    words = text.split()
    chunks = []
    current_chunk = []

    for word in words:
        current_chunk.append(word)
        if len(current_chunk) >= chunk_size:
            chunks.append(" ".join(current_chunk))
            current_chunk = []

    if current_chunk:
        chunks.append(" ".join(current_chunk))

    return [{"text": chunk} for chunk in chunks]

def sanitize_filename(name):
    name = name.strip().replace(" ", "_")
    return re.sub(r'[\\/*?:"<>|]', "", name)

def process_pdf(pdf_path, scope):
    text = extract_text_from_pdf(pdf_path)
    if not text:
        return None, os.path.basename(pdf_path)

    chunks = chunk_text(text)
    document_data = {
        "type": "pdf",
        "scope": scope,
        "original_data": pdf_path,
        "extracted_text": text,
        "chunks": chunks,
    }

    base_name = os.path.splitext(os.path.basename(pdf_path))[0]
    return document_data, base_name

def main():
    pdf_path = input("Enter path to PDF file: ").strip()
    scope = input("Enter scope (e.g., topic, subject, or context): ").strip()

    result, title = process_pdf(pdf_path, scope)
    if result:
        # Create output directory
        output_dir = "json_output"
        os.makedirs(output_dir, exist_ok=True)

        # Generate safe filename
        safe_title = sanitize_filename(title)
        filename = f"{safe_title}.json"
        filepath = os.path.join(output_dir, filename)

        # Write JSON
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2, ensure_ascii=False)

        print(f"PDF data saved to '{filepath}'.")
    else:
        print("Failed to extract PDF content.")

if __name__ == "__main__":
    main()
