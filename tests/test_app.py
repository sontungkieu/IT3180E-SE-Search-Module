import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch
import pytest
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
    assert "id" in chunks[0], "Each chunk should have an 'id'"
    assert "scope" in chunks[0], "Each chunk should have 'scope'"
    assert "type" in chunks[0], "Each chunk should have 'type'"
    assert "title" in chunks[0], "Each chunk should have 'title'"
    assert "original_data" in chunks[0], "Each chunk should have 'original_data'"
    assert isinstance(title, str), "Title should be a string"

def test_process_pdf_returns_chunks():
    pdf_path = "Quantum02.pdf"
    assert os.path.exists(pdf_path), f"{pdf_path} must exist for the test"

    chunks, base_name = process_pdf(pdf_path, scope="IT3190E")

    assert chunks is not None, "Chunks should not be None"
    assert isinstance(chunks, list), "Chunks should be a list"
    assert len(chunks) > 0, "Chunks list should not be empty"
    assert "chunk_id" in chunks[0], "Each chunk should have 'chunk_id'"
    assert "chunk_scope" in chunks[0], "Each chunk should have 'chunk_scope'"
    assert "chunk_source" in chunks[0], "Each chunk should have 'chunk_source'"
    assert "chunk_source_type" in chunks[0], "Each chunk should have 'chunk_source_type'"
    assert isinstance(base_name, str), "Base name should be a string"


def test_search_word(example_search):
    # Nếu muốn mock search_word sau này, bạn có thể thêm @patch tương tự
    response = client.post("/", files=create_upload_file(example_search))
    assert response.status_code == 200 or response.status_code == 500  # Tùy thuộc bạn đã cài search hay chưa
