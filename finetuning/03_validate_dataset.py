#!/usr/bin/env python3
"""
Step 3: Validate all generated responses for JSON correctness,
schema compliance, valid commands, grid bounds, and data quality.

Usage:
    python3 03_validate_dataset.py
    python3 03_validate_dataset.py --verbose
"""

import json
import os
import re
import argparse

# Valid values per the lamp server schema
VALID_PATTERN_NAMES = {"solid", "gradient", "breathing", "wave", "rainbow", "pulse", "sparkle"}
VALID_COMMAND_TYPES = {"pattern", "render", "stop"}
VALID_ELEMENT_TYPES = {"fill", "text", "pixel", "rect", "line"}
GRID_W, GRID_H = 10, 14
HEX_RE = re.compile(r'^#([0-9a-fA-F]{3}|[0-9a-fA-F]{6}|[0-9a-fA-F]{8})$')
MAX_RESPONSE_TOKENS = 2000  # rough: 1 token ≈ 4 chars


def validate_color(color):
    """Check if color is a valid hex code."""
    if not isinstance(color, str):
        return False, f"color is not a string: {color}"
    if not HEX_RE.match(color):
        return False, f"invalid hex color: {color}"
    return True, None


def validate_element(elem):
    """Validate a single render element."""
    issues = []
    etype = elem.get("type")
    if etype not in VALID_ELEMENT_TYPES:
        issues.append(f"invalid element type: {etype}")
        return issues

    if etype == "fill":
        ok, msg = validate_color(elem.get("color", ""))
        if not ok:
            issues.append(f"fill: {msg}")

    elif etype == "pixel":
        x, y = elem.get("x"), elem.get("y")
        if not isinstance(x, (int, float)) or not isinstance(y, (int, float)):
            issues.append(f"pixel: x/y not numeric: x={x}, y={y}")
        elif x < 0 or x >= GRID_W or y < 0 or y >= GRID_H:
            issues.append(f"pixel out of bounds: ({x},{y})")
        ok, msg = validate_color(elem.get("color", ""))
        if not ok:
            issues.append(f"pixel: {msg}")

    elif etype == "rect":
        x, y = elem.get("x", 0), elem.get("y", 0)
        w, h = elem.get("w", 1), elem.get("h", 1)
        if not all(isinstance(v, (int, float)) for v in [x, y, w, h]):
            issues.append(f"rect: non-numeric dimensions")
        elif x < 0 or y < 0 or x + w > GRID_W or y + h > GRID_H:
            # Allow slight overflow (common in pixel art)
            if x + w > GRID_W + 2 or y + h > GRID_H + 2:
                issues.append(f"rect far out of bounds: ({x},{y}) {w}x{h}")
        ok, msg = validate_color(elem.get("color", ""))
        if not ok:
            issues.append(f"rect: {msg}")

    elif etype == "line":
        for coord in ["x1", "y1", "x2", "y2"]:
            val = elem.get(coord)
            if not isinstance(val, (int, float)):
                issues.append(f"line: {coord} not numeric: {val}")
        ok, msg = validate_color(elem.get("color", ""))
        if not ok:
            issues.append(f"line: {msg}")

    elif etype == "text":
        ok, msg = validate_color(elem.get("color", ""))
        if not ok:
            issues.append(f"text: {msg}")
        if not isinstance(elem.get("content"), str):
            issues.append(f"text: content not a string")
        x, y = elem.get("x"), elem.get("y")
        if not isinstance(x, (int, float)) or not isinstance(y, (int, float)):
            issues.append(f"text: x/y not numeric")

    return issues


def validate_command(cmd):
    """Validate a step command."""
    issues = []
    ctype = cmd.get("type")
    if ctype not in VALID_COMMAND_TYPES:
        issues.append(f"invalid command type: {ctype}")
        return issues

    if ctype == "pattern":
        name = cmd.get("name")
        if name not in VALID_PATTERN_NAMES:
            issues.append(f"invalid pattern name: {name}")
        params = cmd.get("params", {})
        if not isinstance(params, dict):
            issues.append("params is not a dict")
        else:
            for key in ["color", "color2", "bgColor"]:
                if key in params:
                    ok, msg = validate_color(params[key])
                    if not ok:
                        issues.append(f"pattern.params.{key}: {msg}")
            if "speed" in params:
                speed = params["speed"]
                if not isinstance(speed, (int, float)) or speed <= 0:
                    issues.append(f"invalid speed: {speed}")
            if "density" in params:
                d = params["density"]
                if not isinstance(d, (int, float)) or d < 0 or d > 1:
                    issues.append(f"invalid density: {d}")

    elif ctype == "render":
        elements = cmd.get("elements", [])
        if not isinstance(elements, list):
            issues.append("render elements is not a list")
        else:
            for i, elem in enumerate(elements):
                elem_issues = validate_element(elem)
                for issue in elem_issues:
                    issues.append(f"element[{i}]: {issue}")

    return issues


def validate_program(program_data):
    """Validate a complete program structure. Returns list of issues."""
    issues = []

    if not isinstance(program_data, dict):
        return ["not a dict"]

    if "program" not in program_data:
        return ["missing 'program' key"]

    prog = program_data["program"]
    if not isinstance(prog, dict):
        return ["program is not a dict"]

    if "name" not in prog:
        issues.append("missing program.name")
    if "steps" not in prog:
        return issues + ["missing program.steps"]

    steps = prog["steps"]
    if not isinstance(steps, list) or len(steps) == 0:
        return issues + ["steps is empty or not a list"]

    step_ids = set()
    for i, step in enumerate(steps):
        if not isinstance(step, dict):
            issues.append(f"step[{i}]: not a dict")
            continue

        sid = step.get("id")
        if not sid:
            issues.append(f"step[{i}]: missing id")
        else:
            step_ids.add(sid)

        cmd = step.get("command")
        if not isinstance(cmd, dict):
            issues.append(f"step[{i}]: missing or invalid command")
        else:
            cmd_issues = validate_command(cmd)
            for issue in cmd_issues:
                issues.append(f"step[{i}].command: {issue}")

        dur = step.get("duration")
        if dur is not None:
            if not isinstance(dur, (int, float)):
                issues.append(f"step[{i}]: duration not a number: {dur}")
            elif dur < 0:
                issues.append(f"step[{i}]: negative duration: {dur}")

    # Validate loop references
    loop = prog.get("loop")
    if loop and isinstance(loop, dict):
        start = loop.get("start_step")
        end = loop.get("end_step")
        if start and start not in step_ids:
            issues.append(f"loop.start_step '{start}' not in step ids")
        if end and end not in step_ids:
            issues.append(f"loop.end_step '{end}' not in step ids")
        count = loop.get("count")
        if count is not None and not isinstance(count, (int, float)):
            issues.append(f"loop.count not a number: {count}")

    # Validate on_complete
    oc = prog.get("on_complete")
    if oc and isinstance(oc, dict):
        oc_cmd = oc.get("command")
        if isinstance(oc_cmd, dict):
            cmd_issues = validate_command(oc_cmd)
            for issue in cmd_issues:
                issues.append(f"on_complete: {issue}")

    return issues


def main():
    parser = argparse.ArgumentParser(description="Validate generated dataset")
    parser.add_argument("--verbose", "-v", action="store_true", help="Show details of failures")
    parser.add_argument("--input", default=None, help="Input file")
    args = parser.parse_args()

    data_dir = os.path.join(os.path.dirname(__file__), "data")
    input_path = args.input or os.path.join(data_dir, "raw_responses.jsonl")

    validated = []
    rejected = []
    stats = {
        "total": 0, "valid": 0, "rejected": 0,
        "issues": {},
        "by_category": {},
    }

    with open(input_path) as f:
        for line_num, line in enumerate(f, 1):
            stats["total"] += 1
            item = json.loads(line.strip())
            prompt = item["prompt"]
            category = item["category"]
            response_str = item["response"]

            # Track by category
            if category not in stats["by_category"]:
                stats["by_category"][category] = {"total": 0, "valid": 0}
            stats["by_category"][category]["total"] += 1

            # 1. Parse JSON
            try:
                program_data = json.loads(response_str)
            except json.JSONDecodeError as e:
                rejected.append({"line": line_num, "prompt": prompt, "reason": f"JSON parse error: {e}", "category": category})
                stats["rejected"] += 1
                stats["issues"]["json_parse"] = stats["issues"].get("json_parse", 0) + 1
                continue

            # 2. Validate program structure
            issues = validate_program(program_data)

            # 3. Check response length (rough token estimate)
            if len(response_str) > MAX_RESPONSE_TOKENS * 4:
                issues.append(f"response too long: {len(response_str)} chars (est. {len(response_str)//4} tokens)")

            if issues:
                rejected.append({
                    "line": line_num, "prompt": prompt, "category": category,
                    "issues": issues, "response_preview": response_str[:200],
                })
                stats["rejected"] += 1
                for issue in issues:
                    # Categorize the issue type
                    issue_type = issue.split(":")[0].split("[")[0].strip()
                    stats["issues"][issue_type] = stats["issues"].get(issue_type, 0) + 1
                if args.verbose:
                    print(f"  REJECTED [{line_num}] '{prompt[:50]}': {issues[0]}")
            else:
                validated.append(item)
                stats["valid"] += 1
                stats["by_category"][category]["valid"] += 1

    # Save validated
    valid_path = os.path.join(data_dir, "validated.jsonl")
    with open(valid_path, "w") as f:
        for item in validated:
            f.write(json.dumps(item) + "\n")

    # Save rejected
    reject_path = os.path.join(data_dir, "rejected.jsonl")
    with open(reject_path, "w") as f:
        for item in rejected:
            f.write(json.dumps(item) + "\n")

    # Save stats
    stats_path = os.path.join(data_dir, "stats.json")
    with open(stats_path, "w") as f:
        json.dump(stats, f, indent=2)

    # Print summary
    print(f"\n{'='*60}")
    print(f"  VALIDATION RESULTS")
    print(f"{'='*60}")
    print(f"  Total:    {stats['total']}")
    print(f"  Valid:    {stats['valid']} ({stats['valid']/stats['total']*100:.1f}%)")
    print(f"  Rejected: {stats['rejected']} ({stats['rejected']/stats['total']*100:.1f}%)")

    if stats["issues"]:
        print(f"\n  Issue breakdown:")
        for issue, count in sorted(stats["issues"].items(), key=lambda x: -x[1]):
            print(f"    {issue:40s}: {count}")

    print(f"\n  Per-category pass rates:")
    for cat in sorted(stats["by_category"]):
        cs = stats["by_category"][cat]
        rate = cs["valid"] / cs["total"] * 100 if cs["total"] > 0 else 0
        print(f"    {cat:12s}: {cs['valid']:4d}/{cs['total']:4d} ({rate:.1f}%)")

    print(f"\n  Saved: {valid_path} ({stats['valid']} examples)")
    print(f"         {reject_path} ({stats['rejected']} examples)")
    print(f"         {stats_path}")


if __name__ == "__main__":
    main()
