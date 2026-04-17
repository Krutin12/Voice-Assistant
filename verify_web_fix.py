
import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from wizard.commands.command_router import CommandRouter
from wizard.utils.config_manager import ConfigManager

def test_web_patterns():
    print("Testing Web Patterns...")
    # Create a dummy config
    config = {
        "applications": {}
    }
    router = CommandRouter(config)
    
    test_cases = [
        "open apple website",
        "open microsoft official site",
        "go to google.com",
        "visit wikipedia",
        "open apple phone website"
    ]
    
    for cmd_text in test_cases:
        command = router.parse_command(cmd_text)
        print(f"Command: '{cmd_text}' -> Intent: {command.intent}, Entities: {command.entities}")

if __name__ == "__main__":
    test_web_patterns()
