"""
Command Router Module

This module handles natural language command parsing, intent classification,
and routing commands to appropriate handlers.
"""

import re
import json
from typing import Dict, List, Tuple, Optional, Any, Callable
from dataclasses import dataclass
from datetime import datetime
from difflib import SequenceMatcher
import logging

logger = logging.getLogger(__name__)

# Import content filter for web command filtering
try:
    from wizard.utils.content_filter import create_content_filter
    _content_filter = None
    
    def _get_content_filter():
        """Get or create content filter instance"""
        global _content_filter
        if _content_filter is None:
            _content_filter = create_content_filter()
        return _content_filter
        
except ImportError:
    # Fallback if content filter is not available
    def _get_content_filter():
        return None


@dataclass
class Command:
    """Represents a parsed voice command"""
    intent: str
    entities: Dict[str, Any]
    confidence: float
    raw_text: str
    timestamp: datetime
    user_id: str = "default"


@dataclass
class Response:
    """Represents a response to a command"""
    text: str
    audio_file: Optional[str] = None
    action_taken: bool = False
    error_message: Optional[str] = None
    context_updates: Dict[str, Any] = None

    def __post_init__(self):
        if self.context_updates is None:
            self.context_updates = {}


class CommandRouter:
    """
    Main command router that parses natural language commands and routes them
    to appropriate handlers using pattern matching and fuzzy matching.
    """

    def __init__(self, config: Dict):
        self.config = config
        self.handlers: Dict[str, Callable] = {}
        self.intent_patterns = self._load_intent_patterns()
        self.entity_extractors = self._setup_entity_extractors()
        self.app_names = self._load_application_names()
        
    def _load_intent_patterns(self) -> Dict[str, List[str]]:
        """Load intent recognition patterns"""
        return {
            # System control intents
            "open_application": [
                r"open\s+(.+)",
                r"launch\s+(.+)",
                r"start\s+(.+)",
                r"run\s+(.+)"
            ],
            "close_application": [
                r"close\s+(.+)",
                r"quit\s+(.+)",
                r"exit\s+(.+)",
                r"shut\s+down\s+(.+)"
            ],
            "system_shutdown": [
                r"shutdown\s+computer",
                r"turn\s+off\s+computer",
                r"shut\s+down",
                r"power\s+off"
            ],
            "system_restart": [
                r"restart\s+computer",
                r"reboot",
                r"restart"
            ],
            "system_lock": [
                r"lock\s+computer",
                r"lock\s+screen",
                r"lock"
            ],
            "system_logout": [
                r"logout",
                r"log\s+out",
                r"sign\s+out"
            ],
            
            # Window control
            "minimize_window": [
                r"minimize\s+window",
                r"minimize\s+(.+)",
                r"minimize"
            ],
            "maximize_window": [
                r"maximize\s+window",
                r"maximize\s+(.+)",
                r"maximize"
            ],
            "restore_window": [
                r"restore\s+window",
                r"restore\s+(.+)",
                r"restore"
            ],
            "close_window": [
                r"close\s+window",
                r"close\s+(.+)\s+window"
            ],
            
            # Screenshot and recording
            "take_screenshot": [
                r"take\s+screenshot",
                r"screenshot",
                r"capture\s+screen",
                r"take\s+picture\s+of\s+screen"
            ],
            "screen_recording": [
                r"record\s+screen",
                r"start\s+recording",
                r"screen\s+recording",
                r"record\s+for\s+(\d+)\s+(seconds?|minutes?)"
            ],
            
            # Recycle bin and system info
            "empty_recycle_bin": [
                r"empty\s+recycle\s+bin",
                r"empty\s+trash",
                r"clear\s+recycle\s+bin"
            ],
            "get_running_apps": [
                r"what\s+apps\s+are\s+running",
                r"list\s+running\s+applications",
                r"show\s+running\s+programs",
                r"what\s+programs\s+are\s+open"
            ],
            "get_system_info": [
                r"system\s+information",
                r"system\s+info",
                r"computer\s+specs",
                r"system\s+status"
            ],
            
            # Volume and media control
            "set_volume": [
                r"set\s+volume\s+to\s+(\d+)",
                r"volume\s+(\d+)",
                r"change\s+volume\s+to\s+(\d+)"
            ],
            "volume_up": [
                r"volume\s+up",
                r"increase\s+volume",
                r"turn\s+up\s+volume",
                r"louder"
            ],
            "volume_down": [
                r"volume\s+down",
                r"decrease\s+volume",
                r"turn\s+down\s+volume",
                r"quieter"
            ],
            "mute": [
                r"mute",
                r"silence",
                r"turn\s+off\s+sound"
            ],
            "unmute": [
                r"unmute",
                r"turn\s+on\s+sound"
            ],
            "play_music": [
                r"play\s+(.+)",
                r"start\s+playing\s+(.+)",
                r"put\s+on\s+(.+)"
            ],
            "pause_music": [
                r"pause",
                r"stop\s+playing",
                r"pause\s+music"
            ],
            "next_track": [
                r"next\s+song",
                r"skip\s+song",
                r"next\s+track"
            ],
            "previous_track": [
                r"previous\s+song",
                r"last\s+song",
                r"previous\s+track"
            ],
            
            # File operations
            "search_files": [
                r"find\s+(.+)",
                r"search\s+for\s+(.+)",
                r"locate\s+(.+)",
                r"look\s+for\s+(.+)"
            ],
            "open_file": [
                r"open\s+file\s+(.+)",
                r"open\s+(.+\.\w+)"
            ],
            "create_folder": [
                r"create\s+folder\s+(.+)",
                r"make\s+directory\s+(.+)",
                r"new\s+folder\s+(.+)"
            ],
            "delete_file": [
                r"delete\s+(.+)",
                r"remove\s+(.+)",
                r"trash\s+(.+)"
            ],
            
            # Web and search
            "web_search": [
                r"search\s+for\s+(.+)",
                r"google\s+(.+)",
                r"look\s+up\s+(.+)"
            ],
            "image_search": [
                r"search\s+images?\s+(?:for\s+|of\s+)?(.+)",
                r"show\s+me\s+images?\s+(?:of\s+|about\s+)?(.+)",
                r"find\s+pictures?\s+(?:of\s+|about\s+)?(.+)",
                r"google\s+images?\s+(.+)",
                r"image\s+search\s+(?:for\s+)?(.+)",
                r"pictures?\s+of\s+(.+)"
            ],
            "open_website": [
                r"go\s+to\s+(.+)",
                r"open\s+(.+\.com|\.org|\.net)",
                r"open\s+(.+)\s+website",
                r"open\s+(.+)\s+official\s+site",
                r"visit\s+(.+)",
                r"browse\s+to\s+(.+)",
                r"load\s+(.+)"
            ],
            "youtube_search": [
                r"youtube\s+(.+)",
                r"play\s+video\s+(.+)",
                r"search\s+youtube\s+for\s+(.+)",
                r"search\s+youtube\s+(.+)",
                r"find\s+video\s+(?:about\s+|of\s+)?(.+)",
                r"watch\s+video\s+(?:about\s+|of\s+)?(.+)",
                r"show\s+me\s+video\s+(?:about\s+|of\s+)?(.+)"
            ],
            
            # Productivity
            "set_timer": [
                r"set\s+timer\s+for\s+(\d+)\s+(minutes?|seconds?|hours?)",
                r"timer\s+(\d+)\s+(minutes?|seconds?|hours?)",
                r"remind\s+me\s+in\s+(\d+)\s+(minutes?|seconds?|hours?)"
            ],
            "create_reminder": [
                r"remind\s+me\s+to\s+(.+)",
                r"set\s+reminder\s+(.+)",
                r"create\s+reminder\s+(.+)"
            ],
            "create_alarm": [
                r"set\s+alarm\s+for\s+(.+)",
                r"wake\s+me\s+up\s+at\s+(.+)",
                r"create\s+alarm\s+(.+)"
            ],
            "take_note": [
                r"take\s+note\s+(.+)",
                r"write\s+down\s+(.+)",
                r"note\s+(.+)"
            ],
            "search_notes": [
                r"find\s+notes\s+about\s+(.+)",
                r"search\s+notes\s+for\s+(.+)",
                r"show\s+notes\s+tagged\s+with\s+(.+)"
            ],
            "add_todo": [
                r"add\s+to\s+todo\s+(.+)",
                r"todo\s+(.+)",
                r"task\s+(.+)"
            ],
            "list_todos": [
                r"show\s+my\s+todo\s+list",
                r"what's\s+on\s+my\s+todo\s+list",
                r"list\s+my\s+tasks"
            ],
            "complete_todo": [
                r"mark\s+(.+)\s+as\s+done",
                r"complete\s+task\s+(.+)",
                r"done\s+with\s+(.+)"
            ],
            "create_calendar_event": [
                r"schedule\s+(.+)",
                r"create\s+event\s+for\s+(.+)",
                r"add\s+calendar\s+event\s+for\s+(.+)"
            ],
            "list_calendar_events": [
                r"show\s+my\s+calendar",
                r"what's\s+on\s+my\s+schedule",
                r"list\s+upcoming\s+events"
            ],
            "list_timers": [
                r"show\s+my\s+timers",
                r"what\s+timers\s+are\s+running",
                r"list\s+active\s+timers"
            ],
            "productivity_summary": [
                r"show\s+my\s+productivity\s+summary",
                r"what's\s+my\s+status",
                r"productivity\s+overview"
            ],
            
            # Information queries
            "what_time": [
                r"what\s+time\s+is\s+it",
                r"current\s+time",
                r"time",
                r"what\s+time"
            ],
            "what_date": [
                r"what\s+date\s+is\s+it",
                r"today's\s+date",
                r"date",
                r"what\s+date",
                r"what's\s+today's\s+date"
            ],
            "weather": [
                r"weather",
                r"what's\s+the\s+weather",
                r"how's\s+the\s+weather",
                r"weather\s+forecast",
                r"current\s+weather"
            ],
            "calculate": [
                r"calculate\s+(.+)",
                r"what\s+is\s+(.+)",
                r"compute\s+(.+)",
                r"solve\s+(.+)",
                r"math\s+(.+)"
            ],
            "unit_conversion": [
                r"convert\s+(.+)",
                r"how\s+many\s+(.+)",
                r"(\d+(?:\.\d+)?)\s+(\w+)\s+to\s+(\w+)",
                r"(\d+(?:\.\d+)?)\s+(\w+)\s+in\s+(\w+)"
            ],
            "news": [
                r"news",
                r"headlines",
                r"what's\s+in\s+the\s+news",
                r"latest\s+news",
                r"news\s+headlines"
            ],
            "sports": [
                r"sports",
                r"sports\s+scores",
                r"game\s+scores",
                r"latest\s+scores",
                r"how\s+did\s+(.+)\s+do"
            ],
            "movies": [
                r"movie\s+(.+)",
                r"tell\s+me\s+about\s+(.+)\s+movie"
            ],
            
            # Entertainment
            "tell_joke": [
                r"tell\s+me\s+a\s+joke",
                r"tell\s+me\s+a\s+(.+)\s+joke",
                r"joke",
                r"make\s+me\s+laugh",
                r"say\s+something\s+funny"
            ],
            "fun_fact": [
                r"fun\s+fact",
                r"tell\s+me\s+a\s+fun\s+fact",
                r"give\s+me\s+a\s+(.+)\s+fact",
                r"interesting\s+fact",
                r"tell\s+me\s+something\s+interesting"
            ],
            "trivia_question": [
                r"trivia",
                r"ask\s+me\s+a\s+trivia\s+question",
                r"give\s+me\s+a\s+(.+)\s+question",
                r"quiz\s+me",
                r"test\s+my\s+knowledge"
            ],
            "coin_flip": [
                r"flip\s+a\s+coin",
                r"coin\s+flip",
                r"heads\s+or\s+tails"
            ],
            "roll_dice": [
                r"roll\s+dice",
                r"roll\s+a\s+die",
                r"roll\s+(\d+)\s+dice",
                r"roll\s+a\s+(\d+)\s+sided\s+die"
            ],
            "generate_number": [
                r"generate\s+a\s+number",
                r"random\s+number",
                r"pick\s+a\s+number",
                r"number\s+between\s+(\d+)\s+and\s+(\d+)"
            ],
            "magic_8_ball": [
                r"magic\s+8\s+ball",
                r"8\s+ball",
                r"ask\s+the\s+magic\s+8\s+ball"
            ],
            "rock_paper_scissors": [
                r"rock\s+paper\s+scissors",
                r"play\s+rock\s+paper\s+scissors",
                r"i\s+choose\s+(rock|paper|scissors)"
            ],
            "movie_recommendation": [
                r"recommend\s+a\s+movie",
                r"suggest\s+a\s+movie",
                r"movie\s+recommendation",
                r"recommend\s+(.+)\s+movie",
                r"suggest\s+(.+)\s+movie"
            ],
            "music_recommendation": [
                r"recommend\s+music",
                r"suggest\s+music",
                r"music\s+recommendation",
                r"recommend\s+(.+)\s+music",
                r"suggest\s+(.+)\s+music"
            ],
            "riddle": [
                r"give\s+me\s+a\s+riddle",
                r"tell\s+me\s+a\s+riddle",
                r"ask\s+me\s+a\s+riddle",
                r"riddle",
                r"puzzle"
            ],
            "motivational_quote": [
                r"motivational\s+quote",
                r"inspire\s+me",
                r"give\s+me\s+motivation",
                r"motivate\s+me"
            ],
            "daily_tip": [
                r"daily\s+tip",
                r"tip\s+of\s+the\s+day",
                r"give\s+me\s+a\s+tip",
                r"helpful\s+tip"
            ],
            
            # General AI queries
            "general_query": [
                r"what\s+is\s+(.+)",
                r"tell\s+me\s+about\s+(.+)",
                r"explain\s+(.+)",
                r"define\s+(.+)"
            ],
            
            # Routine and automation
            "execute_routine": [
                r"run\s+routine\s+(.+)",
                r"execute\s+routine\s+(.+)",
                r"start\s+routine\s+(.+)",
                r"do\s+(.+)\s+routine"
            ],
            "good_morning": [
                r"good\s+morning",
                r"morning\s+routine",
                r"start\s+my\s+day",
                r"morning\s+briefing"
            ],
            "good_night": [
                r"good\s+night",
                r"night\s+routine",
                r"bedtime\s+routine",
                r"end\s+my\s+day"
            ],
            "work_mode": [
                r"work\s+mode",
                r"work\s+routine",
                r"start\s+working",
                r"setup\s+work\s+environment"
            ],
            "create_routine": [
                r"create\s+routine\s+(.+)",
                r"make\s+routine\s+(.+)",
                r"new\s+routine\s+(.+)",
                r"setup\s+routine\s+(.+)"
            ],
            "list_routines": [
                r"list\s+routines",
                r"show\s+routines",
                r"what\s+routines\s+are\s+available",
                r"available\s+routines"
            ],
            "schedule_routine": [
                r"schedule\s+(.+)\s+routine",
                r"set\s+(.+)\s+routine\s+for\s+(.+)",
                r"run\s+(.+)\s+routine\s+at\s+(.+)",
                r"automate\s+(.+)\s+at\s+(.+)"
            ],
            "routine_status": [
                r"routine\s+status",
                r"show\s+routine\s+status",
                r"automation\s+status",
                r"what\s+routines\s+are\s+running"
            ],
            
            # Batch operations and automation
            "batch_file_operation": [
                r"batch\s+(copy|move|delete)\s+(.+)",
                r"bulk\s+(copy|move|delete)\s+(.+)",
                r"mass\s+(copy|move|delete)\s+(.+)",
                r"(copy|move|delete)\s+all\s+(.+)"
            ],
            "auto_response_management": [
                r"manage\s+auto\s+responses",
                r"list\s+auto\s+responses",
                r"add\s+auto\s+response",
                r"show\s+automatic\s+responses"
            ],
            "personalized_suggestions": [
                r"suggest\s+something",
                r"what\s+should\s+i\s+do",
                r"give\s+me\s+suggestions",
                r"personalized\s+recommendations",
                r"what\s+do\s+you\s+recommend"
            ],
            "preference_management": [
                r"show\s+my\s+preferences",
                r"clear\s+preferences",
                r"manage\s+preferences",
                r"what\s+have\s+you\s+learned\s+about\s+me"
            ],
            "batch_status": [
                r"batch\s+status",
                r"automation\s+system\s+status",
                r"show\s+batch\s+system\s+status",
                r"learning\s+status"
            ],
            
            # Security and access control
            "set_password": [
                r"set\s+password\s+to\s+(.+)",
                r"create\s+password\s+(.+)",
                r"change\s+password\s+to\s+(.+)",
                r"update\s+password\s+(.+)"
            ],
            "authenticate": [
                r"authenticate\s+with\s+password\s+(.+)",
                r"login\s+with\s+password\s+(.+)",
                r"password\s+(.+)",
                r"my\s+password\s+is\s+(.+)"
            ],
            "enable_safe_mode": [
                r"enable\s+safe\s+mode",
                r"turn\s+on\s+safe\s+mode",
                r"activate\s+safe\s+mode",
                r"safe\s+mode\s+on"
            ],
            "disable_safe_mode": [
                r"disable\s+safe\s+mode",
                r"turn\s+off\s+safe\s+mode",
                r"deactivate\s+safe\s+mode",
                r"safe\s+mode\s+off"
            ],
            "security_status": [
                r"security\s+status",
                r"show\s+security\s+settings",
                r"security\s+information",
                r"what\s+are\s+my\s+security\s+settings"
            ],
            "confirmation_response": [
                r"yes\s+confirm\s+(.+)",
                r"no\s+cancel\s+(.+)",
                r"confirm\s+(.+)",
                r"cancel\s+(.+)"
            ],
            "add_protected_command": [
                r"protect\s+command\s+(.+)",
                r"add\s+password\s+to\s+(.+)",
                r"secure\s+command\s+(.+)",
                r"password\s+protect\s+(.+)"
            ],
            "remove_protected_command": [
                r"unprotect\s+command\s+(.+)",
                r"remove\s+password\s+from\s+(.+)",
                r"unsecure\s+command\s+(.+)",
                r"remove\s+protection\s+from\s+(.+)"
            ],
            "reset_security": [
                r"reset\s+security\s+settings",
                r"clear\s+all\s+security",
                r"reset\s+security",
                r"default\s+security\s+settings"
            ],
            
            # Configuration management
            "set_voice_gender": [
                r"set\s+voice\s+gender\s+to\s+(\w+)",
                r"change\s+voice\s+to\s+(\w+)",
                r"use\s+(\w+)\s+voice",
                r"voice\s+gender\s+(\w+)"
            ],
            "set_voice_speed": [
                r"set\s+voice\s+speed\s+to\s+(\d+)",
                r"change\s+voice\s+speed\s+to\s+(\d+)",
                r"voice\s+speed\s+(\d+)",
                r"speak\s+(faster|slower)",
                r"talk\s+(faster|slower)"
            ],
            "set_voice_pitch": [
                r"set\s+voice\s+pitch\s+to\s+(\d+)",
                r"change\s+voice\s+pitch\s+to\s+(\d+)",
                r"voice\s+pitch\s+(\d+)",
                r"make\s+voice\s+(higher|lower)"
            ],
            "set_voice_volume": [
                r"set\s+voice\s+volume\s+to\s+(\d+)",
                r"change\s+voice\s+volume\s+to\s+(\d+)",
                r"voice\s+volume\s+(\d+)",
                r"speak\s+(louder|quieter)"
            ],
            "set_personality": [
                r"set\s+personality\s+to\s+(\w+)",
                r"change\s+personality\s+to\s+(\w+)",
                r"be\s+more\s+(\w+)",
                r"act\s+(\w+)"
            ],
            "set_humor_level": [
                r"set\s+humor\s+level\s+to\s+(\w+)",
                r"be\s+(more|less)\s+funny",
                r"humor\s+level\s+(\w+)",
                r"make\s+jokes\s+(\w+)"
            ],
            "set_verbosity": [
                r"set\s+verbosity\s+to\s+(\w+)",
                r"be\s+more\s+(\w+)",
                r"give\s+(\w+)\s+responses",
                r"response\s+length\s+(\w+)"
            ],
            "add_wake_word": [
                r"add\s+wake\s+word\s+(.+)",
                r"new\s+wake\s+word\s+(.+)",
                r"create\s+wake\s+word\s+(.+)",
                r"wake\s+word\s+(.+)"
            ],
            "remove_wake_word": [
                r"remove\s+wake\s+word\s+(.+)",
                r"delete\s+wake\s+word\s+(.+)",
                r"stop\s+using\s+wake\s+word\s+(.+)"
            ],
            "list_wake_words": [
                r"list\s+wake\s+words",
                r"show\s+wake\s+words",
                r"what\s+wake\s+words",
                r"available\s+wake\s+words"
            ],
            "set_assistant_name": [
                r"set\s+assistant\s+name\s+to\s+(.+)",
                r"change\s+name\s+to\s+(.+)",
                r"call\s+yourself\s+(.+)",
                r"your\s+name\s+is\s+(.+)"
            ],
            "set_user_name": [
                r"set\s+my\s+name\s+to\s+(.+)",
                r"my\s+name\s+is\s+(.+)",
                r"call\s+me\s+(.+)",
                r"i\s+am\s+(.+)"
            ],
            "add_interest": [
                r"add\s+interest\s+(.+)",
                r"i\s+like\s+(.+)",
                r"i\s+am\s+interested\s+in\s+(.+)",
                r"my\s+interest\s+is\s+(.+)"
            ],
            "remove_interest": [
                r"remove\s+interest\s+(.+)",
                r"i\s+don't\s+like\s+(.+)",
                r"not\s+interested\s+in\s+(.+)",
                r"delete\s+interest\s+(.+)"
            ],
            "list_interests": [
                r"list\s+my\s+interests",
                r"show\s+my\s+interests",
                r"what\s+are\s+my\s+interests",
                r"my\s+interests"
            ],
            "configuration_status": [
                r"configuration\s+status",
                r"show\s+configuration",
                r"current\s+settings",
                r"my\s+settings"
            ],
            "reset_configuration": [
                r"reset\s+configuration",
                r"default\s+settings",
                r"reset\s+all\s+settings",
                r"factory\s+reset"
            ],
            "export_configuration": [
                r"export\s+configuration",
                r"backup\s+settings",
                r"save\s+configuration",
                r"export\s+settings"
            ],
            "set_custom_phrase": [
                r"set\s+(\w+)\s+phrase\s+to\s+(.+)",
                r"change\s+(\w+)\s+message\s+to\s+(.+)",
                r"custom\s+(\w+)\s+(.+)"
            ]
        }
    
    def _setup_entity_extractors(self) -> Dict[str, re.Pattern]:
        """Setup regex patterns for entity extraction"""
        return {
            "number": re.compile(r'\b(\d+)\b'),
            "time": re.compile(r'\b(\d{1,2}):(\d{2})\b'),
            "date": re.compile(r'\b(\d{1,2})/(\d{1,2})/(\d{4})\b'),
            "percentage": re.compile(r'\b(\d+)%\b'),
            "file_extension": re.compile(r'\.(\w+)$'),
            "email": re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'),
            "url": re.compile(r'https?://[^\s]+'),
            "duration": re.compile(r'\b(\d+)\s+(second|minute|hour|day)s?\b', re.IGNORECASE)
        }
    
    def _load_application_names(self) -> Dict[str, str]:
        """Load application names and their executable paths.
        Uses AppDiscovery to dynamically detect ALL installed Windows apps."""
        # Default applications - kept as baseline fallback
        default_apps = {
            "notepad": "notepad.exe",
            "calculator": "calc.exe",
            "chrome": "chrome.exe",
            "firefox": "firefox.exe",
            "spotify": "spotify.exe",
            "discord": "discord.exe",
            "steam": "steam.exe",
            "word": "winword.exe",
            "excel": "excel.exe",
            "powerpoint": "powerpnt.exe",
            "outlook": "outlook.exe",
            "teams": "teams.exe",
            "zoom": "zoom.exe",
            "vlc": "vlc.exe",
            "photoshop": "photoshop.exe",
            "vscode": "code.exe",
            "visual studio code": "code.exe"
        }
        
        # Merge with config applications
        config_apps = self.config.get("applications", {})
        default_apps.update(config_apps)
        
        # Dynamically discover ALL installed apps
        try:
            from wizard.commands.app_discovery import AppDiscovery
            discovery = AppDiscovery(extra_apps=default_apps)
            all_apps = discovery.get_all_apps()
            logger.info(f"CommandRouter loaded {len(all_apps)} application names via discovery")
            return all_apps
        except Exception as e:
            logger.warning(f"App discovery unavailable in CommandRouter, using defaults: {e}")
            return default_apps
    
    def parse_command(self, text: str) -> Command:
        """
        Parse a natural language command into structured format
        
        Args:
            text: Raw voice command text
            
        Returns:
            Command object with intent, entities, and confidence
        """
        text = text.lower().strip()
        logger.info(f"Parsing command: {text}")
        
        # Find best matching intent
        best_intent, confidence, entities = self._classify_intent(text)
        
        # Extract additional entities
        extracted_entities = self._extract_entities(text)
        entities.update(extracted_entities)
        
        # Create command object
        command = Command(
            intent=best_intent,
            entities=entities,
            confidence=confidence,
            raw_text=text,
            timestamp=datetime.now()
        )
        
        logger.info(f"Parsed command - Intent: {best_intent}, Confidence: {confidence:.2f}")
        return command
    
    def _classify_intent(self, text: str) -> Tuple[str, float, Dict[str, Any]]:
        """
        Classify the intent of the command using pattern matching
        
        Args:
            text: Preprocessed command text
            
        Returns:
            Tuple of (intent, confidence, entities)
        """
        best_intent = "general_query"  # Default to AI processing instead of unknown
        best_confidence = 0.3  # Give AI processing a baseline confidence
        best_entities = {"query": text}  # Always include the full text as query
        
        for intent, patterns in self.intent_patterns.items():
            for pattern in patterns:
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    confidence = self._calculate_pattern_confidence(pattern, text)
                    
                    if confidence > best_confidence:
                        best_intent = intent
                        best_confidence = confidence
                        best_entities = self._extract_pattern_entities(match, intent)
        
        # If no strong pattern matches, try fuzzy matching for applications
        if best_confidence < 0.7:  # Increased threshold for fuzzy matching
            app_intent, app_confidence, app_entities = self._fuzzy_match_application(text)
            if app_confidence > best_confidence:
                best_intent = app_intent
                best_confidence = app_confidence
                best_entities = app_entities
        
        # Enhanced natural language detection for common patterns
        if best_confidence < 0.8:  # If still not confident, check for natural language patterns
            nl_intent, nl_confidence, nl_entities = self._detect_natural_language_intent(text)
            if nl_confidence > best_confidence:
                best_intent = nl_intent
                best_confidence = nl_confidence
                best_entities = nl_entities
        
        return best_intent, best_confidence, best_entities
    
    def _detect_natural_language_intent(self, text: str) -> Tuple[str, float, Dict[str, Any]]:
        """Detect intent from natural language patterns"""
        entities = {"query": text}
        
        # Check for common natural language patterns that should go to AI
        ai_patterns = [
            r"what is|tell me about|explain|how does|why does|when is|where is",
            r"can you|could you|would you|will you",
            r"i want to|i need to|i would like to",
            r"help me|assist me|show me",
            r"find|search|look up|google"
        ]
        
        for pattern in ai_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                return "general_query", 0.8, entities
        
        # Check for specific action patterns that might need routing
        if any(word in text for word in ["open", "launch", "start", "run"]):
            # Extract potential application name
            words = text.split()
            for i, word in enumerate(words):
                if word in ["open", "launch", "start", "run"] and i + 1 < len(words):
                    app_name = words[i + 1]
                    return "open_application", 0.7, {"application": app_name, "query": text}
        
        if any(word in text for word in ["search", "find", "look up", "google"]):
            return "web_search", 0.7, {"query": text}
        
        # Default to general AI processing for natural language
        return "general_query", 0.5, entities
    
    def _calculate_pattern_confidence(self, pattern: str, text: str) -> float:
        """Calculate confidence score for pattern match"""
        # Simple confidence based on pattern specificity and text length
        pattern_length = len(pattern.replace(r'\s+', ' ').replace(r'(.+)', ''))
        text_length = len(text)
        
        if text_length == 0:
            return 0.0
        
        # Base confidence from pattern match
        base_confidence = min(pattern_length / text_length, 1.0)
        
        # Boost confidence for exact matches
        if pattern_length == text_length:
            base_confidence *= 1.2
        
        return min(base_confidence, 1.0)
    
    def _extract_pattern_entities(self, match: re.Match, intent: str) -> Dict[str, Any]:
        """Extract entities from regex match groups"""
        entities = {}
        
        if match.groups():
            if intent in ["open_application", "close_application"]:
                entities["application"] = match.group(1).strip()
            elif intent in ["set_volume"]:
                entities["volume_level"] = int(match.group(1))
            elif intent in ["play_music", "youtube_search"]:
                entities["query"] = match.group(1).strip()
            elif intent in ["search_files", "web_search", "general_query", "calculate"]:
                entities["query"] = match.group(1).strip()
            elif intent == "unit_conversion":
                if len(match.groups()) >= 3:
                    # Handle patterns like "5 feet to meters"
                    entities["query"] = f"{match.group(1)} {match.group(2)} to {match.group(3)}"
                else:
                    entities["query"] = match.group(1).strip()
            elif intent in ["news", "sports", "movies"]:
                if match.groups():
                    entities["query"] = match.group(1).strip()
                else:
                    entities["query"] = ""
            elif intent in ["set_timer"]:
                entities["duration"] = int(match.group(1))
                entities["unit"] = match.group(2).rstrip('s')  # Remove plural 's'
            elif intent in ["create_reminder", "take_note", "add_todo"]:
                entities["content"] = match.group(1).strip()
            elif intent in ["create_folder", "delete_file", "open_file"]:
                entities["target"] = match.group(1).strip()
            elif intent in ["tell_joke", "fun_fact", "trivia_question"]:
                if match.groups():
                    entities["category"] = match.group(1).strip()
            elif intent in ["roll_dice"]:
                if match.groups():
                    entities["number"] = int(match.group(1))
            elif intent in ["generate_number"]:
                if len(match.groups()) >= 2:
                    entities["min_number"] = int(match.group(1))
                    entities["max_number"] = int(match.group(2))
            elif intent in ["rock_paper_scissors"]:
                if match.groups():
                    entities["choice"] = match.group(1).strip()
            elif intent in ["movie_recommendation", "music_recommendation"]:
                if match.groups():
                    entities["genre"] = match.group(1).strip()
            elif intent in ["execute_routine", "create_routine"]:
                if match.groups():
                    entities["routine_name"] = match.group(1).strip()
            elif intent in ["schedule_routine"]:
                if len(match.groups()) >= 2:
                    entities["routine_name"] = match.group(1).strip()
                    entities["schedule_time"] = match.group(2).strip()
                elif match.groups():
                    entities["routine_name"] = match.group(1).strip()
            elif intent in ["batch_file_operation"]:
                if len(match.groups()) >= 2:
                    entities["operation_type"] = match.group(1).strip()
                    entities["source_pattern"] = match.group(2).strip()
            elif intent in ["set_password", "authenticate"]:
                if match.groups():
                    entities["password"] = match.group(1).strip()
            elif intent in ["add_protected_command", "remove_protected_command"]:
                if match.groups():
                    entities["command_name"] = match.group(1).strip()
            elif intent in ["confirmation_response"]:
                if match.groups():
                    entities["confirmation_id"] = match.group(1).strip()
            elif intent in ["set_voice_gender", "set_personality", "set_humor_level", "set_verbosity"]:
                if match.groups():
                    key_map = {
                        "set_voice_gender": "gender",
                        "set_personality": "personality", 
                        "set_humor_level": "humor_level",
                        "set_verbosity": "verbosity"
                    }
                    entities[key_map[intent]] = match.group(1).strip()
            elif intent in ["set_voice_speed", "set_voice_pitch", "set_voice_volume"]:
                if match.groups():
                    key_map = {
                        "set_voice_speed": "speed",
                        "set_voice_pitch": "pitch", 
                        "set_voice_volume": "volume"
                    }
                    entities[key_map[intent]] = match.group(1).strip()
            elif intent in ["add_wake_word", "remove_wake_word"]:
                if match.groups():
                    entities["wake_word"] = match.group(1).strip()
            elif intent in ["set_assistant_name", "set_user_name"]:
                if match.groups():
                    entities["name"] = match.group(1).strip()
            elif intent in ["add_interest", "remove_interest"]:
                if match.groups():
                    entities["interest"] = match.group(1).strip()
            elif intent in ["set_custom_phrase"]:
                if len(match.groups()) >= 2:
                    entities["phrase_type"] = match.group(1).strip()
                    entities["phrase_text"] = match.group(2).strip()
        
        return entities
    
    def _fuzzy_match_application(self, text: str) -> Tuple[str, float, Dict[str, Any]]:
        """
        Use fuzzy matching to identify application names in commands
        
        Args:
            text: Command text
            
        Returns:
            Tuple of (intent, confidence, entities)
        """
        best_app = None
        best_confidence = 0.0
        
        # Check for action words
        action_words = {
            "open": "open_application",
            "launch": "open_application", 
            "start": "open_application",
            "run": "open_application",
            "close": "close_application",
            "quit": "close_application",
            "exit": "close_application"
        }
        
        detected_action = None
        for action in action_words:
            if action in text:
                detected_action = action_words[action]
                break
        
        if not detected_action:
            return "unknown", 0.0, {}
        
        # Find best matching application name
        for app_name in self.app_names.keys():
            similarity = SequenceMatcher(None, app_name, text).ratio()
            
            # Also check if app name is contained in text
            if app_name in text:
                similarity = max(similarity, 0.8)
            
            if similarity > best_confidence and similarity > 0.6:
                best_confidence = similarity
                best_app = app_name
        
        if best_app:
            return detected_action, best_confidence, {"application": best_app}
        
        return "unknown", 0.0, {}
    
    def _extract_entities(self, text: str) -> Dict[str, Any]:
        """
        Extract various entities from the command text
        
        Args:
            text: Command text
            
        Returns:
            Dictionary of extracted entities
        """
        entities = {}
        
        for entity_type, pattern in self.entity_extractors.items():
            matches = pattern.findall(text)
            if matches:
                if entity_type == "number":
                    entities["numbers"] = [int(match) for match in matches]
                elif entity_type == "time":
                    entities["times"] = matches
                elif entity_type == "date":
                    entities["dates"] = matches
                elif entity_type == "percentage":
                    entities["percentages"] = [int(match) for match in matches]
                elif entity_type == "duration":
                    entities["durations"] = matches
                else:
                    entities[entity_type] = matches
        
        return entities
    
    def route_command(self, command: Command) -> Response:
        """
        Route a parsed command to the appropriate handler
        
        Args:
            command: Parsed command object
            
        Returns:
            Response object with result
        """
        logger.info(f"Routing command with intent: {command.intent}")
        
        if command.intent in self.handlers:
            try:
                return self.handlers[command.intent](command)
            except Exception as e:
                logger.error(f"Error executing handler for {command.intent}: {e}")
                return Response(
                    text=f"Sorry, I encountered an error while processing your request: {str(e)}",
                    error_message=str(e)
                )
        else:
            # Route unknown commands to general_query handler for AI processing
            logger.info(f"No specific handler for intent: {command.intent}, routing to general AI")
            if "general_query" in self.handlers:
                try:
                    # Update command intent to general_query for AI processing
                    ai_command = Command(
                        intent="general_query",
                        entities={"query": command.raw_text, **command.entities},
                        confidence=command.confidence,
                        raw_text=command.raw_text,
                        timestamp=command.timestamp,
                        user_id=command.user_id
                    )
                    return self.handlers["general_query"](ai_command)
                except Exception as e:
                    logger.error(f"Error in AI handler: {e}")
                    return Response(
                        text=f"I'm having trouble processing that request: {str(e)}",
                        error_message=str(e)
                    )
            else:
                logger.warning(f"No handler registered for intent: {command.intent}")
                return Response(
                    text="I'm not sure how to handle that command. Could you try rephrasing it?",
                    error_message=f"No handler for intent: {command.intent}"
                )
    
    def register_handler(self, intent: str, handler: Callable[[Command], Response]) -> None:
        """
        Register a command handler for a specific intent
        
        Args:
            intent: Intent name to handle
            handler: Function that takes Command and returns Response
        """
        self.handlers[intent] = handler
        logger.info(f"Registered handler for intent: {intent}")
    
    def get_supported_intents(self) -> List[str]:
        """Get list of all supported intents"""
        return list(self.intent_patterns.keys())
    
    def get_application_names(self) -> List[str]:
        """Get list of all known application names"""
        return list(self.app_names.keys())


def _apply_web_content_filtering(url: str, query: str = "") -> tuple[bool, str]:
    """
    Apply content filtering to web commands.
    
    Args:
        url: URL to filter
        query: Search query (if applicable)
        
    Returns:
        Tuple of (allowed, reason_or_response)
    """
    content_filter = _get_content_filter()
    if not content_filter:
        return True, ""
    
    try:
        from wizard.utils.content_filter import WebRequest, RequestType
        
        # Determine request type
        request_type = RequestType.SEARCH if query else RequestType.WEBSITE
        
        # Create web request
        request = WebRequest(
            url=url,
            query=query,
            request_type=request_type
        )
        
        # Apply filtering
        result = content_filter.filter_request(request)
        
        if not result.allowed:
            # Create user-friendly blocked message
            blocked_msg = f"I can't access that content: {result.reason}"
            if result.suggested_alternatives:
                blocked_msg += f" {result.suggested_alternatives[0]}"
            return False, blocked_msg
        
        return True, ""
        
    except Exception as e:
        # If filtering fails, allow by default but log the error
        logger.warning(f"Content filtering error: {e}")
        return True, ""


# Simple route_command function for direct import
def route_command(command_text: str) -> str:
    """
    Simple command router that takes text and returns response string.
    This is the main entry point for voice commands.
    
    Args:
        command_text: The voice command as text
        
    Returns:
        Response string to be spoken by TTS
    """
    import re
    import time
    import pyautogui
    try:
        from wizard.commands import web_browser
        from wizard.commands import text_editor
        from wizard.commands import system_control
        from wizard.commands import volume_control
        from wizard.commands import task_handler
        from wizard.commands import brightness_control
        from wizard.commands import research_assistant
        from wizard.utils.config_manager import ConfigManager
        from wizard.utils.logger import WizardLogger
    except ImportError:
        # Fallback for relative imports
        from . import web_browser
        from . import text_editor
        from . import system_control
        from . import volume_control
        from . import task_handler
        from . import brightness_control
        from . import research_assistant
        from ..utils.config_manager import ConfigManager
        from ..utils.logger import WizardLogger
    
    # Initialize components
    config = ConfigManager()
    logger = WizardLogger()
    researcher = research_assistant.ResearchAssistant(config, logger)
    
    import psutil
    import os
    from pathlib import Path
    
    def _close_all_apps():
        """Close all non-system user applications"""
        closed = 0
        system_procs = {'explorer.exe', 'svchost.exe', 'csrss.exe', 'lsass.exe', 'winlogon.exe',
                       'services.exe', 'smss.exe', 'wininit.exe', 'system', 'registry', 'dwm.exe',
                       'taskhost.exe', 'conhost.exe', 'python.exe', 'py.exe', 'cmd.exe'}
        for proc in psutil.process_iter(['pid', 'name']):
            try:
                name = proc.info['name'].lower()
                if name not in system_procs and proc.pid != os.getpid():
                    proc.terminate()
                    closed += 1
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
        return f"Closed {closed} applications."

    
    # --- DECISION LOGIC START ---
    
    # 1. Normalize Speech
    command = command_text.lower().strip()
    command = re.sub(r'^(wizard|hey wizard)[,\s]+', '', command)
    command = command.strip()
    
    # 2. Analyze Intent & 3. Confirm Safety
    
    # 2a. Identity Queries
    if any(word in command for word in ['who are you', 'your name', 'what are you']):
        assistant_name = config.get_setting('assistant_name', 'Wizard')
        personality = config.config.personality_settings.personality_type
        if personality == 'friendly':
            return f"I'm {assistant_name}, your friendly AI assistant. I'm here to help you manage your computer and find information!"
        return f"I am {assistant_name}, an AI assistant designed to help you with system tasks and information retrieval."

    if any(word in command for word in ['who created you', 'who made you', 'your creator']):
        return "I was created by a team of developers to be your powerful voice assistant."

    # Handle pending confirmations (yes/no with Gujarati support)
    if hasattr(route_command, "pending_action"):
        yes_triggers = ['yes', 'confirm', 'do it', 'proceed', 'ha', 'હા', 'chokkas', 'barabar', 'kari lo', 'thase']
        no_triggers = ['no', 'cancel', 'stop', 'dont', 'don\'t', 'na', 'ના', 'rehwa do', 'reva do', 'nathi karvu']
        
        if any(word in command for word in yes_triggers):
            action = route_command.pending_action
            delattr(route_command, "pending_action")
            return action()
        elif any(word in command for word in no_triggers):
            if hasattr(route_command, "pending_action"):
                delattr(route_command, "pending_action")
            return "Operation cancelled."
        else:
            return "Please confirm by saying 'yes' or 'no'."

    # ==========================================
    # TIME & DATE (Must be checked EARLY before info_request patterns catch them)
    # ==========================================
    if re.search(r'\b(?:what\s+time|current\s+time|time\s+(?:right\s+)?now|kitna\s+baje|samay|સમય)\b', command) and 'timer' not in command:
        return task_handler.get_time()
    
    if re.search(r"\b(?:what(?:'s|\s+is)?\s+(?:today'?s?\s+)?date|today'?s?\s+date|current\s+date|tarikh|તારીખ)\b", command):
        return task_handler.get_date()

    # ==========================================
    # TIMER (Feature #2)
    # ==========================================
    if 'timer' in command and any(word in command for word in ['set', 'start', 'create', 'laga', 'lagao', 'chalu', 'ચાલુ', 'લગાવો']):
        time_match = re.search(r'(\d+)\s*(minute|minutes|hour|hours|second|seconds|min|sec|hr|hrs)', command)
        if time_match:
            amount = int(time_match.group(1))
            unit = time_match.group(2)
            if 'hour' in unit or 'hr' in unit:
                return task_handler.set_timer(amount * 60)
            elif 'second' in unit or 'sec' in unit:
                return task_handler.set_timer(max(1, amount // 60))
            else:
                return task_handler.set_timer(amount)
        return "How long should I set the timer for? Example: 'set a timer for 5 minutes'"

    # ==========================================
    # ALARM (Feature #3)
    # ==========================================
    if re.search(r'\b(?:set|create|make)\s+(?:an?\s+)?alarm\b', command):
        time_match = re.search(r'(?:for|at)\s+(\d{1,2}(?::\d{2})?\s*(?:am|pm)?)', command)
        alarm_time = time_match.group(1) if time_match else "the requested time"
        return f"Alarm set for {alarm_time}. I'll alert you when it's time."

    # ==========================================
    # REMINDER (Feature #4)
    # ==========================================
    if 'remind' in command:
        match = re.search(r'remind\s+me\s+to\s+(.+)', command)
        task = match.group(1).strip() if match else ""
        if task: return f"I'll remind you to {task}"
        return "What would you like me to remind you about?"

    # ==========================================
    # TODO LIST (Feature #5 - TRAINING PHASE)
    # ==========================================
    if re.search(r'\b(?:add|create|put)\b.*?\b(?:todo|to-do|to\s+do\s+list|task\s+list)\b', command):
        task_match = re.search(r'\b(?:add|create|put)\s+(.+?)(?:\s+to\s+(?:my\s+)?(?:todo|to-do|to\s+do|task)\s*(?:list)?)', command)
        task_text = task_match.group(1) if task_match else command
        return f"[Training Phase] Todo added: '{task_text}'. The full todo system is under development."

    if re.search(r'\b(?:show|list|view|my)\s+(?:my\s+)?(?:todo|to-do|to\s+do|task)\s*(?:list|s)?\b', command):
        return "[Training Phase] Todo list feature is under development. Stay tuned!"

    # ==========================================
    # TYPE / WRITE TEXT INTO ACTIVE APP (Feature #6)
    # ==========================================
    if re.search(r'^(?:type|write)\s+(.+?)\s+(?:into|in)\s+(?:the\s+)?(?:active\s+app|current\s+(?:window|app))', command):
        text_match = re.search(r'^(?:type|write)\s+(.+?)\s+(?:into|in)', command)
        if text_match:
            text_to_type = text_match.group(1).strip()
            import time as _time
            _time.sleep(0.5)
            pyautogui.typewrite(text_to_type, interval=0.03)
            return f"Typed '{text_to_type}' into the active app."

    # ==========================================
    # SYSTEM HEALTH / CPU / RAM (Feature #8)
    # ==========================================
    if re.search(r'\b(?:cpu|ram|memory|system\s+health|system\s+status|resource|usage)\b', command):
        cpu = psutil.cpu_percent(interval=1)
        ram = psutil.virtual_memory()
        return f"CPU usage: {cpu}%. RAM usage: {ram.percent}% ({ram.used // (1024**3)}GB used of {ram.total // (1024**3)}GB total)."

    # ==========================================
    # BATTERY STATUS (Feature #9)
    # ==========================================
    if re.search(r'\b(?:battery|charge|charging|power\s+status)\b', command):
        battery = psutil.sensors_battery()
        if battery:
            status = "charging" if battery.power_plugged else "not charging"
            return f"Battery is at {battery.percent}%, {status}."
        return "Battery information is not available on this device."


    # Broaden patterns to include 'laptop', 'system', 'pc', etc.
    # English + Gujarati (computer bandh karo, laptop bandh karo)
    if re.search(r'(?:shutdown|turn\s+off|bandh\s+karo|બંધ\s+કરો)\b.*?\b(?:computer|laptop|system|pc|machine|notebook|કોમ્પ્યુટર|લેપટોપ)', command) or \
       re.search(r'(?:computer|laptop|system|pc|machine|notebook|કોમ્પ્યુટર|લેપટોપ).*?(?:shutdown|turn\s+off|bandh\s+karo|બંધ\s+કરો)', command):
        route_command.pending_action = lambda: system_control.shutdown_computer()
        return "Are you sure you want to shut down the computer? Say yes to confirm. (શું તમે કોમ્પ્યુટર બંધ કરવા માંગો છો?)"
    
    if re.search(r'(?:restart|reboot)\b.*?\b(?:computer|laptop|system|pc|machine|notebook|કોમ્પ્યુટર|લેપટોપ)', command) or \
       re.search(r'(?:computer|laptop|system|pc|machine|notebook|કોમ્પ્યુટર|લેપટોપ).*?(?:restart|reboot)', command) or \
       any(word in command for word in ['reboot', 'ફરીથી ચાલુ']):
        route_command.pending_action = lambda: system_control.restart_computer()
        return "Are you sure you want to restart the computer? Say yes to confirm. (શું તમે કોમ્પ્યુટર ફરીથી ચાલુ કરવા માંગો છો?)"
    
    # Application Installation (Sensitive)
    if re.search(r'\binstall\b\s+(.+)', command):
        match = re.search(r'\binstall\b\s+(.+)', command)
        if match:
            app_name = match.group(1).strip()
            # In a real assistant, this might trigger a downloader/installer
            route_command.pending_action = lambda: f"I have started searching for the {app_name} installer for you."
            return f"Are you trying to install {app_name}? Please say yes to confirm and I will look for it."
    
    # Brightness Control
    # English + Gujarati (tej vadharo, light vadharo)
    if any(word in command for word in ['increase brightness', 'brightness up', 'brighter', 'tej vadharo', 'light vadharo', 'તેજ વધારો']):
        return brightness_control.increase_brightness(10)
    
    if any(word in command for word in ['decrease brightness', 'brightness down', 'dim', 'tej ghataro', 'light ghataro', 'તેજ ઘટાડો']):
        return brightness_control.decrease_brightness(10)
    
    if 'brightness' in command or 'તેજ' in command or 'લાઇટ' in command:
        match = re.search(r'(?:brightness|tej|તેજ|લાઇટ)\s+(?:to\s+)?(\d+)', command)
        if match:
            level = int(match.group(1))
            return brightness_control.set_brightness(level)

    # Volume Control
    # English + Gujarati (avaj vadharo, upar karo)
    if any(word in command for word in ['increase volume', 'volume up', 'louder', 'turn up', 'avaj vadharo', 'vadharo', 'વધારો', 'vadhado']):
        return volume_control.increase_volume(10)
    
    # English + Gujarati (avaj ghataro, dhiro karo)
    if any(word in command for word in ['decrease volume', 'volume down', 'quieter', 'turn down', 'low volume', 'avaj ghataro', 'ghataro', 'ઘટાડો', 'dhiro karo']):
        return volume_control.decrease_volume(10)
    
    if 'set volume' in command or (re.search(r'\b(?:volume|avaj|અવાજ)\b', command) and re.search(r'\d+', command)):
        match = re.search(r'(?:set\s+)?(?:volume|avaj|અવાજ)\s+(?:to\s+|at\s+)?(\d+)', command)
        if match:
            level = int(match.group(1))
            return volume_control.set_volume(level)
    
    if any(word in command for word in ['mute', 'silence', 'avaj bandh', 'બંધ કરો', 'અવાજ બંધ']):
        return volume_control.mute_volume()
    
    if any(word in command for word in ['unmute', 'avaj chalu', 'ચાલુ કરો', 'અવાજ ચાલુ', 'vadhado', 'વધારો']):
        return volume_control.unmute_volume()
    
    # ==========================================
    # SELECT ALL + COPY combined (Feature #21 - TRAINING PHASE)
    # ==========================================
    if re.search(r'\bselect\s+all\b.*?\bcopy\b', command) or re.search(r'\bcopy\s+all\b', command):
        pyautogui.hotkey('ctrl', 'a')
        import time as _time
        _time.sleep(0.3)
        pyautogui.hotkey('ctrl', 'c')
        return "[Training Phase] Selected all and copied to clipboard."

    # Desktop Automation
    if any(word in command for word in ['minimize all', 'show desktop', 'hide everything']):
        return system_control.minimize_all_windows()
    
    if any(word in command for word in ['refresh', 'reload']):
        return system_control.refresh_page()
    
    if any(word in command for word in ['press enter', 'hit enter']):
        return system_control.press_enter()
    
    if any(word in command for word in ['switch window', 'change window', 'alt tab']):
        return system_control.switch_window()
    
    if any(word in command for word in ['select all', 'highlight all']):
        return system_control.select_all()
    
    if any(word in command for word in ['copy that', 'copy this', 'copy selected']):
        return system_control.copy_text()
    
    if any(word in command for word in ['paste that', 'paste this', 'paste here']):
        return system_control.paste_text()

    if re.search(r'take\s+screenshot|capture\s+screen|screen\s+shot', command):
        return system_control.take_screenshot()

    # ==========================================
    # SLEEP COMPUTER (Feature #12)
    # ==========================================
    if re.search(r'\b(?:sleep|hibernate)\b.*?\b(?:computer|laptop|system|pc|machine)\b', command) or \
       re.search(r'\b(?:computer|laptop|system|pc|machine)\b.*?\b(?:sleep|hibernate)\b', command):
        try:
            os.system('rundll32.exe powrprof.dll,SetSuspendState 0,1,0')
            return "Putting the computer to sleep."
        except Exception as e:
            return f"Error putting computer to sleep: {e}"

    # ==========================================
    # LOCK COMPUTER (Feature #13)
    # ==========================================
    if re.search(r'\block\b.*?\b(?:computer|laptop|system|pc|machine|screen)\b', command) or \
       re.search(r'\b(?:computer|laptop|system|pc|machine|screen)\b.*?\block\b', command):
        return system_control.lock_computer()

    # ==========================================
    # CLOSE ALL RUNNING APPS (Feature #14)
    # ==========================================
    if re.search(r'\bclose\s+all\b.*?\b(?:app|apps|application|running|window|windows)\b', command):
        route_command.pending_action = lambda: _close_all_apps()
        return "Are you sure you want to close all running apps? Say yes to confirm."

    # ==========================================
    # WHATSAPP MESSAGING (Feature #17 - Local App)
    # ==========================================
    if re.search(r'\b(?:whatsapp|whats\s*app)\b', command) and any(word in command for word in ['send', 'message', 'msg', 'massage']):
        # Pattern to capture both contact and the message: "send message to [contact] that says [message]" or "saying [message]"
        contact_name = "a contact"
        message_to_send = None

        # Look for the message content first
        msg_match = re.search(r'(?:saying|that\s+says|message\s+is|massage\s+is)\s+(.+?)(?:\s+(?:on|in|through|using)\s+(?:whatsapp|whats\s*app)|$)', command)
        if msg_match:
            message_to_send = msg_match.group(1).strip()
            # Remove the message part from the string to easily extract contact
            cmd_no_msg = command.replace(msg_match.group(0), "")
        else:
            cmd_no_msg = command

        # Extract contact
        contact_match = re.search(r'(?:send|message|msg|massage)\s+(?:a\s+(?:message|massage)\s+)?(?:through\s+whatsapp\s+to\s+|to\s+)?(.+?)(?:\s+(?:on|in|through|using|saying|that\s+says)|$)', cmd_no_msg)
        if not contact_match:
            contact_match = re.search(r'(?:whatsapp|whats\s*app).*?(?:send|message|msg|massage)\s+(?:a\s+(?:message|massage)\s+)?(?:to\s+)?(.+)', cmd_no_msg)
            
        if contact_match:
            contact_name = contact_match.group(1).strip()
            # If the group accidentally caught "message to panthil clg", fix it
            contact_name = re.sub(r'^(?:a\s+)?(?:message\s+to|msg\s+to|to)\s+', '', contact_name).strip()
            # Clean up trailing words like 'on whatsapp' if they leaked in
            contact_name = re.sub(r'\s+(?:on|in|using)\s+(?:whatsapp|whats\s*app)$', '', contact_name).strip()

        # Fallback: if they omitted "saying" and the captured contact is very long (contains the message acting as a name)
        if not message_to_send and contact_name:
            words = contact_name.split()
            if len(words) >= 4:
                # Assume the first 2 words are the contact name, and the rest is the message
                # For example: "panthil clg hello panthil this is..." -> contact: "panthil clg"
                contact_name = " ".join(words[:2])
                message_to_send = " ".join(words[2:])

        if contact_name.lower() in ["whatsapp", "whats app", ""]:
            return "Please specify the contact name. Example: send message to John on whatsapp saying hello"

        import time as _time
        pyautogui.hotkey('win')
        _time.sleep(1)
        pyautogui.typewrite('whatsapp')
        _time.sleep(1)
        pyautogui.press('enter')
        _time.sleep(6)  # Wait for WhatsApp to load
        
        # After WhatsApp opens, simulate pressing Ctrl+F to focus the search bar
        pyautogui.hotkey('ctrl', 'f')
        _time.sleep(1)
        # Type the contact name in the search bar
        pyautogui.typewrite(contact_name)
        _time.sleep(2)
        
        # Press Tab twice to reliably lock onto the first search result in modern WhatsApp UI
        pyautogui.press('tab')
        _time.sleep(0.1)
        pyautogui.press('tab')
        _time.sleep(0.5)
        
        # Hit Enter to open the selected chat
        pyautogui.press('enter')
        _time.sleep(1.5)
        
        if message_to_send:
            pyautogui.typewrite(message_to_send)
            _time.sleep(0.5)
            pyautogui.press('enter')
            return f"Message sent to {contact_name} on WhatsApp."
        else:
            return f"Opened {contact_name}'s chat on WhatsApp. You can now type or dictate the message."
        
    if re.search(r'\b(?:whatsapp|whats\s*app)\b', command):
        import time as _time
        pyautogui.hotkey('win')
        _time.sleep(1)
        pyautogui.typewrite('whatsapp')
        _time.sleep(1)
        pyautogui.press('enter')
        return "Opening WhatsApp."

    # ==========================================
    # LANGUAGE TRANSLATION (Feature #18)
    # ==========================================
    if re.search(r'\btranslat(?:e|ion)\b', command):
        translate_match = re.search(r'translat(?:e|ion)\s+["\']?(.+?)["\']?\s+(?:to|into|in)\s+(\w+)', command)
        if translate_match:
            text_to_translate = translate_match.group(1).strip()
            target_lang = translate_match.group(2).strip()
            try:
                from googletrans import Translator
                translator = Translator()
                lang_map = {'gujarati': 'gu', 'hindi': 'hi', 'spanish': 'es', 'french': 'fr', 'german': 'de', 'japanese': 'ja', 'chinese': 'zh-cn', 'arabic': 'ar', 'korean': 'ko'}
                target_code = lang_map.get(target_lang.lower(), target_lang.lower())
                result = translator.translate(text_to_translate, dest=target_code)
                return f"Translation of '{text_to_translate}' to {target_lang}: {result.text}"
            except ImportError:
                return f"Translation feature requires the 'googletrans' package. Install with: pip install googletrans==4.0.0-rc1"
            except Exception as e:
                return f"Translation error: {e}"
        return "Please specify what to translate and the target language. Example: 'translate hello to gujarati'"

    # ==========================================
    # CLOSE BROWSER TAB (Feature #19)
    # ==========================================
    if re.search(r'\bclose\b.*?\b(?:tab|browser\s+tab|this\s+tab|current\s+tab)\b', command):
        pyautogui.hotkey('ctrl', 'w')
        return "Closing the current browser tab."

    # ==========================================
    # SELECT ALL + COPY combined (Feature #21 - TRAINING PHASE)
    # ==========================================
    if re.search(r'\bselect\s+all\b.*?\bcopy\b', command) or re.search(r'\bcopy\s+all\b', command):
        pyautogui.hotkey('ctrl', 'a')
        import time as _time
        _time.sleep(0.3)
        pyautogui.hotkey('ctrl', 'c')
        return "[Training Phase] Selected all and copied to clipboard."

    # ==========================================
    # NEWS HEADLINES (Feature #22)
    # ==========================================
    if re.search(r'\b(?:news|headline|headlines|latest\s+news|top\s+news|samachar)\b', command):
        try:
            import webbrowser
            webbrowser.open("https://news.google.com")
            return "Opening Google News for the latest headlines."
        except Exception as e:
            return f"Error opening news: {e}"

    # ==========================================
    # DAILY BRIEFING / MORNING UPDATE (Feature #23)
    # ==========================================
    if re.search(r'\b(?:daily\s+briefing|morning\s+update|good\s+morning|day\s+summary|brief\s+me)\b', command):
        import datetime
        now = datetime.datetime.now()
        greeting = "Good morning" if now.hour < 12 else "Good afternoon" if now.hour < 17 else "Good evening"
        time_str = now.strftime("%I:%M %p")
        date_str = now.strftime("%B %d, %Y")
        cpu = psutil.cpu_percent(interval=0.5)
        ram = psutil.virtual_memory()
        battery = psutil.sensors_battery()
        batt_str = f"Battery: {battery.percent}%." if battery else ""
        return f"{greeting}! It's {time_str} on {date_str}. System: CPU {cpu}%, RAM {ram.percent}%. {batt_str} How can I help you today?"

    # ==========================================
    # WEATHER (Feature #25)
    # ==========================================
    if re.search(r'\b(?:weather|forecast|temperature|mausam)\b', command):
        city_match = re.search(r'(?:weather|forecast|temperature|mausam)\s+(?:in|of|for|at)?\s*(\w[\w\s]*)', command)
        city = city_match.group(1).strip() if city_match else "your location"
        try:
            import webbrowser
            webbrowser.open(f"https://www.google.com/search?q=weather+{city.replace(' ', '+')}")
            return f"Showing weather for {city}."
        except:
            return f"I don't have live weather data yet, but I'm searching the weather for {city}."

    # ==========================================
    # MAPS & NAVIGATION (Feature #26)
    # ==========================================
    if re.search(r'\b(?:navigate|navigation|directions|direction|route|drive\s+to)\b', command):
        dest_match = re.search(r'(?:navigate|directions|direction|route|drive)\s+(?:to|from)?\s*(.+?)$', command)
        if dest_match:
            destination = dest_match.group(1).strip()
            import webbrowser
            webbrowser.open(f"https://www.google.com/maps/dir//{destination.replace(' ', '+')}")
            return f"Opening Google Maps with directions to {destination}."
        import webbrowser
        webbrowser.open("https://www.google.com/maps")
        return "Opening Google Maps."


    # Handles: "write about [topic] in this app", "write about AI in notepad", 
    # "describe quantum physics in word", "research climate change and type it",
    # "write a blog about space exploration", "write about AI in 300 words"
    # Does NOT open any browser - all research happens in background
    
    write_triggers = ['write about', 'write on', 'type about', 'type information', 
                      'research and write', 'research and type', 'describe about',
                      'write a blog', 'write an essay', 'write a report', 'make ppt', 'make professional ppt',
                      'create presentation', 'make presentation', 'prepare ppt', 'prepare presentation',
                      'લખો', 'વિષે લખો', 'માહિતી લખો',   # Gujarati
                      'likho', 'likh', 'vistar thi likho']  # Transliterated Gujarati
    
    has_write_trigger = any(trigger in command for trigger in write_triggers)
    
    if not has_write_trigger:
        has_write_trigger = bool(re.search(
            r'(?:write|create|type|describe|research|make|prepare)\s+(?:something\s+|a\s+(?:professional\s+)?)?(?:about\s+|on\s+)?'
            r'.*?\s*(?:in|on|using)\s+(?:this\s+app|notepad|word|note|excel|powerpoint|ppt|power\s+point)',
            command
        )) or command.strip() in ['make professional ppt', 'create ppt']
    
    if has_write_trigger:
        from wizard.commands.smart_writer import write_about_topic
        
        # Extract topic, target app, style, and word limit
        topic = None
        target_app = 'active'  # Default: type into currently active app
        style = 'assignment'   # Default style
        word_limit = 500       # Default word limit
        
        # Detect target app
        if any(w in command for w in ['in word', 'in microsoft word', 'word file']):
            target_app = 'word'
        elif any(w in command for w in ['in excel', 'in microsoft excel', 'excel file', 'dataset', 'xlsx']):
            target_app = 'excel'
        elif any(w in command for w in ['in powerpoint', 'in ppt', 'presentation', 'power point']):
            target_app = 'powerpoint'
        elif 'in notepad' in command or 'in note' in command:
            target_app = 'notepad'
        elif 'in this app' in command or 'here' in command:
            target_app = 'active'
        
        # Detect writing style
        if any(w in command for w in ['blog', 'blog post', 'article']):
            style = 'blog'
        elif any(w in command for w in ['report', 'professional', 'formal']):
            style = 'professional'
        elif any(w in command for w in ['essay', 'assignment', 'homework']):
            style = 'assignment'
        
        # Detect word limit (e.g., "in 300 words", "500 word")
        word_match = re.search(r'(\d+)\s*(?:words?|shabd)', command)
        if word_match:
            word_limit = int(word_match.group(1))
            # Clamp to reasonable range
            word_limit = max(100, min(word_limit, 2000))
        
        # Extract topic using multiple patterns
        
        # Check for complex phrasing: "collect information about AI and write into powerpoint"
        complex_match = re.search(r'(?:collect|gather)\s+(?:all\s+)?(?:information|info)\s+(?:about|on|regarding|for)\s+(.+?)(?:\s+and\s+(?:combine|write|put|type|describe|make|create))', command)
        
        if complex_match:
            topic = complex_match.group(1).strip()
        else:
            if not match:
                # Pattern 1: "write about [topic] in/on [app]"
                match = re.search(
                    r'(?:write|create|make|type|describe|research|prepare|likho|likh)\s+'
                    r'(?:into\s+|in\s+|on\s+)?'
                    r'(?:a\s+(?:blog|essay|report|article|presentation|professional\s+ppt|ppt|professional\s+presentation|dataset)\s+(?:about|on|for)\s+)?'
                    r'(?:something\s+)?(?:about|on|regarding|for)?\s*'
                    r'(.+?)'
                    r'(?:\s+(?:in|on|using)\s+(?:this\s+app|word|notepad|note|microsoft\s+word|excel|powerpoint|ppt|power\s+point))?'
                    r'(?:\s+in\s+\d+\s+words?)?'
                    r'(?:\s+here)?$',
                    command
                )
                
                if not match:
                    # Pattern 2: Simpler fallback - "write about AI"
                    match = re.search(
                        r'(?:write|type|describe|research|make|prepare|collect|gather)\s+(?:a\s+(?:professional\s+)?(?:ppt|presentation)\s+(?:about|on)\s+|about\s+|on\s+|all\s+information\s+about\s+)?(.+?)(?:\s+(?:in|on)\s+|\s+here|$)',
                        command
                    )
            
            if match:
                topic = match.group(1).strip()
            
        if topic:
            # Clean up topic - remove style/app words that leaked in
            cleanup_words = ['blog', 'essay', 'report', 'article', 'assignment',
                             'word', 'notepad', 'note', 'this app', 'here',
                             'and type it', 'and write it', 'information',
                             'excel', 'powerpoint', 'ppt', 'presentation', 'dataset', 'power point', 'word file', 'excel file', 'xlsx']
            for cw in cleanup_words:
                topic = re.sub(r'\b' + re.escape(cw) + r'\b', '', topic, flags=re.IGNORECASE).strip()
            # Remove trailing prepositions
            topic = re.sub(r'\s+(in|on|at|the|a|an|into)\s*$', '', topic).strip()
        
        if not topic or len(topic) < 2:
            return "What topic should I write about? For example: 'write about artificial intelligence in this app'"
        
        # Execute: Research in background + Write into app
        return write_about_topic(topic, target_app=target_app, style=style, word_limit=word_limit)

    # Web & Research (Background Information - Voice only fallback)
    # Wikipedia-specific queries
    wiki_match = re.search(r'(?:search|open|look\s+up|find)\s+(?:on\s+)?(?:wikipedia|wiki)\s+(?:for\s+|about\s+)?(.+)', command)
    if not wiki_match:
        wiki_match = re.search(r'(?:wikipedia|wiki)\s+(?:and\s+)?(?:search|find|look\s+up)\s+(?:for\s+|about\s+)?(.+)', command)
    if not wiki_match:
        wiki_match = re.search(r'(.+?)\s+(?:on|in)\s+(?:wikipedia|wiki)', command)
    if wiki_match:
        topic = wiki_match.group(1).strip()
        # Clean the topic
        topic = re.sub(r'^(about|for|the|of)\s+', '', topic).strip()
        if topic:
            return researcher.search_and_summarize(topic)

    # Broad informational queries - "give me all info about X"
    info_request_patterns = [
        r'(?:give\s+me\s+)?(?:the\s+|all\s+|some\s+|detailed\s+)*information\s+(?:about|on|regarding|regarding|for)\s+(.+)',
        r'(?:collect|gather|find)\s+(?:information|data|details)\s+(?:from\s+online\s+platform\s+)?(?:about|on|regarding)\s+(.+)',
        r'(?:what\s+is|tell\s+me\s+about|explain|who\s+is|where\s+is|when\s+is|how\s+is)\s+(.+)',
        r'(?:janavo|mahiti\s+apo|જણાવો|માહિતી\s+આપો)\s+(.+)',
        r'(.+?)\s+(?:vise|vishe|vishe|વિશે)\s+(?:janavo|mahiti\s+apo|જણાવો|માહિતી\s+આપો|karo|કરો)'
    ]
    
    for pattern in info_request_patterns:
        match = re.search(pattern, command)
        if match:
            if 'time' not in command and 'date' not in command and 'weather' not in command and 'battery' not in command:
                topic = match.group(1).strip()
                # Clean the topic of common informational prefixes
                topic = re.sub(r'^(about|on|for|the|detailed|all|some|information|regarding|ise|vishe|vishe)\s+', '', topic).strip()
                if topic:
                    return researcher.search_and_summarize(topic)

    if any(word in command for word in ['who created you', 'who made you', 'your creator']):
        return "I was created by a team of developers to be your powerful voice assistant."

    # Handle pending confirmations
    if hasattr(route_command, "pending_action"):
        # English + Gujarati (હા, ચોક્કસ, બરાબર, કરી લો)
        yes_triggers = ['yes', 'confirm', 'do it', 'proceed', 'ha', 'હા', 'chokkas', 'barabar', 'kari lo', 'thase']
        # English + Gujarati (ના, રહેવા દો, બંધ કરો, કેન્સલ)
        no_triggers = ['no', 'cancel', 'stop', 'dont', 'don\'t', 'na', 'ના', 'rehwa do', 'reva do', 'nathi karvu']
        
        if any(word in command for word in yes_triggers):
            action = route_command.pending_action
            delattr(route_command, "pending_action")
            return action()
        elif any(word in command for word in no_triggers):
            if hasattr(route_command, "pending_action"):
                delattr(route_command, "pending_action")
            return "Operation cancelled."
        else:
            return "Please confirm by saying 'yes' or 'no'. (તમે હા અથવા ના કહીને કન્ફર્મ કરી શકો છો)"

    # ==========================================
    # TIME & DATE (Must be checked early before info_request patterns catch them)
    # ==========================================
    if re.search(r'\b(?:what\s+time|current\s+time|time\s+(?:right\s+)?now|kitna\s+baje|samay|સમય)\b', command) and 'timer' not in command:
        return task_handler.get_time()
    
    if re.search(r"\b(?:what(?:'s|\s+is)?\s+(?:today'?s?\s+)?date|today'?s?\s+date|current\s+date|tarikh|તારીખ)\b", command):
        return task_handler.get_date()

    # ==========================================
    # ALARM (Feature #3)
    # ==========================================
    if re.search(r'\b(?:set|create|make)\s+(?:an?\s+)?alarm\b', command):
        time_match = re.search(r'(?:for|at)\s+(\d{1,2}(?::\d{2})?\s*(?:am|pm)?)', command)
        alarm_time = time_match.group(1) if time_match else "the requested time"
        return f"Alarm set for {alarm_time}. I'll alert you when it's time."

    # ==========================================
    # TODO LIST (Feature #5 - TRAINING PHASE)
    # ==========================================
    if re.search(r'\b(?:add|create|put)\b.*?\b(?:todo|to-do|to\s+do\s+list|task\s+list)\b', command):
        task_match = re.search(r'\b(?:add|create|put)\s+(.+?)(?:\s+to\s+(?:my\s+)?(?:todo|to-do|to\s+do|task)\s*(?:list)?)', command)
        task_text = task_match.group(1) if task_match else command
        return f"[Training Phase] Todo added: '{task_text}'. The full todo system is under development."

    if re.search(r'\b(?:show|list|view|my)\s+(?:my\s+)?(?:todo|to-do|to\s+do|task)\s*(?:list|s)?\b', command):
        return "[Training Phase] Todo list feature is under development. Stay tuned!"

    # ==========================================
    # TYPE / WRITE TEXT INTO ACTIVE APP (Feature #6)
    # ==========================================
    if re.search(r'^(?:type|write)\s+(.+?)\s+(?:into|in)\s+(?:the\s+)?(?:active\s+app|current\s+(?:window|app))', command):
        text_match = re.search(r'^(?:type|write)\s+(.+?)\s+(?:into|in)', command)
        if text_match:
            text_to_type = text_match.group(1).strip()
            import time as _time
            _time.sleep(0.5)
            pyautogui.typewrite(text_to_type, interval=0.03)
            return f"Typed '{text_to_type}' into the active app."

    # ==========================================
    # SYSTEM HEALTH / CPU / RAM (Feature #8)
    # ==========================================
    if re.search(r'\b(?:cpu|ram|memory|system\s+health|system\s+status|resource|usage)\b', command):
        cpu = psutil.cpu_percent(interval=1)
        ram = psutil.virtual_memory()
        return f"CPU usage: {cpu}%. RAM usage: {ram.percent}% ({ram.used // (1024**3)}GB used of {ram.total // (1024**3)}GB total)."

    # ==========================================
    # BATTERY STATUS (Feature #9)
    # ==========================================
    if re.search(r'\b(?:battery|charge|charging|power\s+status)\b', command):
        battery = psutil.sensors_battery()
        if battery:
            status = "charging" if battery.power_plugged else "not charging"
            return f"Battery is at {battery.percent}%, {status}."
        return "Battery information is not available on this device."

    # ==========================================
    # SLEEP COMPUTER (Feature #12)
    # ==========================================
    if re.search(r'\b(?:sleep|hibernate)\b.*?\b(?:computer|laptop|system|pc|machine)\b', command) or \
       re.search(r'\b(?:computer|laptop|system|pc|machine)\b.*?\b(?:sleep|hibernate)\b', command):
        try:
            os.system('rundll32.exe powrprof.dll,SetSuspendState 0,1,0')
            return "Putting the computer to sleep."
        except Exception as e:
            return f"Error putting computer to sleep: {e}"

    # ==========================================
    # LOCK COMPUTER (Feature #13)
    # ==========================================
    if re.search(r'\block\b.*?\b(?:computer|laptop|system|pc|machine|screen)\b', command) or \
       re.search(r'\b(?:computer|laptop|system|pc|machine|screen)\b.*?\block\b', command):
        return system_control.lock_computer()

    # ==========================================
    # CLOSE ALL RUNNING APPS (Feature #14)
    # ==========================================
    if re.search(r'\bclose\s+all\b.*?\b(?:app|apps|application|running|window|windows)\b', command):
        route_command.pending_action = lambda: _close_all_apps()
        return "Are you sure you want to close all running apps? Say yes to confirm."

    # ==========================================
    # WHATSAPP MESSAGING (Feature #17 - TRAINING PHASE)
    # ==========================================
    if re.search(r'\b(?:whatsapp|whats\s*app)\b', command):
        return "[Training Phase] WhatsApp integration is under development. For now, I can open WhatsApp Web for you."

    # ==========================================
    # LANGUAGE TRANSLATION (Feature #18)
    # ==========================================
    if re.search(r'\btranslat(?:e|ion)\b', command):
        translate_match = re.search(r'translat(?:e|ion)\s+["\']?(.+?)["\']?\s+(?:to|into|in)\s+(\w+)', command)
        if translate_match:
            text_to_translate = translate_match.group(1).strip()
            target_lang = translate_match.group(2).strip()
            try:
                from googletrans import Translator
                translator = Translator()
                lang_map = {'gujarati': 'gu', 'hindi': 'hi', 'spanish': 'es', 'french': 'fr', 'german': 'de', 'japanese': 'ja', 'chinese': 'zh-cn', 'arabic': 'ar', 'korean': 'ko'}
                target_code = lang_map.get(target_lang.lower(), target_lang.lower())
                result = translator.translate(text_to_translate, dest=target_code)
                return f"Translation of '{text_to_translate}' to {target_lang}: {result.text}"
            except ImportError:
                return f"Translation feature requires the 'googletrans' package. Install it with: pip install googletrans==4.0.0-rc1"
            except Exception as e:
                return f"Translation error: {e}"
        return "Please specify what to translate and the target language. Example: 'translate hello to gujarati'"

    # ==========================================
    # CLOSE BROWSER TAB (Feature #19)
    # ==========================================
    if re.search(r'\bclose\b.*?\b(?:tab|browser\s+tab|this\s+tab|current\s+tab)\b', command):
        pyautogui.hotkey('ctrl', 'w')
        return "Closing the current browser tab."


    # NEWS HEADLINES (Feature #22)
    # ==========================================
    if re.search(r'\b(?:news|headline|headlines|latest\s+news|top\s+news|samachar|સમાચાર)\b', command):
        try:
            import webbrowser
            webbrowser.open("https://news.google.com")
            return "Opening Google News for the latest headlines."
        except Exception as e:
            return f"Error opening news: {e}"

    # ==========================================
    # DAILY BRIEFING / MORNING UPDATE (Feature #23)
    # ==========================================
    if re.search(r'\b(?:daily\s+briefing|morning\s+update|good\s+morning|day\s+summary|brief\s+me)\b', command):
        import datetime
        now = datetime.datetime.now()
        greeting = "Good morning" if now.hour < 12 else "Good afternoon" if now.hour < 17 else "Good evening"
        time_str = now.strftime("%I:%M %p")
        date_str = now.strftime("%B %d, %Y")
        cpu = psutil.cpu_percent(interval=0.5)
        ram = psutil.virtual_memory()
        battery = psutil.sensors_battery()
        batt_str = f"Battery: {battery.percent}%." if battery else ""
        return f"{greeting}! It's {time_str} on {date_str}. System: CPU {cpu}%, RAM {ram.percent}%. {batt_str} How can I help you today?"

    # ==========================================
    # WEATHER (Feature #25)
    # ==========================================
    if re.search(r'\b(?:weather|forecast|temperature|mausam|હવામાન)\b', command):
        city_match = re.search(r'(?:weather|forecast|temperature|mausam)\s+(?:in|of|for|at)?\s*(\w[\w\s]*)', command)
        city = city_match.group(1).strip() if city_match else "your location"
        try:
            import webbrowser
            webbrowser.open(f"https://www.google.com/search?q=weather+{city.replace(' ', '+')}")
            return f"Showing weather for {city}."
        except:
            return f"I don't have live weather data yet, but I'm opening the weather for {city}."

    # ==========================================
    # MAPS & NAVIGATION (Feature #26)
    # ==========================================
    if re.search(r'\b(?:navigate|navigation|directions|direction|route|map|maps|drive\s+to)\b', command):
        dest_match = re.search(r'(?:navigate|directions|direction|route|drive)\s+(?:to|from)?\s*(.+?)$', command)
        if dest_match:
            destination = dest_match.group(1).strip()
            import webbrowser
            webbrowser.open(f"https://www.google.com/maps/dir//{destination.replace(' ', '+')}")
            return f"Opening Google Maps with directions to {destination}."
        import webbrowser
        webbrowser.open("https://www.google.com/maps")
        return "Opening Google Maps."

    # "Open Google and search" pattern
    google_search_match = re.search(r'(?:open\s+google\s+and\s+search|google\s+and\s+search|open\s+google\s+and\s+find)\s+(?:for\s+|about\s+)?(.+)', command)
    if google_search_match:
        query = google_search_match.group(1).strip()
        if query:
            return web_browser.search_google(query)

    # Enhanced search extraction for English and Gujarati
    search_patterns = [
        # Gujarati: "python vise sodh", "google par python sodho"
        r'(.+?)\s*(?:વિશે|vise|vishe)\s*(?:શોધો|શોધ|sodh|shodh|shodho|search|તપાસો|tapasvo|karo|કરો)',
        r'(?:google|ગૂગલ)\s*(?:પર|par|per|ઉપર|upar)?\s*(.+?)\s*(?:વિશે|vise|vishe)?\s*(?:શોધો|શોધ|sodh|shodh|shodho|search|karo|કરો)?$',
        # English: "search python on google", "google python search", "search for python"
        r'search\s+(?:for\s+)?(.+?)\s+(?:on|in|at)\s+google',
        r'google\s+search\s+(?:for\s+)?(.+)',
        r'(?:search\s+for|google|look\s+up|find\s+information\s+on)\s+(.+)'
    ]
    
    for pattern in search_patterns:
        match = re.search(pattern, command)
        if match:
            query = match.group(1).strip()
            # Clean up query from common Gujarati/Hindi/English fillers
            fillers = [
                ' par', ' પર', ' upar', ' ઉપર', ' per', ' vise', ' vishe', ' વિશે', 
                ' sodh', ' શોધ', ' search', ' karo', ' કરો', ' open', ' wala', ' વાળો', ' song', ' video',
                ' nu', ' no', ' na', ' ni', ' નું', ' ના', ' નો', ' ની', # Gujarati possessives
                ' on google', ' in google', ' at google', ' google par', ' google per'
            ]
            for filler in fillers:
                if query.endswith(filler):
                    query = query[:-len(filler)].strip()
                if query.startswith(filler.strip()):
                    query = query[len(filler.strip()):].strip()
            
            if query:
                # If the user says "search [website] on google", open it
                if any(ext in query for ext in ['.com', '.org', '.net', '.edu']):
                    return web_browser.open_website(query)
                return web_browser.search_google(query)

    # Web Browser (Foreground - Opening Google Home)
    if re.search(r'open\s+google|search\s+google|google\s+search|open\s+search', command):
        return web_browser.open_google()
    
    # ==========================================
    # Application Control (Folders) — BEFORE media to avoid conflicts
    # ==========================================
    if re.search(r'\b(?:open|launch|kholo|ખોલો)\b.*?\b(folder|directory|documents|pictures|music|downloads|download|videos|video|desktop|file\s+explorer|explorer)\b', command):
        target = 'documents'
        if 'pictures' in command or 'photo' in command: target = 'pictures'
        elif 'music' in command or 'audio' in command: target = 'music'
        elif 'download' in command: target = 'downloads'
        elif 'video' in command: target = 'videos'
        elif 'desktop' in command: target = 'desktop'
        elif 'explorer' in command or 'folder' in command:
            try:
                os.startfile('explorer')
                return "Opening File Explorer"
            except: pass
            
        try:
            folder_path = str(Path.home() / target.capitalize())
            os.startfile(folder_path)
            return f"Opening your {target} folder"
        except: return f"I couldn't open the {target} folder"

    # ==========================================
    # Launch Apps — BEFORE media control to prevent "open X" going to Spotify
    # ==========================================
    # English + Gujarati (chrome kholo, notepad chalu karo)
    app_match = re.search(r'^(?:open|launch|start|run|chalu\s+karo|ચાલુ\s+કરો|kholo|ખોલો)\s+([a-zA-Z0-9\s]+)$', command)
    if not app_match:
        # Reverse pattern: "chrome chalu karo"
        app_match = re.search(r'^([a-zA-Z0-9\s]+)\s+(?:chalu\s+karo|ચાલુ\s+કરો|kholo|ખોલો|chalo\s+karo)$', command)
    
    if app_match:
        app = app_match.group(1).strip()
        # Only block specific words that are NOT applications
        blocked_words = ['listening', 'search', 'folder', 'directory', 'my', 'documents', 'pictures', 'downloads', 'download', 'music', 'explorer']
        app_words = set(app.lower().split())
        is_blocked = any(word in app_words for word in blocked_words)
        
        # EXCLUDE media-related words from being treated as app names
        media_indicators = ['song', 'video', 'music', 'geet', 'ganu', 'ગીત', 'વિડિયો', 'trending', 'play', 'vagad']
        is_media = any(word in app for word in media_indicators)
        
        # If user says "open youtube" or "open spotify", let it fall through to media/web handler
        media_platforms = ['youtube', 'spotify', 'google', 'સ્પોટિફાય', 'યુટ્યુબ']
        if not is_blocked and app not in media_platforms and not is_media:
            # Check known website names — open website instead of app
            known_websites = ['wikipedia', 'facebook', 'twitter', 'gmail', 'github', 'reddit', 
                              'instagram', 'linkedin', 'amazon', 'netflix', 'stackoverflow']
            if app in known_websites:
                return web_browser.open_website(app)
            return system_control.open_application(app)

    # ==========================================
    # Platform-Specific YouTube Controls
    # ==========================================
    # YouTube-specific commands (when user explicitly mentions YouTube)
    if 'youtube' in command or 'યુટ્યુબ' in command:
        # Next video on YouTube
        if any(word in command for word in ['next video', 'next youtube', 'skip video', 'agalnu video', 'આગળનું વિડિયો']):
            return system_control.youtube_next_video()
        # Previous video on YouTube
        if any(word in command for word in ['previous video', 'last video', 'pachalnu video', 'પાછળનું વિડિયો']):
            return system_control.youtube_previous_video()
        # Play/pause YouTube
        if any(word in command for word in ['pause youtube', 'play youtube', 'resume youtube', 'youtube pause', 'youtube play']):
            return system_control.youtube_play_pause()
        # Fullscreen YouTube
        if any(word in command for word in ['fullscreen', 'full screen', 'maximize video', 'ફુલ સ્ક્રીન']):
            return system_control.youtube_fullscreen()
        # Skip YouTube ad
        if any(word in command for word in ['skip ad', 'skip advertisement', 'skip the ad', 'ad skip', 'એડ સ્કીપ']):
            return system_control.youtube_skip_ad()
        # Mute/unmute YouTube
        if any(word in command for word in ['mute youtube', 'unmute youtube', 'youtube mute']):
            return system_control.youtube_mute_unmute()
        # Seek forward on YouTube
        if any(word in command for word in ['forward', 'seek forward', 'skip forward', 'fast forward', 'આગળ જાવ']):
            return system_control.youtube_seek_forward()
        # Seek backward on YouTube  
        if any(word in command for word in ['rewind', 'seek backward', 'go back', 'પાછળ જાવ']):
            return system_control.youtube_seek_backward()

    # ==========================================
    # Platform-Specific Spotify Controls
    # ==========================================
    # Spotify-specific commands (when user explicitly mentions Spotify)
    if 'spotify' in command or 'સ્પોટિફાય' in command:
        # Next track on Spotify
        if any(word in command for word in ['next song', 'next track', 'skip song', 'skip track', 'આગળનું ગીત']):
            return system_control.spotify_next_track()
        # Previous track on Spotify
        if any(word in command for word in ['previous song', 'previous track', 'last song', 'પાછળનું ગીત']):
            return system_control.spotify_previous_track()
        # Play/pause Spotify
        if any(word in command for word in ['pause spotify', 'play spotify', 'resume spotify', 'spotify pause', 'spotify play']):
            return system_control.spotify_play_pause()
        # Shuffle Spotify
        if any(word in command for word in ['shuffle', 'random', 'mix', 'શફલ']):
            return system_control.spotify_shuffle_toggle()
        # Repeat Spotify
        if any(word in command for word in ['repeat', 'loop', 'રીપીટ', 'લૂપ']):
            return system_control.spotify_repeat_toggle()



    # ==========================================
    # Media Control (Spotify / YouTube Search & Play)
    # Supporting English + Gujarati verbs + Aggressive Matching
    # NOTE: 'open' is NOT a media verb — "open calculator" should launch the app, not play on Spotify
    # ==========================================

    has_media_platform = any(p in command for p in ['youtube', 'spotify', 'યુટ્યુબ', 'સ્પોટિફાય'])
    has_media_type = any(t in command for t in ['song', 'video', 'music', 'geet', 'ganu', 'ગીત', 'વિડિયો', 'trending', 'dhun', 'bhajan'])
    # FIXED: Removed 'open' from media_verbs — it was causing "open calculator" to go to Spotify
    # Added 'chalu karo' and 'kholo' to media verbs for Gujarati support
    media_verbs = ['play', 'listen to', 'watch', 'vagad', 'vagado', 'vagaad', 'વગાડ', 'વગાડો', 'bagad', 'bagado', 'baja', 'bajado', 'chalu karo', 'ચાલુ કરો', 'kholo', 'ખોલો']
    has_media_verb = any(v in command for v in media_verbs)

    # Only trigger media control when:
    # 1. A media platform is mentioned (youtube/spotify) AND there's a verb or type
    # 2. OR a real media verb (play/watch/listen) is used — NOT "open"
    if (has_media_platform and (has_media_type or has_media_verb)) or (has_media_verb and not command.startswith('open ')):
        # Platform directed pattern ([platform] [item])
        # Try this first if platform is mentioned
        match = None
        media_suffixes = r'vagad|vagado|vagaad|વગાડ|વગાડો|bagad|bagado|baja|bajado|play|wala|વાળો|karo|કરો|song|video|music|geet|ganu|ગીત|વિડિયો'
        
        if has_media_platform:
            match = re.search(r'(?:youtube|spotify|યુટ્યુબ|સ્પોટિફાય)\s*(?:per|par|પર|upar|ઉપર|on)?\s*(?:search|play)?\s*(.+?)(?:\s*(?:' + media_suffixes + r'))*$', command)
        
        if not match:
            # Verb first pattern: "play malang on spotify", "play malang song"
            # FIXED: Removed 'open' and 'search' to prevent false matches
            match = re.search(r'(?:play|listen\s+to|watch|vagad|vagado|vagaad|વગાડ|વગાડો|bagad|bagado|baja|bajado)\s+(.+?)(?:\s+(?:on|per|par|પર|upar|ઉપર)\s+(?:spotify|youtube|સ્પોટિફાય|યુટ્યુબ))?$', command)
        
        if not match:
            # Verb last pattern ([item] vagad)
            match = re.search(r'^(.+?)\s*(?:on|per|par|પર|upar|ઉપર)?\s*(?:spotify|youtube)?\s*(?:' + media_suffixes + r')$', command)
        
        if match:
            query = match.group(1).strip()
            # Clean up query - remove platform names, media type words, fillers
            for platform in ['on spotify', 'on youtube', 'spotify', 'youtube', 'સ્પોટિફાય', 'યુટ્યુબ']:
                query = query.replace(platform, '').strip()
                
            # If the user literally wanted "song" or "video", don't remove it yet
            is_generic = query in ['song', 'video', 'music', 'play song', 'play video']
            
            # Remove filler words (only as standalone whole words, not partial matches)
            filler_words = [
                'the', 'koi', 'some', 'wala', 'વાળો', 'ka', 'kotha', 'na', 'nu', 'no', 'ni', 'નું', 'ના', 'નો', 'ની', 'ne', 'ને',
                'geet', 'ganu', 'ગીત', 'વિડિયો', 'video', 'song', 'music', 'dhun', 'bhajan', 'chalu', 'karo', 'kholo', 'vagad', 'vagado', 'vagaad', 'chalo'
            ]
            if not is_generic:
                for filler in filler_words:
                    query = re.sub(r'(?i)\b' + re.escape(filler) + r'\b', '', query).strip()
                
                # Strip trailing media type keywords again just in case
                query = re.sub(r'\s+(song|video|geet|ganu|music|trending|dhun|bhajan|chalu|karo|kholo)$', '', query).strip()

            if not query or query in ['music', 'song', 'video']: query = "trending songs"

            if 'youtube' in command or 'video' in command:
                from wizard.commands import web_browser
                return web_browser.search_youtube(query, auto_play=True)
            else:
                from wizard.commands import system_control
                return system_control.play_spotify_music(query)

    if 'play music' in command or 'start music' in command:
        return system_control.open_application('spotify')

    # ==========================================
    # General Playback Control (Smart Detection) — AFTER specific media search
    # ==========================================
    # Works globally for Spotify, YouTube, and any media player
    # Uses smart detection to pick the right method based on active app
    playback_commands = {
        'pause': ['pause', 'stop playing', 'stop music', 'stop song', 'stop video', 'thobho', 'atkao', 'થોભો', 'અટકાવો', 'બંધ કરો', 'પોઝ', 'rok', 'roko'],
        'resume': ['resume', 'continue', 'continue playing', 'start playing', 'chalu karo', 'ચાલુ કરો', 'પ્લે', 'phirse chalu'],
        'next': ['next song', 'next track', 'next video', 'skip', 'skip song', 'skip video', 'agalnu', 'agal', 'આગળનું', 'આગળ', 'નેક્સ્ટ', 'agle', 'agla'],
        'previous': ['previous song', 'previous track', 'previous video', 'last song', 'go back', 'pachalnu', 'પેલાનું', 'પાછળનું', 'પ્રીવિયસ', 'pichla', 'pichla song']
    }

    # Check pause first
    if any(word in command for word in playback_commands['pause']):
        if 'stop listening' not in command and 'sleep' not in command and 'stop assistant' not in command:
            return system_control.smart_play_pause()
            
    if any(word in command for word in playback_commands['resume']):
        return system_control.smart_play_pause()
    
    if any(phrase in command for phrase in playback_commands['next']) or command.strip() in ['next', 'skip', 'આગળ', 'agal']:
        return system_control.smart_next()
            
    if any(phrase in command for phrase in playback_commands['previous']) or command.strip() in ['previous', 'પાછળ', 'pachal', 'back']:
        return system_control.smart_previous()

    # Reminders
    if 'remind' in command:
        match = re.search(r'remind\s+me\s+to\s+(.+)', command)
        task = match.group(1).strip() if match else ""
        if task: return f"I'll remind you to {task}"
        return "What would you like me to remind you about?"

    # Basic Info (time/date already handled above, this is a fallback)
    if 'time' in command and 'timer' not in command: return task_handler.get_time()
    if 'date' in command: return task_handler.get_date()

    # Notepad & Text Editing (Manual typing)
    if any(word in command for word in ['open notepad', 'launch notepad']):
        return text_editor.open_notepad()
    
    if any(word in command for word in ['write', 'type', 'add', 'note']) and any(app in command for app in ['notepad', 'word', 'note']):
        # If it contains "about" or is a request for info, it should have been caught by research above.
        # This is for direct text input: "type Hello World in notepad"
        match = re.search(r'(?:write|type|add|note)\s+(.+)', command)
        if match:
            text = match.group(1).strip()
            text = re.sub(r'\s+in\s+(notepad|word|note)', '', text)
            if 'word' in command: return text_editor.write_in_word(text)
            return text_editor.write_in_notepad(text)

    # Notepad Fallback / Calculator
    if 'calculate' in command:
        match = re.search(r'calculate\s+(.+)', command)
        if match: return task_handler.calculate(match.group(1).strip())

    # Fallback to general search if no intent matched but sounds like a question
    if '?' in command_text or len(command.split()) > 3:
        return researcher.search_and_summarize(command)

    # Final Default response
    return "I'm not sure how to handle that command yet. I can open websites, search for info, play music, or help with system tasks. What specifically would you like me to do?"
