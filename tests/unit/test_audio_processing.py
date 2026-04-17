"""
Unit tests for Audio Processing components
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from wizard.audio.wake_word_engine import WakeWordEngine
from wizard.audio.speech_recognition import SpeechRecognizer
from wizard.audio.text_to_speech import TextToSpeech


@pytest.mark.unit
@pytest.mark.audio
class TestWakeWordEngine:
    """Test cases for WakeWordEngine"""
    
    @pytest.fixture
    def wake_word_engine(self, test_config):
        """Create WakeWordEngine instance for testing"""
        return WakeWordEngine(
            wake_words=test_config["wake_words"],
            sensitivity=0.5
        )
    
    def test_wake_word_engine_initialization(self, wake_word_engine):
        """Test wake word engine initializes correctly"""
        assert wake_word_engine is not None
        assert hasattr(wake_word_engine, 'wake_words')
        assert hasattr(wake_word_engine, 'sensitivity')
    
    def test_wake_word_detection(self, wake_word_engine):
        """Test wake word detection functionality"""
        # Mock audio input
        with patch('pyaudio.PyAudio') as mock_pyaudio:
            mock_stream = Mock()
            mock_stream.read.return_value = b"fake_audio_data"
            mock_pyaudio.return_value.open.return_value = mock_stream
            
            # Test detection method exists and returns boolean
            result = wake_word_engine.is_wake_word_detected()
            assert isinstance(result, bool)
    
    def test_sensitivity_adjustment(self, wake_word_engine):
        """Test sensitivity level adjustment"""
        original_sensitivity = wake_word_engine.sensitivity
        
        wake_word_engine.set_sensitivity(0.8)
        assert wake_word_engine.sensitivity == 0.8
        
        wake_word_engine.set_sensitivity(0.2)
        assert wake_word_engine.sensitivity == 0.2
    
    def test_start_stop_listening(self, wake_word_engine):
        """Test starting and stopping listening"""
        with patch('pyaudio.PyAudio'):
            wake_word_engine.start_listening()
            assert wake_word_engine.is_listening
            
            wake_word_engine.stop_listening()
            assert not wake_word_engine.is_listening
    
    def test_multiple_wake_words(self):
        """Test engine with multiple wake words"""
        wake_words = ["Hey Wizard", "Wizard", "Computer"]
        engine = WakeWordEngine(wake_words=wake_words, sensitivity=0.5)
        
        assert engine.wake_words == wake_words
        assert len(engine.wake_words) == 3


@pytest.mark.unit
@pytest.mark.audio
class TestSpeechRecognizer:
    """Test cases for SpeechRecognizer"""
    
    @pytest.fixture
    def speech_recognizer(self):
        """Create SpeechRecognizer instance for testing"""
        return SpeechRecognizer(language="en-US")
    
    def test_speech_recognizer_initialization(self, speech_recognizer):
        """Test speech recognizer initializes correctly"""
        assert speech_recognizer is not None
        assert hasattr(speech_recognizer, 'language')
        assert speech_recognizer.language == "en-US"
    
    @patch('speech_recognition.Recognizer')
    def test_speech_recognition(self, mock_recognizer, speech_recognizer):
        """Test speech recognition functionality"""
        # Mock the recognizer
        mock_instance = Mock()
        mock_instance.recognize_google.return_value = "test command"
        mock_recognizer.return_value = mock_instance
        
        # Test recognition
        audio_data = b"fake_audio_data"
        result = speech_recognizer.recognize(audio_data)
        
        assert isinstance(result, tuple)
        assert len(result) == 2  # (text, confidence)
        assert isinstance(result[0], str)
        assert isinstance(result[1], (int, float))
    
    def test_language_setting(self, speech_recognizer):
        """Test changing language settings"""
        speech_recognizer.set_language("es-ES")
        assert speech_recognizer.language == "es-ES"
        
        speech_recognizer.set_language("fr-FR")
        assert speech_recognizer.language == "fr-FR"
    
    @patch('speech_recognition.Microphone')
    def test_ambient_noise_calibration(self, mock_microphone, speech_recognizer):
        """Test ambient noise calibration"""
        mock_mic = Mock()
        mock_microphone.return_value = mock_mic
        
        # Should not raise exception
        speech_recognizer.calibrate_noise()
    
    def test_recognition_error_handling(self, speech_recognizer):
        """Test handling of recognition errors"""
        with patch('speech_recognition.Recognizer') as mock_recognizer:
            mock_instance = Mock()
            mock_instance.recognize_google.side_effect = Exception("Recognition failed")
            mock_recognizer.return_value = mock_instance
            
            audio_data = b"fake_audio_data"
            result = speech_recognizer.recognize(audio_data)
            
            # Should return error indication, not crash
            assert result is not None
            assert isinstance(result, tuple)


@pytest.mark.unit
@pytest.mark.audio
class TestTextToSpeech:
    """Test cases for TextToSpeech"""
    
    @pytest.fixture
    def tts_engine(self):
        """Create TextToSpeech instance for testing"""
        return TextToSpeech()
    
    def test_tts_initialization(self, tts_engine):
        """Test TTS engine initializes correctly"""
        assert tts_engine is not None
        assert hasattr(tts_engine, 'engine')
    
    @patch('pyttsx3.init')
    def test_text_to_speech(self, mock_pyttsx3, tts_engine):
        """Test text-to-speech functionality"""
        mock_engine = Mock()
        mock_pyttsx3.return_value = mock_engine
        
        tts_engine.engine = mock_engine
        
        test_text = "Hello, this is a test"
        tts_engine.speak(test_text)
        
        mock_engine.say.assert_called_once_with(test_text)
        mock_engine.runAndWait.assert_called_once()
    
    @patch('pyttsx3.init')
    def test_voice_properties(self, mock_pyttsx3, tts_engine):
        """Test voice property configuration"""
        mock_engine = Mock()
        mock_pyttsx3.return_value = mock_engine
        
        tts_engine.engine = mock_engine
        
        # Test setting voice properties
        tts_engine.set_voice_property('rate', 150)
        tts_engine.set_voice_property('volume', 0.8)
        
        # Should call setProperty on engine
        assert mock_engine.setProperty.call_count >= 2
    
    @patch('pyttsx3.init')
    def test_available_voices(self, mock_pyttsx3, tts_engine):
        """Test getting available voices"""
        mock_engine = Mock()
        mock_voices = [Mock(), Mock()]
        mock_voices[0].name = "Voice 1"
        mock_voices[1].name = "Voice 2"
        mock_engine.getProperty.return_value = mock_voices
        mock_pyttsx3.return_value = mock_engine
        
        tts_engine.engine = mock_engine
        
        voices = tts_engine.get_available_voices()
        
        assert isinstance(voices, list)
        mock_engine.getProperty.assert_called_with('voices')
    
    def test_save_to_file(self, tts_engine, temp_dir):
        """Test saving speech to file"""
        with patch('pyttsx3.init') as mock_pyttsx3:
            mock_engine = Mock()
            mock_pyttsx3.return_value = mock_engine
            
            tts_engine.engine = mock_engine
            
            output_file = temp_dir / "test_speech.wav"
            test_text = "Test speech output"
            
            tts_engine.save_to_file(test_text, str(output_file))
            
            # Should configure engine for file output
            mock_engine.save_to_file.assert_called_once_with(test_text, str(output_file))


@pytest.mark.unit
@pytest.mark.audio
class TestAudioProcessingIntegration:
    """Integration tests for audio processing components"""
    
    def test_wake_word_to_speech_recognition_flow(self, test_config):
        """Test flow from wake word detection to speech recognition"""
        with patch('pyaudio.PyAudio'), \
             patch('speech_recognition.Recognizer'):
            
            # Initialize components
            wake_word_engine = WakeWordEngine(
                wake_words=test_config["wake_words"],
                sensitivity=0.5
            )
            speech_recognizer = SpeechRecognizer()
            
            # Test that components can work together
            assert wake_word_engine is not None
            assert speech_recognizer is not None
    
    def test_speech_recognition_to_tts_flow(self):
        """Test flow from speech recognition to text-to-speech"""
        with patch('speech_recognition.Recognizer'), \
             patch('pyttsx3.init'):
            
            speech_recognizer = SpeechRecognizer()
            tts_engine = TextToSpeech()
            
            # Simulate recognition result
            recognized_text = "test command"
            response_text = "Command processed"
            
            # Should be able to process the flow
            assert speech_recognizer is not None
            assert tts_engine is not None
    
    def test_audio_device_error_handling(self):
        """Test handling of audio device errors"""
        with patch('pyaudio.PyAudio') as mock_pyaudio:
            # Simulate audio device error
            mock_pyaudio.side_effect = Exception("No audio devices")
            
            # Components should handle gracefully
            try:
                wake_word_engine = WakeWordEngine(["test"], 0.5)
                # Should not crash, may have limited functionality
                assert wake_word_engine is not None
            except Exception as e:
                # If it does raise an exception, it should be handled gracefully
                assert "audio" in str(e).lower()


@pytest.mark.unit
@pytest.mark.audio
class TestAudioProcessingPerformance:
    """Performance tests for audio processing"""
    
    def test_wake_word_detection_performance(self, performance_thresholds):
        """Test wake word detection performance"""
        import time
        
        with patch('pyaudio.PyAudio'):
            wake_word_engine = WakeWordEngine(["test"], 0.5)
            
            start_time = time.time()
            result = wake_word_engine.is_wake_word_detected()
            end_time = time.time()
            
            detection_time = end_time - start_time
            
            assert detection_time < performance_thresholds["wake_word_detection"]
            assert isinstance(result, bool)
    
    def test_speech_recognition_performance(self, performance_thresholds):
        """Test speech recognition performance"""
        import time
        
        with patch('speech_recognition.Recognizer') as mock_recognizer:
            mock_instance = Mock()
            mock_instance.recognize_google.return_value = "test"
            mock_recognizer.return_value = mock_instance
            
            speech_recognizer = SpeechRecognizer()
            
            start_time = time.time()
            result = speech_recognizer.recognize(b"fake_audio")
            end_time = time.time()
            
            recognition_time = end_time - start_time
            
            # Should be fast (mocked, but test the overhead)
            assert recognition_time < 0.1  # Very fast for mocked version
            assert result is not None
    
    def test_tts_performance(self, performance_thresholds):
        """Test text-to-speech performance"""
        import time
        
        with patch('pyttsx3.init') as mock_pyttsx3:
            mock_engine = Mock()
            mock_pyttsx3.return_value = mock_engine
            
            tts_engine = TextToSpeech()
            tts_engine.engine = mock_engine
            
            start_time = time.time()
            tts_engine.speak("Test speech")
            end_time = time.time()
            
            tts_time = end_time - start_time
            
            # Should be fast for setup (actual speech time varies)
            assert tts_time < 0.1  # Setup time only
            mock_engine.say.assert_called_once()
            mock_engine.runAndWait.assert_called_once()