"""
AI Brain Module

This module implements the local AI brain with knowledge base, pattern-based
response generation, and conversation context management.
"""

import sqlite3
import json
import re
import random
import subprocess
import webbrowser
import urllib.parse
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
from pathlib import Path
import logging
from wizard.utils.language_manager import LanguageManager
from wizard.commands import text_editor, research_assistant
from wizard.utils.config_manager import ConfigManager

logger = logging.getLogger(__name__)


class AIBrain:
    """
    Local AI brain with knowledge base and conversation management
    """
    
    def __init__(self, db_path: str = "wizard/data/knowledge.db"):
        self.db_path = db_path
        self.context = {}
        self.conversation_history = []
        self.response_patterns = self._load_response_patterns()
        self.knowledge_facts = self._load_knowledge_facts()
        
        # Initialize database
        self._init_database()
        self._populate_initial_knowledge()
    
    def _init_database(self):
        """Initialize the SQLite database with required tables"""
        # Ensure directory exists
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Facts table for storing knowledge
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS facts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    category TEXT NOT NULL,
                    question TEXT NOT NULL,
                    answer TEXT NOT NULL,
                    confidence REAL DEFAULT 1.0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Conversations table for context management
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS conversations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT NOT NULL,
                    user_input TEXT NOT NULL,
                    assistant_response TEXT NOT NULL,
                    intent TEXT,
                    entities TEXT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # User preferences table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS user_preferences (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Response patterns table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS response_patterns (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    intent TEXT NOT NULL,
                    pattern TEXT NOT NULL,
                    response_template TEXT NOT NULL,
                    priority INTEGER DEFAULT 1,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            conn.commit()
            logger.info("Database initialized successfully")
    
    def _load_response_patterns(self) -> Dict[str, List[Dict]]:
        """Load response patterns for different intents (English and Gujarati only)"""
        return {
            "greeting": [
                {"pattern": r"hello|hi|hey|good morning|good afternoon|good evening", "responses": [
                    "Hello! How can I help you?",
                    "Hi there! What can I do for you?",
                    "Hey! I'm here to assist."
                ]},
                {"pattern": r"નમસ્તે|કેમ છો|કેમ લ્યા|kem cho|kemcho|namaste|kem lya", "lang": "gu", "responses": [
                    "નમસ્તે! હું તમારી શું help કરી શકું?",
                    "કેમ છો! I am here to help you. બોલો, શું કામ છે?",
                    "નમસ્તે! વિઝાર્ડ અહીં તમારી સહાય માટે ready છે."
                ]}
            ],
            "goodbye": [
                {"pattern": r"bye|goodbye|see you|farewell", "responses": [
                    "Goodbye! Have a great day!",
                    "See you later!",
                    "Take care!"
                ]},
                {"pattern": r"આવજો|ફરી મળીશું|aavjo|bye", "lang": "gu", "responses": [
                    "આવજો! તમારો day સારો રહે.",
                    "ફરી મળીશું! Take care."
                ]}
            ],
            "thanks": [
                {"pattern": r"thank you|thanks|appreciate", "responses": [
                    "You're welcome!",
                    "Happy to help!",
                    "No problem!"
                ]},
                {"pattern": r"આભાર|aabhar|dhanyavad|thanks", "lang": "gu", "responses": [
                    "તમારું welcome છે!",
                    "મદદ કરીને pleasure મળ્યો."
                ]}
            ],
            "what_time": [
                {"pattern": r"what time|current time|time is it", "responses": [
                    "It's {time} now.",
                    "The time is {time}."
                ]},
                {"pattern": r"કેટલા વાગ્યા|સમય શું છે|ટાઈમ શું થયો|હું થયો|ketla vagya|time shu thayo|hu thayo", "lang": "gu", "responses": [
                    "અત્યારે {time} વાગ્યા છે.",
                    "The time is {time}.",
                    "અત્યારે time {time} થયો છે."
                ]}
            ],
            "how_are_you": [
                {"pattern": r"how are you|how do you feel|are you okay", "responses": [
                    "I'm doing great! How are you?",
                    "I'm functioning perfectly. How can I assist?",
                    "All systems are good! What can I help with?"
                ]},
                {"pattern": r"કેમ છો|કેવું ચાલે છે|kem cho|kevu chale che", "lang": "gu", "responses": [
                    "હું મજામાં છું, આભાર! તમે કેમ છો?",
                    "બધું બરાબર છે. હું તમારી શું મદદ કરી શકું?"
                ]}
            ],
            "capabilities": [
                {"pattern": r"what can you do|help me|your capabilities", "responses": [
                    "I can help with info, calculations, system control, and more.",
                    "I'm here to assist with tasks, questions, and system operations."
                ]},
                {"pattern": r"તમે શું કરી શકો|તમે હું કરી શકો|મદદ કરો|tame shu kari sako|tame hu kari sako|help", "lang": "gu", "responses": [
                    "હું info શોધવા, calculations કરવા અને system control કરવામાં help કરી શકું છું.",
                    "હું તમારા ઘણા tasks માં help કરી શકું છું. બોલો, what can I do for you?"
                ]}
            ],
            "weather": [
                {"pattern": r"weather|temperature|forecast", "responses": [
                    "I don't have live weather data yet, but you can check your local app.",
                    "For weather, please check your local forecast."
                ]},
                {"pattern": r"હવામાન કેવું છે|તાપમાન", "lang": "gu", "responses": [
                    "મારી પાસે અત્યારે હવામાનની લાઈવ માહિતી નથી. કૃપા કરીને તમારી એપ્લિકેશન તપાસો."
                ]}
            ],
            "who_are_you": [
                {"pattern": r"who are you|your name", "responses": [
                    "I'm Wizard, your AI assistant.",
                    "My name is Wizard, here to help."
                ]},
                {"pattern": r"તમે કોણ છો|તમારું નામ", "lang": "gu", "responses": [
                    "હું વિઝાર્ડ છું, તમારો એઆઈ સહાયક.",
                    "મારું નામ વિઝાર્ડ છે, હું તમારી મદદ માટે છું."
                ]}
            ],
            "unknown": [
                {"pattern": r".*", "responses": [
                    "I'm not sure I understand. Could you rephrase?",
                    "I didn't catch that. Could you say it differently?"
                ]},
                {"pattern": r".*", "lang": "gu", "responses": [
                    "મને સમજાયું નથી. શું તમે ફરીથી કહી શકો?",
                    "હું સાંભળી શક્યો નથી. કૃપા કરીને સ્પષ્ટ કરો."
                ]}
            ]
        }
    
    def _load_knowledge_facts(self) -> Dict[str, List[Dict]]:
        """Load basic knowledge facts for the AI brain"""
        return {
            "definitions": [
                {"question": "what is artificial intelligence", "answer": "Artificial Intelligence (AI) is the simulation of human intelligence in machines that are programmed to think and learn like humans."},
                {"question": "what is machine learning", "answer": "Machine Learning is a subset of AI that enables computers to learn and improve from experience without being explicitly programmed."},
                {"question": "what is python", "answer": "Python is a high-level, interpreted programming language known for its simplicity and readability."},
                {"question": "what is windows", "answer": "Windows is a series of operating systems developed by Microsoft for personal computers and servers."},
                {"question": "what is voice assistant", "answer": "A voice assistant is an AI-powered software that can understand and respond to spoken commands and questions."},
                {"question": "what is natural language processing", "answer": "Natural Language Processing (NLP) is a branch of AI that helps computers understand, interpret and manipulate human language."},
            ],
            "science": [
                {"question": "speed of light", "answer": "The speed of light in a vacuum is approximately 299,792,458 meters per second."},
                {"question": "earth distance from sun", "answer": "Earth is approximately 93 million miles (150 million kilometers) away from the Sun."},
                {"question": "human body temperature", "answer": "Normal human body temperature is around 98.6°F (37°C)."},
                {"question": "gravity acceleration", "answer": "The acceleration due to gravity on Earth is approximately 9.8 meters per second squared."},
                {"question": "water boiling point", "answer": "Water boils at 100°C (212°F) at standard atmospheric pressure."},
                {"question": "water freezing point", "answer": "Water freezes at 0°C (32°F) at standard atmospheric pressure."},
            ],
            "mathematics": [
                {"question": "pi value", "answer": "Pi (π) is approximately 3.14159265359."},
                {"question": "golden ratio", "answer": "The golden ratio is approximately 1.618033988749."},
                {"question": "euler number", "answer": "Euler's number (e) is approximately 2.71828182846."},
                {"question": "square root of 2", "answer": "The square root of 2 is approximately 1.41421356237."},
            ],
            "history": [
                {"question": "when was the internet invented", "answer": "The Internet was developed in the late 1960s, with ARPANET being created in 1969."},
                {"question": "when was the first computer built", "answer": "The first electronic computer, ENIAC, was completed in 1946."},
                {"question": "when was world war 2", "answer": "World War II lasted from 1939 to 1945."},
                {"question": "when was the moon landing", "answer": "The first moon landing was on July 20, 1969, during the Apollo 11 mission."},
            ],
            "geography": [
                {"question": "tallest mountain", "answer": "Mount Everest is the tallest mountain in the world at 29,032 feet (8,849 meters)."},
                {"question": "largest ocean", "answer": "The Pacific Ocean is the largest ocean, covering about 46% of the world's water surface."},
                {"question": "largest country", "answer": "Russia is the largest country in the world by land area."},
                {"question": "smallest country", "answer": "Vatican City is the smallest country in the world."},
                {"question": "longest river", "answer": "The Nile River is generally considered the longest river in the world at about 4,135 miles."},
            ],
            "technology": [
                {"question": "what is the internet", "answer": "The Internet is a global network of interconnected computers that communicate using standardized protocols."},
                {"question": "what is wifi", "answer": "WiFi is a wireless networking technology that allows devices to connect to the internet without cables."},
                {"question": "what is bluetooth", "answer": "Bluetooth is a short-range wireless communication technology for connecting devices."},
                {"question": "what is cloud computing", "answer": "Cloud computing is the delivery of computing services over the internet, including storage, processing, and software."},
            ],
            "general_knowledge": [
                {"question": "how many days in a year", "answer": "There are 365 days in a regular year and 366 days in a leap year."},
                {"question": "how many hours in a day", "answer": "There are 24 hours in a day."},
                {"question": "how many minutes in an hour", "answer": "There are 60 minutes in an hour."},
                {"question": "how many seconds in a minute", "answer": "There are 60 seconds in a minute."},
                {"question": "how many continents", "answer": "There are 7 continents: Asia, Africa, North America, South America, Antarctica, Europe, and Australia."},
            ]
        }
    
    def _populate_initial_knowledge(self):
        """Populate the database with initial knowledge facts"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Check if facts already exist
            cursor.execute("SELECT COUNT(*) FROM facts")
            count = cursor.fetchone()[0]
            
            if count == 0:
                logger.info("Populating initial knowledge base...")
                
                for category, facts in self.knowledge_facts.items():
                    for fact in facts:
                        cursor.execute('''
                            INSERT INTO facts (category, question, answer, confidence)
                            VALUES (?, ?, ?, ?)
                        ''', (category, fact["question"], fact["answer"], 1.0))
                
                conn.commit()
                logger.info(f"Added {sum(len(facts) for facts in self.knowledge_facts.values())} facts to knowledge base")
    
    def process_query(self, query: str, context: Dict = None) -> str:
        """
        Process a user query and generate an appropriate response
        
        Args:
            query: User's question or statement
            context: Additional context information
            
        Returns:
            Generated response string
        """
        if context:
            self.context.update(context)
        
        # Detect language if not provided
        lang = self.context.get("detected_lang")
        if not lang:
            lang = LanguageManager.detect_language(query)
            self.context["detected_lang"] = lang
            
        query_lower = query.lower().strip()
        
        # Check master prompt logic first (broken features, emotional, future features, etc.)
        master_prompt_response = self._check_master_prompt_logic(query_lower)
        if master_prompt_response:
            self._store_conversation(query, master_prompt_response, "master_prompt_logic")
            return master_prompt_response
        
        # First try intelligent command processing for action-oriented queries
        intelligent_response = self._process_intelligent_command(query, query_lower)
        if intelligent_response:
            self._store_conversation(query, intelligent_response, "intelligent_command")
            return intelligent_response
        
        # Check for follow-up questions
        follow_up_response = self.handle_follow_up_question(query_lower)
        if follow_up_response:
            self._store_conversation(query, follow_up_response, "follow_up")
            return follow_up_response
        
        # Try to find a direct knowledge match
        knowledge_response = self._search_knowledge_base(query_lower)
        if knowledge_response:
            self._store_conversation(query, knowledge_response, "knowledge_lookup")
            return knowledge_response
        
        # Try pattern-based responses
        pattern_response = self._generate_pattern_response(query_lower, context)
        if pattern_response:
            self._store_conversation(query, pattern_response, context.get("intent", "pattern_match") if context else "pattern_match")
            return pattern_response
        
        # Generate contextual response
        contextual_response = self._generate_contextual_response(query_lower)
        
        # Apply dialect transformations if it's Gujarati
        final_response = self._apply_dialect(contextual_response if contextual_response else pattern_response)
        
        self._store_conversation(query, final_response, "processed")
        return final_response

    def _check_master_prompt_logic(self, query_lower: str) -> Optional[str]:
        """Check for specific conditions defined in the Master System Prompt"""
        
        # 1. Advanced / Developer Mode
        if "enable developer mode" in query_lower or "developer mode" in query_lower:
            return "Developer mode enabled.\nReasoning Steps: Active\nCommand Mapping: Exposed\nFallback Logic: Detailed"
            
        # 2. Learning Mode
        if "teach you a new command" in query_lower or "learn a new command" in query_lower:
            return "Learning mode activated. Please provide the trigger phrase, action mapping, and required parameters."
            
        # 3. Emotional Intelligence
        if any(phrase in query_lower for phrase in ["i feel sad", "i'm stressed", "i am sad", "i am stressed", "feeling down"]):
            return "I'm here for you. Do you want to talk about it or take a short breathing break?"
            
        # 4. Research & Writing Mode
        if "research" in query_lower and ("write" in query_lower or "report" in query_lower):
            return "Research Mode Activated.\n1. Searching for requested topic...\n2. Summarizing key findings...\n3. Structuring content...\n4. Formatting report clearly...\nWould you like to export the result when finished?"
            
        # 5. Future Features Awareness
        future_features = ["pdf reader", "ocr", "plugin system", "read pdf", "read this pdf"]
        if any(feature in query_lower for feature in future_features):
            return "This feature is planned in Phase X of development. Would you like me to simulate basic functionality?"
            
        # 6. Broken Features Handling / Maintenance
        broken_features = [
            "take notes", "take a note", "screenshot", "take a screenshot",
            "send email", "send an email", "calculator", "research assistant",
            "gujarati recognition issue", "emotional check-in", "memory recall"
        ]
        
        # Exception for actual calculator opening (which works via the app system) vs math solving
        if "calculator" in query_lower and not ("open" in query_lower or "launch" in query_lower):
            return "This feature is under maintenance. I am working on improving it."
            
        if any(feature in query_lower for feature in [f for f in broken_features if f != "calculator"]):
            return "This feature is under maintenance. I am working on improving it."
            
        return None

    def _apply_dialect(self, response: str) -> str:
        """Apply dialect-specific transformations to the response"""
        if not response:
            return response
            
        dialect = self.context.get("dialect")
        lang = self.context.get("detected_lang")
        
        if lang != 'gu' or not dialect:
            return response
            
        # Standard to Kathiyavadi mappings
        if dialect == 'kathiyavadi':
            mappings = {
                "શું": "હું", # shu -> hu
                "કેમ": "કેમ લ્યા", # kem -> kem lya
                "તમે": "તમે ભાઈ", # tame -> tame bhai
                "છે": "છે લ્યા", # che -> che lya (contextual)
            }
            for k, v in mappings.items():
                if k in response:
                    response = response.replace(k, v)
            
            # Suffixes
            if not any(word in response for word in ['ભાઈ', 'લ્યા']):
                response = response.rstrip('।. ') + " ભાઈ."
                
        # Standard to Surati mappings
        elif dialect == 'surati':
            if not any(word in response for word in ['લો', 'ને']):
                response = response.rstrip('।. ') + " લો."
        
        return response
    
    def _process_intelligent_command(self, original_query: str, query_lower: str) -> Optional[str]:
        """
        Intelligently process commands that require actions
        
        Args:
            original_query: Original user query with proper capitalization
            query_lower: Lowercase version for pattern matching
            
        Returns:
            Response string if command was processed, None otherwise
        """
        try:
            # Analyze command intent and entities
            intent = self._analyze_command_intent(query_lower)
            entities = self._extract_command_entities(original_query, query_lower)
            
            if intent == "open_application":
                return self._handle_open_command(entities, original_query)
            elif intent == "web_search":
                return self._handle_search_command(entities, original_query)
            elif intent == "system_action":
                return self._handle_system_command(entities, original_query)
            elif intent == "media_control":
                return self._handle_media_command(entities, original_query)
            elif intent == "productivity":
                return self._handle_productivity_command(entities, original_query)
            elif intent == "information_request":
                return self._handle_information_command(entities, original_query)
            
            return None
            
        except Exception as e:
            logger.error(f"Error in intelligent command processing: {e}")
            return None
    
    def _analyze_command_intent(self, query_lower: str) -> str:
        """Analyze the intent of a command with multilingual support"""
        
        # Application opening patterns
        if any(pattern in query_lower for pattern in [
            'open ', 'launch ', 'start ', 'run ', 'execute ', 'load ', 'ખોલો', 'ખોલ'
        ]):
            return "open_application"
        
        # Search patterns (En + Gu)
        if any(pattern in query_lower for pattern in [
            'search for', 'find ', 'look up', 'google ', 'browse for', 'research ', 'describe ',
            'શોધો', 'તપાસો', 'વિશે જણાવો', 'describe', 'research', 'shodho', 'tapasvo', 'janavo'
        ]):
            return "web_search"
        
        # System action patterns
        if any(pattern in query_lower for pattern in [
            'shutdown', 'restart', 'lock', 'sleep', 'hibernate', 'volume ', 'brightness',
            'અવાજ', 'પ્રકાશ', 'avaj'
        ]):
            return "system_action"
        
        # Aggressive Media control patterns (En + Gu + Transliterated Gu)
        # If it has (YouTube/Spotify) AND (Song/Video/Music/Play), it's media
        has_media_platform = any(p in query_lower for p in ['youtube', 'spotify', 'યુટ્યુબ', 'સ્પોટિફાય'])
        has_media_type = any(t in query_lower for t in ['song', 'video', 'music', 'geet', 'ganu', 'ગીત', 'વિડિયો', 'trending'])
        has_media_verb = any(v in query_lower for v in ['play', 'start', 'listen', 'watch', 'vagad', 'વગાડ', 'vagado', 'વગાડો', 'bagad', 'bagado', 'baja', 'bajado', 'open'])
        
        if (has_media_platform and (has_media_type or has_media_verb)) or has_media_verb or has_media_type:
            # Special case: "what is a song" should be an information request, not media
            if not any(q in query_lower for q in ['what is', 'explain', 'tell me about']):
                if has_media_verb or (has_media_platform and has_media_type):
                    return "media_control"
        
        # Productivity patterns
        if any(pattern in query_lower for pattern in [
            'remind me', 'set timer', 'set alarm', 'schedule', 'note', 'calendar', 'write', 'type',
            'લખો', 'નોંધ', 'યાદ કરાવો', 'remind', 'timer', 'alarm'
        ]):
            return "productivity"
        
        # Information request patterns
        if any(re.search(r'\b' + pattern + r'\b', query_lower) for pattern in [
            'what is', 'tell me about', 'explain', 'how does', 'why does', 'when is', 'information about', 'information on',
            'શું છે', 'ક્યારે', 'કોણ', 'shu che', 'su che', 'mahiti', 'janavo'
        ]) or (re.search(r'\bકેમ\b', query_lower) and 'છો' not in query_lower) or any(q in query_lower for q in ['janavo', 'znavo', 'batavo', 'mahiti', 'information']):
            return "information_request"
        
        return "unknown"
        
        return "unknown"
    
    def _extract_command_entities(self, original_query: str, query_lower: str) -> Dict[str, Any]:
        """Extract entities from the command"""
        entities = {}
        
        # Extract application names
        app_keywords = {
            'browser': ['chrome', 'firefox', 'edge', 'safari', 'browser', 'internet'],
            'music': ['spotify', 'music', 'itunes', 'media player', 'songs'],
            'calculator': ['calculator', 'calc', 'math'],
            'notepad': ['notepad', 'text editor', 'notes'],
            'email': ['outlook', 'mail', 'email', 'gmail'],
            'video': ['youtube', 'videos', 'vlc'],
            'social': ['facebook', 'twitter', 'instagram', 'linkedin'],
            'office': ['word', 'excel', 'powerpoint', 'office'],
            'chat': ['discord', 'slack', 'teams', 'whatsapp']
        }
        
        for category, keywords in app_keywords.items():
            for keyword in keywords:
                if keyword in query_lower:
                    entities['application'] = keyword
                    entities['app_category'] = category
                    break
        
        # Extract search terms with support for Gujarati word order
        search_term = ""
        # Try Gujarati patterns first
        # Pattern like "python vishe sodh"
        gu_match = re.search(r'(.+?)\s*(?:વિશે|vise|vishe)\s*(?:શોધો|શોધ|sodh|shodh|shodho|search|તપાસો|tapasvo|karo|કરો)', query_lower)
        if gu_match:
            search_term = original_query[:gu_match.end(1)].strip()
        else:
            # Pattern like "google par python sodho"
            gu_match2 = re.search(r'(?:google|ગૂગલ)\s*(?:પર|par|per|ઉપર|upar)?\s*(.+?)(?:\s*(?:વિશે|vise|vishe)?\s*(?:શોધો|શોધ|sodh|shodh|shodho|search|karo|કરો))?$', query_lower)
            if gu_match2:
                search_term = original_query[gu_match2.start(1):gu_match2.end(1)].strip()
            else:
                # English patterns
                search_triggers = ['search for', 'find', 'look up', 'google', 'browse for']
                for trigger in search_triggers:
                    if trigger in query_lower:
                        start_idx = query_lower.find(trigger) + len(trigger)
                        search_term = original_query[start_idx:].strip()
                        break
        
            # Final clean up for search term
            if search_term:
                # Remove leading/trailing Gujarati particles and possessives
                particles = [
                    ' par', ' પર', ' upar', ' ઉપર', ' vise', ' vishe', ' વિશે', ' sodh', ' શોધ',
                    ' nu', ' no', ' na', ' ni', ' નું', ' ના', ' નો', ' ની'
                ]
                for particle in particles:
                    if search_term.lower().endswith(particle):
                        search_term = search_term[:-len(particle)].strip()
                    if search_term.lower().startswith(particle.strip()):
                        search_term = search_term[len(particle.strip()):].strip()
            
            entities['search_term'] = search_term
        
        # Extract time-related entities
        time_patterns = [
            r'(\d+)\s*(minute|minutes|hour|hours|second|seconds)',
            r'in\s+(\d+)\s*(minute|minutes|hour|hours)',
            r'for\s+(\d+)\s*(minute|minutes|hour|hours)'
        ]
        
        for pattern in time_patterns:
            match = re.search(pattern, query_lower)
            if match:
                entities['time_value'] = match.group(1)
                entities['time_unit'] = match.group(2)
                break
        
        # Extract reminder text
        reminder_patterns = [
            r'remind me to (.+)',
            r'reminder to (.+)',
            r'set reminder (.+)'
        ]
        
        for pattern in reminder_patterns:
            match = re.search(pattern, query_lower)
            if match:
                entities['reminder_text'] = match.group(1)
                break
        
        return entities
    
    def _handle_open_command(self, entities: Dict, original_query: str) -> str:
        """Handle application opening commands"""
        app = entities.get('application', '')
        category = entities.get('app_category', '')
        
        if not app and not category:
            # Try to extract app name from the query
            words = original_query.lower().split()
            if 'open' in words:
                open_idx = words.index('open')
                if open_idx + 1 < len(words):
                    app = words[open_idx + 1]
            elif 'launch' in words:
                launch_idx = words.index('launch')
                if launch_idx + 1 < len(words):
                    app = words[launch_idx + 1]
        
        if app or category:
            # Actually open the application
            try:
                result = self._open_application(app or category)
                return result
            except Exception as e:
                return f"I tried to open {app or category} but encountered an issue: {e}"
        else:
            return "I'd be happy to open an application for you! Which application would you like me to open?"
    
    def _open_application(self, app_name: str) -> str:
        """Internal method to open applications and websites"""
        try:
            # Web platforms and URLs
            web_platforms = {
                'google': 'https://www.google.com',
                'youtube': 'https://www.youtube.com',
                'facebook': 'https://www.facebook.com',
                'twitter': 'https://www.twitter.com',
                'instagram': 'https://www.instagram.com',
                'linkedin': 'https://www.linkedin.com',
                'github': 'https://www.github.com',
                'stackoverflow': 'https://stackoverflow.com',
                'reddit': 'https://www.reddit.com',
                'netflix': 'https://www.netflix.com',
                'amazon': 'https://www.amazon.com',
                'gmail': 'https://mail.google.com',
                'outlook': 'https://outlook.live.com',
                'whatsapp': 'https://web.whatsapp.com',
                'discord': 'https://discord.com/app',
                'spotify': 'https://open.spotify.com',
                'news': 'https://news.google.com',
                'weather': 'https://weather.com',
                'browser': 'https://www.google.com',
                'internet': 'https://www.google.com'
            }
            
            # Desktop applications
            app_mappings = {
                'calculator': 'calc',
                'calc': 'calc',
                'notepad': 'notepad',
                'text editor': 'notepad',
                'paint': 'mspaint',
                'chrome': 'chrome',
                'google chrome': 'chrome',
                'firefox': 'firefox',
                'edge': 'msedge',
                'microsoft edge': 'msedge',
                'explorer': 'explorer',
                'file explorer': 'explorer',
                'file manager': 'explorer',
                'cmd': 'cmd',
                'command prompt': 'cmd',
                'powershell': 'powershell',
                'word': 'winword',
                'excel': 'excel',
                'powerpoint': 'powerpnt'
            }
            
            app_lower = app_name.lower().strip()
            
            # Check if it's a web platform
            if app_lower in web_platforms:
                webbrowser.open(web_platforms[app_lower])
                return f"Opening {app_name} in your default browser..."
            
            # Check for partial matches in web platforms
            for platform, url in web_platforms.items():
                if platform in app_lower or app_lower in platform:
                    webbrowser.open(url)
                    return f"Opening {platform} in your default browser..."
            
            # Handle desktop applications
            app_command = app_mappings.get(app_lower, app_name)
            
            # Try to open desktop application
            subprocess.Popen(app_command, shell=True)
            return f"Opening {app_name}..."
            
        except Exception as e:
            return f"I couldn't open {app_name}. Error: {e}"
    
    def _handle_search_command(self, entities: Dict, original_query: str) -> str:
        """Handle web search commands"""
        search_term = entities.get('search_term', '')
        
        if not search_term:
            # Try to extract search term differently
            query_lower = original_query.lower()
            if 'search' in query_lower:
                parts = original_query.split('search', 1)
                if len(parts) > 1:
                    search_term = parts[1].strip()
                    # Remove common prefixes
                    for prefix in ['for ', 'about ', 'on ']:
                        if search_term.startswith(prefix):
                            search_term = search_term[len(prefix):]
                            break
        
        if search_term:
            # Actually perform the search
            try:
                return self._perform_web_search(search_term)
            except Exception as e:
                return f"I tried to search for '{search_term}' but encountered an issue: {e}"
        else:
            return "What would you like me to search for?"
    
    def _perform_web_search(self, query: str) -> str:
        """Internal method to perform web searches"""
        try:
            if not query.strip():
                return "What would you like me to search for?"
            
            # Create Google search URL
            search_url = f"https://www.google.com/search?q={urllib.parse.quote(query)}"
            webbrowser.open(search_url)
            
            return f"Searching Google for '{query}'..."
            
        except Exception as e:
            return f"I couldn't perform the search: {e}"
    
    def _handle_system_command(self, entities: Dict, original_query: str) -> str:
        """Handle system control commands"""
        query_lower = original_query.lower()
        
        if 'volume' in query_lower:
            if 'up' in query_lower or 'increase' in query_lower:
                return "I'll increase the system volume for you."
            elif 'down' in query_lower or 'decrease' in query_lower:
                return "I'll decrease the system volume for you."
            else:
                return "I can help you adjust the volume. Try saying 'volume up' or 'volume down'."
        
        elif any(word in query_lower for word in ['shutdown', 'turn off', 'બંધ કર', 'બંધ કરો', 'shut down']):
            from wizard.commands.command_router import route_command
            from wizard.commands import system_control
            # Set pending action in command_router so "yes" works
            route_command.pending_action = lambda: system_control.shutdown_computer()
            return "Are you sure you want to shut down the computer? Say yes to confirm."
        
        elif any(word in query_lower for word in ['restart', 'રીસ્ટાર્ટ', 'ફરી ચાલુ કરો']):
            from wizard.commands.command_router import route_command
            from wizard.commands import system_control
            route_command.pending_action = lambda: system_control.restart_computer()
            return "Are you sure you want to restart the computer? Say yes to confirm."
        
        else:
            return "I can help with system controls like volume adjustment. What would you like me to do?"
    
    def _handle_media_command(self, entities: Dict, original_query: str) -> str:
        """Handle media control commands with improved Gujarati support"""
        query_lower = original_query.lower()
        
        play_verbs = ['play', 'start', 'listen to', 'watch', 'vagad', 'vagado', 'vagaad', 'વગાડ', 'વગાડો', 'bagad', 'bagado', 'baja', 'bajado']
        
        if any(word in query_lower for word in play_verbs):
            item = ""
            platform = ""
            
            # Detect platform
            if 'youtube' in query_lower or 'video' in query_lower:
                platform = 'youtube'
            elif 'spotify' in query_lower or 'music' in query_lower or 'song' in query_lower or 'geet' in query_lower:
                platform = 'spotify'
            else:
                platform = 'spotify' # Default
                
            # Improved extraction (Sync with Command Router)
            match = None
            media_suffixes = r'vagad|vagado|vagaad|વગાડ|વગાડો|bagad|bagado|baja|bajado|play|wala|વાળો|karo|કરો|song|video|music|geet|ganu|ગીત|વિડિયો'
            
            if platform == 'youtube' or 'youtube' in query_lower:
                match = re.search(r'(?:youtube|spotify|યુટ્યુબ|સ્પોટિફાય)\s*(?:per|par|પર|upar|ઉપર|on)?\s*(?:open|search|play)?\s*(.+?)(?:\s*(?:' + media_suffixes + r'))*$', query_lower)
            
            if not match:
                match = re.search(r'(?:play|listen\s+to|watch|start|vagad|vagado|vagaad|વગાડ|વગાડો|bagad|bagado|baja|bajado|open|search)\s+(?:a\s+song|music|the\s+video|the\s+song)?\s*(.+?)(?:\s+on|per|par|પર|upar|ઉપર)?\s*(?:spotify|youtube)?$', query_lower)
            
            if not match:
                match = re.search(r'^(.+?)\s*(?:on|per|par|પર|upar|ઉપર)?\s*(?:spotify|youtube)?\s*(?:' + media_suffixes + r')$', query_lower)

            if match:
                item = match.group(1).strip()
            else:
                item = query_lower
                for verb in play_verbs: item = item.replace(verb, '')
                for p in ['spotify', 'youtube', 'per', 'par', 'પર', 'upar', 'ઉપર', 'on']: item = item.replace(p, '')
                item = item.strip()

            # Clean up the extracted item (Advanced)
            media_fillers = [
                ' a ', ' the ', ' koi ', ' some ', ' trending ', ' song ', ' video ', ' geet ', 
                ' ganu ', ' open ', ' search ', ' wala ', ' વાળો ', ' ka ', ' kotha ', 
                ' nu ', ' no ', ' na ', ' ni ', ' નું ', ' ના ', ' નો ', ' ની ', ' ne ', ' ને '
            ]
            for filler in media_fillers:
                item = re.sub(r'(?i)\b' + re.escape(filler.strip()) + r'\b', '', item).strip()
            
            # Final specific cleanup
            if item.startswith("open "): item = item[5:].strip()
            if item.endswith(" wala"): item = item[:-5].strip()
            # Remove trailing possessives again just in case
            item = re.sub(r'\s+(nu|no|na|ni|નું|ના|નો|ની|ne|ને)$', '', item).strip()

            if not item or item in ['music', 'song', 'video', 'something']:
                item = "trending songs" # Default to trending if nothing specific

            if platform == 'youtube':
                from wizard.commands import web_browser
                web_browser.search_youtube(item, auto_play=True)
                return f"Playing {item} on YouTube for you."
            else:
                from wizard.commands import system_control
                system_control.play_spotify_music(item)
                return f"Playing {item} on Spotify for you."
        
        elif 'pause' in query_lower:
            return "I'll pause the current media playback."
        
        elif 'stop' in query_lower:
            return "I'll stop the current media playback."
        
        elif any(word in query_lower for word in ['next', 'skip']):
            return "I'll skip to the next track."
        
        elif 'previous' in query_lower:
            return "I'll go back to the previous track."
        
        else:
            return "I can help control media playback. Try saying 'play music', 'pause', 'next song', or 'previous song'."
    
    def _handle_productivity_command(self, entities: Dict, original_query: str) -> str:
        """Handle productivity commands"""
        time_value = entities.get('time_value')
        time_unit = entities.get('time_unit')
        reminder_text = entities.get('reminder_text')
        
        query_lower = original_query.lower()
        
        if 'timer' in query_lower and time_value and time_unit:
            return f"I'll set a {time_value} {time_unit} timer for you."
        
        elif 'remind' in query_lower:
            if reminder_text:
                return f"I'll set a reminder for you: {reminder_text}"
            else:
                return "What would you like me to remind you about?"
        
        elif any(word in query_lower for word in ['write', 'type', 'describe', 'research', 'search online', 'lakho', 'લખો', 'vishe', 'વિશે']):
            # Match "write about X in word", "describe X in notepad", etc.
            match = re.search(r'(?:write|type|describe|research|search)\s+(?:about\s+|on\s+)?(.+?)(?:\s+in\s+(word|notepad|note))(?:\s+file)?$', query_lower)
            
            # Match Gujarati word order: "Topic vishe Word ma lakho" (transliterated or script)
            if not match:
                match = re.search(r'(.+?)\s+(?:vishe|વિશે)\s+(word|notepad|note)\s+(?:ma|માં)\s+(?:lakho|લખો)', query_lower)
            
            if match:
                topic = match.group(1).strip()
                target_app = match.group(2)
                
                config = ConfigManager()
                researcher = research_assistant.ResearchAssistant(config, logger)
                summary = researcher.search_and_summarize(topic)
                
                if not summary or "didn't find" in summary.lower() or "error" in summary.lower():
                    return f"I researched {topic} but couldn't find a good summary to write down."
                
                if 'word' in target_app:
                    text_editor.write_in_word(summary)
                    return f"I've researched {topic} and written it in Microsoft Word for you."
                else:
                    text_editor.write_in_notepad(summary)
                    return f"I've researched {topic} and written it in Notepad for you."
            
            return "I can help you take notes or write descriptions of topics in Word. What would you like me to write?"
            
        else:
            return "I can help with productivity tasks like setting timers, reminders, and writing documents. What would you like to do?"
            
    
    def _handle_information_command(self, entities: Dict, original_query: str) -> str:
        """Handle information request commands"""
        query_lower = original_query.lower()
        
        # Check if it's asking about a specific topic
        if 'what is' in query_lower:
            topic = original_query.lower().replace('what is', '').strip()
            if topic:
                return f"Let me tell you about {topic}. {self._get_topic_information(topic)}"
        
        elif 'tell me about' in query_lower:
            topic = original_query.lower().replace('tell me about', '').strip()
            if topic:
                return f"Here's what I know about {topic}: {self._get_topic_information(topic)}"
        
        elif 'explain' in query_lower:
            topic = original_query.lower().replace('explain', '').strip()
            if topic:
                return f"Let me explain {topic}: {self._get_topic_information(topic)}"
        
        # Fallback to general information response
        return "I'd be happy to provide information! What specific topic would you like to know about?"
    
    def _get_topic_information(self, topic: str) -> str:
        """Get information about a specific topic"""
        topic_lower = topic.lower().strip()
        
        # Basic topic information
        topic_info = {
            'artificial intelligence': "Artificial Intelligence (AI) is the simulation of human intelligence in machines that are programmed to think and learn like humans.",
            'machine learning': "Machine Learning is a subset of AI that enables computers to learn and improve from experience without being explicitly programmed.",
            'python': "Python is a high-level, interpreted programming language known for its simplicity and readability, widely used in web development, data science, and AI.",
            'programming': "Programming is the process of creating instructions for computers to execute, involving writing code in various programming languages.",
            'computer': "A computer is an electronic device that processes data according to instructions, capable of storing, retrieving, and processing information.",
            'internet': "The Internet is a global network of interconnected computers that communicate using standardized protocols, enabling worldwide information sharing.",
            'technology': "Technology refers to the application of scientific knowledge for practical purposes, including tools, machines, and systems that solve problems."
        }
        
        # Check for direct matches
        for key, info in topic_info.items():
            if key in topic_lower:
                return info
        
        # Check for partial matches
        for key, info in topic_info.items():
            if any(word in topic_lower for word in key.split()):
                return info
        
        return "That's an interesting topic! I'd recommend searching for more detailed information online or consulting relevant resources."
    
    def _search_knowledge_base(self, query: str) -> Optional[str]:
        """Search the knowledge base for relevant information"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Direct question match
            cursor.execute('''
                SELECT answer, confidence FROM facts 
                WHERE LOWER(question) LIKE ? 
                ORDER BY confidence DESC 
                LIMIT 1
            ''', (f"%{query}%",))
            
            result = cursor.fetchone()
            if result:
                return result[0]
            
            # Keyword-based search
            keywords = query.split()
            for keyword in keywords:
                if len(keyword) > 3:  # Skip short words
                    cursor.execute('''
                        SELECT answer, confidence FROM facts 
                        WHERE LOWER(question) LIKE ? OR LOWER(answer) LIKE ?
                        ORDER BY confidence DESC 
                        LIMIT 1
                    ''', (f"%{keyword}%", f"%{keyword}%"))
                    
                    result = cursor.fetchone()
                    if result:
                        return result[0]
        
        return None
    
    def _generate_pattern_response(self, query: str, context: Dict = None) -> Optional[str]:
        """Generate response based on pattern matching with language support"""
        provided_intent = context.get("intent") if context else None
        lang = self.context.get("detected_lang", "en")
        
        # If intent is provided, only look at that intent
        if provided_intent and provided_intent != "unknown":
            intents_to_check = [provided_intent]
        else:
            # Otherwise check all available intents (priority order)
            intents_to_check = list(self.response_patterns.keys())
            # Ensure 'unknown' is last
            if "unknown" in intents_to_check:
                intents_to_check.remove("unknown")
                intents_to_check.append("unknown")

        for intent in intents_to_check:
            patterns = self.response_patterns.get(intent, [])
            
            # Filter by language
            lang_patterns = [p for p in patterns if p.get("lang") == lang]
            if not lang_patterns and lang != 'en':
                lang_patterns = [p for p in patterns if not p.get("lang")]
            elif not lang_patterns:
                lang_patterns = patterns

            for pattern_info in lang_patterns:
                pattern = pattern_info["pattern"]
                if re.search(pattern, query, re.IGNORECASE):
                    responses = pattern_info["responses"]
                    response = random.choice(responses)
                    
                    # Fill in template variables
                    response = self._fill_response_template(response, context)
                    # Update context with the matched intent
                    if context is not None:
                        context["intent"] = intent
                    return response
        
        return None
    
    def _fill_response_template(self, template: str, context: Dict = None) -> str:
        """Fill response template with dynamic values"""
        if context is None:
            context = {}
        
        # Current time and date
        now = datetime.now()
        template = template.replace("{time}", now.strftime("%I:%M %p"))
        template = template.replace("{date}", now.strftime("%A, %B %d, %Y"))
        
        # User preferences
        user_name = self.get_user_preference("name", "User")
        template = template.replace("{name}", user_name)
        
        # Context variables
        for key, value in context.items():
            template = template.replace(f"{{{key}}}", str(value))
        
        return template
    
    def _generate_contextual_response(self, query: str) -> str:
        """Generate a contextual response when no patterns match"""
        # Check conversation history for context
        recent_conversations = self._get_recent_conversations(5)
        
        # Handle follow-up questions
        if recent_conversations:
            last_conversation = recent_conversations[0]
            last_intent = last_conversation.get("intent", "")
            
            # Handle follow-up patterns
            if any(word in query for word in ["more", "tell me more", "continue", "elaborate"]):
                if last_intent == "knowledge_lookup":
                    return "I've shared what I know about that topic. Is there something specific you'd like to know more about?"
                return "What would you like me to elaborate on?"
            
            if any(word in query for word in ["why", "how", "explain"]):
                if last_intent == "knowledge_lookup":
                    return "That's an interesting follow-up question. Let me see if I have more detailed information about that."
        
        # Simple contextual responses based on query type
        if any(word in query for word in ["calculate", "math", "compute", "solve"]):
            return "I can help with calculations. Try asking me to calculate something specific like '2 plus 2' or 'square root of 16'."
        
        if any(word in query for word in ["open", "launch", "start", "run"]):
            return "I can help you open applications. Try saying 'open' followed by the application name like 'open notepad' or 'open calculator'."
        
        if any(word in query for word in ["play", "music", "song", "audio"]):
            return "I can help control music playback. Try saying 'play music', 'pause', 'next song', or 'previous song'."
        
        if any(word in query for word in ["weather", "temperature", "forecast"]):
            return "For weather information, I recommend checking your local weather app or website. I don't have access to current weather data."
        
        if any(word in query for word in ["time", "clock"]):
            now = datetime.now()
            return f"The current time is {now.strftime('%I:%M %p')}"
        
        if any(word in query for word in ["date", "today", "calendar"]):
            now = datetime.now()
            return f"Today is {now.strftime('%A, %B %d, %Y')}"
        
        if any(word in query for word in ["file", "folder", "document", "search"]):
            return "I can help you manage files and folders. Try asking me to 'find files' or 'search for documents'."
        
        if any(word in query for word in ["reminder", "remind", "alarm", "timer"]):
            return "I can help you set reminders and timers. Try saying 'set a timer for 5 minutes' or 'remind me to call John at 3 PM'."
        
        if any(word in query for word in ["joke", "funny", "laugh", "humor"]):
            jokes = [
                "Why don't scientists trust atoms? Because they make up everything!",
                "Why did the scarecrow win an award? He was outstanding in his field!",
                "Why don't eggs tell jokes? They'd crack each other up!",
                "What do you call a fake noodle? An impasta!"
            ]
            return random.choice(jokes)
        
        if any(word in query for word in ["fact", "interesting", "trivia", "knowledge"]):
            facts = [
                "Honey never spoils. Archaeologists have found pots of honey in ancient Egyptian tombs that are over 3,000 years old and still perfectly edible.",
                "A group of flamingos is called a 'flamboyance'.",
                "Bananas are berries, but strawberries aren't.",
                "The shortest war in history was between Britain and Zanzibar on August 27, 1896. Zanzibar surrendered after 38 minutes.",
                "Octopuses have three hearts and blue blood.",
                "A day on Venus is longer than its year."
            ]
            return random.choice(facts)
        
        # Check if this might be a follow-up to a previous conversation
        if len(query.split()) <= 3 and recent_conversations:
            return "Could you be more specific? I want to make sure I understand what you're asking about."
        
        # Default response
        return "I'm not sure how to help with that. Could you try rephrasing your question or asking about something specific like time, calculations, or general information?"
    
    def _store_conversation(self, user_input: str, assistant_response: str, intent: str = "unknown"):
        """Store conversation in the database"""
        session_id = self.context.get("session_id", "default")
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO conversations (session_id, user_input, assistant_response, intent, entities)
                VALUES (?, ?, ?, ?, ?)
            ''', (session_id, user_input, assistant_response, intent, json.dumps(self.context)))
            conn.commit()
    
    def _get_recent_conversations(self, limit: int = 10) -> List[Dict]:
        """Get recent conversations for context"""
        session_id = self.context.get("session_id", "default")
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT user_input, assistant_response, intent, entities, timestamp
                FROM conversations 
                WHERE session_id = ?
                ORDER BY timestamp DESC 
                LIMIT ?
            ''', (session_id, limit))
            
            conversations = []
            for row in cursor.fetchall():
                conversations.append({
                    "user_input": row[0],
                    "assistant_response": row[1],
                    "intent": row[2],
                    "entities": json.loads(row[3]) if row[3] else {},
                    "timestamp": row[4]
                })
            
            return conversations
    
    def update_context(self, key: str, value: Any) -> None:
        """Update conversation context"""
        self.context[key] = value
        logger.debug(f"Updated context: {key} = {value}")
    
    def get_context(self, key: str, default: Any = None) -> Any:
        """Get value from conversation context"""
        return self.context.get(key, default)
    
    def clear_context(self) -> None:
        """Clear conversation context"""
        self.context.clear()
        logger.info("Conversation context cleared")
    
    def add_knowledge_fact(self, category: str, question: str, answer: str, confidence: float = 1.0) -> bool:
        """
        Add a new fact to the knowledge base
        
        Args:
            category: Category of the fact
            question: Question or topic
            answer: Answer or information
            confidence: Confidence score (0.0 to 1.0)
            
        Returns:
            True if successful, False otherwise
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO facts (category, question, answer, confidence)
                    VALUES (?, ?, ?, ?)
                ''', (category, question, answer, confidence))
                conn.commit()
                logger.info(f"Added knowledge fact: {question}")
                return True
        except Exception as e:
            logger.error(f"Error adding knowledge fact: {e}")
            return False
    
    def search_facts(self, query: str, category: str = None) -> List[Dict]:
        """
        Search for facts in the knowledge base
        
        Args:
            query: Search query
            category: Optional category filter
            
        Returns:
            List of matching facts
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            if category:
                cursor.execute('''
                    SELECT id, category, question, answer, confidence
                    FROM facts 
                    WHERE category = ? AND (LOWER(question) LIKE ? OR LOWER(answer) LIKE ?)
                    ORDER BY confidence DESC
                ''', (category, f"%{query.lower()}%", f"%{query.lower()}%"))
            else:
                cursor.execute('''
                    SELECT id, category, question, answer, confidence
                    FROM facts 
                    WHERE LOWER(question) LIKE ? OR LOWER(answer) LIKE ?
                    ORDER BY confidence DESC
                ''', (f"%{query.lower()}%", f"%{query.lower()}%"))
            
            facts = []
            for row in cursor.fetchall():
                facts.append({
                    "id": row[0],
                    "category": row[1],
                    "question": row[2],
                    "answer": row[3],
                    "confidence": row[4]
                })
            
            return facts
    
    def get_user_preference(self, key: str, default: Any = None) -> Any:
        """Get user preference from database"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT value FROM user_preferences WHERE key = ?', (key,))
            result = cursor.fetchone()
            
            if result:
                try:
                    return json.loads(result[0])
                except json.JSONDecodeError:
                    return result[0]
            
            return default
    
    def set_user_preference(self, key: str, value: Any) -> bool:
        """Set user preference in database"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT OR REPLACE INTO user_preferences (key, value, updated_at)
                    VALUES (?, ?, CURRENT_TIMESTAMP)
                ''', (key, json.dumps(value) if not isinstance(value, str) else value))
                conn.commit()
                return True
        except Exception as e:
            logger.error(f"Error setting user preference: {e}")
            return False
    
    def get_response(self, intent: str, entities: Dict = None) -> str:
        """
        Get a response for a specific intent and entities
        
        Args:
            intent: The classified intent
            entities: Extracted entities
            
        Returns:
            Generated response string
        """
        if entities is None:
            entities = {}
        
        # Update context with entities
        self.context.update(entities)
        
        # Handle specific intents
        if intent == "what_time":
            now = datetime.now()
            return f"The current time is {now.strftime('%I:%M %p')}"
        
        elif intent == "what_date":
            now = datetime.now()
            return f"Today is {now.strftime('%A, %B %d, %Y')}"
        
        elif intent == "calculate":
            if "query" in entities:
                return f"I can help with calculations, but I need a more specific mathematical expression for: {entities['query']}"
            return "What would you like me to calculate?"
        
        elif intent == "general_query":
            if "query" in entities:
                knowledge_response = self._search_knowledge_base(entities["query"])
                if knowledge_response:
                    return knowledge_response
                return f"I don't have specific information about {entities['query']} in my knowledge base."
            return "What would you like to know?"
        
        elif intent == "tell_joke":
            jokes = [
                "Why don't scientists trust atoms? Because they make up everything!",
                "Why did the scarecrow win an award? He was outstanding in his field!",
                "Why don't eggs tell jokes? They'd crack each other up!",
                "What do you call a fake noodle? An impasta!"
            ]
            return random.choice(jokes)
        
        elif intent == "fun_fact":
            facts = [
                "Honey never spoils. Archaeologists have found pots of honey in ancient Egyptian tombs that are over 3,000 years old and still perfectly edible.",
                "A group of flamingos is called a 'flamboyance'.",
                "Bananas are berries, but strawberries aren't.",
                "The shortest war in history was between Britain and Zanzibar on August 27, 1896. Zanzibar surrendered after 38 minutes."
            ]
            return random.choice(facts)
        
        # Default response for unknown intents
        return "I'm not sure how to help with that. Could you try rephrasing your request?"
    
    def start_new_session(self, session_id: str = None) -> str:
        """
        Start a new conversation session
        
        Args:
            session_id: Optional custom session ID
            
        Returns:
            The session ID that was created
        """
        if session_id is None:
            session_id = f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        self.context["session_id"] = session_id
        self.context["session_start"] = datetime.now().isoformat()
        
        logger.info(f"Started new conversation session: {session_id}")
        return session_id
    
    def end_session(self) -> None:
        """End the current conversation session"""
        session_id = self.context.get("session_id", "unknown")
        logger.info(f"Ended conversation session: {session_id}")
        self.clear_context()
    
    def get_session_summary(self) -> Dict[str, Any]:
        """Get a summary of the current session"""
        session_id = self.context.get("session_id", "default")
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Get session conversations
            cursor.execute('''
                SELECT COUNT(*), MIN(timestamp), MAX(timestamp)
                FROM conversations 
                WHERE session_id = ?
            ''', (session_id,))
            
            result = cursor.fetchone()
            conversation_count = result[0] if result else 0
            start_time = result[1] if result else None
            end_time = result[2] if result else None
            
            # Get most common intents in this session
            cursor.execute('''
                SELECT intent, COUNT(*) as count 
                FROM conversations 
                WHERE session_id = ?
                GROUP BY intent 
                ORDER BY count DESC 
                LIMIT 3
            ''', (session_id,))
            
            common_intents = cursor.fetchall()
            
            return {
                "session_id": session_id,
                "conversation_count": conversation_count,
                "start_time": start_time,
                "end_time": end_time,
                "common_intents": common_intents,
                "context_keys": list(self.context.keys())
            }
    
    def handle_follow_up_question(self, query: str) -> Optional[str]:
        """
        Handle follow-up questions based on conversation context
        
        Args:
            query: The follow-up question
            
        Returns:
            Response if it's a follow-up, None otherwise
        """
        recent_conversations = self._get_recent_conversations(3)
        
        if not recent_conversations:
            return None
        
        last_conversation = recent_conversations[0]
        last_response = last_conversation.get("assistant_response", "")
        last_intent = last_conversation.get("intent", "")
        
        # Handle common follow-up patterns
        follow_up_patterns = {
            r"why|how|explain": "That's a great follow-up question. Let me provide more details.",
            r"more|tell me more|continue": "Here's additional information on that topic.",
            r"when|where": "Let me see if I have more specific details about that.",
            r"who|what else": "I can provide more related information.",
        }
        
        for pattern, response_template in follow_up_patterns.items():
            if re.search(pattern, query, re.IGNORECASE):
                # Try to find more specific information
                if last_intent == "knowledge_lookup":
                    # Extract the topic from the last conversation
                    topic_words = last_conversation.get("user_input", "").split()
                    for word in topic_words:
                        if len(word) > 3:  # Skip short words
                            additional_info = self._search_knowledge_base(f"{word} {query}")
                            if additional_info and additional_info != last_response:
                                return additional_info
                
                return response_template
        
        return None
    
    def get_conversation_stats(self) -> Dict[str, Any]:
        """Get statistics about conversations"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Total conversations
            cursor.execute("SELECT COUNT(*) FROM conversations")
            total_conversations = cursor.fetchone()[0]
            
            # Most common intents
            cursor.execute('''
                SELECT intent, COUNT(*) as count 
                FROM conversations 
                GROUP BY intent 
                ORDER BY count DESC 
                LIMIT 5
            ''')
            common_intents = cursor.fetchall()
            
            # Recent activity
            cursor.execute('''
                SELECT COUNT(*) FROM conversations 
                WHERE timestamp > datetime('now', '-24 hours')
            ''')
            recent_activity = cursor.fetchone()[0]
            
            return {
                "total_conversations": total_conversations,
                "common_intents": common_intents,
                "recent_activity_24h": recent_activity,
                "knowledge_base_size": self._get_knowledge_base_size()
            }
    
    def _get_knowledge_base_size(self) -> int:
        """Get the number of facts in the knowledge base"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM facts")
            return cursor.fetchone()[0]
    
    def learn_from_conversation(self, user_input: str, correct_response: str, category: str = "learned") -> bool:
        """
        Learn from user corrections and feedback
        
        Args:
            user_input: The user's original input
            correct_response: The correct response
            category: Category for the learned fact
            
        Returns:
            True if learning was successful
        """
        try:
            # Add the corrected information as a new fact
            return self.add_knowledge_fact(category, user_input, correct_response, 0.8)
        except Exception as e:
            logger.error(f"Error learning from conversation: {e}")
            return False
    
    def get_similar_questions(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """
        Find similar questions in the knowledge base
        
        Args:
            query: The query to find similar questions for
            limit: Maximum number of similar questions to return
            
        Returns:
            List of similar questions with their answers
        """
        query_words = set(query.lower().split())
        similar_questions = []
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT question, answer, confidence FROM facts")
            
            for row in cursor.fetchall():
                question, answer, confidence = row
                question_words = set(question.lower().split())
                
                # Calculate similarity based on common words
                common_words = query_words.intersection(question_words)
                if common_words:
                    similarity = len(common_words) / max(len(query_words), len(question_words))
                    if similarity > 0.2:  # Minimum similarity threshold
                        similar_questions.append({
                            "question": question,
                            "answer": answer,
                            "confidence": confidence,
                            "similarity": similarity
                        })
            
            # Sort by similarity and return top results
            similar_questions.sort(key=lambda x: x["similarity"], reverse=True)
            return similar_questions[:limit]
    
    def export_conversation_history(self, session_id: str = None, format: str = "json") -> str:
        """
        Export conversation history for a session
        
        Args:
            session_id: Session ID to export (current session if None)
            format: Export format ('json' or 'text')
            
        Returns:
            Exported conversation data as string
        """
        if session_id is None:
            session_id = self.context.get("session_id", "default")
        
        conversations = []
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT user_input, assistant_response, intent, timestamp
                FROM conversations 
                WHERE session_id = ?
                ORDER BY timestamp
            ''', (session_id,))
            
            for row in cursor.fetchall():
                conversations.append({
                    "user_input": row[0],
                    "assistant_response": row[1],
                    "intent": row[2],
                    "timestamp": row[3]
                })
        
        if format == "json":
            return json.dumps(conversations, indent=2)
        else:  # text format
            text_output = f"Conversation History - Session: {session_id}\n"
            text_output += "=" * 50 + "\n\n"
            
            for conv in conversations:
                text_output += f"[{conv['timestamp']}] User: {conv['user_input']}\n"
                text_output += f"Assistant: {conv['assistant_response']}\n"
                text_output += f"Intent: {conv['intent']}\n\n"
            return text_output