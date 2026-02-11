#!/usr/bin/env python3
"""
Merge all v2 response files, deduplicate, validate, and create final training data.
Combines with existing v1 data to produce the full 7,500-example dataset.
"""
import json
import os
import re
import random
import sys

DATA = os.path.join(os.path.dirname(__file__), "data")

# Import system prompt
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "llm"))
from prompts import LAMP_PROGRAM_SYSTEM_PROMPT

USER_TEMPLATE = "Create a light program for this request.\n\nRequest: {input}\n\nRespond with ONLY a JSON program. No text."

VALID_PATTERN_NAMES = {"solid", "gradient", "breathing", "wave", "rainbow", "pulse", "sparkle"}
VALID_COMMAND_TYPES = {"pattern", "render", "stop"}
VALID_ELEMENT_TYPES = {"fill", "text", "pixel", "rect", "line"}
HEX_RE = re.compile(r'^#([0-9a-fA-F]{3}|[0-9a-fA-F]{6}|[0-9a-fA-F]{8})$')


def validate_program(data):
    """Validate a lamp program JSON structure."""
    if not isinstance(data, dict):
        return False, "not a dict"
    if "program" not in data:
        if "type" in data:
            return True, "raw_command"
        return False, "no program key"

    prog = data["program"]
    if not isinstance(prog, dict):
        return False, "program not dict"
    if "name" not in prog:
        return False, "no name"
    if "steps" not in prog or not prog["steps"]:
        return False, "no steps"

    for step in prog["steps"]:
        if "id" not in step or "command" not in step:
            return False, "step missing id/command"
        cmd = step["command"]
        ctype = cmd.get("type")
        if ctype not in VALID_COMMAND_TYPES:
            return False, f"bad command type: {ctype}"
        if ctype == "pattern":
            if cmd.get("name") not in VALID_PATTERN_NAMES:
                return False, f"bad pattern: {cmd.get('name')}"
            if "params" not in cmd:
                return False, "pattern missing params"
        if ctype == "render":
            elements = cmd.get("elements", [])
            if not elements:
                return False, "render no elements"
            for elem in elements:
                if elem.get("type") not in VALID_ELEMENT_TYPES:
                    return False, f"bad element: {elem.get('type')}"

    return True, "ok"


def load_chunk_responses(filepath):
    """Load {"prompt": "...", "response": "..."} format."""
    pairs = []
    errors = 0
    with open(filepath) as f:
        for i, line in enumerate(f):
            line = line.strip()
            if not line:
                continue
            try:
                item = json.loads(line)
                prompt = item["prompt"]
                resp_str = item["response"]

                # Parse the response to validate
                resp_data = json.loads(resp_str) if isinstance(resp_str, str) else resp_str
                valid, reason = validate_program(resp_data)

                if valid:
                    # Re-compact
                    compact = json.dumps(resp_data, separators=(',', ':'))
                    pairs.append((prompt, compact))
                else:
                    errors += 1
            except (json.JSONDecodeError, KeyError) as e:
                errors += 1
    return pairs, errors


def load_pairs_format(filepath):
    """Load {"p": "...", "r": {...}} format from pairs_agent3.jsonl."""
    pairs = []
    errors = 0
    with open(filepath) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                item = json.loads(line)
                prompt = item["p"]
                resp_data = item["r"]
                valid, reason = validate_program(resp_data)
                if valid:
                    compact = json.dumps(resp_data, separators=(',', ':'))
                    pairs.append((prompt, compact))
                else:
                    errors += 1
            except (json.JSONDecodeError, KeyError):
                errors += 1
    return pairs, errors


def format_training_example(prompt, response):
    """Format as training conversation."""
    return {
        "conversations": [
            {"role": "system", "content": LAMP_PROGRAM_SYSTEM_PROMPT},
            {"role": "user", "content": USER_TEMPLATE.format(input=prompt)},
            {"role": "assistant", "content": response}
        ]
    }


def main():
    print("=" * 60)
    print("  MERGING AND FORMATTING TRAINING DATA")
    print("=" * 60)

    # --- Load all v2 response files ---
    all_pairs = []  # (prompt, response_str)
    total_errors = 0

    # Chunk response files
    for i in range(1, 6):
        path = os.path.join(DATA, f"responses_chunk_{i}.jsonl")
        if os.path.exists(path):
            pairs, errs = load_chunk_responses(path)
            all_pairs.extend(pairs)
            total_errors += errs
            print(f"  responses_chunk_{i}.jsonl: {len(pairs)} valid, {errs} errors")

    # Previous agent response files
    for fname in ["responses_v2_agent4.jsonl", "responses_v2_agent5.jsonl"]:
        path = os.path.join(DATA, fname)
        if os.path.exists(path):
            pairs, errs = load_chunk_responses(path)
            all_pairs.extend(pairs)
            total_errors += errs
            print(f"  {fname}: {len(pairs)} valid, {errs} errors")

    # pairs_agent3 uses different format
    path = os.path.join(DATA, "pairs_agent3.jsonl")
    if os.path.exists(path):
        pairs, errs = load_pairs_format(path)
        all_pairs.extend(pairs)
        total_errors += errs
        print(f"  pairs_agent3.jsonl: {len(pairs)} valid, {errs} errors")

    print(f"\n  Total v2 pairs before dedup: {len(all_pairs)}")
    print(f"  Total validation errors: {total_errors}")

    # --- Deduplicate by prompt ---
    seen = {}
    for prompt, response in all_pairs:
        prompt_lower = prompt.strip().lower()
        if prompt_lower not in seen:
            seen[prompt_lower] = (prompt, response)

    v2_pairs = list(seen.values())
    print(f"  After dedup: {len(v2_pairs)} unique v2 pairs")

    # --- Load existing v1 training data ---
    v1_train_path = os.path.join(DATA, "train.jsonl")
    v1_val_path = os.path.join(DATA, "val.jsonl")
    v1_examples = []
    v1_prompts = set()

    for path in [v1_train_path, v1_val_path]:
        if os.path.exists(path):
            with open(path) as f:
                for line in f:
                    item = json.loads(line.strip())
                    v1_examples.append(item)
                    # Extract prompt from user message
                    for conv in item["conversations"]:
                        if conv["role"] == "user":
                            # Extract the actual request from the template
                            text = conv["content"]
                            if "Request: " in text:
                                prompt = text.split("Request: ")[1].split("\n")[0]
                                v1_prompts.add(prompt.strip().lower())

    print(f"  Existing v1 examples: {len(v1_examples)}")

    # --- Remove v2 pairs that overlap with v1 ---
    v2_filtered = [(p, r) for p, r in v2_pairs if p.strip().lower() not in v1_prompts]
    print(f"  v2 after removing v1 overlaps: {len(v2_filtered)}")

    # --- Format v2 as training examples ---
    v2_examples = [format_training_example(p, r) for p, r in v2_filtered]

    # --- Combine all ---
    all_examples = v1_examples + v2_examples
    print(f"\n  Combined total: {len(all_examples)}")

    # --- Shuffle and split 90/10 ---
    random.seed(42)
    random.shuffle(all_examples)

    split_idx = int(len(all_examples) * 0.9)
    train = all_examples[:split_idx]
    val = all_examples[split_idx:]

    # --- Save ---
    train_out = os.path.join(DATA, "train_v2.jsonl")
    val_out = os.path.join(DATA, "val_v2.jsonl")

    with open(train_out, "w") as f:
        for ex in train:
            f.write(json.dumps(ex) + "\n")

    with open(val_out, "w") as f:
        for ex in val:
            f.write(json.dumps(ex) + "\n")

    print(f"\n{'=' * 60}")
    print(f"  FINAL OUTPUT")
    print(f"{'=' * 60}")
    print(f"  Training set:   {len(train)} examples -> {train_out}")
    print(f"  Validation set: {len(val)} examples -> {val_out}")
    print(f"  Total:          {len(all_examples)} examples")
    print(f"{'=' * 60}")

    # --- Category distribution of v2 ---
    # Quick check: how many of each command type in v2
    pattern_count = 0
    render_count = 0
    multi_step_count = 0
    for p, r in v2_filtered:
        try:
            data = json.loads(r)
            steps = data.get("program", {}).get("steps", [])
            if len(steps) > 1:
                multi_step_count += 1
            elif steps:
                cmd_type = steps[0].get("command", {}).get("type")
                if cmd_type == "render":
                    render_count += 1
                else:
                    pattern_count += 1
        except:
            pass

    print(f"\n  v2 command type breakdown:")
    print(f"    Pattern (single):    {pattern_count}")
    print(f"    Render (single):     {render_count}")
    print(f"    Multi-step:          {multi_step_count}")


if __name__ == "__main__":
    main()
