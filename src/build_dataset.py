import os
import json
import glob
import logging
import re
import hashlib
import random

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

def clean_text(text: str) -> str:
    """Enterprise text sanitization pass."""
    # Remove markdown links [text](url) -> text
    text = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', text)
    # Remove HTML tags
    text = re.sub(r'<[^>]+>', '', text)
    # Remove citation brackets e.g. [1], [1, 2], [Smith, 2026]
    text = re.sub(r'\[[0-9,\sA-Za-z-]+\]', '', text)
    # Remove multiple spaces and newlines
    text = re.sub(r' +', ' ', text)
    text = re.sub(r'\n+', '\n', text)
    return text.strip()

def chunk_text(text: str, max_words: int = 200) -> list:
    """Chunks text into logical segments by double newline."""
    paragraphs = text.split('\n')
    chunks = []
    current_chunk = []
    current_word_count = 0
    
    for p in paragraphs:
        p = p.strip()
        if not p:
            continue
            
        words = p.split()
        if current_word_count + len(words) > max_words and current_chunk:
            chunks.append(" ".join(current_chunk))
            current_chunk = [p]
            current_word_count = len(words)
        else:
            current_chunk.append(p)
            current_word_count += len(words)
            
    if current_chunk:
        chunks.append(" ".join(current_chunk))
    return chunks

def get_diverse_instruction(first_sentence: str) -> str:
    """Returns a diverse, conceptually randomized prompt."""
    prompts = [
        f"Provide details regarding the following topic from the research papers: '{first_sentence}'",
        f"Based on the theoretical framework, explain the concept beginning with: '{first_sentence}'",
        f"Summarize the findings and mechanism related to this point: '{first_sentence}'",
        f"Elaborate on the architectural design mentioned here: '{first_sentence}'",
        f"What does the research indicate about the following: '{first_sentence}'"
    ]
    return random.choice(prompts)

def build_instruction_pair(chunk: str) -> dict:
    """Constructs a conversation history suitable for ChatML / standard HF formats."""
    sentences = chunk.split('. ')
    if len(sentences) > 1:
        first_sentence = sentences[0] + '.'
        rest_of_text = '. '.join(sentences[1:])
        user_content = get_diverse_instruction(first_sentence)
        assistant_content = rest_of_text
    else:
        user_content = "State a key finding or mechanism from the research papers."
        assistant_content = chunk
        
    return {
        "messages": [
            {"role": "user", "content": user_content.strip()},
            {"role": "assistant", "content": assistant_content.strip()}
        ]
    }

def main():
    raw_dir = os.path.join("data", "raw")
    processed_dir = os.path.join("data", "processed")
    os.makedirs(processed_dir, exist_ok=True)
    
    md_files = glob.glob(os.path.join(raw_dir, "*.md"))
    if not md_files:
        logging.error("No markdown files found in data/raw/")
        return
        
    dataset_out = os.path.join(processed_dir, "dataset.jsonl")
    
    seen_hashes = set()
    processed_count = 0
    dropped_count = 0

    with open(dataset_out, "w", encoding="utf-8") as out_f:
        for filepath in md_files:
            with open(filepath, "r", encoding="utf-8") as f:
                content = f.read()
            
            # Clean text globally before chunking
            content = clean_text(content)
            chunks = chunk_text(content)
            
            for chunk in chunks:
                words = chunk.split()
                # Strict length constraints (reject noise)
                if len(words) < 15:
                    dropped_count += 1
                    continue
                
                # Deduplication
                chunk_hash = hashlib.md5(chunk.encode('utf-8')).hexdigest()
                if chunk_hash in seen_hashes:
                    dropped_count += 1
                    continue
                seen_hashes.add(chunk_hash)

                row = build_instruction_pair(chunk)
                out_f.write(json.dumps(row) + "\n")
                processed_count += 1
                
    logging.info(f"Successfully compiled {processed_count} training examples.")
    logging.info(f"Dropped {dropped_count} fragments due to duplication or low semantic density.")

if __name__ == "__main__":
    main()
