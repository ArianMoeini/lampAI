#!/usr/bin/env python3
"""Identify prompts that still need responses and split into chunks for agents."""
import json
import os

DATA = os.path.join(os.path.dirname(__file__), "data")

# Load all prompts
all_prompts = []
with open(os.path.join(DATA, "prompts_v2.jsonl")) as f:
    for line in f:
        all_prompts.append(json.loads(line.strip()))

print(f"Total v2 prompts: {len(all_prompts)}")

# Collect already-completed prompts
done_prompts = set()

# responses_v2_agent4.jsonl and agent5 use {"prompt": "...", "response": "..."}
for fname in ["responses_v2_agent4.jsonl", "responses_v2_agent5.jsonl"]:
    path = os.path.join(DATA, fname)
    if os.path.exists(path):
        with open(path) as f:
            for line in f:
                item = json.loads(line.strip())
                done_prompts.add(item["prompt"])
        print(f"  {fname}: {sum(1 for _ in open(path))} entries")

# pairs_agent3.jsonl uses {"p": "...", "r": {...}}
path = os.path.join(DATA, "pairs_agent3.jsonl")
if os.path.exists(path):
    with open(path) as f:
        for line in f:
            item = json.loads(line.strip())
            done_prompts.add(item["p"])
    print(f"  pairs_agent3.jsonl: {sum(1 for _ in open(path))} entries")

print(f"\nAlready completed: {len(done_prompts)}")

# Filter remaining
remaining = [p for p in all_prompts if p["prompt"] not in done_prompts]
print(f"Remaining to generate: {len(remaining)}")

# Category breakdown of remaining
cats = {}
for p in remaining:
    cats[p["category"]] = cats.get(p["category"], 0) + 1
print("\nRemaining by category:")
for cat, cnt in sorted(cats.items(), key=lambda x: -x[1]):
    print(f"  {cat:20s}: {cnt}")

# Split into 5 chunks
chunk_size = len(remaining) // 5
chunks = []
for i in range(5):
    start = i * chunk_size
    end = start + chunk_size if i < 4 else len(remaining)
    chunks.append(remaining[start:end])

for i, chunk in enumerate(chunks):
    out_path = os.path.join(DATA, f"remaining_chunk_{i+1}.jsonl")
    with open(out_path, "w") as f:
        for item in chunk:
            f.write(json.dumps(item) + "\n")
    # Category breakdown per chunk
    chunk_cats = {}
    for p in chunk:
        chunk_cats[p["category"]] = chunk_cats.get(p["category"], 0) + 1
    print(f"\nChunk {i+1}: {len(chunk)} prompts -> {out_path}")
    for cat, cnt in sorted(chunk_cats.items(), key=lambda x: -x[1]):
        print(f"  {cat:20s}: {cnt}")
