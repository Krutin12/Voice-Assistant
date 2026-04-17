#!/usr/bin/env python3
"""
Python 3.13 Compatible Installation Script for Wizard Voice Assistant
Handles compatibility issues with newer Python versions
"""

import os
import sys
import subprocess
import platform
from pathlib import Path

def install_essential_packages():
    """Install essential packages that work with Python 3.13"""
    print("🐍 Python 3.13 Compatible Installation")
    print("=" * 40)
    
    # Check Python version
    if sys.version_info < (3, 8):
        print(f"❌ Python 3.8+ required. Current: {sys.version}")
        return False
    
    print(f"✅ Python {sys.version_info.major}.{sys.version_info.minor} detected")
    
    # Essential packages that should work with Python 3.13
    essential_packages = [
        "pyttsx3",           # Text-to-speech
        "requests",          # HTTP requests
        "nltk",              # Natural language processing
        "psutil",            # System utilities
        "pyyaml",            # YAML support
        "click",             # CLI interface
        "rich",              # Rich text output
        "colorlog",          # Colored logging
        "python-dateutil",   # Date utilities
        "pytz",              # Timezone support
        "schedule",          # Task scheduling
        "pytest",            # Testing framework
        "fuzzywuzzy",        # Fuzzy string matching
        "beautifulsoup4",    # Web scraping
        "feedparser",        # RSS parsing
        "watchdog",          # File monitoring
        "plyer",             # Cross-platform features
        "appdirs",           # App directories
        "cryptography",      # Security
        "bcrypt",            # Password hashing
        "cachetools",        # Caching
        "tqdm",              # Progress bars
        "toml"               # TOML support
    ]
    
    # Optional packages (may fail on Python 3.13)
    optional_packages = [
        "numpy",             # Numerical computing
        "pandas",            # Data manipulation
        "sympy",             # Symbolic math
        "python-Levenshtein" # Fast string matching
    ]
    
    print("\n📦 Installing essential packages...")
    
    # Upgrade pip first
    try:
        subprocess.run([sys.executable, "-m", "pip", "install", "--upgrade", "pip"], 
                      check=True, capture_output=True)
        print("✅ Pip upgraded successfully")
    except subprocess.CalledProcessError:
        print("⚠️  Pip upgrade failed, continuing...")
    
    # Install essential packages
    success_count = 0
    failed_packages = []
    
    for package in essential_packages:
        try:
            print(f"  Installing {package}...")
            subprocess.run([sys.executable, "-m", "pip", "install", package], 
                          check=True, capture_output=True)
            success_count += 1
        except subprocess.CalledProcessError:
            print(f"  ❌ Failed to install {package}")
            failed_packages.append(package)
    
    print(f"\n✅ Installed {success_count}/{len(essential_packages)} essential packages")
    
    # Try optional packages
    print("\n📦 Installing optional packages...")
    optional_success = 0
    
    for package in optional_packages:
        try:
            print(f"  Installing {package}...")
            subprocess.run([sys.executable, "-m", "pip", "install", package], 
                          check=True, capture_output=True)
            optional_success += 1
        except subprocess.CalledProcessError:
            print(f"  ⚠️  Optional package {package} failed (this is okay)")
    
    print(f"✅ Installed {optional_success}/{len(optional_packages)} optional packages")
    
    # Audio packages (likely to fail on Python 3.13)
    print("\n🎵 Attempting audio packages (may fail on Python 3.13)...")
    audio_packages = ["SpeechRecognition", "pyaudio", "pydub", "gTTS"]
    audio_success = 0
    
    for package in audio_packages:
        try:
            print(f"  Installing {package}...")
            subprocess.run([sys.executable, "-m", "pip", "install", package], 
                          check=True, capture_output=True)
            audio_success += 1
            print(f"  ✅ {package} installed successfully!")
        except subprocess.CalledProcessError:
            print(f"  ❌ {package} failed (expected on Python 3.13)")
    
    if audio_success == 0:
        print("\n⚠️  Audio packages failed to install.")
        print("   This is expected on Python 3.13. You can:")
        print("   1. Use text-only mode for now")
        print("   2. Install Python 3.11 or 3.12 for full audio support")
        print("   3. Try manual installation of audio packages later")
    
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
  "applications": {},
  "audio_enabled": false,
  "text_mode": true,
  "python_version": "3.13"
}"""
    
    config_file = Path("config/wizard_config.json")
    config_file.parent.mkdir(exist_ok=True)
    with open(config_file, 'w') as f:
        f.write(config_content)
    print("✅ Basic configuration created")
    
    # Summary
    print(f"\n🎉 Installation Summary:")
    print(f"  Essential packages: {success_count}/{len(essential_packages)}")
    print(f"  Optional packages: {optional_success}/{len(optional_packages)}")
    print(f"  Audio packages: {audio_success}/{len(audio_packages)}")
    
    if failed_packages:
        print(f"\n❌ Failed packages: {', '.join(failed_packages)}")
    
    if success_count >= len(essential_packages) * 0.8:  # 80% success rate
        print(f"\n✅ Installation completed successfully!")
        print(f"\nNext steps:")
        print(f"  1. Run 'python wizard/main.py' to start Wizard")
        print(f"  2. Use text-based commands for now")
        print(f"  3. Consider Python 3.11/3.12 for full audio support")
        return True
    else:
        print(f"\n❌ Installation had significant issues.")
        print(f"   Consider using Python 3.11 or 3.12 for better compatibility.")
        return False

def main():
    """Main installation entry point"""
    success = install_essential_packages()
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()