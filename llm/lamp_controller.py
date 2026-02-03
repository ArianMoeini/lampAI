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

    def __init__(self, model: str = OLLAMA_MODEL):
        self.model = model
        self.system_prompt = LAMP_CONTROLLER_SYSTEM_PROMPT

    def process_input(self, user_input: str) -> dict | None:
        """Convert natural language to lamp command."""
        if not HAS_OLLAMA:
            print("Ollama not available. Using fallback command.")
            return self._fallback_command(user_input)

        try:
            prompt = MOOD_MAPPING_PROMPT.format(input=user_input)

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
            return self._fallback_command(user_input)

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
        """Extract JSON from LLM response."""
        # Try to find JSON in the response
        text = text.strip()

        # Remove markdown code blocks if present
        if text.startswith("```"):
            text = re.sub(r"```(?:json)?\n?", "", text)
            text = text.rstrip("`").strip()

        # Try direct parse
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            pass

        # Try to find JSON object in text
        match = re.search(r"\{[^{}]*\}", text, re.DOTALL)
        if match:
            try:
                return json.loads(match.group())
            except json.JSONDecodeError:
                pass

        print(f"Could not parse JSON from: {text[:100]}...")
        return None

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


def interactive_mode(lamp: LampController, llm: LLMController):
    """Run interactive command-line interface."""
    print("\n🔮 Moonside Lamp Controller")
    print("=" * 40)
    print("Type natural language commands to control the lamp.")
    print("Examples:")
    print("  - 'make it warm and cozy'")
    print("  - 'calm blue breathing'")
    print("  - 'energetic rainbow'")
    print("  - 'turn off'")
    print("Type 'quit' or 'exit' to stop.\n")

    while True:
        try:
            user_input = input("🌈 > ").strip()

            if not user_input:
                continue

            if user_input.lower() in ("quit", "exit", "q"):
                print("Goodbye!")
                break

            print("Processing...")
            command = llm.process_input(user_input)

            if command:
                print(f"Command: {json.dumps(command, indent=2)}")
                if lamp.send_command(command):
                    print("✓ Command sent successfully\n")
                else:
                    print("✗ Failed to send command\n")
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

    command = llm.process_input(command_text)

    if command:
        print(f"Command: {json.dumps(command, indent=2)}")
        if lamp.send_command(command):
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
