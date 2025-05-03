# models/embedding_model.py
from sentence_transformers import SentenceTransformer

class EmbeddingModel:
    def __init__(self, model_path: str):
        self.model = SentenceTransformer(model_path)

    def generate_embedding(self, text: str) -> list:
        return self.model.encode(text).tolist()
