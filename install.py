#!/usr/bin/env python3
"""
Quick Installation Script for Wizard Voice Assistant
Simplified setup for basic installation
"""

import os
import sys
import subprocess
import platform
from pathlib import Path

def quick_install():
    """Quick installation with minimal configuration"""
    print("🚀 Wizard Voice Assistant - Quick Install")
    print("=" * 40)
    
    # Check Python version
    if sys.version_info < (3, 8):
        print(f"❌ Python 3.8+ required. Current: {sys.version}")
        return False
    
    print(f"✅ Python {sys.version_info.major}.{sys.version_info.minor} detected")
    
    # Install dependencies
    print("\n📦 Installing dependencies...")
    try:
        subprocess.run([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"], 
                      check=True)
        print("✅ Dependencies installed")
    except subprocess.CalledProcessError:
        print("❌ Failed to install dependencies")
        return False
    
    # Create basic directories
    print("\n📁 Creating directories...")
    directories = ["logs", "audio_cache", "config"]
    for directory in directories:
        Path(directory).mkdir(exist_ok=True)
    print("✅ Directories created")
    
    # Create basic config
    print("\n⚙️  Creating basic configuration...")
    config_content = """{
  "assistant_name": "Wizard",
  "wake_words": ["Hey Wizard", "Wizard"],
  "voice": {
    "gender": "female",
    "speed": 1.0,
    "volume": 0.8
  },
  "security": {
    "require_confirmation": true,
    "safe_mode": false
  },
  "applications": {}
}"""
    
    config_file = Path("config/wizard_config.json")
    config_file.parent.mkdir(exist_ok=True)
    with open(config_file, 'w') as f:
        f.write(config_content)
    print("✅ Basic configuration created")
    
    print("\n🎉 Quick installation complete!")
    print("\nTo start Wizard:")
    print("  python wizard/main.py")
    print("\nFor full setup with customization:")
    print("  python setup.py")
    
    return True

if __name__ == "__main__":
    success = quick_install()
    sys.exit(0 if success else 1)