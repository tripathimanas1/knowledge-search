import pytest
import json
from backend.app.ingest import normalize_doc, clean_text

def test_normalization_logic():
    """Test standard normalization with a fake document."""
    raw = "Subject: Important News\n\nThis is a sample document that definitely has more than fifty characters to ensure it passes the filter."
    doc = normalize_doc(1, raw)
    
    assert doc is not None
    assert doc["doc_id"] == "doc_0001"
    assert doc["title"] == "Subject: Important News"
    assert "sample document" in doc["text"]
    assert doc["source"] == "20newsgroups"
    assert "created_at" in doc

def test_truncation_logic():
    """Ensure text is truncated to 2000 chars and title to 80 chars."""
    long_raw = "A" * 100 + "\n" + ("LongText " * 300)
    doc = normalize_doc(2, long_raw)
    
    assert len(doc["text"]) == 2000
    assert len(doc["title"]) == 80

def test_skip_short_docs():
    """Verify that documents shorter than 50 chars are skipped."""
    short_raw = "Too short."
    doc = normalize_doc(3, short_raw)
    assert doc is None

def test_jsonl_output_validity():
    """Verify that normalize_doc outputs are valid JSON-serializable dictionaries."""
    raw_texts = [
        "First document content that is long enough.",
        "Second document content that is also long enough.",
        "Third document content for the test case."
    ]
    
    for i, text in enumerate(raw_texts):
        doc = normalize_doc(i, text)
        line = json.dumps(doc)
        parsed = json.loads(line)
        assert "doc_id" in parsed
        assert "text" in parsed
