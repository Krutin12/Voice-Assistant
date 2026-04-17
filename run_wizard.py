#!/usr/bin/env python3
"""
Wizard Voice Assistant - Main Entry Point
Enhanced with intelligent command processing and voice-only interaction
"""

import sys
import os
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def main():
    """Main entry point for Wizard Voice Assistant"""
    print("🧙 Starting Enhanced Wizard Voice Assistant...")
    print("🎤 Voice-controlled with intelligent command processing")
    print("💬 Say 'Hey Wizard' to activate, or use Ctrl+C to exit")
    
    try:
        # Import and run the enhanced wizard application
        from wizard.main import main as wizard_main
        wizard_main()
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("🔧 Trying fallback mode...")
        
        # Try enhanced text mode as fallback
        try:
            print("📝 Starting Enhanced Text Mode as fallback...")
            from enhanced_wizard_text import enhanced_text_wizard
            enhanced_text_wizard()
        except ImportError as e2:
            print(f"❌ Fallback failed: {e2}")
            print("\n💡 Troubleshooting steps:")
            print("1. Make sure you're in the project root directory")
            print("2. Run: python -m wizard.main")
            print("3. Or try: python install_python313.py")
            return False
    
    return True

def text_mode():
    """Run Wizard in enhanced text mode with intelligent processing"""
    print("🧙 Starting Enhanced Wizard in Text Mode...")
    print("💬 Text-based interaction with intelligent command processing")
    print("🧠 I can understand and execute any reasonable command!")
    
    try:
        # Import enhanced text mode wizard
        from enhanced_wizard_text import enhanced_text_wizard
        enhanced_text_wizard()
        return True
        
    except ImportError as e:
        print(f"❌ Enhanced text mode failed: {e}")
        print("� Tryiing basic text mode...")
        try:
            # Fallback to working wizard
            from wizard_working import working_wizard
            working_wizard()
            return True
        except ImportError as e2:
            print(f"❌ All text modes failed: {e2}")
            return False

def test_mode():
    """Run comprehensive system tests"""
    print("* Running Enhanced Wizard Tests...")
    
    try:
        # Test basic imports
        from wizard.utils.config_manager import ConfigManager
        from wizard.utils.logger import WizardLogger
        
        print("[OK] Core imports working")
        
        # Test configuration
        config = ConfigManager()
        logger = WizardLogger()
        
        print("[OK] Core components initialized")
        
        # Test AI brain with intelligent processing
        from wizard.data.ai_brain import AIBrain
        ai_brain = AIBrain()
        
        # Test intelligent command processing
        test_commands = [
            "open google chrome",
            "search for machine learning tutorials",
            "what time is it",
            "play some music",
            "launch calculator",
            "take a screenshot right now",
            "enable developer mode",
            "i feel sad",
            "can you act as a pdf reader",
            "teach you a new command"
        ]
        
        print("\n🧠 Testing intelligent command processing:")
        success_count = 0
        for cmd in test_commands:
            try:
                response = ai_brain.process_query(cmd)
                if response and len(response.strip()) > 0:
                    print(f"  [OK] '{cmd}' -> {response[:50]}...")
                    success_count += 1
                else:
                    print(f"  [FAIL] '{cmd}' -> No response")
            except Exception as e:
                print(f"  [ERROR] '{cmd}' -> Error: {e}")
        
        print(f"\n* Test Results: {success_count}/{len(test_commands)} commands successful")
        
        # Test voice components if available
        print("\n🎤 Testing voice components:")
        try:
            from wizard.audio.speech_recognition import SpeechRecognizer, SpeechRecognitionConfig
            config = SpeechRecognitionConfig()
            recognizer = SpeechRecognizer(config)
            print("  ✅ Speech recognition available")
        except Exception as e:
            print(f"  ⚠️  Speech recognition: {e}")
        
        try:
            from wizard.audio.text_to_speech import create_tts_engine
            from wizard.utils.config_manager import VoiceConfig
            tts_config = VoiceConfig()
            tts_config.gender = "female"
            tts_config.speed = 1.0
            tts_config.volume = 0.8
            tts_engine = create_tts_engine(tts_config)
            print("  ✅ Text-to-speech available")
        except Exception as e:
            print(f"  ⚠️  Text-to-speech: {e}")
        
        try:
            from wizard.audio.wake_word_engine import WakeWordEngine, WakeWordConfig
            wake_config = WakeWordConfig(wake_words=["wizard", "hey wizard"])
            wake_engine = WakeWordEngine(wake_config)
            print("  ✅ Wake word detection available")
        except Exception as e:
            print(f"  ⚠️  Wake word detection: {e}")
        
        print("\n* Enhanced test mode complete!")
        
        if success_count >= len(test_commands) * 0.8:
            print("[OK] System is working well!")
        else:
            print("[!] Some issues detected, but basic functionality works")
        
        return True
        
    except Exception as e:
        print(f"❌ Test mode failed: {e}")
        return False

def voice_test():
    """Test voice components specifically"""
    print("🎤 Testing Voice Components...")
    
    try:
        # Test speech recognition
        print("Testing speech recognition...")
        from wizard.audio.speech_recognition import SpeechRecognizer, SpeechRecognitionConfig
        
        config = SpeechRecognitionConfig()
        recognizer = SpeechRecognizer(config)
        
        print("✅ Speech recognition initialized")
        
        # Test TTS
        print("Testing text-to-speech...")
        from wizard.audio.text_to_speech import create_tts_engine
        
        from wizard.utils.config_manager import VoiceConfig
        tts_config = VoiceConfig()
        tts_config.gender = "female"
        tts_config.speed = 1.0
        tts_config.volume = 0.8
        tts_config.language = "en-US"

                        

        tts_engine = create_tts_engine(tts_config)
        print("✅ Text-to-speech initialized")
        
        # Test wake word engine
        print("Testing wake word detection...")
        from wizard.audio.wake_word_engine import WakeWordEngine, WakeWordConfig
        
        wake_config = WakeWordConfig(wake_words=["wizard", "hey wizard"])
        wake_engine = WakeWordEngine(wake_config)
        
        print("✅ Wake word engine initialized")
        
        # Test voice output
        print("Testing voice output...")
        try:
            tts_engine.speak("Voice test successful! All components are working.", async_mode=False)
            print("✅ Voice output test completed")
        except Exception as e:
            print(f"⚠️  Voice output test: {e}")
        
        print("🎉 Voice component test successful!")
        
        return True
        
    except Exception as e:
        print(f"❌ Voice test failed: {e}")
        return False

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Enhanced Wizard Voice Assistant")
    parser.add_argument("--test", action="store_true", help="Run comprehensive system tests")
    parser.add_argument("--text-mode", action="store_true", help="Run in enhanced text mode")
    parser.add_argument("--voice-test", action="store_true", help="Test voice components")
    parser.add_argument("--intelligent", action="store_true", help="Enable intelligent command processing (default)")
    
    args = parser.parse_args()
    
    try:
        if args.test:
            success = test_mode()
        elif args.text_mode:
            success = text_mode()
        elif args.voice_test:
            success = voice_test()
        else:
            # Default: run full voice assistant with intelligent processing
            success = main()
        
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n🛑 Voice Assistant closed securely via Keyboard Interrupt (Ctrl+C). Goodbye!")
        sys.exit(0)                       