"""
Integration tests for complete voice interaction workflows
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
import sys
import time
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from wizard.main import WizardApp
from wizard.commands.command_router import CommandRouter
from wizard.audio.wake_word_engine import WakeWordEngine
from wizard.audio.speech_recognition import SpeechRecognizer
from wizard.audio.text_to_speech import TextToSpeech


@pytest.mark.integration
class TestCompleteVoiceWorkflow:
    """Test complete voice interaction workflows"""
    
    @pytest.fixture
    def wizard_app(self, config_manager):
        """Create WizardApp instance for testing"""
        with patch('pyaudio.PyAudio'), \
             patch('pyttsx3.init'), \
             patch('speech_recognition.Recognizer'):
            return WizardApp(config_manager, test_mode=True)
    
    def test_wake_word_to_response_workflow(self, wizard_app):
        """Test complete workflow from wake word to response"""
        with patch.object(wizard_app, 'wake_word_engine') as mock_wake_word, \
             patch.object(wizard_app, 'speech_recognizer') as mock_speech, \
             patch.object(wizard_app, 'tts_engine') as mock_tts, \
             patch.object(wizard_app, 'command_router') as mock_router:
            
            # Setup mocks
            mock_wake_word.is_wake_word_detected.return_value = True
            mock_speech.recognize.return_value = ("what time is it", 0.95)
            mock_router.process_command.return_value = "It's 3:45 PM"
            
            # Simulate workflow
            result = wizard_app.process_voice_interaction()
            
            # Verify workflow steps
            mock_wake_word.is_wake_word_detected.assert_called()
            mock_speech.recognize.assert_called()
            mock_router.process_command.assert_called_with("what time is it")
            mock_tts.speak.assert_called_with("It's 3:45 PM")
    
    def test_command_processing_pipeline(self, wizard_app, sample_commands):
        """Test processing multiple commands through the pipeline"""
        with patch.object(wizard_app, 'speech_recognizer') as mock_speech, \
             patch.object(wizard_app, 'tts_engine') as mock_tts:
            
            responses = []
            
            for i, command in enumerate(sample_commands[:3]):  # Test first 3 commands
                mock_speech.recognize.return_value = (command, 0.9)
                
                response = wizard_app.process_voice_command()
                responses.append(response)
            
            # All commands should produce responses
            assert len(responses) == 3
            for response in responses:
                assert response is not None
                assert len(response) > 0
    
    def test_error_recovery_workflow(self, wizard_app):
        """Test error recovery in voice workflow"""
        with patch.object(wizard_app, 'speech_recognizer') as mock_speech, \
             patch.object(wizard_app, 'tts_engine') as mock_tts, \
             patch.object(wizard_app, 'command_router') as mock_router:
            
            # Simulate speech recognition error
            mock_speech.recognize.side_effect = Exception("Recognition failed")
            
            # Should handle error gracefully
            result = wizard_app.process_voice_command()
            
            # Should return error message, not crash
            assert result is not None
            assert isinstance(result, str)
    
    def test_continuous_listening_simulation(self, wizard_app):
        """Test continuous listening simulation"""
        with patch.object(wizard_app, 'wake_word_engine') as mock_wake_word, \
             patch.object(wizard_app, 'speech_recognizer') as mock_speech, \
             patch.object(wizard_app, 'tts_engine') as mock_tts:
            
            # Simulate wake word detection sequence
            wake_word_sequence = [False, False, True, False, False]
            mock_wake_word.is_wake_word_detected.side_effect = wake_word_sequence
            mock_speech.recognize.return_value = ("test command", 0.9)
            
            interactions = 0
            for _ in range(5):
                if wizard_app.check_for_wake_word():
                    interactions += 1
                    wizard_app.process_voice_command()
            
            # Should have detected wake word once
            assert interactions == 1
    
    def test_multi_turn_conversation(self, wizard_app):
        """Test multi-turn conversation handling"""
        with patch.object(wizard_app, 'speech_recognizer') as mock_speech, \
             patch.object(wizard_app, 'command_router') as mock_router:
            
            # Simulate conversation
            conversation = [
                ("what is artificial intelligence", "AI is machine intelligence"),
                ("tell me more", "AI includes machine learning and neural networks"),
                ("thank you", "You're welcome!")
            ]
            
            responses = []
            for command, expected_response in conversation:
                mock_speech.recognize.return_value = (command, 0.9)
                mock_router.process_command.return_value = expected_response
                
                response = wizard_app.process_voice_command()
                responses.append(response)
            
            assert len(responses) == 3
            for response in responses:
                assert response is not None


@pytest.mark.integration
class TestSystemIntegration:
    """Test integration with system components"""
    
    def test_file_system_integration(self, wizard_app, sample_file_structure):
        """Test file system operations integration"""
        with patch.object(wizard_app, 'speech_recognizer') as mock_speech:
            
            # Test file search
            mock_speech.recognize.return_value = ("find test.txt", 0.9)
            response = wizard_app.process_voice_command()
            
            assert response is not None
            # Should indicate file search was performed
    
    def test_application_integration(self, wizard_app):
        """Test application launch integration"""
        with patch.object(wizard_app, 'speech_recognizer') as mock_speech, \
             patch('subprocess.run') as mock_subprocess:
            
            mock_subprocess.return_value.returncode = 0
            mock_speech.recognize.return_value = ("open calculator", 0.9)
            
            response = wizard_app.process_voice_command()
            
            assert response is not None
            # Should indicate application launch attempt
    
    def test_media_control_integration(self, wizard_app):
        """Test media control integration"""
        with patch.object(wizard_app, 'speech_recognizer') as mock_speech, \
             patch('pycaw.pycaw.AudioUtilities') as mock_audio:
            
            mock_speech.recognize.return_value = ("set volume to 50", 0.9)
            
            response = wizard_app.process_voice_command()
            
            assert response is not None
            # Should indicate volume control attempt


@pytest.mark.integration
class TestPerformanceIntegration:
    """Test performance of integrated systems"""
    
    def test_end_to_end_response_time(self, wizard_app, performance_thresholds):
        """Test end-to-end response time"""
        with patch.object(wizard_app, 'speech_recognizer') as mock_speech, \
             patch.object(wizard_app, 'tts_engine') as mock_tts:
            
            mock_speech.recognize.return_value = ("what time is it", 0.9)
            
            start_time = time.time()
            response = wizard_app.process_voice_command()
            end_time = time.time()
            
            response_time = end_time - start_time
            
            assert response_time < performance_thresholds["command_processing"]
            assert response is not None
    
    def test_memory_usage_integration(self, wizard_app):
        """Test memory usage during operation"""
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        # Simulate multiple interactions
        with patch.object(wizard_app, 'speech_recognizer') as mock_speech:
            for i in range(10):
                mock_speech.recognize.return_value = (f"test command {i}", 0.9)
                wizard_app.process_voice_command()
        
        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_increase = final_memory - initial_memory
        
        # Memory increase should be reasonable
        assert memory_increase < 100  # Less than 100MB increase
    
    def test_concurrent_operations(self, wizard_app):
        """Test handling concurrent operations"""
        import threading
        import time
        
        results = []
        
        def process_command(command):
            with patch.object(wizard_app, 'speech_recognizer') as mock_speech:
                mock_speech.recognize.return_value = (command, 0.9)
                result = wizard_app.process_voice_command()
                results.append(result)
        
        # Start multiple threads
        threads = []
        commands = ["what time is it", "open calculator", "set timer for 5 minutes"]
        
        for command in commands:
            thread = threading.Thread(target=process_command, args=(command,))
            threads.append(thread)
            thread.start()
        
        # Wait for all threads
        for thread in threads:
            thread.join(timeout=5)
        
        # All commands should complete
        assert len(results) == len(commands)
        for result in results:
            assert result is not None


@pytest.mark.integration
class TestErrorHandlingIntegration:
    """Test error handling across integrated systems"""
    
    def test_audio_device_failure_recovery(self, wizard_app):
        """Test recovery from audio device failures"""
        with patch.object(wizard_app, 'wake_word_engine') as mock_wake_word:
            
            # Simulate audio device failure
            mock_wake_word.is_wake_word_detected.side_effect = Exception("Audio device error")
            
            # Should handle gracefully
            result = wizard_app.check_for_wake_word()
            
            # Should return False or handle error, not crash
            assert isinstance(result, bool) or result is None
    
    def test_speech_recognition_failure_recovery(self, wizard_app):
        """Test recovery from speech recognition failures"""
        with patch.object(wizard_app, 'speech_recognizer') as mock_speech:
            
            # Simulate recognition failure
            mock_speech.recognize.side_effect = Exception("Recognition failed")
            
            # Should handle gracefully
            result = wizard_app.process_voice_command()
            
            # Should return error message, not crash
            assert result is not None
            assert isinstance(result, str)
    
    def test_command_execution_failure_recovery(self, wizard_app):
        """Test recovery from command execution failures"""
        with patch.object(wizard_app, 'command_router') as mock_router:
            
            # Simulate command execution failure
            mock_router.process_command.side_effect = Exception("Command failed")
            
            with patch.object(wizard_app, 'speech_recognizer') as mock_speech:
                mock_speech.recognize.return_value = ("test command", 0.9)
                
                result = wizard_app.process_voice_command()
                
                # Should handle gracefully
                assert result is not None
                assert isinstance(result, str)
    
    def test_tts_failure_recovery(self, wizard_app):
        """Test recovery from TTS failures"""
        with patch.object(wizard_app, 'tts_engine') as mock_tts, \
             patch.object(wizard_app, 'speech_recognizer') as mock_speech:
            
            # Simulate TTS failure
            mock_tts.speak.side_effect = Exception("TTS failed")
            mock_speech.recognize.return_value = ("test command", 0.9)
            
            # Should handle gracefully
            result = wizard_app.process_voice_command()
            
            # Should still process command even if TTS fails
            assert result is not None


@pytest.mark.integration
@pytest.mark.slow
class TestLongRunningIntegration:
    """Test long-running integration scenarios"""
    
    def test_extended_operation(self, wizard_app, integration_test_config):
        """Test extended operation simulation"""
        duration = integration_test_config["test_duration"]
        command_interval = integration_test_config["command_interval"]
        
        start_time = time.time()
        command_count = 0
        successful_responses = 0
        
        with patch.object(wizard_app, 'speech_recognizer') as mock_speech:
            
            while time.time() - start_time < duration:
                mock_speech.recognize.return_value = ("what time is it", 0.9)
                
                try:
                    response = wizard_app.process_voice_command()
                    command_count += 1
                    
                    if response and len(response) > 0:
                        successful_responses += 1
                        
                except Exception as e:
                    # Log but continue
                    print(f"Command failed: {e}")
                
                time.sleep(command_interval)
        
        # Calculate success rate
        success_rate = successful_responses / command_count if command_count > 0 else 0
        
        assert command_count > 0
        assert success_rate >= integration_test_config["expected_accuracy"]
    
    def test_memory_stability(self, wizard_app):
        """Test memory stability over time"""
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        # Run many operations
        with patch.object(wizard_app, 'speech_recognizer') as mock_speech:
            for i in range(100):
                mock_speech.recognize.return_value = (f"test command {i}", 0.9)
                wizard_app.process_voice_command()
                
                # Check memory every 10 operations
                if i % 10 == 0:
                    current_memory = process.memory_info().rss / 1024 / 1024
                    memory_increase = current_memory - initial_memory
                    
                    # Memory shouldn't grow excessively
                    assert memory_increase < 200  # Less than 200MB increase
        
        final_memory = process.memory_info().rss / 1024 / 1024
        total_increase = final_memory - initial_memory
        
        # Total memory increase should be reasonable
        assert total_increase < 300  # Less than 300MB total increase