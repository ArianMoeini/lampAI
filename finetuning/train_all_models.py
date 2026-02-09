"""
LAMP Fine-Tuning — Full fine-tune all 3 models on RunPod H200
Trains Llama 3.2 3B, Gemma 3 4B, and Phi-4 Mini sequentially.
Exports each to GGUF Q4_K_M for Ollama on Pi 5.

Usage: python train_all_models.py
"""

import json
import os
import time
import gc
import torch
from datasets import Dataset

# ─── Model configs ───────────────────────────────────────────────────────────

MODELS = {
    "llama": {
        "model_name": "unsloth/Llama-3.2-3B-Instruct",
        "output_name": "lamp-llama-3b",
        "max_seq_length": 4096,
        "stop_token": "<|eot_id|>",
    },
    "gemma": {
        "model_name": "unsloth/gemma-3-4b-it",
        "output_name": "lamp-gemma-4b",
        "max_seq_length": 4096,
        "stop_token": "<end_of_turn>",
    },
    "phi": {
        "model_name": "unsloth/Phi-4-mini-instruct",
        "output_name": "lamp-phi-mini",
        "max_seq_length": 4096,
        "stop_token": "<|endoftext|>",
    },
}

# ─── Training hyperparams ────────────────────────────────────────────────────

TRAIN_CONFIG = {
    "per_device_train_batch_size": 8,
    "gradient_accumulation_steps": 2,  # effective batch = 16
    "warmup_ratio": 0.05,
    "num_train_epochs": 3,
    "learning_rate": 2e-4,
    "logging_steps": 10,
    "optim": "adamw_8bit",
    "weight_decay": 0.01,
    "lr_scheduler_type": "cosine",
    "seed": 42,
    "save_strategy": "epoch",
    "eval_strategy": "epoch",
    "report_to": "none",
}

# LoRA config — high rank on bf16 base for near full-fine-tune quality
LORA_CONFIG = {
    "r": 128,
    "lora_alpha": 256,
    "lora_dropout": 0.05,
    "target_modules": [
        "q_proj", "k_proj", "v_proj", "o_proj",
        "gate_proj", "up_proj", "down_proj",
    ],
    "bias": "none",
    "use_gradient_checkpointing": "unsloth",
    "random_state": 42,
}

# ─── Data loading ────────────────────────────────────────────────────────────

def read_jsonl(path):
    with open(path) as f:
        return [json.loads(line) for line in f]


def load_data():
    train = Dataset.from_list(read_jsonl("data/train.jsonl"))
    val = Dataset.from_list(read_jsonl("data/val.jsonl"))
    print(f"Dataset: {len(train)} train, {len(val)} val")
    return train, val


# ─── Quick eval ──────────────────────────────────────────────────────────────

TEST_PROMPTS = [
    "warm and cozy",
    "show a heart",
    "countdown from 5",
    "party mode",
    "thunderstorm",
]


def quick_eval(model, tokenizer, system_prompt):
    from unsloth import FastLanguageModel
    FastLanguageModel.for_inference(model)

    valid = 0
    for prompt in TEST_PROMPTS:
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Create a light program for this request.\n\nRequest: {prompt}\n\nRespond with ONLY a JSON program. No text."},
        ]
        inputs = tokenizer.apply_chat_template(
            messages, tokenize=True, add_generation_prompt=True, return_tensors="pt"
        ).to("cuda")

        outputs = model.generate(
            input_ids=inputs, max_new_tokens=2048,
            temperature=0.3, do_sample=True,
        )
        response = tokenizer.decode(outputs[0][inputs.shape[1]:], skip_special_tokens=True)

        try:
            json.loads(response)
            valid += 1
            status = "VALID"
        except Exception:
            status = "INVALID"

        print(f"  [{status}] {prompt}: {response[:120]}...")

    print(f"  Score: {valid}/{len(TEST_PROMPTS)}")
    return valid


# ─── Train one model ─────────────────────────────────────────────────────────

def train_model(key, config):
    from unsloth import FastLanguageModel
    from trl import SFTTrainer, SFTConfig

    print(f"\n{'='*60}")
    print(f"  TRAINING: {config['model_name']}")
    print(f"{'='*60}\n")

    start = time.time()

    # Load model in bf16 (NOT 4-bit) — full precision for H200
    model, tokenizer = FastLanguageModel.from_pretrained(
        model_name=config["model_name"],
        max_seq_length=config["max_seq_length"],
        dtype=None,
        load_in_4bit=False,
    )

    # Apply LoRA with high rank (r=128) for near full-fine-tune quality
    model = FastLanguageModel.get_peft_model(model, **LORA_CONFIG)

    trainable = sum(p.numel() for p in model.parameters() if p.requires_grad)
    total = sum(p.numel() for p in model.parameters())
    print(f"Trainable: {trainable:,} / {total:,} ({trainable/total*100:.1f}%)")

    # Load & format data
    train_data, val_data = load_data()

    def fmt(examples):
        return {
            "text": [
                tokenizer.apply_chat_template(c, tokenize=False, add_generation_prompt=False)
                for c in examples["conversations"]
            ]
        }

    train_data = train_data.map(fmt, batched=True)
    val_data = val_data.map(fmt, batched=True)

    # Train
    output_dir = f"outputs/{config['output_name']}"
    args = SFTConfig(
        output_dir=output_dir,
        bf16=True,  # H200 supports bf16 natively
        fp16=False,
        **TRAIN_CONFIG,
    )

    trainer = SFTTrainer(
        model=model,
        tokenizer=tokenizer,
        train_dataset=train_data,
        eval_dataset=val_data,
        args=args,
        dataset_text_field="text",
        max_seq_length=config["max_seq_length"],
        packing=False,
    )

    trainer.train()

    elapsed = time.time() - start
    print(f"\nTraining done in {elapsed/60:.1f} minutes")

    # Quick eval
    print("\n--- Quick Eval ---")
    system_prompt = read_jsonl("data/train.jsonl")[0]["conversations"][0]["content"]
    quick_eval(model, tokenizer, system_prompt)

    # Export GGUF Q8_0 (best quality)
    print(f"\nExporting GGUF Q8_0...")
    os.makedirs("exports", exist_ok=True)
    model.save_pretrained_gguf(
        f"exports/{config['output_name']}",
        tokenizer,
        quantization_method="q8_0",
    )

    # Create Ollama Modelfile
    modelfile = f"""FROM ./{config['output_name']}-unsloth.Q8_0.gguf
PARAMETER temperature 0.3
PARAMETER num_predict 4096
PARAMETER stop {config['stop_token']}
"""
    with open(f"exports/Modelfile.{config['output_name']}", "w") as f:
        f.write(modelfile)

    print(f"Saved: exports/{config['output_name']}*.gguf + Modelfile")

    # Free GPU memory before next model
    del model, tokenizer, trainer
    gc.collect()
    torch.cuda.empty_cache()

    return elapsed


# ─── Main ────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("LAMP Fine-Tuning — H200 Full Run")
    print(f"Models: {', '.join(MODELS.keys())}")
    print(f"Training: bf16 base + LoRA r=128 (near full-fine-tune)")
    print(f"GPU: {torch.cuda.get_device_name(0)}")
    print(f"VRAM: {torch.cuda.get_device_properties(0).total_mem / 1e9:.0f} GB")
    print()

    total_start = time.time()
    results = {}

    for key, config in MODELS.items():
        elapsed = train_model(key, config)
        results[key] = elapsed

    total = time.time() - total_start

    print(f"\n{'='*60}")
    print(f"  ALL DONE — Total: {total/60:.1f} minutes")
    print(f"{'='*60}")
    for key, elapsed in results.items():
        print(f"  {key}: {elapsed/60:.1f} min")

    print(f"\nExported files:")
    for f in sorted(os.listdir("exports")):
        path = os.path.join("exports", f)
        size = os.path.getsize(path) / 1e9
        if size > 0.01:
            print(f"  {f} ({size:.1f} GB)")
        else:
            print(f"  {f}")

    print(f"\nNext steps:")
    print(f"  1. Download GGUF files from exports/")
    print(f"  2. On Pi 5: ollama create lamp-llama-3b -f Modelfile.lamp-llama-3b")
    print(f"  3. Test: ollama run lamp-llama-3b 'warm and cozy'")
    print(f"  4. Run benchmark: python 07_eval_finetuned.py")
