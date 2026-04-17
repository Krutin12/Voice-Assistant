import sys
import os
from pathlib import Path

# Fix encoding
try:
    sys.stdout.reconfigure(encoding='utf-8')
except AttributeError:
    pass

sys.path.insert(0, str(Path(__file__).parent))

from wizard.commands.command_router import route_command

print("="*50)
print("  Test Task: Sending a Message")
print("="*50)

command = "send a hello world message to john"
print(f"Q: '{command}'")
response = route_command(command)

# Match Voice Loop logic in main.py
if "couldn't find" in response.lower() or "not sure" in response.lower():
    from wizard.data.ai_brain import AIBrain
    print("-> Triggering AI Brain natural language backup...")
    try:
        brain = AIBrain()
        response = brain.process_query(command)
    except Exception as e:
        response = f"AI Error: {e}"

print(f"\nA: {response}")
print("="*50)
