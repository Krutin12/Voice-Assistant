"""
Batch Operations Module

This module handles batch file operations, auto-response system for common queries,
and user preference learning for personalized suggestions.
"""

import json
import os
import shutil
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from pathlib import Path
import logging
from collections import defaultdict, Counter

from .command_router import Command, Response

logger = logging.getLogger(__name__)


@dataclass
class BatchFileOperation:
    """Represents a batch file operation"""
    operation_type: str  # 'copy', 'move', 'delete', 'rename'
    source_pattern: str
    destination: Optional[str] = None
    recursive: bool = False
    confirm_each: bool = True
    dry_run: bool = False


@dataclass
class AutoResponse:
    """Represents an automatic response for common queries"""
    trigger_patterns: List[str]
    response_text: str
    confidence_threshold: float = 0.8
    enabled: bool = True
    usage_count: int = 0
    last_used: Optional[datetime] = None


@dataclass
class UserPreference:
    """Represents a learned user preference"""
    category: str
    preference_key: str
    preference_value: Any
    confidence: float
    usage_count: int = 1
    last_updated: datetime = None
    
    def __post_init__(self):
        if self.last_updated is None:
            self.last_updated = datetime.now()


class BatchOperationSystem:
    """
    System for handling batch operations, auto-responses, and user preferences
    """
    
    def __init__(self, config: Dict):
        self.config = config
        
        # Storage paths
        self.data_dir = Path("wizard/data")
        self.auto_responses_file = self.data_dir / "auto_responses.json"
        self.user_preferences_file = self.data_dir / "user_preferences.json"
        self.command_history_file = self.data_dir / "command_history.json"
        
        # Ensure data directory exists
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        # Data structures
        self.auto_responses: Dict[str, AutoResponse] = {}
        self.user_preferences: Dict[str, UserPreference] = {}
        self.command_history: List[Dict[str, Any]] = []
        self.preference_patterns: Dict[str, List[str]] = defaultdict(list)
        
        # Load existing data
        self._load_auto_responses()
        self._load_user_preferences()
        self._load_command_history()
        
        # Setup default auto-responses
        self._setup_default_auto_responses()
        
        # Start preference learning
        self._start_preference_learning()
    
    def _load_auto_responses(self) -> None:
        """Load auto-responses from JSON file"""
        if not self.auto_responses_file.exists():
            return
        
        try:
            with open(self.auto_responses_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            for name, response_data in data.items():
                auto_response = AutoResponse(
                    trigger_patterns=response_data['trigger_patterns'],
                    response_text=response_data['response_text'],
                    confidence_threshold=response_data.get('confidence_threshold', 0.8),
                    enabled=response_data.get('enabled', True),
                    usage_count=response_data.get('usage_count', 0),
                    last_used=datetime.fromisoformat(response_data['last_used']) if response_data.get('last_used') else None
                )
                self.auto_responses[name] = auto_response
                
        except Exception as e:
            logger.error(f"Error loading auto-responses: {e}")
    
    def _load_user_preferences(self) -> None:
        """Load user preferences from JSON file"""
        if not self.user_preferences_file.exists():
            return
        
        try:
            with open(self.user_preferences_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            for key, pref_data in data.items():
                preference = UserPreference(
                    category=pref_data['category'],
                    preference_key=pref_data['preference_key'],
                    preference_value=pref_data['preference_value'],
                    confidence=pref_data['confidence'],
                    usage_count=pref_data.get('usage_count', 1),
                    last_updated=datetime.fromisoformat(pref_data['last_updated'])
                )
                self.user_preferences[key] = preference
                
        except Exception as e:
            logger.error(f"Error loading user preferences: {e}")
    
    def _load_command_history(self) -> None:
        """Load command history from JSON file"""
        if not self.command_history_file.exists():
            return
        
        try:
            with open(self.command_history_file, 'r', encoding='utf-8') as f:
                self.command_history = json.load(f)
                
        except Exception as e:
            logger.error(f"Error loading command history: {e}")
            self.command_history = [] 
   
    def _save_auto_responses(self) -> bool:
        """Save auto-responses to JSON file"""
        try:
            data = {}
            for name, response in self.auto_responses.items():
                data[name] = {
                    'trigger_patterns': response.trigger_patterns,
                    'response_text': response.response_text,
                    'confidence_threshold': response.confidence_threshold,
                    'enabled': response.enabled,
                    'usage_count': response.usage_count,
                    'last_used': response.last_used.isoformat() if response.last_used else None
                }
            
            with open(self.auto_responses_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            return True
            
        except Exception as e:
            logger.error(f"Error saving auto-responses: {e}")
            return False
    
    def _save_user_preferences(self) -> bool:
        """Save user preferences to JSON file"""
        try:
            data = {}
            for key, preference in self.user_preferences.items():
                data[key] = {
                    'category': preference.category,
                    'preference_key': preference.preference_key,
                    'preference_value': preference.preference_value,
                    'confidence': preference.confidence,
                    'usage_count': preference.usage_count,
                    'last_updated': preference.last_updated.isoformat()
                }
            
            with open(self.user_preferences_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            return True
            
        except Exception as e:
            logger.error(f"Error saving user preferences: {e}")
            return False
    
    def _save_command_history(self) -> bool:
        """Save command history to JSON file"""
        try:
            # Keep only last 1000 commands
            if len(self.command_history) > 1000:
                self.command_history = self.command_history[-1000:]
            
            with open(self.command_history_file, 'w', encoding='utf-8') as f:
                json.dump(self.command_history, f, indent=2, ensure_ascii=False)
            return True
            
        except Exception as e:
            logger.error(f"Error saving command history: {e}")
            return False
    
    def _setup_default_auto_responses(self) -> None:
        """Setup default auto-responses for common queries"""
        default_responses = {
            'greeting': AutoResponse(
                trigger_patterns=['hello', 'hi', 'hey', 'good morning', 'good afternoon'],
                response_text="Hello! How can I help you today?",
                confidence_threshold=0.9
            ),
            'thanks': AutoResponse(
                trigger_patterns=['thank you', 'thanks', 'appreciate it'],
                response_text="You're welcome! Is there anything else I can help you with?",
                confidence_threshold=0.9
            ),
            'status_check': AutoResponse(
                trigger_patterns=['how are you', 'status', 'are you working'],
                response_text="I'm working perfectly and ready to help! All systems are operational.",
                confidence_threshold=0.8
            ),
            'capabilities': AutoResponse(
                trigger_patterns=['what can you do', 'help me', 'capabilities'],
                response_text="I can help with system control, file management, productivity tasks, entertainment, and much more. Just ask me what you need!",
                confidence_threshold=0.8
            )
        }
        
        # Add default responses if they don't exist
        for name, response in default_responses.items():
            if name not in self.auto_responses:
                self.auto_responses[name] = response
        
        self._save_auto_responses()
    
    def _start_preference_learning(self) -> None:
        """Start background preference learning from command history"""
        def learn_preferences():
            try:
                self._analyze_command_patterns()
                self._update_preference_confidence()
            except Exception as e:
                logger.error(f"Error in preference learning: {e}")
        
        # Run preference learning in background thread
        learning_thread = threading.Thread(target=learn_preferences)
        learning_thread.daemon = True
        learning_thread.start()
    
    def execute_batch_file_operation(self, operation: BatchFileOperation) -> Response:
        """
        Execute a batch file operation
        
        Args:
            operation: BatchFileOperation to execute
            
        Returns:
            Response with operation results
        """
        try:
            results = []
            errors = []
            
            # Find files matching the pattern
            source_path = Path(operation.source_pattern)
            
            if source_path.is_absolute():
                search_dir = source_path.parent
                pattern = source_path.name
            else:
                search_dir = Path.cwd()
                pattern = operation.source_pattern
            
            # Find matching files
            if operation.recursive:
                matching_files = list(search_dir.rglob(pattern))
            else:
                matching_files = list(search_dir.glob(pattern))
            
            if not matching_files:
                return Response(
                    text=f"No files found matching pattern: {operation.source_pattern}",
                    error_message="No matching files"
                )
            
            # Execute operation on each file
            for file_path in matching_files:
                try:
                    if operation.dry_run:
                        results.append(f"Would {operation.operation_type}: {file_path}")
                        continue
                    
                    if operation.operation_type == "delete":
                        if operation.confirm_each:
                            # In a real implementation, this would prompt the user
                            logger.info(f"Deleting file: {file_path}")
                        
                        if file_path.is_file():
                            file_path.unlink()
                        elif file_path.is_dir():
                            shutil.rmtree(file_path)
                        
                        results.append(f"Deleted: {file_path}")
                    
                    elif operation.operation_type == "copy":
                        if not operation.destination:
                            errors.append(f"No destination specified for copy operation")
                            continue
                        
                        dest_path = Path(operation.destination)
                        if dest_path.is_dir():
                            dest_path = dest_path / file_path.name
                        
                        shutil.copy2(file_path, dest_path)
                        results.append(f"Copied: {file_path} -> {dest_path}")
                    
                    elif operation.operation_type == "move":
                        if not operation.destination:
                            errors.append(f"No destination specified for move operation")
                            continue
                        
                        dest_path = Path(operation.destination)
                        if dest_path.is_dir():
                            dest_path = dest_path / file_path.name
                        
                        shutil.move(str(file_path), str(dest_path))
                        results.append(f"Moved: {file_path} -> {dest_path}")
                    
                except Exception as e:
                    errors.append(f"Error processing {file_path}: {str(e)}")
            
            # Format response
            response_text = f"Batch operation completed:\n"
            if results:
                response_text += f"Successful operations ({len(results)}):\n"
                for result in results[:10]:  # Limit to first 10 results
                    response_text += f"• {result}\n"
                if len(results) > 10:
                    response_text += f"... and {len(results) - 10} more\n"
            
            if errors:
                response_text += f"\nErrors ({len(errors)}):\n"
                for error in errors[:5]:  # Limit to first 5 errors
                    response_text += f"• {error}\n"
                if len(errors) > 5:
                    response_text += f"... and {len(errors) - 5} more errors\n"
            
            return Response(
                text=response_text.strip(),
                action_taken=len(results) > 0,
                error_message="; ".join(errors) if errors else None
            )
            
        except Exception as e:
            logger.error(f"Error executing batch operation: {e}")
            return Response(
                text=f"Error executing batch operation: {str(e)}",
                error_message=str(e)
            )
    
    def check_auto_response(self, command_text: str) -> Optional[Response]:
        """
        Check if command matches any auto-response patterns
        
        Args:
            command_text: Raw command text
            
        Returns:
            Response if auto-response found, None otherwise
        """
        command_lower = command_text.lower().strip()
        
        for name, auto_response in self.auto_responses.items():
            if not auto_response.enabled:
                continue
            
            # Check if any trigger pattern matches
            for pattern in auto_response.trigger_patterns:
                if pattern.lower() in command_lower:
                    # Calculate confidence based on pattern match
                    confidence = len(pattern) / len(command_lower)
                    
                    if confidence >= auto_response.confidence_threshold:
                        # Update usage statistics
                        auto_response.usage_count += 1
                        auto_response.last_used = datetime.now()
                        self._save_auto_responses()
                        
                        return Response(
                            text=auto_response.response_text,
                            action_taken=True
                        )
        
        return None
    
    def add_auto_response(self, name: str, trigger_patterns: List[str], response_text: str, confidence_threshold: float = 0.8) -> bool:
        """
        Add a new auto-response
        
        Args:
            name: Unique name for the auto-response
            trigger_patterns: List of patterns that trigger this response
            response_text: Text to respond with
            confidence_threshold: Minimum confidence required to trigger
            
        Returns:
            True if auto-response was added successfully
        """
        try:
            auto_response = AutoResponse(
                trigger_patterns=trigger_patterns,
                response_text=response_text,
                confidence_threshold=confidence_threshold
            )
            
            self.auto_responses[name] = auto_response
            self._save_auto_responses()
            
            logger.info(f"Added auto-response: {name}")
            return True
            
        except Exception as e:
            logger.error(f"Error adding auto-response: {e}")
            return False
    
    def record_command(self, command: Command, response: Response) -> None:
        """
        Record a command and response for preference learning
        
        Args:
            command: Command that was executed
            response: Response that was generated
        """
        try:
            command_record = {
                'timestamp': datetime.now().isoformat(),
                'intent': command.intent,
                'raw_text': command.raw_text,
                'entities': command.entities,
                'confidence': command.confidence,
                'response_text': response.text,
                'action_taken': response.action_taken,
                'error': response.error_message is not None
            }
            
            self.command_history.append(command_record)
            self._save_command_history()
            
            # Learn from this command
            self._learn_from_command(command, response)
            
        except Exception as e:
            logger.error(f"Error recording command: {e}")
    
    def _learn_from_command(self, command: Command, response: Response) -> None:
        """Learn user preferences from a command"""
        try:
            # Learn application preferences
            if command.intent in ["open_application", "close_application"] and "application" in command.entities:
                app_name = command.entities["application"]
                self._update_preference("applications", "preferred_app", app_name, 0.1)
            
            # Learn time preferences
            if command.intent in ["set_timer", "create_reminder"]:
                current_hour = datetime.now().hour
                if 6 <= current_hour < 12:
                    time_period = "morning"
                elif 12 <= current_hour < 18:
                    time_period = "afternoon"
                else:
                    time_period = "evening"
                
                self._update_preference("time_patterns", f"{command.intent}_time", time_period, 0.05)
            
            # Learn entertainment preferences
            if command.intent in ["tell_joke", "fun_fact", "movie_recommendation"] and "category" in command.entities:
                category = command.entities["category"]
                self._update_preference("entertainment", f"{command.intent}_category", category, 0.1)
            
            # Learn volume preferences
            if command.intent == "set_volume" and "volume_level" in command.entities:
                volume = command.entities["volume_level"]
                self._update_preference("audio", "preferred_volume", volume, 0.05)
            
        except Exception as e:
            logger.error(f"Error learning from command: {e}")
    
    def _update_preference(self, category: str, key: str, value: Any, confidence_increment: float) -> None:
        """Update a user preference"""
        pref_key = f"{category}_{key}_{value}"
        
        if pref_key in self.user_preferences:
            # Update existing preference
            pref = self.user_preferences[pref_key]
            pref.usage_count += 1
            pref.confidence = min(1.0, pref.confidence + confidence_increment)
            pref.last_updated = datetime.now()
        else:
            # Create new preference
            pref = UserPreference(
                category=category,
                preference_key=key,
                preference_value=value,
                confidence=confidence_increment
            )
            self.user_preferences[pref_key] = pref
        
        self._save_user_preferences()
    
    def get_personalized_suggestions(self, context: str = None) -> List[str]:
        """
        Get personalized suggestions based on learned preferences
        
        Args:
            context: Optional context for suggestions
            
        Returns:
            List of personalized suggestions
        """
        suggestions = []
        
        try:
            # Get top preferences by category
            app_prefs = self._get_top_preferences("applications", limit=3)
            entertainment_prefs = self._get_top_preferences("entertainment", limit=2)
            
            # Generate suggestions based on time of day
            current_hour = datetime.now().hour
            
            if 6 <= current_hour < 12:  # Morning
                suggestions.append("Would you like me to run your morning routine?")
                if app_prefs:
                    suggestions.append(f"Should I open {app_prefs[0]['value']} for you?")
            
            elif 12 <= current_hour < 18:  # Afternoon
                suggestions.append("Need help with any productivity tasks?")
                if entertainment_prefs:
                    suggestions.append(f"How about a {entertainment_prefs[0]['value']} break?")
            
            else:  # Evening
                suggestions.append("Ready to wind down? I can run your night routine.")
                if entertainment_prefs:
                    suggestions.append(f"Want to hear a {entertainment_prefs[0]['value']}?")
            
            # Add context-specific suggestions
            if context:
                if "work" in context.lower():
                    suggestions.append("I can help set up your work environment.")
                elif "entertainment" in context.lower():
                    suggestions.extend([
                        "I can tell jokes, share fun facts, or recommend movies.",
                        "Want to play a quick game like rock paper scissors?"
                    ])
            
        except Exception as e:
            logger.error(f"Error generating suggestions: {e}")
        
        return suggestions[:5]  # Return top 5 suggestions
    
    def _get_top_preferences(self, category: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Get top preferences for a category"""
        category_prefs = []
        
        for pref in self.user_preferences.values():
            if pref.category == category:
                category_prefs.append({
                    'key': pref.preference_key,
                    'value': pref.preference_value,
                    'confidence': pref.confidence,
                    'usage_count': pref.usage_count
                })
        
        # Sort by confidence and usage count
        category_prefs.sort(key=lambda x: (x['confidence'], x['usage_count']), reverse=True)
        
        return category_prefs[:limit]
    
    def _analyze_command_patterns(self) -> None:
        """Analyze command history for patterns"""
        if len(self.command_history) < 10:
            return
        
        # Analyze recent commands (last 100)
        recent_commands = self.command_history[-100:]
        
        # Count intent frequencies
        intent_counts = Counter(cmd['intent'] for cmd in recent_commands)
        
        # Update preferences based on frequent intents
        for intent, count in intent_counts.most_common(10):
            confidence = min(0.8, count / len(recent_commands))
            self._update_preference("usage_patterns", "frequent_intent", intent, confidence * 0.1)
    
    def _update_preference_confidence(self) -> None:
        """Update preference confidence based on usage patterns"""
        # Decay old preferences
        cutoff_date = datetime.now() - timedelta(days=30)
        
        for pref in self.user_preferences.values():
            if pref.last_updated < cutoff_date:
                pref.confidence *= 0.9  # Decay by 10%
        
        self._save_user_preferences()
    
    def get_batch_operation_status(self) -> Dict[str, Any]:
        """Get status of batch operation system"""
        return {
            'auto_responses': len(self.auto_responses),
            'enabled_auto_responses': sum(1 for r in self.auto_responses.values() if r.enabled),
            'user_preferences': len(self.user_preferences),
            'command_history_size': len(self.command_history),
            'top_preferences': self._get_top_preferences("usage_patterns", 5)
        }