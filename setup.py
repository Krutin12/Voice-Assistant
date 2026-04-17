#!/usr/bin/env python3
"""
Wizard Voice Assistant Setup Script
Automated installation and configuration system
"""

import os
import sys
import subprocess
import platform
import json
import shutil
from pathlib import Path
from typing import Dict, List, Optional

class WizardSetup:
    """Main setup class for Wizard Voice Assistant"""
    
    def __init__(self):
        self.system = platform.system().lower()
        self.python_version = sys.version_info
        self.wizard_dir = Path(__file__).parent
        self.config_dir = self.wizard_dir / "config"
        self.data_dir = self.wizard_dir / "wizard" / "data"
        
    def check_python_version(self) -> bool:
        """Check if Python version meets requirements"""
        if self.python_version < (3, 8):
            print(f"❌ Python 3.8+ required. Current version: {sys.version}")
            return False
        elif self.python_version >= (3, 13):
            print(f"⚠️  Python {sys.version} detected. Some packages may have compatibility issues.")
            print("   Consider using Python 3.11 or 3.12 for best compatibility.")
        print(f"✅ Python version {sys.version} is compatible")
        return True
    
    def check_system_requirements(self) -> bool:
        """Check system-specific requirements"""
        print(f"🔍 Checking system requirements for {self.system}...")
        
        if self.system == "windows":
            return self._check_windows_requirements()
        elif self.system == "darwin":  # macOS
            return self._check_macos_requirements()
        elif self.system == "linux":
            return self._check_linux_requirements()
        else:
            print(f"⚠️  Unsupported system: {self.system}")
            return False
    
    def _check_windows_requirements(self) -> bool:
        """Check Windows-specific requirements"""
        try:
            import win32api
            print("✅ Windows API access available")
            return True
        except ImportError:
            print("⚠️  Windows API not available - will install pywin32")
            return True
    
    def _check_macos_requirements(self) -> bool:
        """Check macOS-specific requirements"""
        # Check for Homebrew (optional but recommended)
        if shutil.which("brew"):
            print("✅ Homebrew detected")
        else:
            print("⚠️  Homebrew not found - some features may be limited")
        return True
    
    def _check_linux_requirements(self) -> bool:
        """Check Linux-specific requirements"""
        # Check for audio system
        audio_systems = ["pulseaudio", "alsa"]
        for system in audio_systems:
            if shutil.which(system):
                print(f"✅ Audio system {system} detected")
                return True
        print("⚠️  No audio system detected - may need manual configuration")
        return True
    
    def install_dependencies(self) -> bool:
        """Install Python dependencies"""
        print("📦 Installing Python dependencies...")
        
        try:
            # Upgrade pip first
            subprocess.run([sys.executable, "-m", "pip", "install", "--upgrade", "pip"], 
                         check=True, capture_output=True)
            
            # Install requirements with error handling for Python 3.13
            requirements_file = self.wizard_dir / "requirements.txt"
            if requirements_file.exists():
                try:
                    subprocess.run([sys.executable, "-m", "pip", "install", "-r", str(requirements_file)], 
                                 check=True)
                    print("✅ Dependencies installed successfully")
                    return True
                except subprocess.CalledProcessError as e:
                    print(f"⚠️  Some dependencies failed to install. Trying individual packages...")
                    return self._install_dependencies_individually()
            else:
                print("❌ requirements.txt not found")
                return False
                
        except subprocess.CalledProcessError as e:
            print(f"❌ Failed to upgrade pip: {e}")
            print("Continuing with dependency installation...")
            return self._install_dependencies_individually()
    
    def _install_dependencies_individually(self) -> bool:
        """Install dependencies one by one, skipping problematic ones"""
        essential_packages = [
            "pyttsx3==2.90",
            "SpeechRecognition==3.10.0", 
            "requests==2.31.0",
            "nltk==3.8.1",
            "psutil==5.9.5",
            "pyyaml==6.0.1",
            "click==8.1.6"
        ]
        
        optional_packages = [
            "pyaudio==0.2.11",  # May fail on some systems
            "vosk==0.3.45",     # May not be available for Python 3.13
            "pydub==0.25.1",
            "gTTS==2.3.2"
        ]
        
        success_count = 0
        
        # Install essential packages
        for package in essential_packages:
            try:
                subprocess.run([sys.executable, "-m", "pip", "install", package], 
                             check=True, capture_output=True)
                print(f"✅ Installed {package}")
                success_count += 1
            except subprocess.CalledProcessError:
                print(f"❌ Failed to install {package}")
        
        # Try optional packages
        for package in optional_packages:
            try:
                subprocess.run([sys.executable, "-m", "pip", "install", package], 
                             check=True, capture_output=True)
                print(f"✅ Installed {package}")
                success_count += 1
            except subprocess.CalledProcessError:
                print(f"⚠️  Optional package {package} failed to install (this is okay)")
        
        if success_count >= len(essential_packages):
            print("✅ Essential dependencies installed successfully")
            return True
        else:
            print("❌ Failed to install essential dependencies")
            return False
    
    def setup_directories(self) -> bool:
        """Create necessary directories"""
        print("📁 Setting up directories...")
        
        directories = [
            self.config_dir,
            self.data_dir,
            self.wizard_dir / "logs",
            self.wizard_dir / "audio_cache",
            Path.home() / ".wizard",
            Path.home() / ".wizard" / "backups",
            Path.home() / ".wizard" / "user_data"
        ]
        
        try:
            for directory in directories:
                directory.mkdir(parents=True, exist_ok=True)
                print(f"✅ Created directory: {directory}")
            return True
        except Exception as e:
            print(f"❌ Failed to create directories: {e}")
            return False
    
    def run_configuration_wizard(self) -> bool:
        """Run interactive configuration wizard"""
        print("\n🧙 Welcome to the Wizard Voice Assistant Configuration Wizard!")
        print("This will help you set up your personalized voice assistant.\n")
        
        config = {}
        
        # Basic settings
        config["assistant_name"] = input("What would you like to call your assistant? [Wizard]: ").strip() or "Wizard"
        
        # Wake words
        print(f"\nWake words are phrases that activate {config['assistant_name']}.")
        default_wake_words = [f"Hey {config['assistant_name']}", config['assistant_name']]
        wake_words_input = input(f"Enter wake words (comma-separated) [{', '.join(default_wake_words)}]: ").strip()
        
        if wake_words_input:
            config["wake_words"] = [word.strip() for word in wake_words_input.split(",")]
        else:
            config["wake_words"] = default_wake_words
        
        # Voice settings
        print("\n🎵 Voice Settings")
        config["voice"] = {}
        config["voice"]["gender"] = input("Preferred voice gender (male/female) [female]: ").strip().lower() or "female"
        
        try:
            speed = input("Speech speed (0.5-2.0) [1.0]: ").strip()
            config["voice"]["speed"] = float(speed) if speed else 1.0
        except ValueError:
            config["voice"]["speed"] = 1.0
        
        try:
            volume = input("Voice volume (0.0-1.0) [0.8]: ").strip()
            config["voice"]["volume"] = float(volume) if volume else 0.8
        except ValueError:
            config["voice"]["volume"] = 0.8
        
        # Security settings
        print("\n🔒 Security Settings")
        config["security"] = {}
        config["security"]["require_confirmation"] = input("Require confirmation for system operations? (y/n) [y]: ").strip().lower() != "n"
        config["security"]["safe_mode"] = input("Enable safe mode (limited commands)? (y/n) [n]: ").strip().lower() == "y"
        
        # Applications
        print("\n📱 Application Settings")
        config["applications"] = {}
        
        common_apps = {
            "browser": "Default browser",
            "music": "Music player (Spotify, iTunes, etc.)",
            "email": "Email client",
            "calculator": "Calculator app"
        }
        
        for app_key, app_desc in common_apps.items():
            app_path = input(f"Path to {app_desc} (optional): ").strip()
            if app_path:
                config["applications"][app_key] = app_path
        
        # Save configuration
        config_file = self.config_dir / "wizard_config.json"
        try:
            with open(config_file, 'w') as f:
                json.dump(config, f, indent=2)
            print(f"\n✅ Configuration saved to {config_file}")
            return True
        except Exception as e:
            print(f"❌ Failed to save configuration: {e}")
            return False
    
    def setup_startup_integration(self) -> bool:
        """Set up system startup integration"""
        print("\n🚀 Setting up startup integration...")
        
        if input("Would you like Wizard to start automatically on boot? (y/n) [n]: ").strip().lower() == "y":
            return self._create_startup_entry()
        else:
            print("⏭️  Skipping startup integration")
            return True
    
    def _create_startup_entry(self) -> bool:
        """Create system-specific startup entry"""
        try:
            if self.system == "windows":
                return self._create_windows_startup()
            elif self.system == "darwin":
                return self._create_macos_startup()
            elif self.system == "linux":
                return self._create_linux_startup()
            else:
                print(f"⚠️  Startup integration not supported for {self.system}")
                return False
        except Exception as e:
            print(f"❌ Failed to create startup entry: {e}")
            return False
    
    def _create_windows_startup(self) -> bool:
        """Create Windows startup entry"""
        import winreg
        
        key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
        app_name = "WizardVoiceAssistant"
        app_path = f'"{sys.executable}" "{self.wizard_dir / "wizard" / "main.py"}"'
        
        try:
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_SET_VALUE)
            winreg.SetValueEx(key, app_name, 0, winreg.REG_SZ, app_path)
            winreg.CloseKey(key)
            print("✅ Windows startup entry created")
            return True
        except Exception as e:
            print(f"❌ Failed to create Windows startup entry: {e}")
            return False
    
    def _create_macos_startup(self) -> bool:
        """Create macOS startup entry (LaunchAgent)"""
        plist_content = f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.wizard.voiceassistant</string>
    <key>ProgramArguments</key>
    <array>
        <string>{sys.executable}</string>
        <string>{self.wizard_dir / "wizard" / "main.py"}</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
</dict>
</plist>"""
        
        launch_agents_dir = Path.home() / "Library" / "LaunchAgents"
        launch_agents_dir.mkdir(exist_ok=True)
        
        plist_file = launch_agents_dir / "com.wizard.voiceassistant.plist"
        with open(plist_file, 'w') as f:
            f.write(plist_content)
        
        print("✅ macOS LaunchAgent created")
        return True
    
    def _create_linux_startup(self) -> bool:
        """Create Linux startup entry (desktop file)"""
        desktop_content = f"""[Desktop Entry]
Type=Application
Name=Wizard Voice Assistant
Exec={sys.executable} {self.wizard_dir / "wizard" / "main.py"}
Hidden=false
NoDisplay=false
X-GNOME-Autostart-enabled=true
"""
        
        autostart_dir = Path.home() / ".config" / "autostart"
        autostart_dir.mkdir(parents=True, exist_ok=True)
        
        desktop_file = autostart_dir / "wizard-voice-assistant.desktop"
        with open(desktop_file, 'w') as f:
            f.write(desktop_content)
        
        # Make executable
        os.chmod(desktop_file, 0o755)
        
        print("✅ Linux autostart entry created")
        return True
    
    def download_models(self) -> bool:
        """Download required offline models"""
        print("\n📥 Downloading offline models...")
        
        try:
            # Download NLTK data
            import nltk
            nltk.download('punkt', quiet=True)
            nltk.download('stopwords', quiet=True)
            nltk.download('wordnet', quiet=True)
            print("✅ NLTK data downloaded")
            
            # Download Vosk model (small English model)
            vosk_model_dir = self.data_dir / "vosk_model"
            if not vosk_model_dir.exists():
                print("📥 Downloading Vosk speech recognition model...")
                # This would typically download from Vosk's repository
                # For now, we'll create a placeholder
                vosk_model_dir.mkdir(parents=True, exist_ok=True)
                print("✅ Vosk model directory created (manual download may be required)")
            
            return True
        except Exception as e:
            print(f"⚠️  Model download failed: {e}")
            print("You may need to download models manually")
            return True  # Don't fail setup for this
    
    def run_setup(self) -> bool:
        """Run complete setup process"""
        print("🧙 Welcome to Wizard Voice Assistant Setup!")
        print("=" * 50)
        
        steps = [
            ("Checking Python version", self.check_python_version),
            ("Checking system requirements", self.check_system_requirements),
            ("Installing dependencies", self.install_dependencies),
            ("Setting up directories", self.setup_directories),
            ("Running configuration wizard", self.run_configuration_wizard),
            ("Downloading models", self.download_models),
            ("Setting up startup integration", self.setup_startup_integration),
        ]
        
        for step_name, step_func in steps:
            print(f"\n📋 {step_name}...")
            if not step_func():
                print(f"❌ Setup failed at: {step_name}")
                return False
        
        print("\n🎉 Setup completed successfully!")
        print("\nNext steps:")
        print("1. Run 'python wizard/main.py' to start Wizard")
        print("2. Say your wake word to activate the assistant")
        print("3. Try commands like 'What time is it?' or 'Open calculator'")
        print("\nFor help, see the documentation in the 'docs' folder")
        
        return True

def main():
    """Main setup entry point"""
    if len(sys.argv) > 1 and sys.argv[1] == "--help":
        print("Wizard Voice Assistant Setup")
        print("Usage: python setup.py [--help]")
        print("\nThis script will:")
        print("- Check system requirements")
        print("- Install Python dependencies")
        print("- Run configuration wizard")
        print("- Set up startup integration")
        print("- Download required models")
        return
    
    setup = WizardSetup()
    success = setup.run_setup()
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()