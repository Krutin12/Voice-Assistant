"""
Wake Word Detection Engine for Wizard Voice Assistant

Implements lightweight wake word detection using pattern matching and simple ML model
with configurable sensitivity and multiple wake word support.
"""

import threading
import time
import logging
from typing import List, Callable, Optional
from dataclasses import dataclass
import pyaudio
import numpy as np
from collections import deque
import re


@dataclass
class WakeWordConfig:
    """Configuration for wake word detection"""
    wake_words: List[str]
    sensitivity: float = 0.7  # 0.0 to 1.0
    sample_rate: int = 16000
    chunk_size: int = 1024
    audio_format: int = pyaudio.paInt16
    channels: int = 1
    buffer_duration: float = 2.0  # seconds of audio to keep in buffer


class WakeWordEngine:
    """
    Lightweight wake word detection engine that continuously monitors audio input
    for activation phrases with configurable sensitivity and multiple wake word support.
    """
    
    def __init__(self, config: WakeWordConfig, callback: Optional[Callable] = None):
        """
        Initialize the wake word detection engine.
        
        Args:
            config: Wake word configuration
            callback: Optional callback function to call when wake word is detected
        """
        self.config = config
        self.callback = callback
        self.logger = logging.getLogger(__name__)
        
        # Audio processing components
        self.audio = None
        self.stream = None
        self.audio_buffer = deque(maxlen=int(config.sample_rate * config.buffer_duration))
        
        # Threading and state management
        self.listening = False
        self.listen_thread = None
        self._stop_event = threading.Event()
        
        # Wake word detection state
        self.wake_word_detected = False
        self.last_detection_time = 0
        self.detection_cooldown = 0.5  # seconds between detections
        
        # Preprocess wake words for pattern matching
        self._prepare_wake_words()
        
    def _prepare_wake_words(self):
        """Prepare wake words for efficient pattern matching"""
        self.wake_word_patterns = []
        for wake_word in self.config.wake_words:
            # Create regex pattern for flexible matching
            # Convert to lowercase and create pattern that allows for variations
            pattern = wake_word.lower().replace(' ', r'\s*')
            self.wake_word_patterns.append(re.compile(pattern, re.IGNORECASE))
            
        self.logger.info(f"Prepared {len(self.wake_word_patterns)} wake word patterns")
    
    def start_listening(self) -> bool:
        """
        Start continuous listening for wake words.
        
        Returns:
            bool: True if listening started successfully, False otherwise
        """
        if self.listening:
            self.logger.warning("Wake word engine is already listening")
            return True
            
        try:
            # Initialize PyAudio
            self.audio = pyaudio.PyAudio()
            
            # Open audio stream with working microphone device
            self.stream = self.audio.open(
                format=self.config.audio_format,
                channels=self.config.channels,
                rate=self.config.sample_rate,
                input=True,
                input_device_index=8,  # Use Steam Streaming Microphone
                frames_per_buffer=self.config.chunk_size,
                stream_callback=self._audio_callback
            )
            
            # Start listening thread
            self._stop_event.clear()
            self.listening = True
            self.listen_thread = threading.Thread(target=self._listen_loop, daemon=True)
            self.listen_thread.start()
            
            self.logger.info("Wake word engine started listening")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to start wake word engine: {e}")
            self._cleanup_audio()
            return False
    
    def stop_listening(self) -> None:
        """Stop listening for wake words and cleanup resources"""
        if not self.listening:
            return
            
        self.logger.info("Stopping wake word engine")
        
        # Signal stop and wait for thread
        self._stop_event.set()
        self.listening = False
        
        if self.listen_thread and self.listen_thread.is_alive():
            self.listen_thread.join(timeout=2.0)
            
        # Cleanup audio resources
        self._cleanup_audio()
        
        self.logger.info("Wake word engine stopped")
    
    def _cleanup_audio(self):
        """Cleanup audio resources"""
        try:
            if self.stream:
                self.stream.stop_stream()
                self.stream.close()
                self.stream = None
                
            if self.audio:
                self.audio.terminate()
                self.audio = None
                
        except Exception as e:
            self.logger.error(f"Error cleaning up audio resources: {e}")
    
    def _audio_callback(self, in_data, frame_count, time_info, status):
        """PyAudio callback for processing audio data"""
        if status:
            self.logger.warning(f"Audio callback status: {status}")
            
        # Convert audio data to numpy array
        audio_data = np.frombuffer(in_data, dtype=np.int16)
        
        # Add to circular buffer
        self.audio_buffer.extend(audio_data)
        
        return (None, pyaudio.paContinue)
    
    def _listen_loop(self):
        """Main listening loop that processes audio for wake word detection"""
        self.logger.info("Wake word detection loop started")
        
        while not self._stop_event.is_set() and self.listening:
            try:
                # Check if we have enough audio data
                if len(self.audio_buffer) < self.config.sample_rate * 0.5:  # 0.5 seconds minimum
                    time.sleep(0.1)
                    continue
                
                # Process audio buffer for wake word detection
                self._process_audio_buffer()
                
                # Small delay to prevent excessive CPU usage
                time.sleep(0.05)
                
            except Exception as e:
                self.logger.error(f"Error in wake word detection loop: {e}")
                time.sleep(0.1)
        
        self.logger.info("Wake word detection loop ended")
    
    def _process_audio_buffer(self):
        """Process the audio buffer to detect wake words"""
        try:
            # Convert buffer to numpy array
            audio_array = np.array(list(self.audio_buffer))
            
            # Simple energy-based voice activity detection
            if not self._has_voice_activity(audio_array):
                return
            
            print("🎤 Audio detected, processing...")
            
            # Use real speech recognition on the audio buffer
            detected_text = self._simulate_speech_recognition(audio_array)
            
            if detected_text and self._check_wake_words(detected_text):
                self._handle_wake_word_detection()
                
        except Exception as e:
            self.logger.error(f"Error processing audio buffer: {e}")
    
    def _has_voice_activity(self, audio_data: np.ndarray) -> bool:
        """
        Simple voice activity detection based on audio energy.
        
        Args:
            audio_data: Audio data as numpy array
            
        Returns:
            bool: True if voice activity is detected
        """
        # Calculate RMS energy
        rms = np.sqrt(np.mean(audio_data.astype(np.float32) ** 2))
        
        # Very low threshold for maximum sensitivity
        threshold = 10 * (1.0 - self.config.sensitivity)
        
        return rms > threshold
    
    def _simulate_speech_recognition(self, audio_data: np.ndarray) -> Optional[str]:
        """
        Use real speech recognition to detect wake words.
        
        Args:
            audio_data: Audio data as numpy array
            
        Returns:
            Optional[str]: Recognized text or None
        """
        try:
            import speech_recognition as sr
            
            # Convert numpy array back to audio bytes
            audio_bytes = audio_data.astype(np.int16).tobytes()
            
            # Create AudioData object for speech recognition
            audio_sr = sr.AudioData(audio_bytes, self.config.sample_rate, 2)
            
            # Use speech recognition to get text
            recognizer = sr.Recognizer()
            recognizer.energy_threshold = 300  # Lower threshold for better sensitivity
            text = recognizer.recognize_google(audio_sr, language="en-US")
            
            self.logger.info(f"Speech recognized: {text}")
            return text.lower()
            
        except sr.UnknownValueError:
            # No speech detected
            return None
        except sr.RequestError as e:
            self.logger.debug(f"Speech recognition request error: {e}")
            return None
        except Exception as e:
            self.logger.debug(f"Speech recognition error: {e}")
            return None
    
    def _check_wake_words(self, text: str) -> bool:
        """
        Check if the recognized text contains any wake words.
        
        Args:
            text: Recognized text to check
            
        Returns:
            bool: True if wake word is detected
        """
        if not text:
            return False
            
        text_lower = text.lower().strip()
        
        # Check against all wake word patterns
        for pattern in self.wake_word_patterns:
            if pattern.search(text_lower):
                self.logger.debug(f"Wake word pattern matched: {pattern.pattern} in '{text}'")
                return True
        
        return False
    
    def _handle_wake_word_detection(self):
        """Handle wake word detection with cooldown and callback"""
        current_time = time.time()
        
        # Check cooldown period
        if current_time - self.last_detection_time < self.detection_cooldown:
            return
        
        self.last_detection_time = current_time
        self.wake_word_detected = True
        
        self.logger.info("🎯 Wake word detected!")
        print("🎯 Wake word detected! Processing command...")
        
        # Call callback if provided
        if self.callback:
            try:
                self.callback()
            except Exception as e:
                self.logger.error(f"Error in wake word callback: {e}")
    
    def is_wake_word_detected(self) -> bool:
        """
        Check if a wake word was detected and reset the flag.
        
        Returns:
            bool: True if wake word was detected since last check
        """
        if self.wake_word_detected:
            self.wake_word_detected = False
            return True
        return False
    
    def set_sensitivity(self, sensitivity: float) -> None:
        """
        Set the wake word detection sensitivity.
        
        Args:
            sensitivity: Sensitivity level (0.0 to 1.0)
        """
        if not 0.0 <= sensitivity <= 1.0:
            raise ValueError("Sensitivity must be between 0.0 and 1.0")
            
        self.config.sensitivity = sensitivity
        self.logger.info(f"Wake word sensitivity set to {sensitivity}")
    
    def add_wake_word(self, wake_word: str) -> None:
        """
        Add a new wake word to the detection list.
        
        Args:
            wake_word: New wake word to add
        """
        if wake_word not in self.config.wake_words:
            self.config.wake_words.append(wake_word)
            self._prepare_wake_words()
            self.logger.info(f"Added wake word: {wake_word}")
    
    def remove_wake_word(self, wake_word: str) -> bool:
        """
        Remove a wake word from the detection list.
        
        Args:
            wake_word: Wake word to remove
            
        Returns:
            bool: True if wake word was removed, False if not found
        """
        if wake_word in self.config.wake_words:
            self.config.wake_words.remove(wake_word)
            self._prepare_wake_words()
            self.logger.info(f"Removed wake word: {wake_word}")
            return True
        return False
    
    def get_wake_words(self) -> List[str]:
        """
        Get the current list of wake words.
        
        Returns:
            List[str]: Current wake words
        """
        return self.config.wake_words.copy()
    
    def __enter__(self):
        """Context manager entry"""
        self.start_listening()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.stop_listening()


def create_wake_word_engine(wake_words: List[str], sensitivity: float = 0.7, 
                           callback: Optional[Callable] = None) -> WakeWordEngine:
    """
    Factory function to create a wake word engine with default configuration.
    
    Args:
        wake_words: List of wake words to detect
        sensitivity: Detection sensitivity (0.0 to 1.0)
        callback: Optional callback function for wake word detection
        
    Returns:
        WakeWordEngine: Configured wake word engine
    """
    config = WakeWordConfig(
        wake_words=wake_words,
        sensitivity=sensitivity
    )
    
    return WakeWordEngine(config, callback)