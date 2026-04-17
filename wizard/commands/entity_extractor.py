"""
Entity Extraction Module

This module provides advanced entity extraction capabilities for natural language
processing, including numbers, dates, file names, and other parameters.
"""

import re
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


class EntityExtractor:
    """
    Advanced entity extraction for voice commands
    """
    
    def __init__(self):
        self.patterns = self._initialize_patterns()
        self.time_keywords = self._initialize_time_keywords()
        
    def _initialize_patterns(self) -> Dict[str, re.Pattern]:
        """Initialize regex patterns for entity extraction"""
        return {
            # Numbers and quantities
            "integer": re.compile(r'\b(\d+)\b'),
            "decimal": re.compile(r'\b(\d+\.\d+)\b'),
            "ordinal": re.compile(r'\b(\d+)(st|nd|rd|th)\b', re.IGNORECASE),
            "percentage": re.compile(r'\b(\d+(?:\.\d+)?)%\b'),
            
            # Time and date patterns
            "time_12h": re.compile(r'\b(\d{1,2}):(\d{2})\s*(am|pm)\b', re.IGNORECASE),
            "time_24h": re.compile(r'\b(\d{1,2}):(\d{2})\b'),
            "date_mdy": re.compile(r'\b(\d{1,2})/(\d{1,2})/(\d{4})\b'),
            "date_dmy": re.compile(r'\b(\d{1,2})-(\d{1,2})-(\d{4})\b'),
            "relative_time": re.compile(r'\b(in|after)\s+(\d+)\s+(second|minute|hour|day|week|month|year)s?\b', re.IGNORECASE),
            
            # Duration patterns
            "duration": re.compile(r'\b(\d+)\s+(second|minute|hour|day|week|month|year)s?\b', re.IGNORECASE),
            "duration_short": re.compile(r'\b(\d+)(s|m|h|d)\b'),
            
            # File and path patterns
            "file_path": re.compile(r'[A-Za-z]:\\(?:[^\\/:*?"<>|\r\n]+\\)*[^\\/:*?"<>|\r\n]*'),
            "file_name": re.compile(r'\b([a-zA-Z0-9_-]+\.[a-zA-Z0-9]+)\b'),
            "file_extension": re.compile(r'\.([a-zA-Z0-9]+)$'),
            
            # Contact and communication
            "email": re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'),
            "phone": re.compile(r'\b(?:\+?1[-.\s]?)?\(?([0-9]{3})\)?[-.\s]?([0-9]{3})[-.\s]?([0-9]{4})\b'),
            "url": re.compile(r'https?://[^\s]+|www\.[^\s]+'),
            
            # Measurement units
            "temperature": re.compile(r'\b(\d+(?:\.\d+)?)\s*°?([CF])\b', re.IGNORECASE),
            "distance": re.compile(r'\b(\d+(?:\.\d+)?)\s*(km|kilometer|mile|meter|foot|feet|inch|yard)s?\b', re.IGNORECASE),
            "weight": re.compile(r'\b(\d+(?:\.\d+)?)\s*(kg|kilogram|pound|gram|ounce|ton)s?\b', re.IGNORECASE),
            
            # Currency
            "currency": re.compile(r'\$(\d+(?:\.\d{2})?)|(\d+(?:\.\d{2})?)\s*dollars?', re.IGNORECASE),
            
            # Colors
            "color": re.compile(r'\b(red|blue|green|yellow|orange|purple|pink|black|white|gray|grey|brown|cyan|magenta)\b', re.IGNORECASE),
        }
    
    def _initialize_time_keywords(self) -> Dict[str, int]:
        """Initialize time-related keywords and their values"""
        return {
            # Relative time keywords (in minutes)
            "now": 0,
            "immediately": 0,
            "soon": 5,
            "later": 60,
            "tonight": 480,  # 8 hours from now
            "tomorrow": 1440,  # 24 hours
            "next week": 10080,  # 7 days
            
            # Day names (relative to current day)
            "monday": None,  # Will be calculated dynamically
            "tuesday": None,
            "wednesday": None,
            "thursday": None,
            "friday": None,
            "saturday": None,
            "sunday": None,
        }
    
    def extract_all_entities(self, text: str) -> Dict[str, Any]:
        """
        Extract all possible entities from text
        
        Args:
            text: Input text to analyze
            
        Returns:
            Dictionary containing all extracted entities
        """
        entities = {}
        
        # Extract basic patterns
        for entity_type, pattern in self.patterns.items():
            matches = pattern.findall(text)
            if matches:
                entities[entity_type] = self._process_matches(entity_type, matches)
        
        # Extract named entities
        entities.update(self._extract_named_entities(text))
        
        # Extract temporal entities
        entities.update(self._extract_temporal_entities(text))
        
        # Extract application names
        entities.update(self._extract_application_names(text))
        
        return entities
    
    def _process_matches(self, entity_type: str, matches: List) -> Any:
        """Process regex matches based on entity type"""
        if entity_type in ["integer", "decimal", "percentage"]:
            return [float(match) if '.' in str(match) else int(match) for match in matches]
        elif entity_type == "ordinal":
            return [int(match[0]) for match in matches]
        elif entity_type in ["time_12h", "time_24h"]:
            return self._process_time_matches(matches, entity_type)
        elif entity_type in ["date_mdy", "date_dmy"]:
            return self._process_date_matches(matches, entity_type)
        elif entity_type == "duration":
            return self._process_duration_matches(matches)
        elif entity_type == "temperature":
            return [{"value": float(match[0]), "unit": match[1].upper()} for match in matches]
        elif entity_type in ["distance", "weight"]:
            return [{"value": float(match[0]), "unit": match[1]} for match in matches]
        elif entity_type == "currency":
            return [float(match[0] or match[1]) for match in matches]
        else:
            return matches
    
    def _process_time_matches(self, matches: List, time_type: str) -> List[Dict]:
        """Process time matches into structured format"""
        times = []
        for match in matches:
            if time_type == "time_12h":
                hour, minute, period = match
                hour = int(hour)
                minute = int(minute)
                if period.lower() == "pm" and hour != 12:
                    hour += 12
                elif period.lower() == "am" and hour == 12:
                    hour = 0
            else:  # time_24h
                hour, minute = int(match[0]), int(match[1])
            
            times.append({
                "hour": hour,
                "minute": minute,
                "formatted": f"{hour:02d}:{minute:02d}"
            })
        
        return times
    
    def _process_date_matches(self, matches: List, date_type: str) -> List[Dict]:
        """Process date matches into structured format"""
        dates = []
        for match in matches:
            if date_type == "date_mdy":
                month, day, year = int(match[0]), int(match[1]), int(match[2])
            else:  # date_dmy
                day, month, year = int(match[0]), int(match[1]), int(match[2])
            
            try:
                date_obj = datetime(year, month, day)
                dates.append({
                    "day": day,
                    "month": month,
                    "year": year,
                    "date_object": date_obj,
                    "formatted": date_obj.strftime("%Y-%m-%d")
                })
            except ValueError:
                logger.warning(f"Invalid date: {day}/{month}/{year}")
        
        return dates
    
    def _process_duration_matches(self, matches: List) -> List[Dict]:
        """Process duration matches into structured format"""
        durations = []
        for match in matches:
            value, unit = int(match[0]), match[1].lower()
            
            # Convert to minutes for standardization
            multipliers = {
                "second": 1/60,
                "minute": 1,
                "hour": 60,
                "day": 1440,
                "week": 10080,
                "month": 43200,  # Approximate
                "year": 525600   # Approximate
            }
            
            minutes = value * multipliers.get(unit, 1)
            
            durations.append({
                "value": value,
                "unit": unit,
                "total_minutes": minutes,
                "total_seconds": minutes * 60
            })
        
        return durations
    
    def _extract_named_entities(self, text: str) -> Dict[str, Any]:
        """Extract named entities like person names, places, etc."""
        entities = {}
        
        # Simple name detection (capitalized words)
        name_pattern = re.compile(r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b')
        potential_names = name_pattern.findall(text)
        
        # Filter out common words that aren't names
        common_words = {
            "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday",
            "January", "February", "March", "April", "May", "June",
            "July", "August", "September", "October", "November", "December",
            "Google", "YouTube", "Spotify", "Chrome", "Firefox", "Windows", "Microsoft"
        }
        
        names = [name for name in potential_names if name not in common_words]
        if names:
            entities["names"] = names
        
        return entities
    
    def _extract_temporal_entities(self, text: str) -> Dict[str, Any]:
        """Extract temporal expressions and convert to datetime objects"""
        entities = {}
        
        # Relative time expressions
        relative_patterns = {
            "in_minutes": re.compile(r'\bin\s+(\d+)\s+minutes?\b', re.IGNORECASE),
            "in_hours": re.compile(r'\bin\s+(\d+)\s+hours?\b', re.IGNORECASE),
            "in_days": re.compile(r'\bin\s+(\d+)\s+days?\b', re.IGNORECASE),
            "next_week": re.compile(r'\bnext\s+week\b', re.IGNORECASE),
            "tomorrow": re.compile(r'\btomorrow\b', re.IGNORECASE),
            "today": re.compile(r'\btoday\b', re.IGNORECASE),
        }
        
        now = datetime.now()
        temporal_entities = []
        
        for pattern_name, pattern in relative_patterns.items():
            matches = pattern.findall(text)
            if matches:
                if pattern_name == "in_minutes":
                    for match in matches:
                        target_time = now + timedelta(minutes=int(match))
                        temporal_entities.append({
                            "type": "relative_time",
                            "original": f"in {match} minutes",
                            "target_datetime": target_time,
                            "minutes_from_now": int(match)
                        })
                elif pattern_name == "in_hours":
                    for match in matches:
                        target_time = now + timedelta(hours=int(match))
                        temporal_entities.append({
                            "type": "relative_time",
                            "original": f"in {match} hours",
                            "target_datetime": target_time,
                            "minutes_from_now": int(match) * 60
                        })
                elif pattern_name == "in_days":
                    for match in matches:
                        target_time = now + timedelta(days=int(match))
                        temporal_entities.append({
                            "type": "relative_time",
                            "original": f"in {match} days",
                            "target_datetime": target_time,
                            "minutes_from_now": int(match) * 1440
                        })
                elif pattern_name == "tomorrow":
                    target_time = now + timedelta(days=1)
                    temporal_entities.append({
                        "type": "relative_time",
                        "original": "tomorrow",
                        "target_datetime": target_time,
                        "minutes_from_now": 1440
                    })
                elif pattern_name == "today":
                    temporal_entities.append({
                        "type": "relative_time",
                        "original": "today",
                        "target_datetime": now,
                        "minutes_from_now": 0
                    })
        
        if temporal_entities:
            entities["temporal"] = temporal_entities
        
        return entities
    
    def _extract_application_names(self, text: str) -> Dict[str, Any]:
        """Extract application names from text"""
        # Common application names and variations
        app_variations = {
            "chrome": ["chrome", "google chrome"],
            "firefox": ["firefox", "mozilla firefox"],
            "edge": ["edge", "microsoft edge"],
            "notepad": ["notepad", "text editor"],
            "calculator": ["calculator", "calc"],
            "spotify": ["spotify", "music"],
            "discord": ["discord"],
            "steam": ["steam"],
            "word": ["word", "microsoft word", "ms word"],
            "excel": ["excel", "microsoft excel", "ms excel"],
            "powerpoint": ["powerpoint", "microsoft powerpoint", "ms powerpoint"],
            "outlook": ["outlook", "microsoft outlook", "ms outlook"],
            "teams": ["teams", "microsoft teams", "ms teams"],
            "zoom": ["zoom"],
            "vlc": ["vlc", "vlc player"],
            "photoshop": ["photoshop", "adobe photoshop"],
            "vscode": ["vscode", "visual studio code", "vs code", "code"],
        }
        
        detected_apps = []
        text_lower = text.lower()
        
        for app_name, variations in app_variations.items():
            for variation in variations:
                if variation in text_lower:
                    detected_apps.append({
                        "name": app_name,
                        "variation_used": variation,
                        "confidence": len(variation) / len(text_lower)
                    })
                    break
        
        if detected_apps:
            return {"applications": detected_apps}
        
        return {}
    
    def extract_specific_entity(self, text: str, entity_type: str) -> Optional[Any]:
        """
        Extract a specific type of entity from text
        
        Args:
            text: Input text
            entity_type: Type of entity to extract
            
        Returns:
            Extracted entity or None if not found
        """
        if entity_type in self.patterns:
            matches = self.patterns[entity_type].findall(text)
            if matches:
                return self._process_matches(entity_type, matches)
        
        return None
    
    def get_supported_entities(self) -> List[str]:
        """Get list of all supported entity types"""
        return list(self.patterns.keys()) + ["names", "temporal", "applications"]