#!/usr/bin/env python3
"""Comprehensive verification of the v2 training dataset."""
import json
import re
import sys
import os
from collections import Counter

DATA = os.path.join(os.path.dirname(__file__), "data")

VALID_PATTERN_NAMES = {"solid", "gradient", "breathing", "wave", "rainbow", "pulse", "sparkle"}
VALID_COMMAND_TYPES = {"pattern", "render", "stop"}
VALID_ELEMENT_TYPES = {"fill", "text", "pixel", "rect", "line"}
HEX_RE = re.compile(r'^#([0-9a-fA-F]{3}|[0-9a-fA-F]{6}|[0-9a-fA-F]{8})$')

issues = []
stats = {
    "total": 0,
    "valid_json": 0,
    "valid_structure": 0,
    "has_system": 0,
    "has_user": 0,
    "has_assistant": 0,
    "command_types": Counter(),
    "pattern_names": Counter(),
    "step_counts": Counter(),
    "has_loop": 0,
    "has_on_complete": 0,
    "render_element_counts": [],
    "prompt_lengths": [],
    "response_lengths": [],
    "prompts": [],
    "render_objects": 0,
    "element_types": Counter(),
    "color_valid": 0,
    "color_invalid": 0,
    "grid_violations": 0,
}

def check_color(c):
    if isinstance(c, str) and HEX_RE.match(c):
        return True
    return False

def validate_example(idx, item):
    """Validate a single training example."""
    # Structure check
    if "conversations" not in item:
        issues.append(f"Line {idx}: missing 'conversations' key")
        return False

    convs = item["conversations"]
    if len(convs) != 3:
        issues.append(f"Line {idx}: expected 3 conversation turns, got {len(convs)}")
        return False

    roles = [c["role"] for c in convs]
    if roles != ["system", "user", "assistant"]:
        issues.append(f"Line {idx}: unexpected roles {roles}")
        return False

    stats["has_system"] += 1
    stats["has_user"] += 1
    stats["has_assistant"] += 1

    # Extract prompt
    user_content = convs[1]["content"]
    if "Request: " in user_content:
        prompt = user_content.split("Request: ")[1].split("\n")[0].strip()
    else:
        prompt = user_content
    stats["prompts"].append(prompt)
    stats["prompt_lengths"].append(len(prompt.split()))

    # Parse assistant response
    response_str = convs[2]["content"]
    stats["response_lengths"].append(len(response_str))

    try:
        resp = json.loads(response_str)
    except json.JSONDecodeError:
        issues.append(f"Line {idx}: assistant response not valid JSON: {response_str[:100]}...")
        return False

    stats["valid_json"] += 1

    # Validate program structure
    if "program" not in resp:
        if "type" in resp:
            # Raw command, acceptable but note it
            return True
        issues.append(f"Line {idx}: no 'program' key in response")
        return False

    prog = resp["program"]
    if "name" not in prog:
        issues.append(f"Line {idx}: program missing 'name'")
        return False
    if "steps" not in prog or not prog["steps"]:
        issues.append(f"Line {idx}: program missing/empty 'steps'")
        return False

    stats["step_counts"][len(prog["steps"])] += 1

    if "loop" in prog and prog["loop"]:
        stats["has_loop"] += 1
    if "on_complete" in prog and prog["on_complete"]:
        stats["has_on_complete"] += 1

    # Validate each step
    for si, step in enumerate(prog["steps"]):
        if "id" not in step:
            issues.append(f"Line {idx}, step {si}: missing 'id'")
        if "command" not in step:
            issues.append(f"Line {idx}, step {si}: missing 'command'")
            continue

        cmd = step["command"]
        ctype = cmd.get("type")
        stats["command_types"][ctype] += 1

        if ctype == "pattern":
            pname = cmd.get("name")
            stats["pattern_names"][pname] += 1
            if pname not in VALID_PATTERN_NAMES:
                issues.append(f"Line {idx}: invalid pattern '{pname}'")

            params = cmd.get("params", {})
            for key in ["color", "color2", "bgColor"]:
                if key in params:
                    if check_color(params[key]):
                        stats["color_valid"] += 1
                    else:
                        stats["color_invalid"] += 1
                        issues.append(f"Line {idx}: invalid color {key}={params[key]}")

        elif ctype == "render":
            stats["render_objects"] += 1
            elements = cmd.get("elements", [])
            stats["render_element_counts"].append(len(elements))
            for elem in elements:
                etype = elem.get("type")
                stats["element_types"][etype] += 1
                if etype not in VALID_ELEMENT_TYPES:
                    issues.append(f"Line {idx}: invalid element type '{etype}'")

                # Grid bounds check
                x = elem.get("x")
                y = elem.get("y")
                if x is not None and (x < 0 or x > 9):
                    stats["grid_violations"] += 1
                if y is not None and (y < 0 or y > 13):
                    stats["grid_violations"] += 1

                # Color check
                for key in ["color"]:
                    if key in elem:
                        if check_color(elem[key]):
                            stats["color_valid"] += 1
                        else:
                            stats["color_invalid"] += 1

        elif ctype == "stop":
            pass
        elif ctype is not None:
            issues.append(f"Line {idx}: unknown command type '{ctype}'")

    stats["valid_structure"] += 1
    return True


def main():
    print("=" * 70)
    print("  DATASET VERIFICATION REPORT")
    print("=" * 70)

    for split_name, filename in [("train", "train_v2.jsonl"), ("val", "val_v2.jsonl")]:
        path = os.path.join(DATA, filename)
        print(f"\n--- Verifying {filename} ---")

        with open(path) as f:
            lines = f.readlines()

        print(f"  Lines: {len(lines)}")

        for i, line in enumerate(lines):
            stats["total"] += 1
            try:
                item = json.loads(line.strip())
                validate_example(i + 1, item)
            except json.JSONDecodeError:
                issues.append(f"Line {i+1}: not valid JSONL")

    # Summary
    print(f"\n{'=' * 70}")
    print(f"  VERIFICATION RESULTS")
    print(f"{'=' * 70}")

    print(f"\n  Total examples:        {stats['total']}")
    print(f"  Valid JSON responses:  {stats['valid_json']}")
    print(f"  Valid structure:       {stats['valid_structure']}")
    print(f"  Pass rate:             {stats['valid_structure']/stats['total']*100:.1f}%")

    print(f"\n  Conversation format:")
    print(f"    Has system prompt:   {stats['has_system']}")
    print(f"    Has user message:    {stats['has_user']}")
    print(f"    Has assistant reply: {stats['has_assistant']}")

    print(f"\n  Command types (across all steps):")
    for ct, count in stats["command_types"].most_common():
        print(f"    {ct:12s}: {count:5d}")

    print(f"\n  Pattern distribution:")
    for pn, count in stats["pattern_names"].most_common():
        print(f"    {pn:12s}: {count:5d}")

    print(f"\n  Step count distribution:")
    for sc, count in sorted(stats["step_counts"].items()):
        print(f"    {sc} step(s):  {count:5d} examples")

    print(f"\n  Programs with loop:        {stats['has_loop']}")
    print(f"  Programs with on_complete: {stats['has_on_complete']}")

    print(f"\n  Render stats:")
    print(f"    Total render commands:   {stats['render_objects']}")
    if stats["render_element_counts"]:
        avg_elems = sum(stats["render_element_counts"]) / len(stats["render_element_counts"])
        print(f"    Avg elements/render:     {avg_elems:.1f}")
        print(f"    Min elements:            {min(stats['render_element_counts'])}")
        print(f"    Max elements:            {max(stats['render_element_counts'])}")

    print(f"\n  Element types in renders:")
    for et, count in stats["element_types"].most_common():
        print(f"    {et:8s}: {count:5d}")

    print(f"\n  Color validation:")
    print(f"    Valid hex colors:    {stats['color_valid']}")
    print(f"    Invalid colors:      {stats['color_invalid']}")
    print(f"    Grid violations:     {stats['grid_violations']} (x>9 or y>13)")

    print(f"\n  Prompt length (words):")
    if stats["prompt_lengths"]:
        avg_len = sum(stats["prompt_lengths"]) / len(stats["prompt_lengths"])
        short = sum(1 for l in stats["prompt_lengths"] if l <= 3)
        medium = sum(1 for l in stats["prompt_lengths"] if 4 <= l <= 8)
        long = sum(1 for l in stats["prompt_lengths"] if l >= 9)
        print(f"    Average:       {avg_len:.1f} words")
        print(f"    Short (1-3):   {short} ({short/len(stats['prompt_lengths'])*100:.0f}%)")
        print(f"    Medium (4-8):  {medium} ({medium/len(stats['prompt_lengths'])*100:.0f}%)")
        print(f"    Long (9+):     {long} ({long/len(stats['prompt_lengths'])*100:.0f}%)")

    print(f"\n  Response length (chars):")
    if stats["response_lengths"]:
        avg_resp = sum(stats["response_lengths"]) / len(stats["response_lengths"])
        print(f"    Average: {avg_resp:.0f} chars")
        print(f"    Min:     {min(stats['response_lengths'])} chars")
        print(f"    Max:     {max(stats['response_lengths'])} chars")

    # Duplicate check
    prompt_counts = Counter(p.lower().strip() for p in stats["prompts"])
    dupes = {p: c for p, c in prompt_counts.items() if c > 1}
    print(f"\n  Duplicates:")
    print(f"    Unique prompts:    {len(prompt_counts)}")
    print(f"    Duplicate prompts: {len(dupes)}")
    if dupes:
        top_dupes = sorted(dupes.items(), key=lambda x: -x[1])[:10]
        for p, c in top_dupes:
            print(f"      [{c}x] {p[:60]}")

    # Issues
    print(f"\n  Issues found: {len(issues)}")
    if issues:
        print(f"  First 20 issues:")
        for iss in issues[:20]:
            print(f"    - {iss}")

    # Final verdict
    print(f"\n{'=' * 70}")
    error_rate = (stats['total'] - stats['valid_structure']) / stats['total'] * 100 if stats['total'] else 0
    if error_rate < 1:
        print(f"  VERDICT: PASS - {error_rate:.2f}% error rate")
    elif error_rate < 5:
        print(f"  VERDICT: ACCEPTABLE - {error_rate:.2f}% error rate")
    else:
        print(f"  VERDICT: NEEDS REVIEW - {error_rate:.2f}% error rate")
    print(f"{'=' * 70}")


if __name__ == "__main__":
    main()
