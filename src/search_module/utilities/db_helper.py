import json
import chromadb
from typing import Dict, Any, List

from sentence_transformers import SentenceTransformer
from chromadb import PersistentClient



# class LocalEmbeddingFunction:
#     """Custom embedding function dùng mô hình local (offline)."""
#     def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
#         self.model = SentenceTransformer(model_name)

#     def __call__(self, input: List[str]) -> List[List[float]]:
#         return self.model.encode(input).tolist()

class LocalEmbeddingFunction:
    """Custom embedding function dùng mô hình local (offline) với ONNX."""
    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        self.model = SentenceTransformer(model_name, backend="onnx")

    def __call__(self, input: List[str]) -> List[List[float]]:
        return self.model.encode(input).tolist()


class VectorDatabase:
    """Vector DB cho dữ liệu chunk hóa, dùng Chroma + offline embedding."""

    def __init__(self, storage_path: str = "./vector_storage"):
        self.client = PersistentClient(path=storage_path)
        self.embedding_fn = LocalEmbeddingFunction()
        self.collection = self.client.get_or_create_collection(
            name="media_vectors",
            embedding_function=self.embedding_fn
        )

    def get_collection_by_scope(self, scope: str):
        """Tạo hoặc lấy collection theo scope."""
        return self.client.get_or_create_collection(
            name=f"scope_{scope}",
            embedding_function=self.embedding_fn
        )

    def add_chunk(self, chunk: Dict[str, Any]) -> Dict[str, Any]:
        """Thêm 1 chunk vào collection tương ứng."""
        try:
            scope = chunk["chunk_scope"]
            collection = self.get_collection_by_scope(scope)
            print("collection name:", collection.name)
            print("chunk:", chunk)
            chunk_text = chunk.get("text", "")
            if not chunk_text.strip():
                print("errooorrr: Empty text.")
                return {"status": "error", "message": "Empty text."}

            chunk_id = f"{scope}_{chunk.get('chunk_id')}_{hash(chunk_text)}"

            chunk_metadata = {
                "location": chunk.get("location"),
                "chunk_source": chunk.get("chunk_source"),
                "scope": scope,
                "chunk_source_type": chunk.get("chunk_source_type"),
                "chunk_id": chunk.get("chunk_id"),
            }
            print("chunk_metadata:", chunk_metadata)
            collection.add(
                documents=[chunk_text],
                metadatas=[chunk_metadata],
                ids=[chunk_id]
            )
            print("add chunk_id ok:", chunk_id)
            return {"status": "success", "chunk_id": chunk_id}

        except Exception as e:
            print("Error adding chunk:", e)
            return {"status": "error", "message": str(e)}

    def semantic_search(self, query: str, scope: str, k: int = 5) -> List[Dict[str, Any]]:
        """Tìm kiếm theo semantic vector embedding."""
        try:
            collection = self.get_collection_by_scope(scope)
            results = collection.query(
                query_texts=[query],
                n_results=k,
                include=["documents", "metadatas", "distances"]
            )

            chunks = []
            for doc, meta, distance in zip(
                results["documents"][0],
                results["metadatas"][0],
                results["distances"][0]
            ):
                chunks.append({
                    "text": doc,
                    "location": meta.get("location"),
                    "chunk_id": meta.get("chunk_id"),
                    "chunk_source": meta.get("chunk_source"),
                    "scope": meta.get("scope"),
                    "chunk_source_type": meta.get("chunk_source_type"),
                    "similarity_score": round(1 - distance, 4)  # Càng gần 1 thì càng giống
                })
            print(chunks)
            return chunks

        except Exception as e:
            return [{"status": "error", "message": str(e)}]

    def word_search(self, query: str, scope: str, k: int = 5) -> List[Dict[str, Any]]:
        """Tìm kiếm theo từ khóa (exact match)."""
        try:
            collection = self.get_collection_by_scope(scope)
            all_docs = collection.get()
            print("len of db:",len(all_docs["documents"]))
            hits = []
            for doc, meta in zip(all_docs["documents"], all_docs["metadatas"]):
                print(doc)
                print(meta)
                if query.lower() in doc.lower():
                    hits.append({
                        "text": doc,
                        "location": meta.get("location"),
                        "chunk_id": meta.get("chunk_id"),
                        "chunk_source": meta.get("chunk_source"),
                        "scope": meta.get("scope"),
                        "chunk_source_type": meta.get("chunk_source_type")
                    })
                    if len(hits) >= k:
                        break

            return hits

        except Exception as e:
            return [{"status": "error", "message": str(e)}]


# ✅ Test đơn giản
if __name__ == "__main__":
    db = VectorDatabase()

    chunk1 = {
        "location": "01:16:25",
        "text": "Tokenizer maps between strings and sequences of integers...",
        "chunk_source": "https://www.youtube.com/watch?v=Rvppog1HZJY&t=3s",
        "scope": "IT3190E",
        "chunk_source_type": "youtube",
        "chunk_id": 49
    }

    chunk2 = {
        "location": "01:18:00",
        "text": "See you next time.",
        "chunk_source": "https://www.youtube.com/watch?v=Rvppog1HZJY&t=3s",
        "scope": "IT3190E",
        "chunk_source_type": "youtube",
        "chunk_id": 50
    }

    print("➕ Add chunk1:", db.add_chunk(chunk1))
    print("➕ Add chunk2:", db.add_chunk(chunk2))

    print("\n🔍 Semantic Search:")
    results = db.semantic_search("tokenizer", scope="IT3190E")
    print(json.dumps(results, indent=2, ensure_ascii=False))

    print("\n🔍 Word Search:")
    results = db.word_search("see you", scope="IT3190E")
    print(json.dumps(results, indent=2, ensure_ascii=False))
