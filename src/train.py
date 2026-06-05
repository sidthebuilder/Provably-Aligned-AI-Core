import os
import torch
import logging
from datasets import load_dataset
from unsloth import FastLanguageModel
from unsloth.chat_templates import get_chat_template
from trl import SFTTrainer
from transformers import TrainingArguments

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

def formatting_prompts_func(examples, tokenizer):
    convos = examples["messages"]
    texts = [tokenizer.apply_chat_template(convo, tokenize=False, add_generation_prompt=False) for convo in convos]
    return { "text" : texts }

def main():
    logging.info("Initializing Premium Fine-Tuning Pipeline...")
    
    dataset_path = "data/processed/dataset.jsonl"
    if not os.path.exists(dataset_path):
        logging.error(f"Dataset not found at {dataset_path}. Run build_dataset.py first.")
        return

    max_seq_length = 2048
    dtype = None 
    load_in_4bit = True 

    logging.info("Loading gemma-2b-it base model and tokenizer...")
    model, tokenizer = FastLanguageModel.from_pretrained(
        model_name = "unsloth/gemma-2b-it-bnb-4bit",
        max_seq_length = max_seq_length,
        dtype = dtype,
        load_in_4bit = load_in_4bit,
    )

    logging.info("Applying DoRA (Weight-Decomposed LoRA) configuration...")
    model = FastLanguageModel.get_peft_model(
        model,
        r = 32,
        target_modules = ["q_proj", "k_proj", "v_proj", "o_proj",
                          "gate_proj", "up_proj", "down_proj",],
        lora_alpha = 32,
        lora_dropout = 0,
        bias = "none",
        use_gradient_checkpointing = "unsloth",
        random_state = 3407,
        use_rslora = True,
        loftq_config = None,
        use_dora = True,
    )

    logging.info("Applying Gemma Chat Template to dataset...")
    tokenizer = get_chat_template(
        tokenizer,
        chat_template = "gemma",
        mapping = {"role" : "role", "content" : "content", "user" : "user", "assistant" : "model"},
    )
    
    dataset = load_dataset("json", data_files=dataset_path, split="train")
    dataset = dataset.map(lambda x: formatting_prompts_func(x, tokenizer), batched=True)

    logging.info("Starting SFTTrainer...")
    trainer = SFTTrainer(
        model = model,
        tokenizer = tokenizer,
        train_dataset = dataset,
        dataset_text_field = "text",
        max_seq_length = max_seq_length,
        dataset_num_proc = 2,
        packing = False,
        args = TrainingArguments(
            per_device_train_batch_size = 2,
            gradient_accumulation_steps = 4,
            warmup_steps = 10,
            max_steps = 100,
            learning_rate = 2e-4,
            fp16 = not torch.cuda.is_bf16_supported(),
            bf16 = torch.cuda.is_bf16_supported(),
            logging_steps = 10,
            optim = "adamw_8bit",
            weight_decay = 0.01,
            lr_scheduler_type = "cosine",
            seed = 3407,
            output_dir = "outputs",
            report_to = "none", # Set to "wandb" if Kaggle env has WANDB_API_KEY
        ),
    )

    trainer.train()

    logging.info("Exporting fine-tuned model to GGUF format (Q4_K_M)...")
    # Export locally or on Kaggle output dir
    out_name = "provably-aligned-gemma-q4_k_m"
    model.save_pretrained_gguf(out_name, tokenizer, quantization_method="q4_k_m")
    
    logging.info("Process completed successfully. Model exported.")

if __name__ == "__main__":
    main()
