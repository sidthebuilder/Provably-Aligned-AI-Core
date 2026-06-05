import os
import json
import glob
import logging

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

def chunk_text(text: str, max_words: int = 200) -> list:
    """Chunks text into logical segments by double newline."""
    paragraphs = text.split('\n\n')
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

def build_instruction_pair(chunk: str) -> dict:
    """Constructs a conversation history suitable for ChatML / standard HF formats."""
    sentences = chunk.split('. ')
    if len(sentences) > 1:
        first_sentence = sentences[0] + '.'
        rest_of_text = '. '.join(sentences[1:])
        user_content = f"Provide details regarding the following topic from the research papers: '{first_sentence}'"
        assistant_content = rest_of_text
    else:
        user_content = "State a key finding from the research papers."
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
    
    processed_count = 0
    with open(dataset_out, "w", encoding="utf-8") as out_f:
        for filepath in md_files:
            with open(filepath, "r", encoding="utf-8") as f:
                content = f.read()
                
            chunks = chunk_text(content)
            for chunk in chunks:
                if len(chunk.split()) < 10:
                    continue
                row = build_instruction_pair(chunk)
                out_f.write(json.dumps(row) + "\n")
                processed_count += 1
                
    logging.info(f"Successfully compiled {processed_count} training examples into {dataset_out}")

if __name__ == "__main__":
    main()
