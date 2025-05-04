import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch
import pytest
from search_module.utilities.db_helper import VectorDatabase
from search_module.utilities.youtube import process_youtube
from search_module.utilities.pdf import process_pdf
import os


from search_module.app import app

client = TestClient(app)

@pytest.fixture
def example_add_youtube():
    return {
        "add": "youtube",
        "data": "https://www.youtube.com/watch?v=Rvppog1HZJY&t=3s",
        "scope": "IT3190E"
    }

@pytest.fixture
def example_add_pdf():
    return {
        "add": "pdf",
        "data": "Quantum02.pdf",
        "scope": "IT3190E"
    }

@pytest.fixture
def example_search():
    return {
        "search": "machine learning",
        "mod": "word",
        "scope": "IT3190E"
    }

def create_upload_file(json_data):
    import io
    import json as js
    return {'file': ('mock.json', io.BytesIO(js.dumps(json_data).encode()), 'application/json')}

def test_process_youtube_returns_chunks():
    chunks, title = process_youtube(
        url="https://www.youtube.com/watch?v=Rvppog1HZJY&t=3s",
        scope="IT3190E",
        lang="en"
    )

    assert chunks is not None, "Chunks should not be None"
    assert isinstance(chunks, list), "Chunks should be a list"
    assert len(chunks) > 0, "Chunks list should not be empty"
    assert "chunk_source" in chunks[0], "Each chunk should have 'chunk_source'"
    assert "chunk_scope" in chunks[0], "Each chunk should have 'chunk_scope'"
    assert "chunk_source_type" in chunks[0], "Each chunk should have 'chunk_source_type'"
    assert "chunk_id" in chunks[0], "Each chunk should have an 'chunk_id'"
    assert isinstance(title, str), "Title should be a string"

def test_process_pdf_returns_chunks():
    pdf_path = "Quantum02.pdf"
    assert os.path.exists(pdf_path), f"{pdf_path} must exist for the test"

    chunks, base_name = process_pdf(pdf_path, scope="IT3190E")

    assert chunks is not None, "Chunks should not be None"
    assert isinstance(chunks, list), "Chunks should be a list"
    assert len(chunks) > 0, "Chunks list should not be empty"
    assert "chunk_source" in chunks[0], "Each chunk should have 'chunk_source'"
    assert "chunk_scope" in chunks[0], "Each chunk should have 'chunk_scope'"
    assert "chunk_source_type" in chunks[0], "Each chunk should have 'chunk_source_type'"
    assert "chunk_id" in chunks[0], "Each chunk should have 'chunk_id'"
    assert isinstance(base_name, str), "Base name should be a string"



@pytest.fixture
def youtube_chunks_sample():
    return [
        {
            "location": "01:16:25",
            "text": "it was also very inefficient. For example, encode loops over the merges. You should only loops over the merges that matter...",
            "chunk_source": "https://www.youtube.com/watch?v=Rvppog1HZJY&t=3s",
            "scope": "IT3190E",
            "chunk_source_type": "youtube",
            "chunk_id": 49
        },
        {
            "location": "01:18:00",
            "text": "see you next time.",
            "chunk_source": "https://www.youtube.com/watch?v=Rvppog1HZJY&t=3s",
            "scope": "IT3190E",
            "chunk_source_type": "youtube",
            "chunk_id": 50
        }
    ]


def test_add_youtube_chunks_and_search(youtube_chunks_sample):
    db = VectorDatabase()

    # Step 1: Add chunks
    for chunk in youtube_chunks_sample:
        res = db.add_chunk(chunk)
        assert res["status"] == "success", f"Failed to add chunk: {res.get('message')}"

    # Step 2: Semantic search
    semantic_results = db.semantic_search("tokenizer", scope="IT3190E")
    assert isinstance(semantic_results, list), "Semantic search should return a list"
    assert len(semantic_results) > 0, "Semantic search should return results"
    assert "text" in semantic_results[0], "Each result must contain 'text'"
    print("\n🔍 Semantic Search:\n", semantic_results)

    # Step 3: Word search
    word_results = db.word_search("see you", scope="IT3190E")
    assert isinstance(word_results, list), "Word search should return a list"
    assert len(word_results) > 0, "Word search should return results"
    assert "text" in word_results[0], "Each result must contain 'text'"
    print("\n🔍 Word Search:\n", word_results)
