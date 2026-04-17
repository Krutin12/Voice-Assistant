"""
Audio processing module for wake word detection, speech recognition, and text-to-speech.
"""

# Import modules individually to avoid dependency issues
__all__ = []

# Text-to-Speech Engine (minimal dependencies)
try:
    from .text_to_speech import TextToSpeechEngine, TTSConfig, VoiceConfig, create_tts_engine
    __all__.extend(['TextToSpeechEngine', 'TTSConfig', 'VoiceConfig', 'create_tts_engine'])
except ImportError as e:
    print(f"Warning: Could not import text-to-speech module: {e}")

# Speech Recognition (requires pyaudio, vosk)
try:
    from .speech_recognition import SpeechRecognizer, SpeechRecognitionConfig, create_speech_recognizer
    __all__.extend(['SpeechRecognizer', 'SpeechRecognitionConfig', 'create_speech_recognizer'])
except ImportError as e:
    print(f"Warning: Could not import speech recognition module: {e}")

# Wake Word Engine (requires pyaudio)
try:
    from .wake_word_engine import WakeWordEngine, WakeWordConfig, create_wake_word_engine
    __all__.extend(['WakeWordEngine', 'WakeWordConfig', 'create_wake_word_engine'])
except ImportError as e:
    print(f"Warning: Could not import wake word engine module: {e}")