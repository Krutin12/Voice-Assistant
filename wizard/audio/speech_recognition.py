"""
Speech Recognition Module for Wizard Voice Assistant

Integrates offline speech recognition library with audio preprocessing,
noise reduction, confidence scoring, and error handling.
"""

import logging
import threading
import time
from typing import Tuple, Optional, Dict, Any
from dataclasses import dataclass
from pathlib import Path
import json

import pyaudio
import numpy as np
import speech_recognition as sr
from pydub import AudioSegment
from pydub.effects import normalize, low_pass_filter, high_pass_filter
import vosk


@dataclass
class SpeechRecognitionConfig:
    """Configuration for speech recognition"""
    language: str = "en-US"
    model_path: Optional[str] = None
    sample_rate: int = 16000
    chunk_size: int = 1024
    audio_format: int = pyaudio.paInt16
    channels: int = 1
    
    # Audio preprocessing settings
    noise_reduction: bool = True
    normalize_audio: bool = True
    low_pass_freq: int = 8000
    high_pass_freq: int = 500  # Cut more background noise/voice rumble
    
    # Recognition settings
    timeout: float = 5.0
    phrase_timeout: float = 1.0
    min_confidence: float = 0.5
    energy_threshold: int = 500  # Less sensitive to background noise
    dynamic_energy_threshold: bool = True


class SpeechRecognizer:
    """
    Offline speech recognition module with audio preprocessing,
    noise reduction, and confidence scoring.
    """
    
    def __init__(self, config: SpeechRecognitionConfig):
        """
        Initialize the speech recognition module.
        
        Args:
            config: Speech recognition configuration
        """
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Initialize recognizers
        self.sr_recognizer = sr.Recognizer()
        self.vosk_model = None
        self.vosk_recognizer = None
        
        # Audio processing
        self.microphone = None
        self.audio_buffer = []
        
        # State management
        self.is_listening = False
        self.calibrated = False
        
        # Initialize components
        self._initialize_recognizers()
        self._setup_audio()
        
    def _initialize_recognizers(self):
        """Initialize speech recognition engines"""
        try:
            # Configure SpeechRecognition library
            self.sr_recognizer.energy_threshold = self.config.energy_threshold
            self.sr_recognizer.dynamic_energy_threshold = self.config.dynamic_energy_threshold
            self.sr_recognizer.pause_threshold = self.config.phrase_timeout
            
            # Initialize Vosk model if available
            if self.config.model_path and Path(self.config.model_path).exists():
                self.vosk_model = vosk.Model(self.config.model_path)
                self.vosk_recognizer = vosk.KaldiRecognizer(
                    self.vosk_model, 
                    self.config.sample_rate
                )
                self.logger.info(f"Vosk model loaded from {self.config.model_path}")
            else:
                self.logger.debug("Vosk model not available, using SpeechRecognition fallback")
                
        except Exception as e:
            self.logger.error(f"Error initializing speech recognizers: {e}")
            
    def _setup_audio(self):
        """Setup audio input device"""
        try:
            # Use the working Steam Streaming Microphone (device 8)
            self.microphone = sr.Microphone(
                device_index=8,
                sample_rate=self.config.sample_rate,
                chunk_size=self.config.chunk_size
            )
            self.logger.info("Audio input device initialized with Steam Streaming Microphone (device 8)")
            
        except Exception as e:
            self.logger.warning(f"Could not use device 8, using default: {e}")
            try:
                self.microphone = sr.Microphone(
                    sample_rate=self.config.sample_rate,
                    chunk_size=self.config.chunk_size
                )
                self.logger.info("Audio input device initialized with default microphone")
            except Exception as e2:
                self.logger.error(f"Error setting up audio: {e2}")
            
    def calibrate_noise(self, duration: float = 2.0) -> bool:
        """
        Calibrate the recognizer for ambient noise.
        
        Args:
            duration: Duration in seconds to listen for ambient noise
            
        Returns:
            bool: True if calibration successful
        """
        if not self.microphone:
            self.logger.error("Microphone not available for calibration")
            return False
            
        try:
            self.logger.info(f"Calibrating for ambient noise ({duration}s)...")
            
            with self.microphone as source:
                self.sr_recognizer.adjust_for_ambient_noise(source, duration=duration)
                
            self.calibrated = True
            self.logger.info(f"Noise calibration complete. Energy threshold: {self.sr_recognizer.energy_threshold}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error during noise calibration: {e}")
            return False
    
    def recognize_speech(self, audio_data: Optional[bytes] = None, 
                        timeout: Optional[float] = None) -> Tuple[str, float]:
        """
        Recognize speech from audio data or microphone input.
        
        Args:
            audio_data: Optional audio data bytes. If None, listens from microphone
            timeout: Optional timeout for listening
            
        Returns:
            Tuple[str, float]: Recognized text and confidence score (0.0 to 1.0)
        """
        if audio_data:
            return self._recognize_from_data(audio_data)
        else:
            return self._recognize_from_microphone(timeout or self.config.timeout)
    
    def _recognize_from_microphone(self, timeout: float) -> Tuple[str, float]:
        """
        Recognize speech from microphone input.
        
        Args:
            timeout: Timeout for listening
            
        Returns:
            Tuple[str, float]: Recognized text and confidence score
        """
        if not self.microphone:
            return "", 0.0
            
        try:
            self.logger.debug("Listening for speech...")
            
            with self.microphone as source:
                # Listen for audio with timeout
                audio = self.sr_recognizer.listen(
                    source, 
                    timeout=timeout,
                    phrase_time_limit=self.config.phrase_timeout
                )
                
            # Process the audio
            return self._process_audio(audio)
            
        except sr.WaitTimeoutError:
            self.logger.debug("Speech recognition timeout")
            return "", 0.0
        except Exception as e:
            self.logger.error(f"Error recognizing speech from microphone: {e}")
            return "", 0.0
    
    def _recognize_from_data(self, audio_data: bytes) -> Tuple[str, float]:
        """
        Recognize speech from audio data bytes.
        
        Args:
            audio_data: Audio data as bytes
            
        Returns:
            Tuple[str, float]: Recognized text and confidence score
        """
        try:
            # Convert bytes to AudioData
            audio = sr.AudioData(
                audio_data,
                self.config.sample_rate,
                2  # 2 bytes per sample for 16-bit audio
            )
            
            return self._process_audio(audio)
            
        except Exception as e:
            self.logger.error(f"Error recognizing speech from data: {e}")
            return "", 0.0
    
    def _process_audio(self, audio: sr.AudioData) -> Tuple[str, float]:
        """
        Process audio data through recognition pipeline.
        
        Args:
            audio: AudioData object from speech_recognition
            
        Returns:
            Tuple[str, float]: Recognized text and confidence score
        """
        try:
            # Preprocess audio if enabled
            if self.config.noise_reduction or self.config.normalize_audio:
                audio = self._preprocess_audio(audio)
            
            # Try Vosk first if available
            if self.vosk_recognizer:
                result = self._recognize_with_vosk(audio)
                if result[0]:  # If Vosk succeeded
                    return result
            
            # Fallback to SpeechRecognition library
            return self._recognize_with_sr(audio)
            
        except Exception as e:
            self.logger.error(f"Error processing audio: {e}")
            return "", 0.0
    
    def _preprocess_audio(self, audio: sr.AudioData) -> sr.AudioData:
        """
        Preprocess audio data for better recognition.
        
        Args:
            audio: Original audio data
            
        Returns:
            sr.AudioData: Preprocessed audio data
        """
        try:
            # Convert to pydub AudioSegment
            audio_segment = AudioSegment(
                data=audio.get_raw_data(),
                sample_width=audio.sample_width,
                frame_rate=audio.sample_rate,
                channels=1
            )
            
            # Apply preprocessing
            if self.config.normalize_audio:
                audio_segment = normalize(audio_segment)
                
            if self.config.noise_reduction:
                # Apply frequency filtering for noise reduction
                audio_segment = high_pass_filter(audio_segment, self.config.high_pass_freq)
                audio_segment = low_pass_filter(audio_segment, self.config.low_pass_freq)
            
            # Convert back to AudioData
            processed_audio = sr.AudioData(
                audio_segment.raw_data,
                audio.sample_rate,
                audio.sample_width
            )
            
            return processed_audio
            
        except Exception as e:
            self.logger.error(f"Error preprocessing audio: {e}")
            return audio  # Return original if preprocessing fails
    
    def _recognize_with_vosk(self, audio: sr.AudioData) -> Tuple[str, float]:
        """
        Recognize speech using Vosk offline engine.
        
        Args:
            audio: Audio data to recognize
            
        Returns:
            Tuple[str, float]: Recognized text and confidence score
        """
        try:
            # Get raw audio data
            raw_data = audio.get_raw_data()
            
            # Process with Vosk
            if self.vosk_recognizer.AcceptWaveform(raw_data):
                result = json.loads(self.vosk_recognizer.Result())
            else:
                result = json.loads(self.vosk_recognizer.PartialResult())
            
            text = result.get('text', '').strip()
            confidence = result.get('confidence', 0.0)
            
            if text and confidence >= self.config.min_confidence:
                self.logger.debug(f"Vosk recognized: '{text}' (confidence: {confidence:.2f})")
                return text, confidence
            
            return "", 0.0
            
        except Exception as e:
            self.logger.error(f"Error with Vosk recognition: {e}")
            return "", 0.0
    
    def _recognize_with_sr(self, audio: sr.AudioData) -> Tuple[str, float]:
        """
        Recognize speech using SpeechRecognition library.
        
        Args:
            audio: Audio data to recognize
            
        Returns:
            Tuple[str, float]: Recognized text and confidence score
        """
        try:
            # Try different recognition engines in order of preference
            engines = [
                ('sphinx', self._recognize_sphinx),
                ('google', self._recognize_google_offline),
            ]
            
            for engine_name, engine_func in engines:
                try:
                    result = engine_func(audio)
                    if result[0]:  # If recognition succeeded
                        self.logger.debug(f"{engine_name} recognized: '{result[0]}' (confidence: {result[1]:.2f})")
                        return result
                except Exception as e:
                    self.logger.debug(f"{engine_name} recognition failed: {e}")
                    continue
            
            return "", 0.0
            
        except Exception as e:
            self.logger.error(f"Error with SpeechRecognition: {e}")
            return "", 0.0
    
    def _recognize_sphinx(self, audio: sr.AudioData) -> Tuple[str, float]:
        """Recognize using CMU Sphinx (offline)"""
        try:
            text = self.sr_recognizer.recognize_sphinx(audio)
            # Sphinx doesn't provide confidence, so we estimate based on text length
            confidence = min(0.8, len(text.split()) * 0.1 + 0.3) if text else 0.0
            return text.strip(), confidence
        except sr.UnknownValueError:
            return "", 0.0
        except Exception as e:
            raise e
    
    def _recognize_google_offline(self, audio: sr.AudioData) -> Tuple[str, float]:
        """Recognize using Google Speech Recognition (offline mode if available)"""
        try:
            # Note: This would typically require internet, but we include it as fallback
            # In a truly offline system, this would be replaced with another offline engine
            text = self.sr_recognizer.recognize_google(audio, language=self.config.language)
            confidence = 0.7  # Default confidence for Google API
            return text.strip(), confidence
        except sr.UnknownValueError:
            return "", 0.0
        except Exception as e:
            raise e
    
    def set_language(self, language: str) -> bool:
        """
        Set the recognition language.
        
        Args:
            language: Language code (e.g., 'en-US', 'es-ES')
            
        Returns:
            bool: True if language was set successfully
        """
        try:
            self.config.language = language
            
            # Reinitialize Vosk model if needed for new language
            if self.config.model_path:
                model_path = Path(self.config.model_path).parent / f"vosk-model-{language}"
                if model_path.exists():
                    self.vosk_model = vosk.Model(str(model_path))
                    self.vosk_recognizer = vosk.KaldiRecognizer(
                        self.vosk_model, 
                        self.config.sample_rate
                    )
                    self.logger.info(f"Switched to language: {language}")
                    return True
            
            self.logger.warning(f"Language model not available for {language}")
            return False
            
        except Exception as e:
            self.logger.error(f"Error setting language: {e}")
            return False
    
    def get_supported_languages(self) -> list:
        """
        Get list of supported languages.
        
        Returns:
            list: List of supported language codes
        """
        # This would typically scan available models
        return ["en-US", "en-GB", "es-ES", "fr-FR", "de-DE"]
    
    def start_continuous_listening(self, callback: callable) -> bool:
        """
        Start continuous listening mode with callback.
        
        Args:
            callback: Function to call with recognized text and confidence
            
        Returns:
            bool: True if started successfully
        """
        if self.is_listening:
            return True
            
        try:
            self.is_listening = True
            self._listen_thread = threading.Thread(
                target=self._continuous_listen_loop,
                args=(callback,),
                daemon=True
            )
            self._listen_thread.start()
            self.logger.info("Started continuous listening")
            return True
            
        except Exception as e:
            self.logger.error(f"Error starting continuous listening: {e}")
            self.is_listening = False
            return False
    
    def stop_continuous_listening(self):
        """Stop continuous listening mode"""
        if self.is_listening:
            self.is_listening = False
            self.logger.info("Stopped continuous listening")
    
    def _continuous_listen_loop(self, callback: callable):
        """Continuous listening loop"""
        while self.is_listening:
            try:
                text, confidence = self.recognize_speech(timeout=1.0)
                if text and confidence >= self.config.min_confidence:
                    callback(text, confidence)
            except Exception as e:
                self.logger.error(f"Error in continuous listening: {e}")
                time.sleep(0.1)
    
    def get_audio_devices(self) -> Dict[int, str]:
        """
        Get available audio input devices.
        
        Returns:
            Dict[int, str]: Dictionary mapping device index to device name
        """
        devices = {}
        try:
            for i in range(sr.Microphone.list_microphone_names().__len__()):
                devices[i] = sr.Microphone.list_microphone_names()[i]
        except Exception as e:
            self.logger.error(f"Error getting audio devices: {e}")
        
        return devices
    
    def set_microphone(self, device_index: Optional[int] = None) -> bool:
        """
        Set the microphone device.
        
        Args:
            device_index: Device index, or None for default
            
        Returns:
            bool: True if microphone was set successfully
        """
        try:
            self.microphone = sr.Microphone(
                device_index=device_index,
                sample_rate=self.config.sample_rate,
                chunk_size=self.config.chunk_size
            )
            self.logger.info(f"Microphone set to device {device_index}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error setting microphone: {e}")
            return False


def create_speech_recognizer(language: str = "en-US", 
                           model_path: Optional[str] = None) -> SpeechRecognizer:
    """
    Factory function to create a speech recognizer with default configuration.
    
    Args:
        language: Recognition language
        model_path: Optional path to Vosk model
        
    Returns:
        SpeechRecognizer: Configured speech recognizer
    """
    config = SpeechRecognitionConfig(
        language=language,
        model_path=model_path
    )
    
    return SpeechRecognizer(config)