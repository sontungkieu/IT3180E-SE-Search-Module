# search_module.py
import chromadb
from sentence_transformers import SentenceTransformer
from typing import List, Dict, Any, Optional
import numpy as np
import json

class SearchModule:
    """
    Handles keyword and semantic search operations within a Chroma vector database.
    """

    def __init__(self, storage_path: str = "./vector_storage", collection_name: str = "media_vectors"):
        """
        Initializes the ChromaDB client, collection, and embedding model.

        Args:
            storage_path (str): Path to the ChromaDB persistent storage directory.
            collection_name (str): Name of the collection to use within ChromaDB.
        """
        try:
            self.client = chromadb.PersistentClient(path=storage_path)
            self.collection = self.client.get_collection(name=collection_name)
            print(f"Successfully connected to collection '{collection_name}' at '{storage_path}'.")
            print(f"Collection contains {self.collection.count()} items.")
        except Exception as e:
            print(f"Error connecting to ChromaDB collection '{collection_name}' at path '{storage_path}': {e}")
            # Optionally, try get_or_create_collection or raise the exception
            # For now, let's try get_or_create to be more robust for first run
            try:
                print("Attempting to get or create collection...")
                self.collection = self.client.get_or_create_collection(name=collection_name)
                print(f"Successfully got or created collection '{collection_name}'.")
                print(f"Collection contains {self.collection.count()} items.")
            except Exception as e_create:
                 print(f"Failed to get or create collection: {e_create}")
                 raise e_create # Re-raise exception if creation also fails

        try:
            # Load the embedding model once
            self.embedder = SentenceTransformer('all-MiniLM-L6-v2')
            print("Sentence Transformer model loaded successfully.")
        except Exception as e:
            print(f"Error loading Sentence Transformer model: {e}")
            self.embedder = None
            raise e

    def keyword_search(self, keywords: str, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Performs a keyword search within the 'documents' field of the collection.

        Args:
            keywords (str): The keyword string to search for. Case-sensitive.
            limit (Optional[int]): Maximum number of results to return. Returns all if None.

        Returns:
            List[Dict[str, Any]]: A list of dictionaries, each containing the 'id',
                                   'text', and 'metadata' of a matching chunk.
                                   Returns an empty list if no matches are found or on error.
        """
        if not keywords:
            print("Keyword search requires non-empty keywords.")
            return []

        try:
            results = self.collection.get(
                where_document={"$contains": keywords},
                include=['documents', 'metadatas'],
                limit=limit # Pass limit directly if supported, otherwise filter after get
            )

            formatted_results = []
            if results and results.get('ids'):
                 # If limit wasn't natively supported or we need to ensure exact limit
                num_results_to_take = limit if limit is not None else len(results['ids'])
                num_results_to_take = min(num_results_to_take, len(results['ids']))

                for i in range(num_results_to_take):
                    formatted_results.append({
                        "id": results['ids'][i],
                        "text": results['documents'][i],
                        "metadata": results['metadatas'][i] if results['metadatas'] else None
                    })
            return formatted_results

        except Exception as e:
            print(f"Error during keyword search for '{keywords}': {e}")
            return []

    def semantic_search(self, query_text: str, n_results: int = 5) -> List[Dict[str, Any]]:
        """
        Performs a semantic search based on the embedding of the query text.

        Args:
            query_text (str): The text query for semantic similarity search.
            n_results (int): The number of most similar results to return.

        Returns:
            List[Dict[str, Any]]: A list of dictionaries, each containing the 'id',
                                   'text', 'metadata', and 'distance' of a matching chunk.
                                   Returns an empty list if no results are found or on error.
        """
        if not self.embedder:
             print("Embedder not loaded. Cannot perform semantic search.")
             return []
        if not query_text:
            print("Semantic search requires non-empty query text.")
            return []

        try:
            query_embedding = self.embedder.encode([query_text]).tolist()

            if not query_embedding:
                 print("Failed to generate embedding for the query.")
                 return []

            results = self.collection.query(
                query_embeddings=query_embedding,
                n_results=n_results,
                include=['documents', 'metadatas', 'distances']
            )

            formatted_results = []
            # Results is a dict where each value is a list containing results for each query embedding
            # Since we only have one query, we access the first element (index 0)
            if results and results.get('ids') and results['ids'][0]:
                for i in range(len(results['ids'][0])):
                     # Ensure all corresponding lists have the element at index i
                    if (results['documents'] and len(results['documents'][0]) > i and
                        results['metadatas'] and len(results['metadatas'][0]) > i and
                        results['distances'] and len(results['distances'][0]) > i):
                        formatted_results.append({
                            "id": results['ids'][0][i],
                            "text": results['documents'][0][i],
                            "metadata": results['metadatas'][0][i],
                            "distance": results['distances'][0][i]
                        })
                    else:
                         print(f"Warning: Inconsistent data for result index {i}. Skipping.")


            return formatted_results

        except Exception as e:
            print(f"Error during semantic search for '{query_text}': {e}")
            # Potentially log the full traceback here
            import traceback
            traceback.print_exc()
            return []

# --- Example Usage ---
if __name__ == "__main__":
    print("Initializing Search Module...")
    try:
        searcher = SearchModule() # Assumes DB is in ./vector_storage

        # --- Keyword Search Example ---
        print("\n--- Keyword Search ---")
        keyword_query = "english"
        print(f"Searching for keywords: '{keyword_query}'")
        keyword_results = searcher.keyword_search(keywords=keyword_query, limit=3)

        if keyword_results:
            print(f"Found {len(keyword_results)} results:")
            for i, result in enumerate(keyword_results):
                print(f"\nResult {i+1}:")
                print(f"  ID: {result['id']}")
                # Truncate long text for display
                text_preview = (result['text'][:150] + '...') if len(result['text']) > 150 else result['text']
                print(f"  Text: {text_preview}")
                print(f"  Metadata: {json.dumps(result.get('metadata', {}), indent=2)}")
        else:
            print("No results found for keyword search.")

        # --- Semantic Search Example ---
        print("\n--- Semantic Search ---")
        semantic_query = "how brain understand information"
        print(f"Searching semantically for: '{semantic_query}'")
        semantic_results = searcher.semantic_search(query_text=semantic_query, n_results=3)

        if semantic_results:
            print(f"Found {len(semantic_results)} results:")
            for i, result in enumerate(semantic_results):
                print(f"\nResult {i+1}:")
                print(f"  ID: {result['id']}")
                # Truncate long text for display
                text_preview = (result['text'][:150] + '...') if len(result['text']) > 150 else result['text']
                print(f"  Text: {text_preview}")
                print(f"  Metadata: {json.dumps(result.get('metadata', {}), indent=2)}")
                print(f"  Distance: {result['distance']:.4f}") # Lower is better
        else:
            print("No results found for semantic search.")

        # --- Example with different keywords ---
        print("\n--- Keyword Search (different keywords) ---")
        keyword_query_2 = "autoencoder"
        print(f"Searching for keywords: '{keyword_query_2}'")
        keyword_results_2 = searcher.keyword_search(keywords=keyword_query_2, limit=2)

        if keyword_results_2:
            print(f"Found {len(keyword_results_2)} results:")
            for i, result in enumerate(keyword_results_2):
                print(f"\nResult {i+1}:")
                print(f"  ID: {result['id']}")
                text_preview = (result['text'][:150] + '...') if len(result['text']) > 150 else result['text']
                print(f"  Text: {text_preview}")
                print(f"  Metadata: {json.dumps(result.get('metadata', {}), indent=2)}")
        else:
            print("No results found for keyword search.")

    except Exception as main_e:
        print(f"\nAn error occurred during the example usage: {main_e}")
