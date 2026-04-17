"""
Configuration Command Handlers for Wizard Voice Assistant

This module provides command handlers for configuration management
including voice customization, personality settings, and user preferences.
"""

from typing import Dict, Any, List
# Add project root to Python path for imports
import sys
from pathlib import Path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))
from wizard.commands.command_router import Command, Response
from wizard.utils.config_manager import ConfigManager
import logging

logger = logging.getLogger(__name__)


class ConfigurationHandlers:
    """Handles configuration-related voice commands"""
    
    def __init__(self, config_manager: ConfigManager):
        self.config = config_manager
    
    def handle_set_voice_gender(self, command: Command) -> Response:
        """Handle setting voice gender"""
        gender = command.entities.get('gender')
        
        if not gender:
            return Response(
                text="Please specify a voice gender: male, female, or neutral.",
                action_taken=False
            )
        
        gender = gender.lower()
        valid_genders = ["male", "female", "neutral"]
        
        if gender not in valid_genders:
            return Response(
                text=f"Invalid gender '{gender}'. Please choose from: {', '.join(valid_genders)}",
                action_taken=False
            )
        
        success = self.config.update_setting('voice_settings', 'gender', gender)
        
        if success:
            return Response(
                text=f"Voice gender set to {gender}.",
                action_taken=True
            )
        else:
            return Response(
                text="Failed to update voice gender setting.",
                action_taken=False,
                error_message="Configuration update failed"
            )
    
    def handle_set_voice_speed(self, command: Command) -> Response:
        """Handle setting voice speed"""
        speed = command.entities.get('speed')
        
        if not speed:
            numbers = command.entities.get('numbers', [])
            if numbers:
                speed = numbers[0]
        
        if not speed:
            return Response(
                text="Please specify a voice speed between 50 and 300. For example, 'set voice speed to 150'",
                action_taken=False
            )
        
        try:
            speed = int(speed)
            if not 50 <= speed <= 300:
                return Response(
                    text="Voice speed must be between 50 and 300.",
                    action_taken=False
                )
            
            success = self.config.update_setting('voice_settings', 'speed', speed)
            
            if success:
                return Response(
                    text=f"Voice speed set to {speed}.",
                    action_taken=True
                )
            else:
                return Response(
                    text="Failed to update voice speed setting.",
                    action_taken=False,
                    error_message="Configuration update failed"
                )
        
        except ValueError:
            return Response(
                text="Please provide a valid number for voice speed.",
                action_taken=False
            )
    
    def handle_set_voice_pitch(self, command: Command) -> Response:
        """Handle setting voice pitch"""
        pitch = command.entities.get('pitch')
        
        if not pitch:
            numbers = command.entities.get('numbers', [])
            if numbers:
                pitch = numbers[0]
        
        if not pitch:
            return Response(
                text="Please specify a voice pitch between 0 and 100. For example, 'set voice pitch to 50'",
                action_taken=False
            )
        
        try:
            pitch = int(pitch)
            if not 0 <= pitch <= 100:
                return Response(
                    text="Voice pitch must be between 0 and 100.",
                    action_taken=False
                )
            
            success = self.config.update_setting('voice_settings', 'pitch', pitch)
            
            if success:
                return Response(
                    text=f"Voice pitch set to {pitch}.",
                    action_taken=True
                )
            else:
                return Response(
                    text="Failed to update voice pitch setting.",
                    action_taken=False,
                    error_message="Configuration update failed"
                )
        
        except ValueError:
            return Response(
                text="Please provide a valid number for voice pitch.",
                action_taken=False
            )
    
    def handle_set_voice_volume(self, command: Command) -> Response:
        """Handle setting voice volume"""
        volume = command.entities.get('volume')
        
        if not volume:
            numbers = command.entities.get('numbers', [])
            if numbers:
                volume = numbers[0] / 100.0  # Convert percentage to decimal
        
        if volume is None:
            return Response(
                text="Please specify a voice volume between 0 and 100 percent. For example, 'set voice volume to 80'",
                action_taken=False
            )
        
        try:
            if isinstance(volume, int):
                volume = volume / 100.0
            
            volume = float(volume)
            if not 0 <= volume <= 1:
                return Response(
                    text="Voice volume must be between 0 and 100 percent.",
                    action_taken=False
                )
            
            success = self.config.update_setting('voice_settings', 'volume', volume)
            
            if success:
                return Response(
                    text=f"Voice volume set to {int(volume * 100)} percent.",
                    action_taken=True
                )
            else:
                return Response(
                    text="Failed to update voice volume setting.",
                    action_taken=False,
                    error_message="Configuration update failed"
                )
        
        except ValueError:
            return Response(
                text="Please provide a valid number for voice volume.",
                action_taken=False
            )
    
    def handle_set_personality(self, command: Command) -> Response:
        """Handle setting personality preset"""
        personality = command.entities.get('personality')
        
        if not personality:
            return Response(
                text="Please specify a personality type: professional, friendly, casual, or formal.",
                action_taken=False
            )
        
        personality = personality.lower()
        success = self.config.set_personality_preset(personality)
        
        if success:
            return Response(
                text=f"Personality set to {personality}. I'll adjust my responses accordingly.",
                action_taken=True
            )
        else:
            return Response(
                text=f"Invalid personality type '{personality}'. Available options: professional, friendly, casual, formal.",
                action_taken=False,
                error_message="Invalid personality preset"
            )
    
    def handle_set_humor_level(self, command: Command) -> Response:
        """Handle setting humor level"""
        humor_level = command.entities.get('humor_level')
        
        if not humor_level:
            return Response(
                text="Please specify a humor level: none, light, moderate, or high.",
                action_taken=False
            )
        
        humor_level = humor_level.lower()
        valid_levels = ["none", "light", "moderate", "high"]
        
        if humor_level not in valid_levels:
            return Response(
                text=f"Invalid humor level '{humor_level}'. Please choose from: {', '.join(valid_levels)}",
                action_taken=False
            )
        
        success = self.config.update_setting('personality_settings', 'humor_level', humor_level)
        
        if success:
            return Response(
                text=f"Humor level set to {humor_level}.",
                action_taken=True
            )
        else:
            return Response(
                text="Failed to update humor level setting.",
                action_taken=False,
                error_message="Configuration update failed"
            )
    
    def handle_set_verbosity(self, command: Command) -> Response:
        """Handle setting response verbosity"""
        verbosity = command.entities.get('verbosity')
        
        if not verbosity:
            return Response(
                text="Please specify verbosity level: brief, normal, or detailed.",
                action_taken=False
            )
        
        verbosity = verbosity.lower()
        valid_levels = ["brief", "normal", "detailed"]
        
        if verbosity not in valid_levels:
            return Response(
                text=f"Invalid verbosity level '{verbosity}'. Please choose from: {', '.join(valid_levels)}",
                action_taken=False
            )
        
        success = self.config.update_setting('personality_settings', 'verbosity', verbosity)
        
        if success:
            return Response(
                text=f"Response verbosity set to {verbosity}.",
                action_taken=True
            )
        else:
            return Response(
                text="Failed to update verbosity setting.",
                action_taken=False,
                error_message="Configuration update failed"
            )
    
    def handle_add_wake_word(self, command: Command) -> Response:
        """Handle adding a new wake word"""
        wake_word = command.entities.get('wake_word')
        
        if not wake_word:
            return Response(
                text="Please specify the wake word to add. For example, 'add wake word hey assistant'",
                action_taken=False
            )
        
        success = self.config.add_wake_word(wake_word)
        
        if success:
            return Response(
                text=f"Wake word '{wake_word}' added successfully.",
                action_taken=True
            )
        else:
            return Response(
                text=f"Failed to add wake word '{wake_word}'. It may already exist.",
                action_taken=False,
                error_message="Wake word addition failed"
            )
    
    def handle_remove_wake_word(self, command: Command) -> Response:
        """Handle removing a wake word"""
        wake_word = command.entities.get('wake_word')
        
        if not wake_word:
            return Response(
                text="Please specify the wake word to remove. For example, 'remove wake word hey wizard'",
                action_taken=False
            )
        
        success = self.config.remove_wake_word(wake_word)
        
        if success:
            return Response(
                text=f"Wake word '{wake_word}' removed successfully.",
                action_taken=True
            )
        else:
            return Response(
                text=f"Failed to remove wake word '{wake_word}'. It may not exist or be the only wake word.",
                action_taken=False,
                error_message="Wake word removal failed"
            )
    
    def handle_list_wake_words(self, command: Command) -> Response:
        """Handle listing current wake words"""
        wake_words = self.config.get_setting('wake_words', '')
        
        if wake_words:
            wake_word_list = ', '.join(wake_words)
            return Response(
                text=f"Current wake words: {wake_word_list}",
                action_taken=True
            )
        else:
            return Response(
                text="No wake words configured.",
                action_taken=True
            )
    
    def handle_set_assistant_name(self, command: Command) -> Response:
        """Handle setting assistant name"""
        name = command.entities.get('name')
        
        if not name:
            return Response(
                text="Please specify the assistant name. For example, 'set assistant name to Jarvis'",
                action_taken=False
            )
        
        success = self.config.update_setting('', 'assistant_name', name)
        
        if success:
            return Response(
                text=f"Assistant name set to {name}.",
                action_taken=True
            )
        else:
            return Response(
                text="Failed to update assistant name.",
                action_taken=False,
                error_message="Configuration update failed"
            )
    
    def handle_set_user_name(self, command: Command) -> Response:
        """Handle setting user name"""
        name = command.entities.get('name')
        
        if not name:
            return Response(
                text="Please specify your name. For example, 'set my name to John'",
                action_taken=False
            )
        
        success = self.config.update_setting('preferences', 'name', name)
        
        if success:
            return Response(
                text=f"Your name set to {name}. Nice to meet you, {name}!",
                action_taken=True
            )
        else:
            return Response(
                text="Failed to update your name.",
                action_taken=False,
                error_message="Configuration update failed"
            )
    
    def handle_add_interest(self, command: Command) -> Response:
        """Handle adding user interest"""
        interest = command.entities.get('interest')
        
        if not interest:
            return Response(
                text="Please specify an interest to add. For example, 'add interest music'",
                action_taken=False
            )
        
        success = self.config.add_user_interest(interest)
        
        if success:
            return Response(
                text=f"Added '{interest}' to your interests. I'll personalize responses accordingly.",
                action_taken=True
            )
        else:
            return Response(
                text=f"Failed to add interest '{interest}'. It may already exist.",
                action_taken=False,
                error_message="Interest addition failed"
            )
    
    def handle_remove_interest(self, command: Command) -> Response:
        """Handle removing user interest"""
        interest = command.entities.get('interest')
        
        if not interest:
            return Response(
                text="Please specify an interest to remove. For example, 'remove interest sports'",
                action_taken=False
            )
        
        success = self.config.remove_user_interest(interest)
        
        if success:
            return Response(
                text=f"Removed '{interest}' from your interests.",
                action_taken=True
            )
        else:
            return Response(
                text=f"Failed to remove interest '{interest}'. It may not exist.",
                action_taken=False,
                error_message="Interest removal failed"
            )
    
    def handle_list_interests(self, command: Command) -> Response:
        """Handle listing user interests"""
        interests = self.config.get_setting('preferences', 'interests')
        
        if interests:
            interest_list = ', '.join(interests)
            return Response(
                text=f"Your interests: {interest_list}",
                action_taken=True
            )
        else:
            return Response(
                text="No interests configured. Add some interests to personalize your experience.",
                action_taken=True
            )
    
    def handle_configuration_status(self, command: Command) -> Response:
        """Handle configuration status inquiry"""
        summary = self.config.get_config_summary()
        
        status_text = f"""Configuration Summary:
- Assistant Name: {summary['assistant_name']}
- Wake Words: {summary['wake_words_count']} configured
- Voice: {summary['voice_gender']} ({summary['voice_language']})
- Personality: {summary['personality_type']} with {summary['humor_level']} humor
- User: {summary['user_name']}
- Learning: {'Enabled' if summary['learning_enabled'] else 'Disabled'}
- Applications: {summary['applications_count']} configured
- Interests: {summary['interests_count']} configured"""
        
        return Response(
            text=status_text,
            action_taken=True
        )
    
    def handle_reset_configuration(self, command: Command) -> Response:
        """Handle resetting configuration to defaults"""
        success = self.config.reset_to_defaults()
        
        if success:
            return Response(
                text="Configuration reset to default settings successfully.",
                action_taken=True
            )
        else:
            return Response(
                text="Failed to reset configuration to defaults.",
                action_taken=False,
                error_message="Configuration reset failed"
            )
    
    def handle_export_configuration(self, command: Command) -> Response:
        """Handle exporting configuration"""
        filename = command.entities.get('filename', 'wizard_config_backup.json')
        
        success = self.config.export_config(f"config/exports/{filename}")
        
        if success:
            return Response(
                text=f"Configuration exported to config/exports/{filename}",
                action_taken=True
            )
        else:
            return Response(
                text="Failed to export configuration.",
                action_taken=False,
                error_message="Configuration export failed"
            )
    
    def handle_set_custom_phrase(self, command: Command) -> Response:
        """Handle setting custom phrases"""
        phrase_type = command.entities.get('phrase_type')
        phrase_text = command.entities.get('phrase_text')
        
        if not phrase_type or not phrase_text:
            return Response(
                text="Please specify both phrase type and text. For example, 'set greeting phrase to Hello there!'",
                action_taken=False
            )
        
        success = self.config.update_custom_phrase(phrase_type, phrase_text)
        
        if success:
            return Response(
                text=f"Custom {phrase_type} phrase set to: {phrase_text}",
                action_taken=True
            )
        else:
            return Response(
                text=f"Failed to set custom {phrase_type} phrase. Valid types: greeting, goodbye, error, confirmation, thinking, unknown",
                action_taken=False,
                error_message="Custom phrase update failed"
            )


def register_configuration_handlers(router, config_manager: ConfigManager) -> None:
    """Register all configuration handlers with the command router"""
    handlers = ConfigurationHandlers(config_manager)
    
    # Voice settings
    router.register_handler("set_voice_gender", handlers.handle_set_voice_gender)
    router.register_handler("set_voice_speed", handlers.handle_set_voice_speed)
    router.register_handler("set_voice_pitch", handlers.handle_set_voice_pitch)
    router.register_handler("set_voice_volume", handlers.handle_set_voice_volume)
    
    # Personality settings
    router.register_handler("set_personality", handlers.handle_set_personality)
    router.register_handler("set_humor_level", handlers.handle_set_humor_level)
    router.register_handler("set_verbosity", handlers.handle_set_verbosity)
    
    # Wake words
    router.register_handler("add_wake_word", handlers.handle_add_wake_word)
    router.register_handler("remove_wake_word", handlers.handle_remove_wake_word)
    router.register_handler("list_wake_words", handlers.handle_list_wake_words)
    
    # Names and identity
    router.register_handler("set_assistant_name", handlers.handle_set_assistant_name)
    router.register_handler("set_user_name", handlers.handle_set_user_name)
    
    # User interests
    router.register_handler("add_interest", handlers.handle_add_interest)
    router.register_handler("remove_interest", handlers.handle_remove_interest)
    router.register_handler("list_interests", handlers.handle_list_interests)
    
    # Configuration management
    router.register_handler("configuration_status", handlers.handle_configuration_status)
    router.register_handler("reset_configuration", handlers.handle_reset_configuration)
    router.register_handler("export_configuration", handlers.handle_export_configuration)
    router.register_handler("set_custom_phrase", handlers.handle_set_custom_phrase)
    
    logger.info("Configuration handlers registered successfully")