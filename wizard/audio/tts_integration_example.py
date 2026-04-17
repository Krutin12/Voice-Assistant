#!/usr/bin/env python3
"""
Example integration of TTS engine with the main Wizard application.
Shows how to properly initialize and use the TTS engine with configuration.
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from wizard.utils.config_manager import ConfigManager
from wizard.audio.text_to_speech import create_tts_engine
from wizard.utils.logger import setup_logging


class WizardTTSManager:
    """
    TTS Manager for the Wizard Voice Assistant.
    Handles TTS engine initialization and integration with the main config system.
    """
    
    def __init__(self, config_manager: ConfigManager):
        """
        Initialize the TTS manager.
        
        Args:
            config_manager: Main configuration manager instance
        """
        self.config_manager = config_manager
        self.config = config_manager.config
        self.logger = setup_logging(log_level="INFO")
        
        # Initialize TTS engine
        self.tts_engine = None
        self._initialize_tts()
    
    def _initialize_tts(self):
        """Initialize the TTS engine with current configuration"""
        try:
            self.tts_engine = create_tts_engine(self.config.voice_settings)
            self.logger.info("TTS engine initialized successfully")
            
            # Log current voice info
            voice_info = self.tts_engine.get_current_voice_info()
            if voice_info:
                self.logger.info(f"Current voice: {voice_info['name']} ({voice_info['gender']})")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize TTS engine: {e}")
    
    def speak(self, text: str, async_mode: bool = True) -> bool:
        """
        Speak the given text using the configured voice settings.
        
        Args:
            text: Text to speak
            async_mode: Whether to speak asynchronously
            
        Returns:
            bool: True if speech was successful
        """
        if not self.tts_engine:
            self.logger.error("TTS engine not initialized")
            return False
        
        return self.tts_engine.speak(text, async_mode=async_mode)
    
    def speak_confirmation(self, message: str) -> bool:
        """
        Speak a confirmation message with appropriate feedback.
        
        Args:
            message: Confirmation message to speak
            
        Returns:
            bool: True if speech was successful
        """
        # Play success feedback sound
        self.tts_engine.play_feedback_sound('success')
        
        # Speak the confirmation
        return self.speak(message, async_mode=False)
    
    def speak_error(self, error_message: str) -> bool:
        """
        Speak an error message with appropriate feedback.
        
        Args:
            error_message: Error message to speak
            
        Returns:
            bool: True if speech was successful
        """
        # Play error feedback sound
        self.tts_engine.play_feedback_sound('error')
        
        # Speak the error
        return self.speak(f"Error: {error_message}", async_mode=False)
    
    def update_voice_settings(self, gender: str = None, speed: int = None, volume: float = None) -> bool:
        """
        Update voice settings and save to configuration.
        
        Args:
            gender: Voice gender preference ('male' or 'female')
            speed: Speech speed in words per minute
            volume: Speech volume (0.0 to 1.0)
            
        Returns:
            bool: True if settings were updated successfully
        """
        try:
            # Update configuration
            if gender:
                self.config_manager.update_setting('voice_settings', 'gender', gender)
            if speed:
                self.config_manager.update_setting('voice_settings', 'speed', speed)
            if volume:
                self.config_manager.update_setting('voice_settings', 'volume', volume)
            
            # Update TTS engine
            if self.tts_engine:
                self.tts_engine.update_from_main_config(self.config.voice_settings)
            
            self.logger.info("Voice settings updated successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to update voice settings: {e}")
            return False
    
    def get_available_voices(self) -> list:
        """
        Get list of available voices.
        
        Returns:
            list: List of available voice information
        """
        if self.tts_engine:
            return self.tts_engine.get_available_voices()
        return []
    
    def set_voice_by_name(self, voice_name: str) -> bool:
        """
        Set voice by name.
        
        Args:
            voice_name: Name of the voice to set
            
        Returns:
            bool: True if voice was set successfully
        """
        if not self.tts_engine:
            return False
        
        voices = self.get_available_voices()
        for voice in voices:
            if voice_name.lower() in voice['name'].lower():
                return self.tts_engine.set_voice(voice['id'])
        
        self.logger.warning(f"Voice not found: {voice_name}")
        return False
    
    def stop_speaking(self):
        """Stop current speech"""
        if self.tts_engine:
            self.tts_engine.stop_speaking()
    
    def shutdown(self):
        """Shutdown the TTS manager"""
        if self.tts_engine:
            self.tts_engine.shutdown()
            self.logger.info("TTS manager shutdown complete")


def main():
    """Example usage of the TTS manager"""
    print("Wizard TTS Manager Example")
    print("=" * 40)
    
    # Initialize configuration
    config_manager = ConfigManager()
    config = config_manager.load_config()
    
    # Initialize TTS manager
    tts_manager = WizardTTSManager(config_manager)
    
    # Example usage
    print("Testing TTS manager functionality...")
    
    # Basic speech
    tts_manager.speak("Hello! I am the Wizard voice assistant.", async_mode=False)
    
    # List available voices
    voices = tts_manager.get_available_voices()
    print(f"\nAvailable voices ({len(voices)}):")
    for i, voice in enumerate(voices, 1):
        print(f"  {i}. {voice['name']} ({voice['gender']})")
    
    # Test confirmation
    tts_manager.speak_confirmation("Task completed successfully!")
    
    # Test error message
    tts_manager.speak_error("Could not find the requested file.")
    
    # Test voice settings update
    print("\nTesting voice settings update...")
    tts_manager.update_voice_settings(speed=160, volume=0.8)
    tts_manager.speak("Voice settings have been updated.", async_mode=False)
    
    # Cleanup
    tts_manager.shutdown()
    print("\nTTS manager example completed.")


if __name__ == "__main__":
    main()