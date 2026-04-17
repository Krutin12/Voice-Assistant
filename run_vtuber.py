#!/usr/bin/env python3
"""
Wizard Voice Assistant Launcher
Starts the 3D character + voice assistant together.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

if __name__ == "__main__":
    from wizard.main import main
    try:
        main(continuous_mode=True, wake_word_mode=False)
    except KeyboardInterrupt:
        print("\n🛑 Voice Assistant closed securely via Keyboard Interrupt (Ctrl+C). Goodbye!")
        sys.exit(0)
