#!/usr/bin/env python3
"""
Wizard Voice Assistant Startup Script
Cross-platform startup script with system integration
"""

import os
import sys
import subprocess
import platform
import json
import time
from pathlib import Path
from typing import Optional

class WizardStarter:
    """Handles starting Wizard with proper initialization"""
    
    def __init__(self):
        self.system = platform.system().lower()
        self.wizard_dir = Path(__file__).parent
        self.config_file = self.wizard_dir / "config" / "wizard_config.json"
        self.main_script = self.wizard_dir / "wizard" / "main.py"
        
    def check_prerequisites(self) -> bool:
        """Check if all prerequisites are met"""
        print("🔍 Checking prerequisites...")
        
        # Check if main script exists
        if not self.main_script.exists():
            print(f"❌ Main script not found: {self.main_script}")
            return False
        
        # Check if configuration exists
        if not self.config_file.exists():
            print("⚠️  Configuration not found. Running quick setup...")
            return self.run_quick_setup()
        
        # Check Python dependencies
        try:
            import pyttsx3
            import speech_recognition
            print("✅ Core dependencies available")
            return True
        except ImportError as e:
            print(f"❌ Missing dependency: {e}")
            print("Run 'python install.py' to install dependencies")
            return False
    
    def run_quick_setup(self) -> bool:
        """Run minimal setup if configuration is missing"""
        try:
            from configure import WizardConfigurator
            configurator = WizardConfigurator()
            
            # Create minimal config
            minimal_config = {
                "assistant_name": "Wizard",
                "wake_words": ["Hey Wizard", "Wizard"],
                "voice": {"gender": "female", "speed": 1.0, "volume": 0.8},
                "security": {"require_confirmation": True, "safe_mode": False},
                "applications": {},
                "preferences": {"response_style": "friendly"}
            }
            
            configurator.config = minimal_config
            return configurator.save_config()
        except Exception as e:
            print(f"❌ Quick setup failed: {e}")
            return False
    
    def load_config(self) -> Optional[dict]:
        """Load Wizard configuration"""
        try:
            with open(self.config_file, 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"❌ Failed to load configuration: {e}")
            return None
    
    def check_audio_devices(self) -> bool:
        """Check if audio input/output devices are available"""
        try:
            import pyaudio
            
            audio = pyaudio.PyAudio()
            
            # Check for input devices
            input_devices = []
            output_devices = []
            
            for i in range(audio.get_device_count()):
                device_info = audio.get_device_info_by_index(i)
                if device_info['maxInputChannels'] > 0:
                    input_devices.append(device_info['name'])
                if device_info['maxOutputChannels'] > 0:
                    output_devices.append(device_info['name'])
            
            audio.terminate()
            
            if not input_devices:
                print("❌ No audio input devices found")
                return False
            
            if not output_devices:
                print("❌ No audio output devices found")
                return False
            
            print(f"✅ Audio devices: {len(input_devices)} input, {len(output_devices)} output")
            return True
            
        except Exception as e:
            print(f"⚠️  Audio device check failed: {e}")
            return True  # Don't fail startup for this
    
    def set_environment_variables(self, config: dict):
        """Set environment variables for Wizard"""
        # Set assistant name
        os.environ['WIZARD_NAME'] = config.get('assistant_name', 'Wizard')
        
        # Set voice preferences
        voice_config = config.get('voice', {})
        os.environ['WIZARD_VOICE_GENDER'] = voice_config.get('gender', 'female')
        os.environ['WIZARD_VOICE_SPEED'] = str(voice_config.get('speed', 1.0))
        os.environ['WIZARD_VOICE_VOLUME'] = str(voice_config.get('volume', 0.8))
        
        # Set security preferences
        security_config = config.get('security', {})
        os.environ['WIZARD_REQUIRE_CONFIRMATION'] = str(security_config.get('require_confirmation', True))
        os.environ['WIZARD_SAFE_MODE'] = str(security_config.get('safe_mode', False))
    
    def start_wizard(self, background: bool = False) -> bool:
        """Start the Wizard voice assistant"""
        print("🚀 Starting Wizard Voice Assistant...")
        
        try:
            if background:
                # Start in background (daemon mode)
                if self.system == "windows":
                    # Use pythonw to run without console window
                    pythonw = sys.executable.replace("python.exe", "pythonw.exe")
                    if Path(pythonw).exists():
                        subprocess.Popen([pythonw, str(self.main_script)], 
                                       creationflags=subprocess.CREATE_NO_WINDOW)
                    else:
                        subprocess.Popen([sys.executable, str(self.main_script)],
                                       creationflags=subprocess.CREATE_NO_WINDOW)
                else:
                    # Unix-like systems
                    subprocess.Popen([sys.executable, str(self.main_script)],
                                   stdout=subprocess.DEVNULL,
                                   stderr=subprocess.DEVNULL)
                
                print("✅ Wizard started in background")
                return True
            else:
                # Start in foreground
                result = subprocess.run([sys.executable, str(self.main_script)])
                return result.returncode == 0
                
        except Exception as e:
            print(f"❌ Failed to start Wizard: {e}")
            return False
    
    def create_desktop_shortcut(self) -> bool:
        """Create desktop shortcut for easy access"""
        try:
            if self.system == "windows":
                return self._create_windows_shortcut()
            elif self.system == "darwin":
                return self._create_macos_shortcut()
            elif self.system == "linux":
                return self._create_linux_shortcut()
            else:
                print(f"⚠️  Shortcut creation not supported for {self.system}")
                return False
        except Exception as e:
            print(f"❌ Failed to create shortcut: {e}")
            return False
    
    def _create_windows_shortcut(self) -> bool:
        """Create Windows desktop shortcut"""
        try:
            import win32com.client
            
            desktop = Path.home() / "Desktop"
            shortcut_path = desktop / "Wizard Voice Assistant.lnk"
            
            shell = win32com.client.Dispatch("WScript.Shell")
            shortcut = shell.CreateShortCut(str(shortcut_path))
            shortcut.Targetpath = sys.executable
            shortcut.Arguments = f'"{self.main_script}"'
            shortcut.WorkingDirectory = str(self.wizard_dir)
            shortcut.IconLocation = sys.executable
            shortcut.save()
            
            print(f"✅ Desktop shortcut created: {shortcut_path}")
            return True
        except ImportError:
            print("⚠️  pywin32 not available for shortcut creation")
            return False
    
    def _create_macos_shortcut(self) -> bool:
        """Create macOS application bundle"""
        app_dir = Path.home() / "Applications" / "Wizard Voice Assistant.app"
        contents_dir = app_dir / "Contents"
        macos_dir = contents_dir / "MacOS"
        
        # Create directory structure
        macos_dir.mkdir(parents=True, exist_ok=True)
        
        # Create Info.plist
        plist_content = f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>CFBundleExecutable</key>
    <string>wizard</string>
    <key>CFBundleIdentifier</key>
    <string>com.wizard.voiceassistant</string>
    <key>CFBundleName</key>
    <string>Wizard Voice Assistant</string>
    <key>CFBundleVersion</key>
    <string>1.0</string>
</dict>
</plist>"""
        
        with open(contents_dir / "Info.plist", 'w') as f:
            f.write(plist_content)
        
        # Create executable script
        script_content = f"""#!/bin/bash
cd "{self.wizard_dir}"
"{sys.executable}" "{self.main_script}"
"""
        
        script_file = macos_dir / "wizard"
        with open(script_file, 'w') as f:
            f.write(script_content)
        
        os.chmod(script_file, 0o755)
        
        print(f"✅ macOS app bundle created: {app_dir}")
        return True
    
    def _create_linux_shortcut(self) -> bool:
        """Create Linux desktop entry"""
        desktop_dir = Path.home() / "Desktop"
        applications_dir = Path.home() / ".local" / "share" / "applications"
        
        desktop_content = f"""[Desktop Entry]
Version=1.0
Type=Application
Name=Wizard Voice Assistant
Comment=AI Voice Assistant
Exec={sys.executable} {self.main_script}
Icon=audio-headphones
Terminal=false
Categories=Utility;AudioVideo;
"""
        
        # Create in both locations
        for directory in [desktop_dir, applications_dir]:
            directory.mkdir(parents=True, exist_ok=True)
            desktop_file = directory / "wizard-voice-assistant.desktop"
            
            with open(desktop_file, 'w') as f:
                f.write(desktop_content)
            
            os.chmod(desktop_file, 0o755)
        
        print("✅ Linux desktop entries created")
        return True
    
    def run_startup_sequence(self, background: bool = False, create_shortcut: bool = False) -> bool:
        """Run complete startup sequence"""
        print("🧙 Wizard Voice Assistant Startup")
        print("=" * 35)
        
        # Check prerequisites
        if not self.check_prerequisites():
            return False
        
        # Load configuration
        config = self.load_config()
        if not config:
            return False
        
        # Check audio devices
        self.check_audio_devices()
        
        # Set environment variables
        self.set_environment_variables(config)
        
        # Create shortcut if requested
        if create_shortcut:
            self.create_desktop_shortcut()
        
        # Start Wizard
        return self.start_wizard(background)

def main():
    """Main startup entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Start Wizard Voice Assistant")
    parser.add_argument("--background", "-b", action="store_true",
                       help="Start in background mode")
    parser.add_argument("--create-shortcut", "-s", action="store_true",
                       help="Create desktop shortcut")
    parser.add_argument("--check", "-c", action="store_true",
                       help="Check prerequisites only")
    
    args = parser.parse_args()
    
    starter = WizardStarter()
    
    if args.check:
        success = starter.check_prerequisites()
        print("✅ All prerequisites met" if success else "❌ Prerequisites check failed")
        sys.exit(0 if success else 1)
    
    success = starter.run_startup_sequence(
        background=args.background,
        create_shortcut=args.create_shortcut
    )
    
    if success:
        if args.background:
            print("\n🎉 Wizard is now running in the background!")
            print("Say your wake word to activate the assistant.")
        else:
            print("\n👋 Wizard has stopped.")
    else:
        print("\n❌ Failed to start Wizard")
        sys.exit(1)

if __name__ == "__main__":
    main()