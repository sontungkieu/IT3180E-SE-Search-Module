import os,json
import numpy as np
import onnxruntime
from transformers import AutoTokenizer
from typing import List, Dict, Any
from chromadb import PersistentClient



# Đường dẫn lưu trữ tokenizer và mô hình ONNX
TOKENIZER_PATH = "./tokenizer"
ONNX_MODEL_PATH = "./onnx_model/model.onnx"

class LocalEmbeddingFunction:
    """Custom embedding function dùng mô hình local (offline) với ONNX."""

    def __init__(self, model_name: str = "sentence-transformers/all-MiniLM-L6-v2"):
        # Tải tokenizer từ thư mục nếu đã có
        if not os.path.exists(TOKENIZER_PATH):
            raise ValueError(f"Tokenizer không tìm thấy tại {TOKENIZER_PATH}")
        
        # Tải mô hình ONNX từ thư mục nếu đã có
        if not os.path.exists(ONNX_MODEL_PATH):
            raise ValueError(f"Mô hình ONNX không tìm thấy tại {ONNX_MODEL_PATH}")
        
        # Load mô hình ONNX và tokenizer
        self.session = onnxruntime.InferenceSession(ONNX_MODEL_PATH)
        self.tokenizer = AutoTokenizer.from_pretrained(TOKENIZER_PATH)

    def __call__(self, input: List[str]) -> List[List[float]]:
        # Tạo input cho mô hình
        inputs = self.tokenizer(input, padding=True, truncation=True, return_tensors="np")
        
        # Lấy các input hợp lệ từ mô hình ONNX
        ort_inputs = {k: v for k, v in inputs.items() if k in [i.name for i in self.session.get_inputs()]}
        
        # Chạy inference và lấy kết quả
        ort_outs = self.session.run(None, ort_inputs)
        
        # Tính toán embeddings bằng cách sử dụng mean pooling
        embeddings = np.mean(ort_outs[0], axis=1)
        
        return embeddings.tolist()



class VectorDatabase:
    """Vector DB cho dữ liệu chunk hóa, dùng Chroma + offline embedding."""

    def __init__(self, storage_path: str = "./vector_storage"):
        self.client = PersistentClient(path=storage_path)
        self.embedding_fn = LocalEmbeddingFunction()
        self.collection = self.client.get_or_create_collection(
            name="media_vectors",
            embedding_function=self.embedding_fn
        )

    def get_all_scopes(self) -> List[str]:
        scopes: List[str] = []
        try:
            names = self.client.list_collections()  # → Sequence[str] ở chroma≥0.6.0
            for col in names:
                # Nếu col là string thì dùng trực tiếp, 
                # nếu là object thì lấy col.name
                if isinstance(col, str):
                    collection_name = col
                else:
                    collection_name = getattr(col, "name", None)
                if collection_name and collection_name.startswith("scope_"):
                    scopes.append(collection_name[len("scope_"):])
        except Exception as e:
            print(f"Error listing collections: {e}")
        return scopes


    def get_collection_by_scope(self, scope: str):
        """Tạo hoặc lấy collection theo scope."""
        return self.client.get_or_create_collection(
            name=f"scope_{scope}",
            embedding_function=self.embedding_fn
        )

    def add_chunk(self, chunk: Dict[str, Any]) -> Dict[str, Any]:
        """Thêm 1 chunk vào collection tương ứng."""
        print("chunk:", chunk)
        if chunk.get("chunk_scope") is None:
            print("errooorrr: chunk_scope is None.",chunk)
            raise ValueError("chunk_scope is None.")
            # return {"status": "error", "message": "chunk_scope is None."}
        try:
            scope = f"scope_{chunk["chunk_scope"]}"
            # scope = chunk.get("chunk_scope")
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
                "chunk_scope": chunk.get("chunk_scope"),
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

    def semantic_search(self, query: str, scope: str, k: int = 5) -> Dict[str, List[Dict[str, Any]]]:
        """Tìm kiếm semantic vector embedding trên nhiều scope cùng lúc."""
        results_by_scope = {}

        # Lấy danh sách tất cả các scope (giả sử bạn có method này)
        all_scopes = self.get_all_scopes()  # ví dụ trả về ['scope1', 'scope2', ...]

        # Đảm bảo scope hiện tại nằm đầu tiên (tùy chọn)
        scope = f"scope_{scope}"
        ordered_scopes = [scope] + [s for s in all_scopes if s != scope]

        for sc in ordered_scopes:
            try:
                collection = self.get_collection_by_scope(sc)
                res = collection.query(
                    query_texts=[query],
                    n_results=k,
                    include=["documents", "metadatas", "distances"]
                )
                chunks = []
                for doc, meta, distance in zip(
                    res["documents"][0],
                    res["metadatas"][0],
                    res["distances"][0]
                ):
                    chunks.append({
                        "text": doc,
                        "location": meta.get("location"),
                        "chunk_id": meta.get("chunk_id"),
                        "chunk_source": meta.get("chunk_source"),
                        "chunk_scope": meta.get("chunk_scope"),
                        "chunk_source_type": meta.get("chunk_source_type"),
                        "similarity_score": round(1 - distance, 4)
                    })
                results_by_scope[sc] = chunks

            except Exception as e:
                # Nếu lỗi thì vẫn báo về scope đó
                results_by_scope[sc] = [{"status": "error", "message": str(e)}]

        return results_by_scope


    def word_search(self, query: str, scope: str, k: int = 5) -> Dict[str, List[Dict[str, Any]]]:
        """Tìm kiếm theo từ khóa (exact match) trên nhiều scope cùng lúc."""
        results_by_scope = {}
        all_scopes = self.get_all_scopes()  # ví dụ ['scope1', 'scope2', ...]

        # Ưu tiên scope hiện tại, rồi mới đến các scope khác
        ordered_scopes = [scope] + [s for s in all_scopes if s != scope]

        for sc in ordered_scopes:
            try:
                collection = self.get_collection_by_scope(sc)
                all_docs = collection.get()
                hits = []
                for doc, meta in zip(all_docs["documents"], all_docs["metadatas"]):
                    if query.lower() in doc.lower():
                        hits.append({
                            "text": doc,
                            "location": meta.get("location"),
                            "chunk_id": meta.get("chunk_id"),
                            "chunk_source": meta.get("chunk_source"),
                            "chunk_scope": meta.get("chunk_scope"),
                            "chunk_source_type": meta.get("chunk_source_type")
                        })
                        if len(hits) >= k:
                            break

                results_by_scope[sc] = hits

            except Exception as e:
                results_by_scope[sc] = [{"status": "error", "message": str(e)}]

        return results_by_scope


# ✅ Test đơn giản
if __name__ == "__main__":
    db = VectorDatabase()

    chunk1 = {
        "location": "01:16:25",
        "text": "Tokenizer maps between strings and sequences of integers...",
        "chunk_source": "https://www.youtube.com/watch?v=Rvppog1HZJY&t=3s",
        "chunk_scope": "IT3190E",
        "chunk_source_type": "youtube",
        "chunk_id": 49
    }

    chunk2 = {
        "location": "01:18:00",
        "text": "See you next time.",
        "chunk_source": "https://www.youtube.com/watch?v=Rvppog1HZJY&t=3s",
        "chunk_scope": "IT3190E",
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
