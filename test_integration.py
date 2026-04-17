import sys
import os
import time
from unittest.mock import patch
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

# Keep track of how many times the microphone is polled
mock_interactions = [
    ("what is artificial intelligence?", "en"),  # First command
    ("tell me a joke", "en"),                    # Second command
    ("exit program", "en")                       # Third command cleans up
]
call_count = 0

def mock_speech_to_text(recognizer, microphone):
    global call_count
    if call_count < len(mock_interactions):
        # Human delay before asking
        time.sleep(2)
        cmd, lang = mock_interactions[call_count]
        call_count += 1
        print(f"\n[Mock Microphone 🎤] -> User says: '{cmd}'")
        return cmd, lang
    
    # Just hang so the GUI stays open until user closes testing
    time.sleep(1)
    return "", "en"

if __name__ == "__main__":
    print("==================================================")
    print(" 🧪 INTEGRATION TEST: FULL E2E VOICE <-> 3D UI")
    print("==================================================")
    print("[INFO] Substituting microphone loop with AI Test Payload...")
    
    # Execute the PyWebView integration block!
    import runpy
    import wizard.main
    import wizard.audio.speech_recognition
    
    # We patch the STT function so we don't need a real microphone for the test!
    wizard.audio.speech_recognition.speech_to_text = mock_speech_to_text
    
    # Run the main __main__ execution
    runpy.run_path("wizard/main.py", run_name="__main__")
