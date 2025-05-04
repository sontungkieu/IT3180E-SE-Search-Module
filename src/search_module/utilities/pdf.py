import os
import json
import re
import PyPDF2

def extract_text_by_page(pdf_path):
    try:
        with open(pdf_path, "rb") as file:
            reader = PyPDF2.PdfReader(file)
            pages_text = []
            for i, page in enumerate(reader.pages):
                text = page.extract_text()
                if text:
                    pages_text.append((i + 1, text))  # page numbers start at 1
            return pages_text
    except Exception as e:
        print(f"Error reading PDF: {e}")
        return []

def chunk_text_by_page(pages_text, chunk_size=250):
    chunks = []
    for page_num, text in pages_text:
        words = text.split()
        current_chunk = []

        for word in words:
            current_chunk.append(word)
            if len(current_chunk) >= chunk_size:
                chunks.append({
                    "text": " ".join(current_chunk),
                    "location": page_num
                })
                current_chunk = []

        if current_chunk:
            chunks.append({
                "text": " ".join(current_chunk),
                "location": page_num
            })

    return chunks

def sanitize_filename(name):
    name = name.strip().replace(" ", "_")
    return re.sub(r'[\\/*?:"<>|]', "", name)

def process_pdf(pdf_path, scope):
    pages_text = extract_text_by_page(pdf_path)
    if not pages_text:
        return None, os.path.basename(pdf_path)

    all_text = "\n".join([text for _, text in pages_text])
    chunks = chunk_text_by_page(pages_text)
    for c_idx, chunk in enumerate(chunks):
        chunks[c_idx]["chunk_source"] = pdf_path
        chunks[c_idx]["chunk_scope"] = scope
        chunks[c_idx]["chunk_source_type"] = "pdf"
        chunks[c_idx]["chunk_id"] = c_idx + 1


    document_data = {
        "type": "pdf",
        "scope": scope,
        "original_data": pdf_path,
        "extracted_text": all_text,
        "chunks": chunks,
    }
    # print(chunks)
    base_name = os.path.splitext(os.path.basename(pdf_path))[0]
    return chunks, base_name

def main():
    pdf_path = input("Enter path to PDF file: ").strip()
    scope = input("Enter scope (e.g., topic, subject, or context): ").strip()

    result, title = process_pdf(pdf_path, scope)
    if result:
        output_dir = "json_output"
        os.makedirs(output_dir, exist_ok=True)

        safe_title = sanitize_filename(title)
        filename = f"{safe_title}.json"
        filepath = os.path.join(output_dir, filename)

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2, ensure_ascii=False)

        print(f"PDF data saved to '{filepath}'.")
    else:
        print("Failed to extract PDF content.")

if __name__ == "__main__":
    main()
