#!/usr/bin/env python3
"""
Wizard Voice Assistant - Main Application
Continuously listens for voice commands and executes them.

ARCHITECTURE:
  The pywebview desktop window MUST run on the main thread.
  The voice assistant loop runs in a background thread.
  Communication happens via the Character3DServer (WebSocket push to frontend).
"""

import speech_recognition as sr
import pyttsx3
import threading
import time
import sys
import os
from pathlib import Path

# Import 3D Character Server
try:
    from wizard.character_server import Character3DServer, CharacterState
    HAS_3D_CHARACTER = True
except ImportError:
    HAS_3D_CHARACTER = False
    print("⚠️  3D Character server not available.")

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Import command router and TTS engine
try:
    from wizard.commands.command_router import route_command
    from wizard.audio.text_to_speech import create_tts_engine, TTSConfig
    from wizard.utils.config_manager import ConfigManager
    from wizard.utils.speech_normalizer import SpeechNormalizer
    from wizard.utils.language_manager import LanguageManager
    
    # Initialize TTS engine with configuration
    config_manager = ConfigManager()
    config_manager.load_config()  # Load the configuration first
    voice_config = config_manager.config.voice_settings  # Access voice settings correctly
    tts = create_tts_engine(voice_config)
    
except ImportError as e:
    print(f"Warning: Could not import advanced TTS engine: {e}")
    # Fallback to simple TTS
    try:
        from wizard.audio.tts_engine import tts
    except ImportError:
        # Final fallback
        class SimpleTTS:
            def __init__(self):
                self.engine = pyttsx3.init()
                self.engine.setProperty('rate', 150)
                self.engine.setProperty('volume', 0.9)
            
            def speak(self, text):
                print(f'Speaking: {text}')
                self.engine.say(text)
                self.engine.runAndWait()
        
        tts = SimpleTTS()
    
    # Fallback command router
    def route_command(command):
        return f"Command received: {command}"

def check_recognition_engines():
    """Check which speech recognition engines are available"""
    engines = {
        'google': False,
        'sphinx': False
    }
    
    recognizer = sr.Recognizer()
    
    # Check if Sphinx is available (offline)
    try:
        import pocketsphinx
        engines['sphinx'] = True
    except ImportError:
        pass
    
    # Google is always available but requires internet
    engines['google'] = True
    
    return engines

def recognize_speech_with_fallback(recognizer, audio, show_confidence=False):
    """
    Recognize speech with automatic fallback to offline mode
    Optimized for better accuracy
    """
    # Try Google first (requires internet) - best accuracy
    try:
        # First try normal en-US
        try:
            result = recognizer.recognize_google(audio, language="en-US")
            if result and result.strip():
                return result.strip(), 'google_en'
        except sr.UnknownValueError:
            pass

        # Try en-IN for better support for Indian accents and mixed queries
        try:
            result = recognizer.recognize_google(audio, language="en-IN")
            if result and result.strip():
                text = result.strip()
                # Check if it contains Gujarati transliterations
                from wizard.utils.language_manager import LanguageManager
                if LanguageManager.detect_language(text) == 'gu':
                    return text, 'google_gu'
                return text, 'google_en'
        except sr.UnknownValueError:
            # If English failed, try Gujarati specifically
            try:
                result = recognizer.recognize_google(audio, language="gu-IN")
                if result and result.strip():
                    return result.strip(), 'google_gu'
            except sr.UnknownValueError:
                # Last resort for Indian languages: try Hindi as it often catches dialect nuances
                try:
                    result = recognizer.recognize_google(audio, language="hi-IN")
                    if result and result.strip():
                        # Still treat it as Gujarati if that's what we want
                        return result.strip(), 'google_gu'
                except:
                    pass
            raise sr.UnknownValueError
    except sr.RequestError as e:
        # Network error - try offline recognition
        error_msg = str(e).lower()
        if "getaddrinfo failed" in error_msg or "connection" in error_msg or "network" in error_msg or "11001" in str(e):
            # Try Sphinx (offline)
            try:
                text = recognizer.recognize_sphinx(audio)
                if text and text.strip():
                    return text.strip(), 'sphinx'
                return None, 'sphinx_failed'
            except ImportError:
                return None, 'none'
            except sr.UnknownValueError:
                return None, 'sphinx_failed'
            except Exception as e2:
                # Log but don't fail completely
                return None, 'sphinx_failed'
        else:
            # Other request error, try offline anyway
            try:
                text = recognizer.recognize_sphinx(audio)
                if text and text.strip():
                    return text.strip(), 'sphinx'
            except:
                pass
            return None, 'network_error'
    except sr.UnknownValueError:
        return None, 'no_speech'
    except Exception as e:
        # Any other error, try offline as last resort
        try:
            text = recognizer.recognize_sphinx(audio)
            if text and text.strip():
                return text.strip(), 'sphinx'
        except:
            pass
        return None, 'recognition_error'

def test_microphone(microphone, recognizer):
    """Test if microphone is working"""
    print("🎤 Testing microphone...")
    try:
        with microphone as source:
            print("   Speak something now...")
            audio = recognizer.listen(source, timeout=3, phrase_time_limit=2)
            try:
                text = recognizer.recognize_google(audio, language="en-US")
                print(f"   ✅ Microphone working! Heard: {text}")
                return True
            except sr.RequestError:
                # Try offline
                try:
                    text = recognizer.recognize_sphinx(audio)
                    print(f"   ✅ Microphone working! Heard (offline): {text}")
                    return True
                except:
                    print("   ⚠️ Microphone detected audio but recognition failed")
                    return True  # Microphone works, recognition might need setup
            except sr.UnknownValueError:
                print("   ⚠️ Microphone detected but couldn't understand speech")
                return True  # Microphone works
    except sr.WaitTimeoutError:
        print("   ❌ No audio detected from microphone")
        print("   💡 Check:")
        print("      - Is microphone connected?")
        print("      - Are microphone permissions enabled?")
        print("      - Is microphone muted?")
        return False
    except Exception as e:
        print(f"   ❌ Microphone test error: {e}")
        return False


# ============================================================
#  VOICE ASSISTANT LOOP — runs in a background thread
# ============================================================

def voice_loop(character=None, continuous_mode=True, wake_word_mode=False):
    """
    The voice assistant listening loop.
    This runs in a BACKGROUND THREAD so the main thread can run the GUI.
    
    Args:
        character: Character3DServer instance (or None)
        continuous_mode: If True, always listens
        wake_word_mode: If True, requires wake word
    """
    print("🧙 Voice loop starting...")
    
    # Check available recognition engines
    engines = check_recognition_engines()
    if engines['sphinx']:
        print("✅ Offline recognition (Sphinx) available - can work without internet")
    else:
        print("⚠️ Offline recognition not available")
        print("   Install with: pip install pocketsphinx")
    
    if continuous_mode:
        print("\n🎤 Mode: CONTINUOUS LISTENING")
        print("   - Always listening for commands")
        print("   - No wake word needed")
        print("   - Say 'stop listening' or 'sleep' to pause")
    elif wake_word_mode:
        print("\n🎤 Mode: WAKE WORD MODE")
        print("   - Say 'Wizard' or 'Hey Wizard' to activate")
    else:
        continuous_mode = True  # Default to continuous
    
    # Initialize speech recognition
    recognizer = sr.Recognizer()
    
    # Try to find available microphone
    microphone = None
    try:
        mic_list = sr.Microphone.list_microphone_names()
        print(f"\n📋 Available microphones ({len(mic_list)} found):")
        for i, mic in enumerate(mic_list):
            print(f"   [{i}] {mic}")
        
        microphone = sr.Microphone()
        print(f"\n✅ Using default microphone: {mic_list[0] if mic_list else 'Default'}")
    except Exception as e:
        print(f"⚠️ Error accessing microphone list: {e}")
        try:
            microphone = sr.Microphone()
        except Exception as e2:
            print(f"❌ Cannot access microphone: {e2}")
            return
    
    # Test microphone first
    mic_working = test_microphone(microphone, recognizer)
    if not mic_working:
        print("\n⚠️ Microphone test failed, but continuing anyway...")
    
    # Calibrate microphone for ambient noise
    try:
        print("\n🎤 Calibrating microphone for ambient noise...")
        print("   (Please stay quiet for 3 seconds)")
        with microphone as source:
            recognizer.adjust_for_ambient_noise(source, duration=2.0)
            recognizer.energy_threshold = 300
            recognizer.dynamic_energy_threshold = True
            recognizer.pause_threshold = 0.8
            recognizer.phrase_threshold = 0.3
            recognizer.non_speaking_duration = 0.5
            recognizer.operation_timeout = None
        print(f"✅ Microphone calibrated successfully")
        print(f"   Energy threshold: {recognizer.energy_threshold}")
    except Exception as e:
        print(f"⚠️ Microphone calibration failed: {e}")
        recognizer.energy_threshold = 150
        recognizer.dynamic_energy_threshold = True
        recognizer.pause_threshold = 0.6
        recognizer.phrase_threshold = 0.3
    
    # Startup message
    if continuous_mode:
        startup_message = "Continuous listening mode activated. I'm always ready for your commands."
    else:
        startup_message = "Assistant is ready. Say Wizard to activate."
    print(f"🗣️ {startup_message}")
    
    # Update character to idle
    if character:
        character.update(state="idle", status="Ready for commands")
    
    # Speak startup message
    if character:
        character.update(state="speaking", status=startup_message[:80])
    tts.speak(startup_message)
    if character:
        character.update(state="idle", status="Ready for commands")
    
    print("\n🎤 Listening for wake words: 'wizard' or 'hey wizard'")
    print("🗣️ Say 'goodbye' to exit")
    print("=" * 50)
    
    # Main listening loop
    print("\n" + "="*50)
    if continuous_mode:
        print("🎤 CONTINUOUS LISTENING MODE")
        print("✅ Always listening - No wake word needed!")
        print("💡 Say 'stop listening' or 'sleep' to pause")
        print("💡 Say 'goodbye' or 'exit' to quit")
    else:
        print("🎤 WAKE WORD MODE")
        print("💡 Say 'Wizard' or 'Hey Wizard' to activate")
    print("="*50 + "\n")
    
    command_count = 0
    is_listening = True
    last_status_time = time.time()
    
    while True:
        try:
            if not is_listening:
                current_time = time.time()
                if current_time - last_status_time > 10:
                    print("😴 Paused. Say 'wake up' or 'resume' to continue...")
                    last_status_time = current_time
                time.sleep(1)
                continue
            
            # Show listening indicator occasionally
            current_time = time.time()
            if continuous_mode and (current_time - last_status_time > 15):
                print("🎤 Listening... (speak your command)")
                last_status_time = current_time
            
            # Update 3D character: listening
            if character and is_listening:
                character.set_state("listening")
            
            # Listen
            try:
                with microphone as source:
                    timeout_val = 3.0 if continuous_mode else 5.0
                    phrase_limit = 15 if continuous_mode else 10
                    audio = recognizer.listen(
                        source, 
                        timeout=timeout_val, 
                        phrase_time_limit=phrase_limit
                    )
            except sr.WaitTimeoutError:
                continue
            except Exception as e:
                print(f"⚠️ Listening error: {e}")
                time.sleep(0.5)
                continue
            
            try:
                # Recognize speech with offline fallback
                text, engine = recognize_speech_with_fallback(recognizer, audio)
                
                if text is None:
                    if engine == 'no_speech':
                        continue
                    elif engine == 'none':
                        if command_count == 0:
                            print("⚠️ No recognition engines available. Install pocketsphinx for offline mode.")
                        time.sleep(1)
                        continue
                    elif engine == 'sphinx_failed':
                        continue
                    else:
                        continue
                
                text = text.lower().strip()
                if not text:
                    continue
                
                # Apply Speech Normalization
                text = SpeechNormalizer.normalize(text)
                if not text:
                    continue
                    
                # Detect language
                lang = LanguageManager.detect_language(text)
                dialect = LanguageManager.detect_dialect(text) if lang == 'gu' else None
                lang_name = LanguageManager.get_language_name(lang)
                if dialect:
                    lang_name += f" ({dialect.capitalize()})"
                
                if engine == 'sphinx':
                    print(f"👂 [Offline] [{lang_name}] You said: {text}")
                else:
                    print(f"👂 [Online] [{lang_name}] You said: {text}")
                
                # Check for pause/resume commands
                if any(word in text for word in ['stop listening', 'sleep', 'pause', 'go to sleep']):
                    print("😴 Pausing... Say 'wake up' or 'resume' to continue")
                    tts.speak("Going to sleep. Say wake up when you need me.", async_mode=False)
                    is_listening = False
                    if character:
                        character.update(state="idle", status="Sleeping...")
                    continue
                
                if any(word in text for word in ['wake up', 'resume', 'start listening']):
                    if not is_listening:
                        print("🌅 Waking up...")
                        tts.speak("I'm awake and ready", async_mode=False)
                        is_listening = True
                    continue
                
                # In continuous mode, process commands directly
                if continuous_mode:
                    command_count += 1
                    last_status_time = time.time()
                    print(f"\n{'='*50}")
                    print(f"🎯 Command #{command_count}: {text}")
                    print(f"{'='*50}")
                    
                    # Update 3D character: thinking
                    if character:
                        character.update(state="thinking", status="Processing...", command=text)
                    
                    # Check for goodbye (exit program)
                    if any(word in text for word in ['exit program', 'quit assistant', 'stop assistant']):
                        goodbye_msg = "Goodbye! Have a great day!"
                        print(f"👋 {goodbye_msg}")
                        if character:
                            character.update(state="speaking", status=goodbye_msg)
                        tts.speak(goodbye_msg, async_mode=False)
                        if character:
                            character.stop()
                        break
                    
                    # Route command and get response
                    try:
                        from wizard.commands.command_router import route_command
                        response = route_command(text)
                        
                        # If route_command doesn't handle it, use AIBrain
                        not_sure_phrases = ["I'm not sure how to handle", "I don't know how to", "not sure how to", "I couldn't perform"]
                        is_not_sure = any(phrase in response for phrase in not_sure_phrases)
                        
                        if is_not_sure:
                            from wizard.data.ai_brain import AIBrain
                            ai_brain = AIBrain()
                            ai_response = ai_brain.process_query(text, context={"detected_lang": lang, "dialect": dialect})
                            
                            if ai_response and not any(phrase in ai_response for phrase in not_sure_phrases):
                                response = ai_response
                        
                        # AI Personal Operating System
                        try:
                            from wizard.data.personal_os import PersonalOS
                            pos = PersonalOS()
                            pos.observe(text, response)
                            suggestion = pos.think(text, response)
                            if suggestion:
                                response += f"\n{suggestion}"
                        except Exception:
                            pass
                        
                        print(f"🧙 [{lang_name}] {response}")
                        
                        # Update 3D character: speaking
                        if character:
                            display_response = response[:80] + "..." if len(response) > 80 else response
                            character.update(state="speaking", status=display_response)
                        
                        # TTS
                        try:
                            response_lang = LanguageManager.detect_language(response)
                        except:
                            response_lang = 'en'
                        tts.speak(response, async_mode=False, language=response_lang)
                        
                        # Back to idle
                        if character:
                            character.update(state="idle", status="Ready for commands", command="")
                        
                    except Exception as cmd_error:
                        error_msg = f"Error executing command: {str(cmd_error)}"
                        print(f"❌ {error_msg}")
                        if character:
                            character.update(state="error", status=f"Error: {str(cmd_error)[:50]}")
                        tts.speak("Sorry, I had trouble with that command.", async_mode=False)
                        if character:
                            character.update(state="idle", status="Ready for commands")
                    
                    print(f"\n✅ Done. Listening for next command...\n")
                    continue
                
                # Wake word mode
                wake_detected = False
                text_words = text.split()
                
                if 'wizard' in text_words or 'wizard' in text:
                    wake_detected = True
                elif 'hey' in text_words and 'wizard' in text_words:
                    wake_detected = True
                elif text.startswith('wizard') or text.startswith('hey wizard'):
                    wake_detected = True
                
                if wake_detected:
                    command_count += 1
                    print(f"\n🎯 Wake word detected! (Command #{command_count})")
                    print("🎯 Listening for your command...")
                    tts.speak("Yes?", async_mode=False)
                    
                    command_received = False
                    try:
                        with microphone as source:
                            command_audio = recognizer.listen(source, timeout=8, phrase_time_limit=15)
                        
                        command, engine = recognize_speech_with_fallback(recognizer, command_audio)
                        
                        if not command or not command.strip():
                            unclear_msg = "I didn't hear a command. Please try again."
                            print(f"❓ {unclear_msg}")
                            tts.speak(unclear_msg, async_mode=False)
                        else:
                            command = command.strip()
                            command_received = True
                            
                            print(f"📝 Command: {command}")
                            print("⚡ Executing...")
                            
                            if 'goodbye' in command.lower() or 'exit' in command.lower():
                                goodbye_msg = "Goodbye! Have a great day!"
                                print(f"👋 {goodbye_msg}")
                                tts.speak(goodbye_msg, async_mode=False)
                                break
                            
                            try:
                                response = route_command(command)
                                print(f"🧙 Response: {response}")
                                tts.speak(response, async_mode=False)
                            except Exception as cmd_error:
                                error_msg = f"Error executing command: {str(cmd_error)}"
                                print(f"❌ {error_msg}")
                                tts.speak("Sorry, I had trouble with that command.", async_mode=False)
                        
                        print("\n" + "=" * 50)
                        print("🔄 Ready for next command. Say 'Wizard' or 'Hey Wizard'...")
                        print("=" * 50 + "\n")
                        continue
                        
                    except sr.WaitTimeoutError:
                        timeout_msg = "I didn't hear a command. Try again."
                        print(f"⏰ {timeout_msg}")
                        tts.speak(timeout_msg, async_mode=False)
                        continue
                    except sr.UnknownValueError:
                        unclear_msg = "I didn't understand that command. Please try again."
                        print(f"❓ {unclear_msg}")
                        tts.speak(unclear_msg, async_mode=False)
                        continue
                    except Exception as e:
                        error_msg = "Sorry, I had trouble processing that command."
                        print(f"❌ Command error: {e}")
                        tts.speak(error_msg, async_mode=False)
                        continue
                else:
                    continue
                
            except sr.UnknownValueError:
                pass
            except sr.RequestError as e:
                error_msg = str(e).lower()
                if "getaddrinfo failed" in error_msg or "connection" in error_msg or "network" in error_msg:
                    if not engines['sphinx']:
                        print(f"⚠️ No internet connection and offline mode not available.")
                else:
                    print(f"❌ Speech recognition error: {e}")
                time.sleep(1)
                
        except KeyboardInterrupt:
            print("\n🛑 Interrupted by user")
            if character:
                character.update(state="speaking", status="Goodbye!")
            tts.speak("Goodbye!", async_mode=False)
            if character:
                character.stop()
            break
        except Exception as e:
            print(f"❌ Unexpected error: {e}")
            time.sleep(1)
    
    if character:
        character.stop()
    
    print("👋 Wizard Voice Assistant stopped")
    return True


# ============================================================
#  MAIN — runs pywebview on main thread, voice loop on background
# ============================================================

def main(continuous_mode=True, wake_word_mode=False):
    """
    Main voice assistant application.
    
    The 3D character window runs on the MAIN THREAD (required by pywebview).
    The voice assistant loop runs in a BACKGROUND THREAD.
    """
    print("🧙 Starting Wizard Voice Assistant...")
    print("=" * 50)
    
    character = None
    
    if HAS_3D_CHARACTER:
        try:
            character = Character3DServer()
            character.start()  # Start HTTP + WebSocket servers
            print("✅ 3D Character servers started (HTTP + WebSocket)")
            
            # Define the voice loop function that will run in background
            def run_voice():
                # Small delay to let the window fully initialize
                time.sleep(3)
                voice_loop(
                    character=character,
                    continuous_mode=continuous_mode,
                    wake_word_mode=wake_word_mode
                )
            
            # This blocks — opens the desktop window on main thread
            # and starts voice_loop in a background thread once loaded
            print("🖥️ Opening 3D character window...")
            print("   Voice assistant will start after window loads.")
            character.start_desktop_window(voice_fn=run_voice)
            
        except Exception as e:
            print(f"⚠️ 3D Character failed: {e}")
            print("🔄 Falling back to voice-only mode...")
            # Run voice loop directly without character
            voice_loop(
                character=None,
                continuous_mode=continuous_mode,
                wake_word_mode=wake_word_mode
            )
    else:
        # No 3D character available — voice only
        print("⚠️ Running in voice-only mode (no 3D character)")
        voice_loop(
            character=None,
            continuous_mode=continuous_mode,
            wake_word_mode=wake_word_mode
        )
    
    print("👋 Wizard Voice Assistant stopped")
    return True


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Wizard Voice Assistant")
    parser.add_argument("--wake-word", action="store_true", 
                       help="Use wake word mode (say 'Wizard' before each command)")
    parser.add_argument("--continuous", action="store_true", default=True,
                       help="Use continuous listening mode (default)")
    
    args = parser.parse_args()
    
    # Determine mode
    if args.wake_word:
        main(continuous_mode=False, wake_word_mode=True)
    else:
        main(continuous_mode=True, wake_word_mode=False)