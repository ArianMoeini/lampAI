#!/usr/bin/env python3
"""Extract prompts that still need responses from each chunk."""
import json
import os

DATA = os.path.join(os.path.dirname(__file__), "data")

for chunk_id in [1, 2, 4, 5]:
    chunk_file = os.path.join(DATA, f"remaining_chunk_{chunk_id}.jsonl")
    resp_file = os.path.join(DATA, f"responses_chunk_{chunk_id}.jsonl")

    # Load all prompts for this chunk
    all_prompts = []
    with open(chunk_file) as f:
        for line in f:
            all_prompts.append(json.loads(line.strip()))

    # Load completed prompts
    done = set()
    if os.path.exists(resp_file):
        with open(resp_file) as f:
            for line in f:
                try:
                    item = json.loads(line.strip())
                    done.add(item["prompt"])
                except:
                    pass

    remaining = [p for p in all_prompts if p["prompt"] not in done]

    if remaining:
        out = os.path.join(DATA, f"todo_chunk_{chunk_id}.jsonl")
        with open(out, "w") as f:
            for p in remaining:
                f.write(json.dumps(p) + "\n")
        print(f"Chunk {chunk_id}: {len(done)} done, {len(remaining)} remaining -> {out}")
    else:
        print(f"Chunk {chunk_id}: ALL DONE ({len(done)})")
