"""
Configuration Manager for Wizard Voice Assistant
Handles loading, validation, and management of configuration settings.
"""

import json
import os
from dataclasses import dataclass, asdict
from typing import Dict, List, Any, Optional
from pathlib import Path


@dataclass
class VoiceConfig:
    """Voice settings configuration"""
    gender: str = "female"
    speed: int = 150
    pitch: int = 50
    volume: float = 0.8
    voice_id: Optional[str] = None  # Specific voice ID for TTS engine
    language: str = "en"
    accent: str = "us"  # us, uk, au, etc.


@dataclass
class PersonalityConfig:
    """Personality and behavior settings"""
    personality_type: str = "professional"  # professional, friendly, casual, formal
    humor_level: str = "moderate"  # none, light, moderate, high
    verbosity: str = "normal"  # brief, normal, detailed
    formality: str = "polite"  # casual, polite, formal
    response_style: str = "helpful"  # helpful, witty, concise, elaborate
    custom_name: str = "Wizard"
    greeting_style: str = "standard"  # standard, casual, formal, custom
    custom_phrases: Dict[str, str] = None
    
    def __post_init__(self):
        if self.custom_phrases is None:
            self.custom_phrases = {
                "greeting": "Hello! How can I help you today?",
                "goodbye": "Goodbye! Have a great day!",
                "error": "I'm sorry, I encountered an issue.",
                "confirmation": "Got it!",
                "thinking": "Let me think about that...",
                "unknown": "I'm not sure I understand. Could you rephrase that?"
            }


@dataclass
class SecurityConfig:
    """Security settings configuration"""
    require_confirmation: bool = True
    password_protected_commands: List[str] = None
    safe_mode: bool = False
    
    def __post_init__(self):
        if self.password_protected_commands is None:
            self.password_protected_commands = ["shutdown", "restart", "delete"]


@dataclass
class UserPreferences:
    """User preference settings"""
    name: str = "User"
    timezone: str = "UTC"
    language: str = "en"
    personalized_responses: bool = True
    learning_enabled: bool = True
    preferred_units: str = "metric"  # metric, imperial
    date_format: str = "MM/DD/YYYY"  # MM/DD/YYYY, DD/MM/YYYY, YYYY-MM-DD
    time_format: str = "12"  # 12, 24
    temperature_unit: str = "fahrenheit"  # celsius, fahrenheit
    currency: str = "USD"
    location: str = ""  # User's location for weather, etc.
    interests: List[str] = None  # User interests for personalized content
    
    def __post_init__(self):
        if self.interests is None:
            self.interests = []


@dataclass
class WizardConfig:
    """Main configuration class for Wizard Voice Assistant"""
    assistant_name: str = "Wizard"
    wake_words: List[str] = None
    voice_settings: VoiceConfig = None
    personality_settings: PersonalityConfig = None
    applications: Dict[str, str] = None
    preferences: UserPreferences = None
    security_settings: SecurityConfig = None
    
    def __post_init__(self):
        if self.wake_words is None:
            self.wake_words = ["hey wizard", "wizard"]
        if self.voice_settings is None:
            self.voice_settings = VoiceConfig()
        if self.personality_settings is None:
            self.personality_settings = PersonalityConfig()
        if self.applications is None:
            self.applications = {}
        if self.preferences is None:
            self.preferences = UserPreferences()
        if self.security_settings is None:
            self.security_settings = SecurityConfig()


class ConfigManager:
    """Manages configuration loading, validation, and saving"""
    
    def __init__(self, config_path: str = "config/wizard_config.json"):
        self.config_path = Path(config_path)
        self.config: WizardConfig = WizardConfig()
        self._ensure_config_directory()
    
    def _ensure_config_directory(self) -> None:
        """Ensure the configuration directory exists"""
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
    
    def load_config(self) -> WizardConfig:
        """Load configuration from JSON file"""
        if not self.config_path.exists():
            self._create_default_config()
            return self.config
        
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                config_data = json.load(f)
            
            self.config = self._parse_config_data(config_data)
            return self.config
        
        except (json.JSONDecodeError, FileNotFoundError, KeyError) as e:
            print(f"Error loading config: {e}. Using default configuration.")
            self._create_default_config()
            return self.config
    
    def _parse_config_data(self, data: Dict[str, Any]) -> WizardConfig:
        """Parse configuration data from dictionary"""
        voice_config = VoiceConfig(**data.get('voice_settings', {}))
        personality_config = PersonalityConfig(**data.get('personality_settings', {}))
        security_config = SecurityConfig(**data.get('security_settings', {}))
        user_prefs = UserPreferences(**data.get('preferences', {}))
        
        return WizardConfig(
            assistant_name=data.get('assistant_name', 'Wizard'),
            wake_words=data.get('wake_words', ['hey wizard', 'wizard']),
            voice_settings=voice_config,
            personality_settings=personality_config,
            applications=data.get('applications', {}),
            preferences=user_prefs,
            security_settings=security_config
        )
    
    def save_config(self) -> bool:
        """Save current configuration to JSON file"""
        try:
            config_dict = self._config_to_dict()
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(config_dict, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"Error saving config: {e}")
            return False
    
    def _config_to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary for JSON serialization"""
        return {
            'assistant_name': self.config.assistant_name,
            'wake_words': self.config.wake_words,
            'voice_settings': asdict(self.config.voice_settings),
            'personality_settings': asdict(self.config.personality_settings),
            'applications': self.config.applications,
            'preferences': asdict(self.config.preferences),
            'security_settings': asdict(self.config.security_settings)
        }
    
    def _create_default_config(self) -> None:
        """Create and save default configuration"""
        self.config = WizardConfig()
        self.save_config()
    
    def update_setting(self, section: str, key: str, value: Any) -> bool:
        """Update a specific configuration setting"""
        try:
            if section == 'voice_settings':
                setattr(self.config.voice_settings, key, value)
            elif section == 'personality_settings':
                setattr(self.config.personality_settings, key, value)
            elif section == 'security_settings':
                setattr(self.config.security_settings, key, value)
            elif section == 'preferences':
                setattr(self.config.preferences, key, value)
            elif section == 'applications':
                self.config.applications[key] = value
            elif section == 'wake_words':
                if key == 'add':
                    if value not in self.config.wake_words:
                        self.config.wake_words.append(value)
                elif key == 'remove':
                    if value in self.config.wake_words:
                        self.config.wake_words.remove(value)
                elif key == 'set':
                    self.config.wake_words = value if isinstance(value, list) else [value]
            elif hasattr(self.config, key):
                setattr(self.config, key, value)
            else:
                return False
            
            return self.save_config()
        except Exception as e:
            print(f"Error updating setting: {e}")
            return False
    
    def get_setting(self, section: str, key: str) -> Any:
        """Get a specific configuration setting"""
        try:
            if section == 'voice_settings':
                return getattr(self.config.voice_settings, key)
            elif section == 'personality_settings':
                return getattr(self.config.personality_settings, key)
            elif section == 'security_settings':
                return getattr(self.config.security_settings, key)
            elif section == 'preferences':
                return getattr(self.config.preferences, key)
            elif section == 'applications':
                return self.config.applications.get(key)
            elif section == 'wake_words':
                return self.config.wake_words
            else:
                return getattr(self.config, key)
        except AttributeError:
            return None
    
    def validate_config(self) -> List[str]:
        """Validate configuration and return list of errors"""
        errors = []
        
        # Validate wake words
        if not self.config.wake_words or len(self.config.wake_words) == 0:
            errors.append("At least one wake word must be configured")
        
        # Validate voice settings
        if not 0 <= self.config.voice_settings.volume <= 1:
            errors.append("Voice volume must be between 0 and 1")
        
        if not 50 <= self.config.voice_settings.speed <= 300:
            errors.append("Voice speed must be between 50 and 300")
        
        if not 0 <= self.config.voice_settings.pitch <= 100:
            errors.append("Voice pitch must be between 0 and 100")
        
        # Validate voice gender
        valid_genders = ["male", "female", "neutral"]
        if self.config.voice_settings.gender not in valid_genders:
            errors.append(f"Voice gender must be one of: {', '.join(valid_genders)}")
        
        # Validate personality settings
        valid_personalities = ["professional", "friendly", "casual", "formal"]
        if self.config.personality_settings.personality_type not in valid_personalities:
            errors.append(f"Personality type must be one of: {', '.join(valid_personalities)}")
        
        valid_humor_levels = ["none", "light", "moderate", "high"]
        if self.config.personality_settings.humor_level not in valid_humor_levels:
            errors.append(f"Humor level must be one of: {', '.join(valid_humor_levels)}")
        
        valid_verbosity = ["brief", "normal", "detailed"]
        if self.config.personality_settings.verbosity not in valid_verbosity:
            errors.append(f"Verbosity must be one of: {', '.join(valid_verbosity)}")
        
        # Validate assistant name
        if not self.config.assistant_name or len(self.config.assistant_name.strip()) == 0:
            errors.append("Assistant name cannot be empty")
        
        # Validate user preferences
        valid_units = ["metric", "imperial"]
        if self.config.preferences.preferred_units not in valid_units:
            errors.append(f"Preferred units must be one of: {', '.join(valid_units)}")
        
        valid_time_formats = ["12", "24"]
        if self.config.preferences.time_format not in valid_time_formats:
            errors.append(f"Time format must be one of: {', '.join(valid_time_formats)}")
        
        return errors
    
    def get_available_voices(self) -> List[Dict[str, str]]:
        """Get list of available TTS voices"""
        # This would integrate with the actual TTS engine
        # For now, return a mock list
        return [
            {"id": "voice_1", "name": "Sarah", "gender": "female", "language": "en", "accent": "us"},
            {"id": "voice_2", "name": "John", "gender": "male", "language": "en", "accent": "us"},
            {"id": "voice_3", "name": "Emma", "gender": "female", "language": "en", "accent": "uk"},
            {"id": "voice_4", "name": "James", "gender": "male", "language": "en", "accent": "uk"},
            {"id": "voice_5", "name": "Maria", "gender": "female", "language": "es", "accent": "es"},
            {"id": "voice_6", "name": "Pierre", "gender": "male", "language": "fr", "accent": "fr"}
        ]
    
    def set_voice_by_characteristics(self, gender: str = None, language: str = None, accent: str = None) -> bool:
        """Set voice based on characteristics"""
        available_voices = self.get_available_voices()
        
        # Filter voices based on criteria
        matching_voices = available_voices
        
        if gender:
            matching_voices = [v for v in matching_voices if v["gender"] == gender]
        if language:
            matching_voices = [v for v in matching_voices if v["language"] == language]
        if accent:
            matching_voices = [v for v in matching_voices if v["accent"] == accent]
        
        if matching_voices:
            # Use the first matching voice
            selected_voice = matching_voices[0]
            self.config.voice_settings.voice_id = selected_voice["id"]
            self.config.voice_settings.gender = selected_voice["gender"]
            self.config.voice_settings.language = selected_voice["language"]
            self.config.voice_settings.accent = selected_voice["accent"]
            return self.save_config()
        
        return False
    
    def add_wake_word(self, wake_word: str) -> bool:
        """Add a new wake word"""
        wake_word = wake_word.lower().strip()
        if wake_word and wake_word not in self.config.wake_words:
            self.config.wake_words.append(wake_word)
            return self.save_config()
        return False
    
    def remove_wake_word(self, wake_word: str) -> bool:
        """Remove a wake word"""
        wake_word = wake_word.lower().strip()
        if wake_word in self.config.wake_words and len(self.config.wake_words) > 1:
            self.config.wake_words.remove(wake_word)
            return self.save_config()
        return False
    
    def set_personality_preset(self, preset: str) -> bool:
        """Set personality using predefined presets"""
        presets = {
            "professional": {
                "personality_type": "professional",
                "humor_level": "light",
                "verbosity": "normal",
                "formality": "polite",
                "response_style": "helpful"
            },
            "friendly": {
                "personality_type": "friendly",
                "humor_level": "moderate",
                "verbosity": "normal",
                "formality": "casual",
                "response_style": "witty"
            },
            "formal": {
                "personality_type": "formal",
                "humor_level": "none",
                "verbosity": "detailed",
                "formality": "formal",
                "response_style": "concise"
            },
            "casual": {
                "personality_type": "casual",
                "humor_level": "high",
                "verbosity": "brief",
                "formality": "casual",
                "response_style": "witty"
            }
        }
        
        if preset in presets:
            preset_config = presets[preset]
            for key, value in preset_config.items():
                setattr(self.config.personality_settings, key, value)
            return self.save_config()
        
        return False
    
    def update_custom_phrase(self, phrase_type: str, phrase: str) -> bool:
        """Update a custom phrase"""
        if phrase_type in self.config.personality_settings.custom_phrases:
            self.config.personality_settings.custom_phrases[phrase_type] = phrase
            return self.save_config()
        return False
    
    def add_user_interest(self, interest: str) -> bool:
        """Add a user interest"""
        interest = interest.lower().strip()
        if interest and interest not in self.config.preferences.interests:
            self.config.preferences.interests.append(interest)
            return self.save_config()
        return False
    
    def remove_user_interest(self, interest: str) -> bool:
        """Remove a user interest"""
        interest = interest.lower().strip()
        if interest in self.config.preferences.interests:
            self.config.preferences.interests.remove(interest)
            return self.save_config()
        return False
    
    def export_config(self, export_path: str) -> bool:
        """Export configuration to a file"""
        try:
            export_path = Path(export_path)
            export_path.parent.mkdir(parents=True, exist_ok=True)
            
            config_dict = self._config_to_dict()
            with open(export_path, 'w', encoding='utf-8') as f:
                json.dump(config_dict, f, indent=2, ensure_ascii=False)
            
            return True
        except Exception as e:
            print(f"Error exporting config: {e}")
            return False
    
    def import_config(self, import_path: str) -> bool:
        """Import configuration from a file"""
        try:
            import_path = Path(import_path)
            if not import_path.exists():
                return False
            
            with open(import_path, 'r', encoding='utf-8') as f:
                config_data = json.load(f)
            
            # Validate imported config
            temp_config = self._parse_config_data(config_data)
            
            # If validation passes, update current config
            self.config = temp_config
            return self.save_config()
        
        except Exception as e:
            print(f"Error importing config: {e}")
            return False
    
    def reset_to_defaults(self) -> bool:
        """Reset configuration to default values"""
        self.config = WizardConfig()
        return self.save_config()
    
    def get_config_summary(self) -> Dict[str, Any]:
        """Get a summary of current configuration"""
        return {
            "assistant_name": self.config.assistant_name,
            "wake_words_count": len(self.config.wake_words),
            "voice_gender": self.config.voice_settings.gender,
            "voice_language": self.config.voice_settings.language,
            "personality_type": self.config.personality_settings.personality_type,
            "humor_level": self.config.personality_settings.humor_level,
            "user_name": self.config.preferences.name,
            "learning_enabled": self.config.preferences.learning_enabled,
            "safe_mode": self.config.security_settings.safe_mode,
            "applications_count": len(self.config.applications),
            "interests_count": len(self.config.preferences.interests)
        }