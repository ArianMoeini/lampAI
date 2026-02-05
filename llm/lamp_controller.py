#!/usr/bin/env python3
"""
Moonside Lamp Controller - LLM Integration

Connects a local Ollama LLM to the lamp control server, allowing
natural language control of the lamp.

Usage:
    # Interactive mode
    python lamp_controller.py

    # Single command
    python lamp_controller.py --command "make it cozy and warm"

    # Autonomous mode (LLM decides patterns over time)
    python lamp_controller.py --autonomous
"""

import argparse
import json
import re
import sys
import time
from datetime import datetime

import requests

try:
    import ollama
    HAS_OLLAMA = True
except ImportError:
    HAS_OLLAMA = False
    print("Warning: ollama package not installed. Install with: pip install ollama")

from prompts import (
    LAMP_CONTROLLER_SYSTEM_PROMPT,
    LAMP_PROGRAM_SYSTEM_PROMPT,
    MOOD_MAPPING_PROMPT,
    AUTONOMOUS_PROMPT,
)

# Configuration
LAMP_SERVER_URL = "http://localhost:3001"
OLLAMA_MODEL = "llama3.2"  # Change to your preferred model


class LampController:
    """Controls the Moonside lamp via the control server."""

    def __init__(self, server_url: str = LAMP_SERVER_URL):
        self.server_url = server_url.rstrip("/")
        self.last_pattern = None

    def send_command(self, command: dict) -> bool:
        """Send a command to the lamp server."""
        try:
            cmd_type = command.get("type", "")

            if cmd_type == "led":
                led_id = command.get("id", 0)
                response = requests.post(
                    f"{self.server_url}/led/{led_id}",
                    json={"color": command.get("color", "#000000")},
                    timeout=5,
                )
            elif cmd_type == "bulk":
                response = requests.post(
                    f"{self.server_url}/leds",
                    json={"leds": command.get("leds", [])},
                    timeout=5,
                )
            elif cmd_type == "pattern":
                response = requests.post(
                    f"{self.server_url}/pattern",
                    json={
                        "name": command.get("name", "solid"),
                        "params": command.get("params", {}),
                    },
                    timeout=5,
                )
            elif cmd_type == "gradient":
                response = requests.post(
                    f"{self.server_url}/gradient",
                    json={
                        "colors": command.get("colors", ["#FF6B4A", "#FFE4C4"]),
                        "direction": command.get("direction", "radial"),
                    },
                    timeout=5,
                )
            elif cmd_type == "stop":
                response = requests.post(f"{self.server_url}/stop", timeout=5)
            else:
                print(f"Unknown command type: {cmd_type}")
                return False

            if response.status_code == 200:
                self.last_pattern = command
                return True
            else:
                print(f"Server error: {response.status_code}")
                return False

        except requests.exceptions.ConnectionError:
            print(f"Cannot connect to lamp server at {self.server_url}")
            print("Make sure the server is running: cd ../server && npm start")
            return False
        except Exception as e:
            print(f"Error sending command: {e}")
            return False

    def send_program(self, program: dict) -> bool:
        """Send a light program to the scheduler."""
        try:
            response = requests.post(
                f"{self.server_url}/program",
                json={"program": program},
                timeout=5,
            )
            if response.status_code == 200:
                result = response.json()
                if result.get("success"):
                    self.last_pattern = program
                    return True
                else:
                    print(f"Program rejected: {result.get('error')}")
                    return False
            else:
                print(f"Server error: {response.status_code}")
                return False
        except requests.exceptions.ConnectionError:
            print(f"Cannot connect to lamp server at {self.server_url}")
            return False
        except Exception as e:
            print(f"Error sending program: {e}")
            return False

    def get_program_status(self) -> dict | None:
        """Get current program status."""
        try:
            response = requests.get(f"{self.server_url}/program/status", timeout=5)
            if response.status_code == 200:
                return response.json()
        except Exception as e:
            print(f"Error getting program status: {e}")
        return None

    def cancel_program(self) -> bool:
        """Cancel the running program."""
        try:
            response = requests.post(f"{self.server_url}/program/cancel", timeout=5)
            return response.status_code == 200
        except Exception as e:
            print(f"Error cancelling program: {e}")
            return False

    def get_state(self) -> dict | None:
        """Get current lamp state."""
        try:
            response = requests.get(f"{self.server_url}/state", timeout=5)
            if response.status_code == 200:
                return response.json()
        except Exception as e:
            print(f"Error getting state: {e}")
        return None


class LLMController:
    """Interfaces with Ollama for natural language processing."""

    def __init__(self, model: str = OLLAMA_MODEL, use_programs: bool = True):
        self.model = model
        self.use_programs = use_programs
        self.system_prompt = LAMP_PROGRAM_SYSTEM_PROMPT if use_programs else LAMP_CONTROLLER_SYSTEM_PROMPT

    def process_input(self, user_input: str) -> dict | None:
        """Convert natural language to a light program (or single command)."""
        if not HAS_OLLAMA:
            print("Ollama not available. Using fallback command.")
            return self._fallback_program(user_input) if self.use_programs else self._fallback_command(user_input)

        try:
            prompt = MOOD_MAPPING_PROMPT.format(input=user_input)

            messages = [
                {"role": "system", "content": self.system_prompt},
                {"role": "user", "content": prompt},
            ]

            # Try up to 2 times — small models occasionally produce malformed JSON
            for attempt in range(2):
                response = ollama.chat(
                    model=self.model,
                    messages=messages,
                    options={"temperature": 0.3},  # Lower temp for more precise JSON
                )

                content = response["message"]["content"]
                result = self._extract_json(content)

                if result is not None:
                    break

                if attempt == 0:
                    print("Retrying LLM call...")

            if result is None:
                return self._fallback_program(user_input) if self.use_programs else self._fallback_command(user_input)

            # If we got a single command but expect programs, wrap it
            if self.use_programs and "program" not in result and "type" in result:
                result = self._wrap_command_as_program(result, user_input)

            return result

        except Exception as e:
            print(f"LLM error: {e}")
            return self._fallback_program(user_input) if self.use_programs else self._fallback_command(user_input)

    def generate_autonomous(self, iteration: int, previous_pattern: dict | None) -> dict | None:
        """Generate a pattern for autonomous mode."""
        if not HAS_OLLAMA:
            return self._autonomous_fallback(iteration)

        try:
            current_time = datetime.now().strftime("%H:%M")
            prev_str = json.dumps(previous_pattern) if previous_pattern else "none"

            prompt = AUTONOMOUS_PROMPT.format(
                time=current_time,
                previous_pattern=prev_str,
                iteration=iteration,
            )

            response = ollama.chat(
                model=self.model,
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": prompt},
                ],
            )

            content = response["message"]["content"]
            return self._extract_json(content)

        except Exception as e:
            print(f"LLM error: {e}")
            return self._autonomous_fallback(iteration)

    def _extract_json(self, text: str) -> dict | None:
        """Extract JSON from LLM response using bracket-counting for nested objects."""
        text = text.strip()

        # Remove markdown code blocks if present
        text = re.sub(r"```(?:json)?\s*", "", text)
        text = text.rstrip("`").strip()

        # Strip trailing non-JSON characters (small models sometimes add trailing quotes)
        text = text.rstrip('"\'')

        # Try direct parse first
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            pass

        # Find the outermost { and its matching } using bracket counting
        start = text.find("{")
        if start == -1:
            print(f"No JSON object found in: {text[:100]}...")
            return None

        depth = 0
        in_string = False
        escape = False
        for i in range(start, len(text)):
            c = text[i]
            if escape:
                escape = False
                continue
            if c == "\\":
                escape = True
                continue
            if c == '"':
                in_string = not in_string
                continue
            if in_string:
                continue
            if c == "{":
                depth += 1
            elif c == "}":
                depth -= 1
                if depth == 0:
                    candidate = text[start : i + 1]
                    try:
                        return json.loads(candidate)
                    except json.JSONDecodeError:
                        # Try bracket repair before giving up
                        repaired = self._repair_json(candidate)
                        if repaired is not None:
                            print("(repaired malformed JSON from LLM)")
                            return repaired
                        print(f"JSON parse error in ({len(candidate)} chars): {candidate[:200]}...")
                        return None

        # Unmatched braces — try closing them
        candidate = text[start:]
        repaired = self._repair_json(candidate)
        if repaired is not None:
            print("(repaired unclosed JSON from LLM)")
            return repaired

        print(f"Unmatched braces in ({len(text)} chars): {text[:200]}...")
        return None

    @staticmethod
    def _repair_json(text: str) -> dict | None:
        """Try to fix common JSON errors from small LLMs (missing brackets)."""
        # Common error: missing ] before , or } at the end
        # Strategy: try adding missing ] and } in likely positions
        for fix in [
            # Fix: missing } before ] (e.g. "duration":300000] → "duration":300000}])
            lambda t: re.sub(r'(\d+)(])', r'\1}\2', t),
            # Fix: missing ] before ,"on_complete" or ,"loop"
            lambda t: re.sub(r'(})(,"(?:on_complete|loop)")', r'\1]\2', t),
            # Fix: add missing closing brackets at end
            lambda t: t + ']' + '}' * (t.count('{') - t.count('}')),
        ]:
            try:
                fixed = fix(text)
                if fixed != text:
                    return json.loads(fixed)
            except (json.JSONDecodeError, Exception):
                continue

        # Brute-force: try adding 1-3 missing ] or } at various positions
        try:
            err = json.loads(text)
            return err  # Shouldn't reach here, but just in case
        except json.JSONDecodeError as e:
            pos = e.pos
            for insert in ['}', ']', '}]', ']}', '}}', ']]']:
                try:
                    return json.loads(text[:pos] + insert + text[pos:])
                except json.JSONDecodeError:
                    continue

        return None

    @staticmethod
    def _wrap_command_as_program(command: dict, name: str = "Quick") -> dict:
        """Wrap a single command in a minimal program structure."""
        return {
            "program": {
                "name": name[:30],
                "steps": [
                    {
                        "id": "main",
                        "command": command,
                        "duration": None,
                    }
                ],
            }
        }

    def _fallback_program(self, user_input: str) -> dict:
        """Simple keyword-based fallback that returns a program."""
        command = self._fallback_command(user_input)
        return self._wrap_command_as_program(command, user_input)

    def _fallback_command(self, user_input: str) -> dict:
        """Simple keyword-based fallback when LLM is unavailable."""
        user_input = user_input.lower()

        if "calm" in user_input or "relax" in user_input:
            return {
                "type": "pattern",
                "name": "breathing",
                "params": {"color": "#4A90D9", "speed": 4000},
            }
        elif "energy" in user_input or "energetic" in user_input:
            return {
                "type": "pattern",
                "name": "rainbow",
                "params": {"speed": 1500},
            }
        elif "warm" in user_input or "cozy" in user_input:
            return {
                "type": "pattern",
                "name": "gradient",
                "params": {"color": "#FF6B4A", "color2": "#FFE4C4"},
            }
        elif "sleep" in user_input or "night" in user_input:
            return {
                "type": "pattern",
                "name": "breathing",
                "params": {"color": "#191970", "speed": 5000},
            }
        elif "off" in user_input or "stop" in user_input:
            return {"type": "stop"}
        else:
            # Default warm gradient
            return {
                "type": "pattern",
                "name": "gradient",
                "params": {"color": "#FF6B4A", "color2": "#FFE4C4"},
            }

    def _autonomous_fallback(self, iteration: int) -> dict:
        """Cycle through patterns when LLM is unavailable."""
        patterns = [
            {"type": "pattern", "name": "gradient", "params": {"color": "#FF6B4A", "color2": "#FFE4C4"}},
            {"type": "pattern", "name": "breathing", "params": {"color": "#4A90D9", "speed": 3000}},
            {"type": "pattern", "name": "wave", "params": {"color": "#FF6B4A", "color2": "#FFE4C4", "speed": 2500}},
            {"type": "pattern", "name": "rainbow", "params": {"speed": 4000}},
        ]
        return patterns[iteration % len(patterns)]


def _send_result(lamp: LampController, result: dict) -> bool:
    """Send an LLM result — either a program or a single command."""
    if "program" in result:
        program = result["program"]
        print(f"Program: {program.get('name', '?')} ({len(program.get('steps', []))} steps)")
        return lamp.send_program(program)
    else:
        return lamp.send_command(result)


def interactive_mode(lamp: LampController, llm: LLMController):
    """Run interactive command-line interface."""
    print("\n🔮 Moonside Lamp Controller")
    print("=" * 40)
    print("Type natural language commands to control the lamp.")
    print("Examples:")
    print("  - 'make it warm and cozy'")
    print("  - 'pomodoro timer 25 min work 5 min break'")
    print("  - 'thunderstorm'")
    print("  - 'turn off'")
    print("Commands: 'status', 'cancel', 'quit'\n")

    while True:
        try:
            user_input = input("🌈 > ").strip()

            if not user_input:
                continue

            if user_input.lower() in ("quit", "exit", "q"):
                print("Goodbye!")
                break

            if user_input.lower() == "status":
                status = lamp.get_program_status()
                if status:
                    print(json.dumps(status, indent=2))
                else:
                    print("Could not get status")
                continue

            if user_input.lower() == "cancel":
                if lamp.cancel_program():
                    print("✓ Program cancelled")
                else:
                    print("✗ Failed to cancel")
                continue

            print("Processing...")
            result = llm.process_input(user_input)

            if result:
                print(f"Output: {json.dumps(result, indent=2)}")
                if _send_result(lamp, result):
                    print("✓ Sent successfully\n")
                else:
                    print("✗ Failed to send\n")
            else:
                print("Could not generate command\n")

        except KeyboardInterrupt:
            print("\nGoodbye!")
            break
        except EOFError:
            break


def autonomous_mode(lamp: LampController, llm: LLMController, interval: int = 30):
    """Run autonomous mode where LLM generates patterns over time."""
    print("\n🔮 Moonside Lamp Controller - Autonomous Mode")
    print("=" * 40)
    print(f"Generating new patterns every {interval} seconds.")
    print("Press Ctrl+C to stop.\n")

    iteration = 0
    previous_pattern = None

    try:
        while True:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] Generating pattern...")

            command = llm.generate_autonomous(iteration, previous_pattern)

            if command:
                print(f"Command: {json.dumps(command)}")
                if lamp.send_command(command):
                    print("✓ Applied\n")
                    previous_pattern = command
                else:
                    print("✗ Failed\n")

            iteration += 1
            time.sleep(interval)

    except KeyboardInterrupt:
        print("\nAutonomous mode stopped.")


def single_command(lamp: LampController, llm: LLMController, command_text: str):
    """Process a single command and exit."""
    print(f"Processing: {command_text}")

    result = llm.process_input(command_text)

    if result:
        print(f"Output: {json.dumps(result, indent=2)}")
        if _send_result(lamp, result):
            print("✓ Success")
        else:
            print("✗ Failed")
            sys.exit(1)
    else:
        print("Could not generate command")
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(description="Control Moonside lamp via LLM")
    parser.add_argument(
        "--command", "-c",
        type=str,
        help="Single command to execute",
    )
    parser.add_argument(
        "--autonomous", "-a",
        action="store_true",
        help="Run in autonomous mode",
    )
    parser.add_argument(
        "--interval", "-i",
        type=int,
        default=30,
        help="Interval between autonomous commands (seconds)",
    )
    parser.add_argument(
        "--server",
        type=str,
        default=LAMP_SERVER_URL,
        help="Lamp server URL",
    )
    parser.add_argument(
        "--model",
        type=str,
        default=OLLAMA_MODEL,
        help="Ollama model to use",
    )

    args = parser.parse_args()

    lamp = LampController(args.server)
    llm = LLMController(args.model)

    # Test connection
    state = lamp.get_state()
    if state is None:
        print("Warning: Cannot connect to lamp server. Commands will fail.")

    if args.command:
        single_command(lamp, llm, args.command)
    elif args.autonomous:
        autonomous_mode(lamp, llm, args.interval)
    else:
        interactive_mode(lamp, llm)


if __name__ == "__main__":
    main()
