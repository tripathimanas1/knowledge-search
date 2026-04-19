import pytest
import json
from backend.app.ingest import normalize_doc, clean_text, run_folder_ingest

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

def test_folder_mode_ingest(tmp_path):
    """Test folder ingestion logic, short file skipping, large file skipping, and ignore extensions."""
    in_dir = tmp_path / "raw"
    in_dir.mkdir()
    out_dir = tmp_path / "processed"
    
    # Create valid files
    (in_dir / "doc1.txt").write_text("This is valid content that is long enough to pass the 50 char filter limit.")
    (in_dir / "doc2.txt").write_text("Another valid doc that is long enough to pass the 50 char filter limit.")
    (in_dir / "doc3.md").write_text("A markdown doc that is long enough to pass the 50 char filter limit.")
    
    # Short file (< 50 chars)
    (in_dir / "short.txt").write_text("Too short.")
    
    # Large file (> 50KB)
    (in_dir / "large.txt").write_text("A" * (50 * 1024 + 10))
    
    # Ignored extensions (.pdf, .docx)
    (in_dir / "ignore1.pdf").write_text("This pdf content is long enough but should be skipped by file extension.")
    (in_dir / "ignore2.docx").write_text("This docx content is long enough but should be skipped by file extension.")
    
    # Run folder mode ingest
    run_folder_ingest(str(in_dir), str(out_dir))
    
    out_path = out_dir / "docs.jsonl"
    assert out_path.exists()
    
    results = []
    with open(out_path, "r", encoding="utf-8") as f:
        for line in f:
            results.append(json.loads(line))
            
    assert len(results) == 3
    titles = set(r["title"] for r in results)
    assert "doc1" in titles
    assert "doc2" in titles
    assert "doc3" in titles
    
    assert "short" not in titles
    assert "large" not in titles
    assert "ignore1" not in titles
    assert "ignore2" not in titles
