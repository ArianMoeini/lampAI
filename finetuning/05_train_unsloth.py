#!/usr/bin/env python3
"""
Step 5: Fine-tune a small LLM on the LAMP dataset using Unsloth.

Supports Llama 3.2 3B, Gemma 3 4B, and Phi-4 Mini.
Uses QLoRA (4-bit quantization) for memory-efficient training.

Usage:
    python3 05_train_unsloth.py --model llama
    python3 05_train_unsloth.py --model gemma
    python3 05_train_unsloth.py --model phi
    python3 05_train_unsloth.py --model llama --epochs 5 --lr 1e-4

Requirements:
    pip install unsloth[colab]   # On Google Colab
    pip install unsloth[cu121]   # On CUDA 12.1
    pip install trl datasets
"""

import json
import os
import argparse

# ══════════════════════════════════════════════════════════════════════════
# MODEL CONFIGS
# ══════════════════════════════════════════════════════════════════════════

MODEL_CONFIGS = {
    "llama": {
        "model_name": "unsloth/Llama-3.2-3B-Instruct",
        "output_name": "lamp-llama-3b",
        "max_seq_length": 4096,
        "chat_template": "llama-3.1",
    },
    "gemma": {
        "model_name": "unsloth/gemma-3-4b-it",
        "output_name": "lamp-gemma-4b",
        "max_seq_length": 4096,
        "chat_template": "gemma-3",
    },
    "phi": {
        "model_name": "unsloth/Phi-4-mini-instruct",
        "output_name": "lamp-phi-mini",
        "max_seq_length": 4096,
        "chat_template": "phi-4",
    },
}

# LoRA target modules (same for all architectures)
LORA_TARGET_MODULES = [
    "q_proj", "k_proj", "v_proj", "o_proj",
    "gate_proj", "up_proj", "down_proj",
]


def load_dataset(train_path, val_path):
    """Load JSONL training data into HuggingFace Dataset format."""
    from datasets import Dataset

    def read_jsonl(path):
        items = []
        with open(path) as f:
            for line in f:
                items.append(json.loads(line.strip()))
        return items

    train_data = read_jsonl(train_path)
    val_data = read_jsonl(val_path)

    return Dataset.from_list(train_data), Dataset.from_list(val_data)


def format_conversations(examples, tokenizer):
    """Apply the chat template to format conversations."""
    texts = []
    for convos in examples["conversations"]:
        text = tokenizer.apply_chat_template(
            convos,
            tokenize=False,
            add_generation_prompt=False,
        )
        texts.append(text)
    return {"text": texts}


def main():
    parser = argparse.ArgumentParser(description="Fine-tune LLM with Unsloth")
    parser.add_argument("--model", choices=["llama", "gemma", "phi"], default="llama",
                        help="Model to fine-tune")
    parser.add_argument("--epochs", type=int, default=3, help="Training epochs")
    parser.add_argument("--lr", type=float, default=2e-4, help="Learning rate")
    parser.add_argument("--batch-size", type=int, default=4, help="Per-device batch size")
    parser.add_argument("--grad-accum", type=int, default=4, help="Gradient accumulation steps")
    parser.add_argument("--lora-rank", type=int, default=32, help="LoRA rank")
    parser.add_argument("--lora-alpha", type=int, default=64, help="LoRA alpha")
    parser.add_argument("--data-dir", default=None, help="Data directory")
    parser.add_argument("--output-dir", default=None, help="Output directory")
    parser.add_argument("--export-gguf", action="store_true", help="Export to GGUF after training")
    parser.add_argument("--gguf-quant", default="q4_k_m", help="GGUF quantization method")
    args = parser.parse_args()

    config = MODEL_CONFIGS[args.model]
    data_dir = args.data_dir or os.path.join(os.path.dirname(__file__), "data")
    output_dir = args.output_dir or os.path.join(os.path.dirname(__file__), "outputs", config["output_name"])

    print(f"{'='*60}")
    print(f"  LAMP Fine-Tuning with Unsloth")
    print(f"{'='*60}")
    print(f"  Model:      {config['model_name']}")
    print(f"  Output:     {output_dir}")
    print(f"  LoRA:       rank={args.lora_rank}, alpha={args.lora_alpha}")
    print(f"  Training:   epochs={args.epochs}, lr={args.lr}")
    print(f"  Batch:      {args.batch_size} x {args.grad_accum} = {args.batch_size * args.grad_accum} effective")
    print(f"{'='*60}\n")

    # ── Step 1: Load model ───────────────────────────────────────────
    print("  [1/5] Loading model...")
    from unsloth import FastLanguageModel

    model, tokenizer = FastLanguageModel.from_pretrained(
        model_name=config["model_name"],
        max_seq_length=config["max_seq_length"],
        dtype=None,  # Auto-detect (float16 on T4, bfloat16 on A100)
        load_in_4bit=True,
    )

    # ── Step 2: Configure LoRA ───────────────────────────────────────
    print("  [2/5] Configuring LoRA adapters...")
    model = FastLanguageModel.get_peft_model(
        model,
        r=args.lora_rank,
        target_modules=LORA_TARGET_MODULES,
        lora_alpha=args.lora_alpha,
        lora_dropout=0.05,
        bias="none",
        use_gradient_checkpointing="unsloth",
        random_state=42,
    )

    # Print trainable params
    trainable = sum(p.numel() for p in model.parameters() if p.requires_grad)
    total = sum(p.numel() for p in model.parameters())
    print(f"         Trainable: {trainable:,} / {total:,} ({trainable/total*100:.2f}%)")

    # ── Step 3: Load and format dataset ──────────────────────────────
    print("  [3/5] Loading dataset...")
    train_path = os.path.join(data_dir, "train.jsonl")
    val_path = os.path.join(data_dir, "val.jsonl")

    train_dataset, val_dataset = load_dataset(train_path, val_path)
    print(f"         Train: {len(train_dataset)} examples")
    print(f"         Val:   {len(val_dataset)} examples")

    # Apply chat template
    print("         Formatting with chat template...")
    train_dataset = train_dataset.map(
        lambda ex: format_conversations(ex, tokenizer),
        batched=True,
    )
    val_dataset = val_dataset.map(
        lambda ex: format_conversations(ex, tokenizer),
        batched=True,
    )

    # ── Step 4: Train ────────────────────────────────────────────────
    print("  [4/5] Starting training...")
    from trl import SFTTrainer, SFTConfig

    training_args = SFTConfig(
        per_device_train_batch_size=args.batch_size,
        gradient_accumulation_steps=args.grad_accum,
        warmup_ratio=0.05,
        num_train_epochs=args.epochs,
        learning_rate=args.lr,
        fp16=True,  # Will auto-switch to bf16 on supported hardware
        logging_steps=10,
        optim="adamw_8bit",
        weight_decay=0.01,
        lr_scheduler_type="cosine",
        seed=42,
        output_dir=output_dir,
        save_strategy="epoch",
        eval_strategy="epoch",
        report_to="none",  # Set to "wandb" if you want W&B logging
    )

    trainer = SFTTrainer(
        model=model,
        tokenizer=tokenizer,
        train_dataset=train_dataset,
        eval_dataset=val_dataset,
        args=training_args,
        dataset_text_field="text",
        max_seq_length=config["max_seq_length"],
        packing=False,
    )

    trainer.train()

    # ── Step 5: Save ─────────────────────────────────────────────────
    print("  [5/5] Saving model...")
    model.save_pretrained(output_dir)
    tokenizer.save_pretrained(output_dir)
    print(f"         Saved to: {output_dir}")

    # ── Optional: Export to GGUF ─────────────────────────────────────
    if args.export_gguf:
        print(f"\n  Exporting to GGUF ({args.gguf_quant})...")
        export_dir = os.path.join(os.path.dirname(__file__), "exports")
        os.makedirs(export_dir, exist_ok=True)

        gguf_path = os.path.join(export_dir, config["output_name"])
        model.save_pretrained_gguf(
            gguf_path,
            tokenizer,
            quantization_method=args.gguf_quant,
        )
        print(f"         GGUF saved to: {gguf_path}")

        # Generate Ollama Modelfile
        modelfile_path = os.path.join(export_dir, f"Modelfile.{config['output_name']}")
        gguf_filename = f"{config['output_name']}-unsloth.{args.gguf_quant.upper()}.gguf"

        with open(modelfile_path, "w") as f:
            f.write(f"FROM ./{gguf_filename}\n")
            f.write(f"PARAMETER temperature 0.3\n")
            f.write(f"PARAMETER num_predict 4096\n")
            f.write(f"PARAMETER stop <|eot_id|>\n")
            f.write(f"PARAMETER stop <end_of_turn>\n")

        print(f"         Modelfile saved to: {modelfile_path}")
        print(f"\n  To use with Ollama:")
        print(f"    cd {export_dir}")
        print(f"    ollama create {config['output_name']} -f Modelfile.{config['output_name']}")

    print(f"\n  Training complete!")
    print(f"  Model: {config['output_name']}")
    print(f"  Output: {output_dir}")


if __name__ == "__main__":
    main()
