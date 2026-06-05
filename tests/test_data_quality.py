import os
import json
import pytest

def test_dataset_exists():
    dataset_path = os.path.join("data", "processed", "dataset.jsonl")
    assert os.path.exists(dataset_path), f"Dataset not found at {dataset_path}. Did build_dataset.py run?"

def test_dataset_format():
    dataset_path = os.path.join("data", "processed", "dataset.jsonl")
    
    with open(dataset_path, "r", encoding="utf-8") as f:
        lines = f.readlines()
        
    assert len(lines) > 0, "Dataset is empty!"
    
    for i, line in enumerate(lines):
        try:
            data = json.loads(line)
        except json.JSONDecodeError:
            pytest.fail(f"Line {i} is not valid JSON.")
            
        assert "messages" in data, f"Line {i} is missing 'messages' key."
        assert len(data["messages"]) == 2, f"Line {i} should have exactly 2 messages (user, assistant)."
        
        roles = [m["role"] for m in data["messages"]]
        assert "user" in roles and "assistant" in roles, f"Line {i} missing user or assistant roles."
        
        for msg in data["messages"]:
            assert isinstance(msg["content"], str), f"Content is not string on line {i}"
            assert len(msg["content"].strip()) > 0, f"Empty content found on line {i}"

def test_dataset_token_bounds():
    dataset_path = os.path.join("data", "processed", "dataset.jsonl")
    
    with open(dataset_path, "r", encoding="utf-8") as f:
        lines = f.readlines()
        
    for i, line in enumerate(lines):
        data = json.loads(line)
        # Rough token approximation (1 token ~= 4 chars)
        total_chars = sum(len(m["content"]) for m in data["messages"])
        approx_tokens = total_chars / 4
        
        # Max context window check (e.g. 2048 tokens)
        assert approx_tokens < 2000, f"Line {i} exceeds safe token bounds (approx {approx_tokens} tokens)."
