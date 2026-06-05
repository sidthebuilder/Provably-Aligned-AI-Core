# Provably Aligned AI Core - Fine-Tuning Pipeline

This repository contains the enterprise MLOps pipeline for fine-tuning the Gemma large language model on the Provably Aligned AI Core research datasets.

## Architecture

* **Data Processing**: Converts raw Markdown documents from `data/raw/` into tokenized, chat-formatted JSONL datasets in `data/processed/`.
* **Automated QA**: GitHub Actions run `pytest` on every push to validate dataset integrity, formatting, and context window limits.
* **Fine-Tuning**: Structured for advanced fine-tuning techniques (DoRA, Flash Attention 2).

## Getting Started

### Local Setup
1. Clone the repository.
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Build the dataset from raw research papers:
   ```bash
   python src/build_dataset.py
   ```
4. Run the test suite:
   ```bash
   pytest tests/test_data_quality.py -v
   ```

### Continuous Integration (GitHub)
Pushing changes to `data/raw/` or `src/build_dataset.py` automatically triggers the GitHub Actions workflow defined in `.github/workflows/data_qa.yml`.
