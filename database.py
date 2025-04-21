import json
import chromadb
from typing import Dict, Any


def load_json_from_file(file_path: str) -> Dict[str, Any]:
    """Load JSON data from a file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        raise Exception(f"File not found: {file_path}")
    except json.JSONDecodeError:
        raise Exception(f"Invalid JSON format: {file_path}")


class VectorDatabase:
    """Handles operations with Chroma vector database."""

    def __init__(self, storage_path: str = "./vector_storage"):
        self.client = chromadb.PersistentClient(path=storage_path)
        self.collection = self.client.get_or_create_collection(name="media_vectors")

    def add_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Add structured chunked data (with text + vector) to the DB."""
        try:
            base_id = f"{data['type']}_{data['scope']}_{hash(data['original_data'])}"

            for idx, chunk in enumerate(data.get("chunks", [])):
                chunk_text = chunk.get("text", "")
                chunk_embedding = chunk.get("embedding", [])

                if not chunk_embedding or not isinstance(chunk_embedding, list):
                    continue

                chunk_id = f"{base_id}_chunk_{idx}"
                chunk_metadata = {
                    "type": data["type"],
                    "scope": data["scope"],
                    "original_data": data["original_data"],
                    "timestamp": chunk.get("timestamp", ""),
                    "chunk_index": idx
                }

                self.collection.add(
                    embeddings=[chunk_embedding],
                    documents=[chunk_text],
                    metadatas=[chunk_metadata],
                    ids=[chunk_id]
                )

            return {"status": "success", "document_id": base_id}

        except Exception as e:
            return {"status": "error", "message": str(e)}


def main():
    db = VectorDatabase()
    file_path = 'json_output/Computational Intelligence and Neuroscience - 2018 - Voulodimos - Deep Learning for Computer Vision A Brief Review_20250331_203813.json'

    try:
        data = load_json_from_file(file_path)
        result = db.add_data(data)
        print(json.dumps({
            "status": result.get("status"),
            "document_id": result.get("document_id")
        }))
    except Exception as e:
        print(json.dumps({
            "status": "error",
            "message": str(e)
        }))


if __name__ == "__main__":
    main()
