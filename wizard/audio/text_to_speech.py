"""
Text-to-Speech Engine for Wizard Voice Assistant

Implements TTS using pyttsx3 with configurable voice settings,
voice selection, speed and volume controls, and audio feedback system.
"""

import logging
import threading
import time
import queue
from typing import Optional, List, Dict, Any, Callable, Tuple
from dataclasses import dataclass
from pathlib import Path
import json

import pyttsx3
from gtts import gTTS
import pygame
from io import BytesIO

# Import the main configuration system
# Add project root to Python path for imports
import sys
from pathlib import Path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))
from wizard.utils.config_manager import VoiceConfig as MainVoiceConfig


@dataclass
class VoiceConfig:
    """Configuration for a voice"""
    voice_id: str
    name: str
    gender: str  # 'male' or 'female'
    language: str
    rate: int = 200  # Words per minute
    volume: float = 0.9  # 0.0 to 1.0


@dataclass
class TTSConfig:
    """Configuration for text-to-speech engine"""
    default_voice: Optional[str] = None
    rate: int = 200  # Words per minute
    volume: float = 0.9  # 0.0 to 1.0
    
    # Audio feedback settings
    enable_feedback: bool = True
    feedback_sounds: Dict[str, str] = None
    
    # Engine settings
    engine: str = "pyttsx3"  # 'pyttsx3' or 'gtts'
    cache_enabled: bool = True
    cache_dir: str = "audio_cache"
    
    # Voice selection preferences
    prefer_gender: Optional[str] = None  # 'male' or 'female'
    prefer_language: str = "en"


class TextToSpeechEngine:
    """
    Text-to-speech engine with configurable voice settings,
    multiple voice support, and audio feedback system.
    """
    
    def __init__(self, config: TTSConfig):
        """
        Initialize the text-to-speech engine.
        
        Args:
            config: TTS configuration
        """
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Initialize engines
        self.pyttsx3_engine = None
        self.available_voices = {}
        self.current_voice = None
        
        # Audio playback
        pygame.mixer.init()
        
        # Speech queue for async playback
        self.speech_queue = queue.Queue()
        self.is_speaking = False
        self.speech_thread = None
        self._stop_speaking = threading.Event()
        
        # Cache management
        self.cache_dir = Path(config.cache_dir)
        self.cache_dir.mkdir(exist_ok=True)
        
        # Initialize components
        self._initialize_engines()
        self._load_feedback_sounds()
        self._start_speech_thread()
        
    def _initialize_engines(self):
        """Initialize TTS engines and discover available voices"""
        try:
            # Initialize pyttsx3 with SAPI5 explicitly on Windows
            import platform
            if platform.system() == 'Windows':
                self.pyttsx3_engine = pyttsx3.init('sapi5')
            else:
                self.pyttsx3_engine = pyttsx3.init()
            
            # Configure engine properties
            self.pyttsx3_engine.setProperty('rate', self.config.rate)
            self.pyttsx3_engine.setProperty('volume', self.config.volume)
            
            # Discover available voices
            self._discover_voices()
            
            # Set default voice
            self._set_default_voice()
            
            self.logger.info(f"TTS engine initialized with {len(self.available_voices)} voices")
            
        except Exception as e:
            self.logger.error(f"Error initializing TTS engines: {e}")
            # Fallback to basic init if SAPI5 fails
            try:
                self.pyttsx3_engine = pyttsx3.init()
            except:
                pass
    
    def _discover_voices(self):
        """Discover and catalog available voices"""
        try:
            voices = self.pyttsx3_engine.getProperty('voices')
            
            for voice in voices:
                # Parse voice information
                voice_info = self._parse_voice_info(voice)
                if voice_info:
                    self.available_voices[voice_info.voice_id] = voice_info
                    
            self.logger.info(f"Discovered {len(self.available_voices)} voices")
            
        except Exception as e:
            self.logger.error(f"Error discovering voices: {e}")
    
    def _parse_voice_info(self, voice) -> Optional[VoiceConfig]:
        """
        Parse voice information from pyttsx3 voice object.
        
        Args:
            voice: pyttsx3 voice object
            
        Returns:
            Optional[VoiceConfig]: Parsed voice configuration
        """
        try:
            voice_id = voice.id
            name = voice.name if hasattr(voice, 'name') else voice_id
            
            # Determine gender from voice name/id (heuristic)
            gender = self._determine_gender(name.lower())
            
            # Determine language from voice id (heuristic)
            language = self._determine_language(voice_id)
            
            return VoiceConfig(
                voice_id=voice_id,
                name=name,
                gender=gender,
                language=language,
                rate=self.config.rate,
                volume=self.config.volume
            )
            
        except Exception as e:
            self.logger.error(f"Error parsing voice info: {e}")
            return None
    
    def _determine_gender(self, voice_name: str) -> str:
        """Determine voice gender from name (heuristic)"""
        female_indicators = ['female', 'woman', 'zira', 'cortana', 'hazel', 'susan', 'karen']
        male_indicators = ['male', 'man', 'david', 'mark', 'richard', 'george']
        
        voice_name_lower = voice_name.lower()
        
        for indicator in female_indicators:
            if indicator in voice_name_lower:
                return 'female'
                
        for indicator in male_indicators:
            if indicator in voice_name_lower:
                return 'male'
                
        return 'unknown'
    
    def _determine_language(self, voice_id: str) -> str:
        """Determine voice language from ID (heuristic) - Simplified for En/Gu"""
        voice_id_lower = voice_id.lower()
        if 'gu' in voice_id_lower or 'gujarati' in voice_id_lower:
            return 'gu'
        return 'en'
    
    def _set_default_voice(self):
        """Set the default voice based on preferences"""
        if not self.available_voices:
            self.logger.warning("No voices available")
            return
            
        # If specific voice is configured, use it
        if self.config.default_voice and self.config.default_voice in self.available_voices:
            self.current_voice = self.available_voices[self.config.default_voice]
            self.pyttsx3_engine.setProperty('voice', self.config.default_voice)
            return
        
        # Select female voice as default unless otherwise specified
        pref_gender = self.config.prefer_gender if (hasattr(self.config, 'prefer_gender') and self.config.prefer_gender) else 'female'
        
        preferred_voices = []
        for voice in self.available_voices.values():
            score = 0
            if voice.gender == pref_gender:
                score += 10
            if voice.language == 'en': # Standard TTS is best for English
                score += 5
            preferred_voices.append((score, voice))
            
        if preferred_voices:
            preferred_voices.sort(key=lambda x: x[0], reverse=True)
            self.current_voice = preferred_voices[0][1]
            self.pyttsx3_engine.setProperty('voice', self.current_voice.voice_id)
            self.logger.info(f"Selected voice: {self.current_voice.name} (Clarified selection)")
    
    def _load_feedback_sounds(self):
        """Load audio feedback sounds"""
        if not self.config.enable_feedback:
            return
            
        try:
            # Default feedback sounds (you would replace these with actual sound files)
            default_sounds = {
                'listening': 'sounds/listening.wav',
                'processing': 'sounds/processing.wav',
                'error': 'sounds/error.wav',
                'success': 'sounds/success.wav'
            }
            
            self.feedback_sounds = self.config.feedback_sounds or default_sounds
            
            # Verify sound files exist (silently)
            for sound_type, sound_path in self.feedback_sounds.items():
                if not Path(sound_path).exists():
                    self.logger.debug(f"Feedback sound not found: {sound_path}")
                    
        except Exception as e:
            self.logger.error(f"Error loading feedback sounds: {e}")
    
    def _start_speech_thread(self):
        """Start the speech processing thread"""
        self.speech_thread = threading.Thread(target=self._speech_worker, daemon=True)
        self.speech_thread.start()
    
    def _speech_worker(self):
        """Worker thread for processing speech queue"""
        while True:
            try:
                if self._stop_speaking.is_set():
                    break
                    
                try:
                    speech_item = self.speech_queue.get(timeout=1.0)
                except queue.Empty:
                    continue
                
                # Process speech item
                self._process_speech_item(speech_item)
                self.speech_queue.task_done()
                
            except Exception as e:
                self.logger.error(f"Error in speech worker: {e}")
    
    def _process_speech_item(self, speech_item: Dict[str, Any]):
        """Process a single speech item"""
        try:
            text = speech_item['text']
            voice_id = speech_item.get('voice_id')
            callback = speech_item.get('callback')
            
            # Set voice if specified
            if voice_id and voice_id in self.available_voices:
                self.pyttsx3_engine.setProperty('voice', voice_id)
            
            # Speak the text
            self.is_speaking = True
            
            # Detect language of text for TTS selection if not specified
            lang = speech_item.get('language')
            is_mixed = False
            if not lang:
                try:
                    from wizard.utils.language_manager import LanguageManager
                    lang = LanguageManager.detect_language(text)
                    is_mixed = LanguageManager.is_mixed(text)
                except ImportError:
                    lang = 'en'
            else:
                try:
                    from wizard.utils.language_manager import LanguageManager
                    is_mixed = LanguageManager.is_mixed(text)
                except ImportError:
                    pass

            # Use gTTS for non-English or when explicitly configured
            spoken = False
            if is_mixed and self.config.engine != 'pyttsx3':
                # Handle mixed language text by splitting and speaking segments
                try:
                    segments = self._split_mixed_text(text)
                    for segment_text, segment_lang in segments:
                        self._speak_with_gtts(segment_text, segment_lang)
                    spoken = True
                except Exception as e:
                    self.logger.warning(f"Mixed TTS failed, falling back: {e}")
            
            if not spoken and (lang != 'en' or self.config.engine == 'gtts'):
                try:
                    self._speak_with_gtts(text, lang)
                    spoken = True
                except Exception as e:
                    self.logger.warning(f"gTTS failed, falling back to pyttsx3: {e}")
            
            if not spoken:
                self._speak_with_pyttsx3(text)
            
            self.is_speaking = False
            
            # Call callback if provided
            if callback:
                callback()
                
        except Exception as e:
            self.logger.error(f"Error processing speech item: {e}")
            # Last resort: try pyttsx3 directly
            try:
                self.pyttsx3_engine.say(speech_item.get('text', ''))
                self.pyttsx3_engine.runAndWait()
            except:
                pass
            self.is_speaking = False
    
    def _speak_with_pyttsx3(self, text: str):
        """Speak text using pyttsx3 engine"""
        try:
            self.pyttsx3_engine.say(text)
            self.pyttsx3_engine.runAndWait()
        except Exception as e:
            self.logger.debug(f"Error with pyttsx3 speech: {e}")
    
    def _speak_with_gtts(self, text: str, lang: str = "en"):
        """Speak text using gTTS engine with language safety and robust playback"""
        import os
        import tempfile
        temp_file = None
        try:
            # Check if language is supported by gTTS, fallback to English if not
            import gtts.lang
            supported_langs = gtts.lang.tts_langs()
            if lang not in supported_langs:
                self.logger.warning(f"Language '{lang}' not supported by gTTS. Falling back to English.")
                lang = "en"

            # Generate speech with gTTS
            tts = gTTS(text=text, lang=lang)
            
            # Create a temporary file with .mp3 extension
            with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as f:
                temp_file = f.name
            
            tts.save(temp_file)
            
            # Ensure mixer is initialized
            if not pygame.mixer.get_init():
                pygame.mixer.init()
            
            # Stop any current music
            pygame.mixer.music.stop()
            pygame.mixer.music.unload() # unloading is better for file access
            
            # Play with pygame
            pygame.mixer.music.load(temp_file)
            pygame.mixer.music.play()
            
            # Wait for playback to complete
            while pygame.mixer.music.get_busy():
                time.sleep(0.1)
                
            # Unload before deleting
            pygame.mixer.music.unload()
                
        except Exception as e:
            self.logger.error(f"Error with gTTS speech: {e}")
        finally:
            # Clean up temporary file
            if temp_file and os.path.exists(temp_file):
                try:
                    os.remove(temp_file)
                except Exception as cleanup_error:
                    self.logger.debug(f"Could not remove temp TTS file: {cleanup_error}")

    def _split_mixed_text(self, text: str) -> List[Tuple[str, str]]:
        """Split text into (segment, lang) tuples based on script for mixed TTS"""
        segments = []
        if not text:
            return segments
            
        current_segment = ""
        current_lang = None
        
        # Heuristic to detect script
        def get_char_lang(c):
            if '\u0A80' <= c <= '\u0AFF': return 'gu'
            if 'a' <= c.lower() <= 'z': return 'en'
            return None # Neutral
            
        for char in text:
            char_lang = get_char_lang(char)
            
            if char_lang is None: # Space or punctuation
                current_segment += char
                continue
                
            if current_lang is None:
                current_lang = char_lang
                current_segment += char
            elif current_lang == char_lang:
                current_segment += char
            else:
                # Language change detected
                if current_segment.strip():
                    segments.append((current_segment, current_lang))
                current_segment = char
                current_lang = char_lang
        
        if current_segment.strip():
            segments.append((current_segment, current_lang))
            
        return segments
    
    def speak(self, text: str, voice_id: Optional[str] = None, 
              async_mode: bool = True, callback: Optional[Callable] = None,
              language: Optional[str] = None) -> bool:
        """
        Speak the given text.
        
        Args:
            text: Text to speak
            voice_id: Optional specific voice ID to use
            async_mode: If True, speak asynchronously
            callback: Optional callback when speech completes
            language: Optional language code
            
        Returns:
            bool: True if speech was queued/started successfully
        """
        if not text.strip():
            return False
            
        try:
            speech_item = {
                'text': text,
                'voice_id': voice_id,
                'callback': callback,
                'language': language
            }
            
            if async_mode:
                self.speech_queue.put(speech_item)
                return True
            else:
                self._process_speech_item(speech_item)
                return True
                
        except Exception as e:
            self.logger.error(f"Error queuing speech: {e}")
            return False
    
    def speak_with_voice(self, text: str, gender: Optional[str] = None, 
                        language: Optional[str] = None) -> bool:
        """
        Speak text with a voice matching specified criteria.
        
        Args:
            text: Text to speak
            gender: Preferred voice gender ('male' or 'female')
            language: Preferred voice language
            
        Returns:
            bool: True if suitable voice found and speech queued
        """
        voice_id = self._find_voice(gender=gender, language=language)
        if voice_id:
            return self.speak(text, voice_id=voice_id)
        else:
            # Fallback to default voice
            return self.speak(text)
    
    def _find_voice(self, gender: Optional[str] = None, 
                   language: Optional[str] = None) -> Optional[str]:
        """
        Find a voice matching the specified criteria.
        
        Args:
            gender: Preferred gender
            language: Preferred language
            
        Returns:
            Optional[str]: Voice ID if found, None otherwise
        """
        best_match = None
        best_score = -1
        
        for voice in self.available_voices.values():
            score = 0
            
            if gender and voice.gender == gender:
                score += 10
                
            if language and voice.language == language:
                score += 5
                
            if score > best_score:
                best_score = score
                best_match = voice.voice_id
        
        return best_match
    
    def stop_speaking(self):
        """Stop current speech"""
        try:
            if self.is_speaking:
                self.pyttsx3_engine.stop()
                pygame.mixer.music.stop()
                
                # Clear speech queue
                while not self.speech_queue.empty():
                    try:
                        self.speech_queue.get_nowait()
                    except queue.Empty:
                        break
                
                self.is_speaking = False
                self.logger.info("Speech stopped")
                
        except Exception as e:
            self.logger.error(f"Error stopping speech: {e}")
    
    def set_voice(self, voice_id: str) -> bool:
        """
        Set the current voice.
        
        Args:
            voice_id: Voice ID to set
            
        Returns:
            bool: True if voice was set successfully
        """
        if voice_id in self.available_voices:
            self.current_voice = self.available_voices[voice_id]
            self.pyttsx3_engine.setProperty('voice', voice_id)
            self.logger.info(f"Voice set to: {self.current_voice.name}")
            return True
        else:
            self.logger.warning(f"Voice not found: {voice_id}")
            return False
    
    def set_rate(self, rate: int) -> bool:
        """
        Set the speech rate.
        
        Args:
            rate: Speech rate in words per minute
            
        Returns:
            bool: True if rate was set successfully
        """
        try:
            if 50 <= rate <= 400:  # Reasonable range
                self.config.rate = rate
                self.pyttsx3_engine.setProperty('rate', rate)
                if self.current_voice:
                    self.current_voice.rate = rate
                self.logger.info(f"Speech rate set to: {rate} WPM")
                return True
            else:
                self.logger.warning(f"Invalid speech rate: {rate}")
                return False
                
        except Exception as e:
            self.logger.error(f"Error setting speech rate: {e}")
            return False
    
    def set_volume(self, volume: float) -> bool:
        """
        Set the speech volume.
        
        Args:
            volume: Volume level (0.0 to 1.0)
            
        Returns:
            bool: True if volume was set successfully
        """
        try:
            if 0.0 <= volume <= 1.0:
                self.config.volume = volume
                self.pyttsx3_engine.setProperty('volume', volume)
                if self.current_voice:
                    self.current_voice.volume = volume
                self.logger.info(f"Speech volume set to: {volume}")
                return True
            else:
                self.logger.warning(f"Invalid volume level: {volume}")
                return False
                
        except Exception as e:
            self.logger.error(f"Error setting speech volume: {e}")
            return False
    
    def get_available_voices(self) -> List[Dict[str, Any]]:
        """
        Get list of available voices.
        
        Returns:
            List[Dict]: List of voice information dictionaries
        """
        voices = []
        for voice in self.available_voices.values():
            voices.append({
                'id': voice.voice_id,
                'name': voice.name,
                'gender': voice.gender,
                'language': voice.language
            })
        return voices
    
    def play_feedback_sound(self, sound_type: str) -> bool:
        """
        Play an audio feedback sound.
        
        Args:
            sound_type: Type of feedback sound ('listening', 'processing', 'error', 'success')
            
        Returns:
            bool: True if sound was played successfully
        """
        if not self.config.enable_feedback:
            return False
            
        try:
            if sound_type in self.feedback_sounds:
                sound_path = self.feedback_sounds[sound_type]
                if Path(sound_path).exists():
                    pygame.mixer.Sound(sound_path).play()
                    return True
                else:
                    self.logger.debug(f"Feedback sound file not found: {sound_path}")
            else:
                self.logger.debug(f"Unknown feedback sound type: {sound_type}")
                
            return False
            
        except Exception as e:
            self.logger.debug(f"Error playing feedback sound: {e}")
            return False
    
    def save_speech_to_file(self, text: str, filename: str, 
                           voice_id: Optional[str] = None) -> bool:
        """
        Save speech to an audio file.
        
        Args:
            text: Text to convert to speech
            filename: Output filename
            voice_id: Optional voice ID to use
            
        Returns:
            bool: True if file was saved successfully
        """
        try:
            # Use gTTS for file output (better quality)
            tts = gTTS(text=text, lang=self.config.prefer_language)
            tts.save(filename)
            self.logger.info(f"Speech saved to: {filename}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error saving speech to file: {e}")
            return False
    
    def get_current_voice_info(self) -> Optional[Dict[str, Any]]:
        """
        Get information about the current voice.
        
        Returns:
            Optional[Dict]: Current voice information
        """
        if self.current_voice:
            return {
                'id': self.current_voice.voice_id,
                'name': self.current_voice.name,
                'gender': self.current_voice.gender,
                'language': self.current_voice.language,
                'rate': self.current_voice.rate,
                'volume': self.current_voice.volume
            }
        return None
    
    def update_from_main_config(self, voice_config: MainVoiceConfig) -> bool:
        """
        Update TTS settings from the main configuration system.
        
        Args:
            voice_config: Voice configuration from main config system
            
        Returns:
            bool: True if settings were updated successfully
        """
        try:
            # Update rate (speed)
            self.set_rate(voice_config.speed)
            
            # Update volume
            self.set_volume(voice_config.volume)
            
            # Update preferred gender if changed
            if voice_config.gender in ['male', 'female']:
                self.config.prefer_gender = voice_config.gender
                # Find and set a voice matching the new gender preference
                voice_id = self._find_voice(gender=voice_config.gender)
                if voice_id:
                    self.set_voice(voice_id)
            
            self.logger.info("TTS settings updated from main configuration")
            return True
            
        except Exception as e:
            self.logger.error(f"Error updating TTS settings from main config: {e}")
            return False

    def shutdown(self):
        """Shutdown the TTS engine and cleanup resources"""
        try:
            self.stop_speaking()
            self._stop_speaking.set()
            
            if self.speech_thread and self.speech_thread.is_alive():
                self.speech_thread.join(timeout=2.0)
            
            pygame.mixer.quit()
            self.logger.info("TTS engine shutdown complete")
            
        except Exception as e:
            self.logger.error(f"Error during TTS shutdown: {e}")


def create_tts_engine(voice_config: Optional[MainVoiceConfig] = None) -> TextToSpeechEngine:
    """
    Factory function to create a TTS engine with configuration from the main config system.
    
    Args:
        voice_config: Voice configuration from the main config system
        
    Returns:
        TextToSpeechEngine: Configured TTS engine
    """
    if voice_config is None:
        voice_config = MainVoiceConfig()
    
    # Map main config to TTS config
    prefer_gender = voice_config.gender if voice_config.gender in ['male', 'female'] else None
    
    config = TTSConfig(
        rate=voice_config.speed,
        volume=voice_config.volume,
        prefer_gender=prefer_gender,
        prefer_language="en"
    )
    
    return TextToSpeechEngine(config)