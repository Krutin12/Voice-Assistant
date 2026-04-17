#!/usr/bin/env python3
"""
Wizard Voice Assistant Configuration Tool
Interactive configuration wizard for customizing settings
"""

import json
import os
import sys
from pathlib import Path
from typing import Dict, Any

class WizardConfigurator:
    """Interactive configuration wizard"""
    
    def __init__(self):
        self.config_dir = Path("config")
        self.config_file = self.config_dir / "wizard_config.json"
        self.config = self.load_existing_config()
    
    def load_existing_config(self) -> Dict[str, Any]:
        """Load existing configuration or create default"""
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                print(f"⚠️  Error loading config: {e}")
        
        # Default configuration
        return {
            "assistant_name": "Wizard",
            "wake_words": ["Hey Wizard", "Wizard"],
            "voice": {
                "gender": "female",
                "speed": 1.0,
                "volume": 0.8
            },
            "security": {
                "require_confirmation": True,
                "safe_mode": False
            },
            "applications": {},
            "preferences": {
                "response_style": "friendly",
                "detailed_responses": True,
                "learning_enabled": True
            }
        }
    
    def save_config(self) -> bool:
        """Save configuration to file"""
        try:
            self.config_dir.mkdir(exist_ok=True)
            with open(self.config_file, 'w') as f:
                json.dump(self.config, f, indent=2)
            print(f"✅ Configuration saved to {self.config_file}")
            return True
        except Exception as e:
            print(f"❌ Failed to save configuration: {e}")
            return False
    
    def configure_basic_settings(self):
        """Configure basic assistant settings"""
        print("\n🧙 Basic Settings")
        print("-" * 20)
        
        current_name = self.config.get("assistant_name", "Wizard")
        new_name = input(f"Assistant name [{current_name}]: ").strip()
        if new_name:
            self.config["assistant_name"] = new_name
        
        # Wake words
        current_wake_words = ", ".join(self.config.get("wake_words", ["Hey Wizard", "Wizard"]))
        print(f"\nCurrent wake words: {current_wake_words}")
        new_wake_words = input("New wake words (comma-separated, or press Enter to keep current): ").strip()
        if new_wake_words:
            self.config["wake_words"] = [word.strip() for word in new_wake_words.split(",")]
    
    def configure_voice_settings(self):
        """Configure voice and speech settings"""
        print("\n🎵 Voice Settings")
        print("-" * 20)
        
        voice_config = self.config.setdefault("voice", {})
        
        # Gender
        current_gender = voice_config.get("gender", "female")
        print(f"Current voice gender: {current_gender}")
        new_gender = input("Voice gender (male/female/neutral): ").strip().lower()
        if new_gender in ["male", "female", "neutral"]:
            voice_config["gender"] = new_gender
        
        # Speed
        current_speed = voice_config.get("speed", 1.0)
        print(f"Current speech speed: {current_speed}")
        try:
            speed_input = input("Speech speed (0.5-2.0): ").strip()
            if speed_input:
                new_speed = float(speed_input)
                if 0.5 <= new_speed <= 2.0:
                    voice_config["speed"] = new_speed
                else:
                    print("⚠️  Speed must be between 0.5 and 2.0")
        except ValueError:
            print("⚠️  Invalid speed value")
        
        # Volume
        current_volume = voice_config.get("volume", 0.8)
        print(f"Current volume: {current_volume}")
        try:
            volume_input = input("Voice volume (0.0-1.0): ").strip()
            if volume_input:
                new_volume = float(volume_input)
                if 0.0 <= new_volume <= 1.0:
                    voice_config["volume"] = new_volume
                else:
                    print("⚠️  Volume must be between 0.0 and 1.0")
        except ValueError:
            print("⚠️  Invalid volume value")
    
    def configure_security_settings(self):
        """Configure security and safety settings"""
        print("\n🔒 Security Settings")
        print("-" * 20)
        
        security_config = self.config.setdefault("security", {})
        
        # Confirmation for critical operations
        current_confirmation = security_config.get("require_confirmation", True)
        print(f"Currently require confirmation for critical operations: {current_confirmation}")
        confirmation_input = input("Require confirmation for system operations? (y/n): ").strip().lower()
        if confirmation_input in ["y", "yes", "n", "no"]:
            security_config["require_confirmation"] = confirmation_input in ["y", "yes"]
        
        # Safe mode
        current_safe_mode = security_config.get("safe_mode", False)
        print(f"Currently in safe mode: {current_safe_mode}")
        safe_mode_input = input("Enable safe mode (limited commands)? (y/n): ").strip().lower()
        if safe_mode_input in ["y", "yes", "n", "no"]:
            security_config["safe_mode"] = safe_mode_input in ["y", "yes"]
        
        # Password protection (optional)
        password_input = input("Set password for restricted commands? (y/n): ").strip().lower()
        if password_input in ["y", "yes"]:
            import getpass
            password = getpass.getpass("Enter password: ")
            if password:
                # In a real implementation, this would be hashed
                security_config["password_protected"] = True
                print("✅ Password protection enabled (password hashing recommended)")
    
    def configure_applications(self):
        """Configure application paths and preferences"""
        print("\n📱 Application Settings")
        print("-" * 20)
        
        apps_config = self.config.setdefault("applications", {})
        
        common_apps = {
            "browser": "Web browser",
            "music_player": "Music player (Spotify, iTunes, etc.)",
            "email": "Email client",
            "calculator": "Calculator",
            "text_editor": "Text editor",
            "file_manager": "File manager"
        }
        
        print("Configure paths for common applications (press Enter to skip):")
        for app_key, app_desc in common_apps.items():
            current_path = apps_config.get(app_key, "")
            if current_path:
                print(f"Current {app_desc} path: {current_path}")
            
            new_path = input(f"Path to {app_desc}: ").strip()
            if new_path:
                if Path(new_path).exists():
                    apps_config[app_key] = new_path
                    print(f"✅ {app_desc} configured")
                else:
                    print(f"⚠️  Path not found: {new_path}")
    
    def configure_preferences(self):
        """Configure user preferences and behavior"""
        print("\n⚙️  Preferences")
        print("-" * 20)
        
        prefs_config = self.config.setdefault("preferences", {})
        
        # Response style
        current_style = prefs_config.get("response_style", "friendly")
        print(f"Current response style: {current_style}")
        style_options = ["friendly", "professional", "casual", "formal"]
        print(f"Available styles: {', '.join(style_options)}")
        new_style = input("Response style: ").strip().lower()
        if new_style in style_options:
            prefs_config["response_style"] = new_style
        
        # Detailed responses
        current_detailed = prefs_config.get("detailed_responses", True)
        print(f"Currently provide detailed responses: {current_detailed}")
        detailed_input = input("Provide detailed responses? (y/n): ").strip().lower()
        if detailed_input in ["y", "yes", "n", "no"]:
            prefs_config["detailed_responses"] = detailed_input in ["y", "yes"]
        
        # Learning
        current_learning = prefs_config.get("learning_enabled", True)
        print(f"Currently learning from interactions: {current_learning}")
        learning_input = input("Enable learning from interactions? (y/n): ").strip().lower()
        if learning_input in ["y", "yes", "n", "no"]:
            prefs_config["learning_enabled"] = learning_input in ["y", "yes"]
    
    def show_current_config(self):
        """Display current configuration"""
        print("\n📋 Current Configuration")
        print("=" * 30)
        print(json.dumps(self.config, indent=2))
    
    def interactive_menu(self):
        """Main interactive configuration menu"""
        while True:
            print("\n🧙 Wizard Configuration Menu")
            print("=" * 30)
            print("1. Basic Settings (name, wake words)")
            print("2. Voice Settings (gender, speed, volume)")
            print("3. Security Settings (confirmations, safe mode)")
            print("4. Application Paths")
            print("5. Preferences (response style, behavior)")
            print("6. Show Current Configuration")
            print("7. Save and Exit")
            print("8. Exit Without Saving")
            
            choice = input("\nSelect option (1-8): ").strip()
            
            if choice == "1":
                self.configure_basic_settings()
            elif choice == "2":
                self.configure_voice_settings()
            elif choice == "3":
                self.configure_security_settings()
            elif choice == "4":
                self.configure_applications()
            elif choice == "5":
                self.configure_preferences()
            elif choice == "6":
                self.show_current_config()
            elif choice == "7":
                if self.save_config():
                    print("✅ Configuration saved successfully!")
                    break
                else:
                    print("❌ Failed to save configuration")
            elif choice == "8":
                print("👋 Exiting without saving")
                break
            else:
                print("⚠️  Invalid option. Please select 1-8.")

def main():
    """Main configuration entry point"""
    if len(sys.argv) > 1:
        if sys.argv[1] == "--help":
            print("Wizard Voice Assistant Configuration Tool")
            print("Usage: python configure.py [--help] [--show]")
            print("\nOptions:")
            print("  --help    Show this help message")
            print("  --show    Show current configuration")
            return
        elif sys.argv[1] == "--show":
            configurator = WizardConfigurator()
            configurator.show_current_config()
            return
    
    print("🧙 Welcome to Wizard Configuration!")
    configurator = WizardConfigurator()
    configurator.interactive_menu()

if __name__ == "__main__":
    main()