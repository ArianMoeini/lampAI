#!/usr/bin/env python3
"""
Step 4: Format validated data into ChatML conversation format for fine-tuning.
Creates stratified train/val split and optionally includes the 21 Opus
benchmark reference programs.

Usage:
    python3 04_format_training_data.py
    python3 04_format_training_data.py --val-ratio 0.1 --include-opus
"""

import json
import os
import sys
import random
import argparse

# Import the system prompt from the lamp codebase
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "llm"))
try:
    from prompts import LAMP_PROGRAM_SYSTEM_PROMPT
except ImportError:
    # Fallback: read it directly
    LAMP_PROGRAM_SYSTEM_PROMPT = None

# User message template (matches what the lamp controller sends)
USER_TEMPLATE = "Create a light program for this request.\n\nRequest: {input}\n\nRespond with ONLY a JSON program. No text."


def load_opus_benchmarks():
    """Load the 21 Opus benchmark programs as additional training data."""
    opus_path = os.path.join(os.path.dirname(__file__), "..", "llm", "benchmark_opus.py")
    if not os.path.exists(opus_path):
        print("  Warning: benchmark_opus.py not found, skipping Opus examples")
        return []

    # Parse the TEST_CASES from the file
    import importlib.util
    spec = importlib.util.spec_from_file_location("benchmark_opus", opus_path)
    mod = importlib.util.module_from_spec(spec)

    # We need to handle the import without running __main__
    try:
        spec.loader.exec_module(mod)
        test_cases = getattr(mod, "TEST_CASES", [])
    except Exception as e:
        print(f"  Warning: could not load benchmark_opus.py: {e}")
        return []

    examples = []
    for tc in test_cases:
        prompt = tc.get("prompt", "")
        program = tc.get("program", {})
        if prompt and program:
            response = json.dumps(program, separators=(',', ':'))
            examples.append({
                "prompt": prompt,
                "category": tc.get("category", "opus_benchmark"),
                "response": response,
            })

    return examples


def format_conversation(system_prompt, prompt, response):
    """Format as a ChatML conversation."""
    return {
        "conversations": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": USER_TEMPLATE.format(input=prompt)},
            {"role": "assistant", "content": response},
        ]
    }


def main():
    parser = argparse.ArgumentParser(description="Format data for fine-tuning")
    parser.add_argument("--val-ratio", type=float, default=0.1, help="Validation split ratio")
    parser.add_argument("--include-opus", action="store_true", default=True, help="Include Opus benchmark examples")
    parser.add_argument("--no-opus", action="store_true", help="Exclude Opus benchmark examples")
    parser.add_argument("--seed", type=int, default=42, help="Random seed")
    parser.add_argument("--input", default=None, help="Input validated file")
    args = parser.parse_args()

    rng = random.Random(args.seed)
    data_dir = os.path.join(os.path.dirname(__file__), "data")

    # Load system prompt
    system_prompt = LAMP_PROGRAM_SYSTEM_PROMPT
    if not system_prompt:
        print("  ERROR: Could not load LAMP_PROGRAM_SYSTEM_PROMPT")
        sys.exit(1)

    print(f"  System prompt loaded: {len(system_prompt)} chars")

    # Load validated data
    input_path = args.input or os.path.join(data_dir, "validated.jsonl")
    items = []
    with open(input_path) as f:
        for line in f:
            items.append(json.loads(line.strip()))
    print(f"  Loaded {len(items)} validated examples")

    # Optionally add Opus benchmark programs
    if args.include_opus and not args.no_opus:
        opus = load_opus_benchmarks()
        if opus:
            items.extend(opus)
            print(f"  Added {len(opus)} Opus benchmark examples")

    # Compact JSON responses (remove whitespace)
    for item in items:
        try:
            parsed = json.loads(item["response"])
            item["response"] = json.dumps(parsed, separators=(',', ':'))
        except json.JSONDecodeError:
            pass  # Keep original

    # Format into conversations
    conversations = []
    for item in items:
        conv = format_conversation(system_prompt, item["prompt"], item["response"])
        conv["_category"] = item.get("category", "unknown")
        conversations.append(conv)

    # Compute token estimates
    total_tokens = 0
    response_lengths = []
    for conv in conversations:
        # Rough estimate: 1 token ≈ 4 chars
        total_chars = sum(len(m["content"]) for m in conv["conversations"])
        total_tokens += total_chars // 4
        response_lengths.append(len(conv["conversations"][2]["content"]))

    # Stratified train/val split
    by_cat = {}
    for conv in conversations:
        cat = conv["_category"]
        if cat not in by_cat:
            by_cat[cat] = []
        by_cat[cat].append(conv)

    train_set = []
    val_set = []

    for cat, cat_convs in by_cat.items():
        rng.shuffle(cat_convs)
        n_val = max(1, int(len(cat_convs) * args.val_ratio))
        val_set.extend(cat_convs[:n_val])
        train_set.extend(cat_convs[n_val:])

    rng.shuffle(train_set)
    rng.shuffle(val_set)

    # Remove internal metadata before saving
    for conv in train_set + val_set:
        conv.pop("_category", None)

    # Save
    train_path = os.path.join(data_dir, "train.jsonl")
    val_path = os.path.join(data_dir, "val.jsonl")

    with open(train_path, "w") as f:
        for conv in train_set:
            f.write(json.dumps(conv) + "\n")

    with open(val_path, "w") as f:
        for conv in val_set:
            f.write(json.dumps(conv) + "\n")

    # Print summary
    print(f"\n{'='*60}")
    print(f"  TRAINING DATA FORMATTED")
    print(f"{'='*60}")
    print(f"  Total examples:     {len(conversations)}")
    print(f"  Training set:       {len(train_set)}")
    print(f"  Validation set:     {len(val_set)}")
    print(f"  Val ratio:          {len(val_set)/len(conversations)*100:.1f}%")
    print(f"\n  Token estimates (rough):")
    print(f"    Total tokens:     ~{total_tokens:,}")
    print(f"    Avg per example:  ~{total_tokens//len(conversations):,}")
    print(f"    System prompt:    ~{len(system_prompt)//4:,} tokens")
    print(f"\n  Response length stats:")
    print(f"    Min:   {min(response_lengths):,} chars")
    print(f"    Max:   {max(response_lengths):,} chars")
    print(f"    Mean:  {sum(response_lengths)//len(response_lengths):,} chars")
    print(f"    Median:{sorted(response_lengths)[len(response_lengths)//2]:,} chars")

    # Category distribution in train set
    train_cats = {}
    for conv in train_set:
        # Re-detect from response content if needed
        train_cats["train"] = train_cats.get("train", 0) + 1

    print(f"\n  Saved:")
    print(f"    {train_path}")
    print(f"    {val_path}")


if __name__ == "__main__":
    main()
