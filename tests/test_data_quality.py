import os
import json
import pytest
import re
import hashlib

DATASET_PATH = os.path.join("data", "processed", "dataset.jsonl")

def get_lines():
    assert os.path.exists(DATASET_PATH), f"Dataset not found at {DATASET_PATH}"
    with open(DATASET_PATH, "r", encoding="utf-8") as f:
        return f.readlines()

def get_parsed_data():
    return [json.loads(line) for line in get_lines()]

# Criterion 1
def test_json_schema_validity():
    """1. Ensures the dataset file is perfectly parsable JSONL."""
    lines = get_lines()
    assert len(lines) > 0, "Dataset is empty!"
    for i, line in enumerate(lines):
        try:
            json.loads(line)
        except json.JSONDecodeError:
            pytest.fail(f"Line {i} is not valid JSON.")

# Criterion 2
def test_role_structure_integrity():
    """2. Verifies every conversation has exactly one user prompt and one assistant response."""
    for i, data in enumerate(get_parsed_data()):
        assert "messages" in data, f"Line {i} is missing 'messages' key."
        assert len(data["messages"]) == 2, f"Line {i} should have exactly 2 messages."
        roles = [m["role"] for m in data["messages"]]
        assert roles == ["user", "assistant"], f"Line {i} invalid roles: {roles}"
        for msg in data["messages"]:
            assert isinstance(msg["content"], str), f"Content is not string on line {i}"
            assert len(msg["content"].strip()) > 0, f"Empty content found on line {i}"

# Criterion 3
def test_markdown_html_sanitization():
    """3. Scans for leaked markdown links or HTML tags."""
    for i, data in enumerate(get_parsed_data()):
        for msg in data["messages"]:
            content = msg["content"]
            assert not re.search(r'\[([^\]]+)\]\([^\)]+\)', content), f"Unresolved markdown link found on line {i}"
            assert not re.search(r'<[^>]+>', content), f"Unresolved HTML found on line {i}"

# Criterion 4
def test_citation_artifact_removal():
    """4. Scans for leaked academic citation brackets."""
    for i, data in enumerate(get_parsed_data()):
        for msg in data["messages"]:
            content = msg["content"]
            assert not re.search(r'\[\d+\]', content), f"Unresolved citation bracket found on line {i}"

# Criterion 5
def test_semantic_density_minimums():
    """5. Fails if any assistant response contains fewer than 10 words."""
    for i, data in enumerate(get_parsed_data()):
        assistant_content = data["messages"][1]["content"]
        word_count = len(assistant_content.split())
        assert word_count >= 10, f"Line {i} lacks semantic density (only {word_count} words)."

# Criterion 6
def test_token_length_boundaries():
    """6. Fails if any chunk exceeds the 2048 token context window."""
    for i, data in enumerate(get_parsed_data()):
        total_chars = sum(len(m["content"]) for m in data["messages"])
        approx_tokens = total_chars / 4
        assert approx_tokens < 2000, f"Line {i} exceeds safe token bounds (approx {approx_tokens} tokens)."

# Criterion 7
def test_cryptographic_deduplication():
    """7. Verifies absolutely no duplicate assistant responses exist."""
    seen = set()
    for i, data in enumerate(get_parsed_data()):
        content = data["messages"][1]["content"]
        content_hash = hashlib.md5(content.encode('utf-8')).hexdigest()
        assert content_hash not in seen, f"Duplicate assistant response found on line {i}."
        seen.add(content_hash)
