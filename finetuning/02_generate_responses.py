#!/usr/bin/env python3
"""
Step 2: Generate high-quality JSON lamp program responses using the Anthropic API.

Sends each prompt to Claude Opus 4.6 with the exact system prompt from
llm/prompts.py, so every training example has a genuine Opus-generated response
with full creativity and variation.

Usage:
    # Set your API key first:
    export ANTHROPIC_API_KEY=sk-ant-...

    python3 02_generate_responses.py                      # Generate all
    python3 02_generate_responses.py --resume              # Resume from last checkpoint
    python3 02_generate_responses.py --batch-size 50       # Process in batches of 50
    python3 02_generate_responses.py --model claude-sonnet-4-5-20250929  # Use Sonnet (cheaper)

Requirements:
    pip install anthropic
"""

import json
import os
import re
import sys
import time
import argparse

try:
    import anthropic
    HAS_ANTHROPIC = True
except ImportError:
    HAS_ANTHROPIC = False

# Import the system prompt from the lamp codebase
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "llm"))
try:
    from prompts import LAMP_PROGRAM_SYSTEM_PROMPT
except ImportError:
    LAMP_PROGRAM_SYSTEM_PROMPT = None

# User message template (matches what the lamp controller sends)
USER_TEMPLATE = "Create a light program for this request.\n\nRequest: {input}\n\nRespond with ONLY a JSON program. No text."

# Valid values for validation
VALID_PATTERN_NAMES = {"solid", "gradient", "breathing", "wave", "rainbow", "pulse", "sparkle"}
VALID_COMMAND_TYPES = {"pattern", "render", "stop"}
VALID_ELEMENT_TYPES = {"fill", "text", "pixel", "rect", "line"}
HEX_RE = re.compile(r'^#([0-9a-fA-F]{3}|[0-9a-fA-F]{6}|[0-9a-fA-F]{8})$')


def extract_json(text):
    """Extract JSON from LLM response, handling markdown fences and partial output."""
    if not text:
        return None
    text = text.strip()
    text = re.sub(r"```(?:json)?\s*", "", text)
    text = text.rstrip("`").strip()
    text = text.rstrip("\"'")

    # Direct parse
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # Bracket counting
    start = text.find("{")
    if start == -1:
        return None

    depth = 0
    for i in range(start, len(text)):
        c = text[i]
        if c == "{":
            depth += 1
        elif c == "}":
            depth -= 1
            if depth == 0:
                candidate = text[start : i + 1]
                try:
                    return json.loads(candidate)
                except json.JSONDecodeError:
                    for fix in ["}", "]}", "]}"]:]
                        try:
                            return json.loads(candidate + fix)
                        except json.JSONDecodeError:
                            continue
                    return None

    # Unclosed — try adding brackets
    candidate = text[start:]
    missing = candidate.count("{") - candidate.count("}")
    if missing > 0:
        for fix in ["}" * missing, "]" + "}" * missing]:
            try:
                return json.loads(candidate + fix)
            except json.JSONDecodeError:
                continue
    return None


def quick_validate(data):
    """Quick check that the response is a valid lamp program."""
    if not isinstance(data, dict):
        return False, "not a dict"
    if "program" not in data:
        # Maybe it's a raw command — that's okay, we can wrap it
        if "type" in data:
            return True, "raw_command"
        return False, "no program key"

    prog = data["program"]
    if not isinstance(prog, dict):
        return False, "program not dict"
    if "steps" not in prog or not prog["steps"]:
        return False, "no steps"

    for step in prog["steps"]:
        cmd = step.get("command", {})
        ctype = cmd.get("type")
        if ctype not in VALID_COMMAND_TYPES:
            return False, f"bad command type: {ctype}"
        if ctype == "pattern" and cmd.get("name") not in VALID_PATTERN_NAMES:
            return False, f"bad pattern: {cmd.get('name')}"
        if ctype == "render":
            for elem in cmd.get("elements", []):
                if elem.get("type") not in VALID_ELEMENT_TYPES:
                    return False, f"bad element type: {elem.get('type')}"

    return True, "ok"


def wrap_if_needed(data, prompt):
    """Wrap a raw command in a program structure if needed."""
    if "program" not in data and "type" in data:
        return {
            "program": {
                "name": prompt[:30].title(),
                "steps": [{"id": "main", "command": data, "duration": None}]
            }
        }
    return data


def generate_response(client, prompt, model, max_retries=2):
    """Call the Anthropic API to generate a response for a single prompt."""
    user_msg = USER_TEMPLATE.format(input=prompt)

    for attempt in range(max_retries + 1):
        try:
            response = client.messages.create(
                model=model,
                max_tokens=4096,
                temperature=0.4,
                system=LAMP_PROGRAM_SYSTEM_PROMPT,
                messages=[{"role": "user", "content": user_msg}],
            )

            raw_text = response.content[0].text
            parsed = extract_json(raw_text)

            if parsed is None:
                if attempt < max_retries:
                    time.sleep(1)
                    continue
                return None, raw_text, "json_parse_error"

            parsed = wrap_if_needed(parsed, prompt)
            valid, reason = quick_validate(parsed)

            if not valid:
                if attempt < max_retries:
                    time.sleep(1)
                    continue
                return parsed, raw_text, f"validation_error: {reason}"

            # Compact the JSON
            compact = json.dumps(parsed, separators=(',', ':'))
            return parsed, compact, "ok"

        except anthropic.RateLimitError:
            wait = 30 * (attempt + 1)
            print(f"    Rate limited, waiting {wait}s...")
            time.sleep(wait)
        except anthropic.APIError as e:
            print(f"    API error: {e}")
            if attempt < max_retries:
                time.sleep(5)
            else:
                return None, str(e), "api_error"

    return None, "", "max_retries"


def main():
    parser = argparse.ArgumentParser(description="Generate responses via Anthropic API")
    parser.add_argument("--model", default="claude-opus-4-6",
                        help="Anthropic model (default: claude-opus-4-6)")
    parser.add_argument("--batch-size", type=int, default=100,
                        help="Save checkpoint every N responses")
    parser.add_argument("--resume", action="store_true",
                        help="Resume from existing output file")
    parser.add_argument("--delay", type=float, default=0.5,
                        help="Delay between API calls (seconds)")
    parser.add_argument("--input", default=None, help="Input prompts file")
    parser.add_argument("--max-retries", type=int, default=2,
                        help="Max retries per prompt on failure")
    args = parser.parse_args()

    if not HAS_ANTHROPIC:
        print("ERROR: anthropic package not installed.")
        print("  pip install anthropic")
        sys.exit(1)

    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print("ERROR: ANTHROPIC_API_KEY not set.")
        print("  export ANTHROPIC_API_KEY=sk-ant-...")
        print("  Get your key at: https://console.anthropic.com/settings/keys")
        sys.exit(1)

    if not LAMP_PROGRAM_SYSTEM_PROMPT:
        print("ERROR: Could not load system prompt from llm/prompts.py")
        sys.exit(1)

    client = anthropic.Anthropic(api_key=api_key)

    # Load prompts
    data_dir = os.path.join(os.path.dirname(__file__), "data")
    input_path = args.input or os.path.join(data_dir, "prompts.jsonl")

    prompts = []
    with open(input_path) as f:
        for line in f:
            prompts.append(json.loads(line.strip()))

    print(f"  Loaded {len(prompts)} prompts")
    print(f"  Model: {args.model}")
    print(f"  Delay: {args.delay}s between calls")

    # Resume support
    out_path = os.path.join(data_dir, "raw_responses.jsonl")
    completed = set()
    existing_results = []

    if args.resume and os.path.exists(out_path):
        with open(out_path) as f:
            for line in f:
                item = json.loads(line.strip())
                completed.add(item["prompt"])
                existing_results.append(item)
        print(f"  Resuming: {len(completed)} already done, {len(prompts) - len(completed)} remaining")

    # Process prompts
    results = list(existing_results)
    ok_count = len([r for r in results if r.get("status") == "ok"])
    error_count = len([r for r in results if r.get("status") != "ok"])
    remaining = [p for p in prompts if p["prompt"] not in completed]

    print(f"\n  Starting generation ({len(remaining)} prompts)...\n")

    for i, item in enumerate(remaining):
        prompt = item["prompt"]
        category = item["category"]

        parsed, response_str, status = generate_response(
            client, prompt, args.model, args.max_retries
        )

        if status == "ok":
            ok_count += 1
            results.append({
                "prompt": prompt,
                "category": category,
                "response": response_str,
            })
        else:
            error_count += 1
            results.append({
                "prompt": prompt,
                "category": category,
                "response": response_str if response_str else "",
                "status": status,
            })

        # Progress
        total_done = ok_count + error_count
        if (i + 1) % 10 == 0 or status != "ok":
            pct = total_done / len(prompts) * 100
            print(f"  [{total_done:4d}/{len(prompts)}] ({pct:5.1f}%) ok={ok_count} err={error_count}  |  {prompt[:50]}")

        # Checkpoint save
        if (i + 1) % args.batch_size == 0:
            with open(out_path, "w") as f:
                for r in results:
                    f.write(json.dumps(r) + "\n")
            print(f"  -- checkpoint saved ({total_done} responses) --")

        # Rate limiting delay
        if args.delay > 0:
            time.sleep(args.delay)

    # Final save
    with open(out_path, "w") as f:
        for r in results:
            f.write(json.dumps(r) + "\n")

    # Filter out errors for the clean output
    clean_results = [r for r in results if r.get("status", "ok") == "ok"]

    print(f"\n{'='*60}")
    print(f"  GENERATION COMPLETE")
    print(f"{'='*60}")
    print(f"  Total:      {len(prompts)}")
    print(f"  Successful: {ok_count} ({ok_count/len(prompts)*100:.1f}%)")
    print(f"  Errors:     {error_count}")
    print(f"  Saved to:   {out_path}")

    # Category breakdown
    cats = {}
    for r in clean_results:
        cats[r["category"]] = cats.get(r["category"], 0) + 1
    print(f"\n  Category breakdown:")
    for cat, cnt in sorted(cats.items()):
        print(f"    {cat:12s}: {cnt:4d}")

    # Cost estimate
    # Rough: ~1500 input tokens/call (system prompt) + ~300 output tokens/call
    est_input = len(prompts) * 1500
    est_output = ok_count * 300
    if "opus" in args.model:
        cost = est_input / 1_000_000 * 15 + est_output / 1_000_000 * 75
    elif "sonnet" in args.model:
        cost = est_input / 1_000_000 * 3 + est_output / 1_000_000 * 15
    else:
        cost = 0
    print(f"\n  Estimated API cost: ~${cost:.2f}")


if __name__ == "__main__":
    main()
