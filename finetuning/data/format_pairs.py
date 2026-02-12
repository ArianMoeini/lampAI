#!/usr/bin/env python3
"""
Formatter that takes hand-crafted prompt-response pairs and wraps them
in ChatML format with the system prompt. Does ZERO generation - purely mechanical formatting.
"""
import json
import sys

# Read system prompt from prompts.py
sys.path.insert(0, '/Users/arianmoeini/Desktop/PROJECTS/Above/lamp/llm')
from prompts import LAMP_PROGRAM_SYSTEM_PROMPT

USER_TEMPLATE = "Create a light program for this request.\n\nRequest: {prompt}\n\nRespond with ONLY a JSON program. No text."

def format_pairs(input_file, output_file):
    count = 0
    with open(input_file, 'r') as fin, open(output_file, 'w') as fout:
        for line in fin:
            line = line.strip()
            if not line:
                continue
            pair = json.loads(line)
            prompt = pair["p"]
            response = pair["r"]

            # If response is a dict, stringify it
            if isinstance(response, dict):
                response_str = json.dumps(response, separators=(',', ':'))
            else:
                response_str = response

            conversation = {
                "conversations": [
                    {"role": "system", "content": LAMP_PROGRAM_SYSTEM_PROMPT},
                    {"role": "user", "content": USER_TEMPLATE.format(prompt=prompt)},
                    {"role": "assistant", "content": response_str}
                ]
            }
            fout.write(json.dumps(conversation, ensure_ascii=False) + '\n')
            count += 1
    print(f"Formatted {count} pairs to {output_file}")

if __name__ == "__main__":
    format_pairs(
        '/Users/arianmoeini/Desktop/PROJECTS/Above/lamp/finetuning/data/pairs_agent3.jsonl',
        '/Users/arianmoeini/Desktop/PROJECTS/Above/lamp/finetuning/data/responses_v2_agent3.jsonl'
    )
