"""
Security Module for Wizard Voice Assistant

This module handles security features including confirmation systems,
password protection, and safe mode operations.
"""

import hashlib
import json
import os
from typing import Dict, List, Optional, Set, Callable
from dataclasses import dataclass
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


@dataclass
class SecuritySettings:
    """Security configuration settings"""
    require_confirmation: bool = True
    password_protected_commands: List[str] = None
    safe_mode: bool = False
    password_hash: Optional[str] = None
    failed_attempts: int = 0
    max_failed_attempts: int = 3
    lockout_duration: int = 300  # 5 minutes in seconds
    
    def __post_init__(self):
        if self.password_protected_commands is None:
            self.password_protected_commands = [
                "shutdown", "restart", "delete_file", "empty_recycle_bin",
                "system_shutdown", "system_restart", "batch_file_operation"
            ]


class SecurityModule:
    """
    Handles security and access control for voice commands
    """
    
    def __init__(self, config_path: str = "config/security_config.json"):
        self.config_path = Path(config_path)
        self.settings = SecuritySettings()
        self.authenticated_session = False
        self.pending_confirmations: Dict[str, Dict] = {}
        self.safe_mode_commands: Set[str] = self._get_safe_mode_commands()
        self._load_security_config()
    
    def _get_safe_mode_commands(self) -> Set[str]:
        """Define commands allowed in safe mode"""
        return {
            # Basic information queries
            "what_time", "what_date", "weather", "calculate", "unit_conversion",
            
            # Entertainment (safe)
            "tell_joke", "fun_fact", "trivia_question", "coin_flip", "roll_dice",
            "generate_number", "magic_8_ball", "motivational_quote", "daily_tip",
            
            # Basic productivity (read-only)
            "list_todos", "list_calendar_events", "list_timers", "search_notes",
            "productivity_summary",
            
            # Basic media control (non-destructive)
            "set_volume", "volume_up", "volume_down", "mute", "unmute",
            "play_music", "pause_music", "next_track", "previous_track",
            
            # Basic file operations (read-only)
            "search_files", "open_file",
            
            # Basic web operations (read-only)
            "web_search", "youtube_search",
            
            # General queries
            "general_query",
            
            # System info (read-only)
            "get_system_info", "get_running_apps"
        }
    
    def _load_security_config(self) -> None:
        """Load security configuration from file"""
        if not self.config_path.exists():
            self._create_default_security_config()
            return
        
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                config_data = json.load(f)
            
            self.settings = SecuritySettings(**config_data)
            logger.info("Security configuration loaded successfully")
        
        except (json.JSONDecodeError, FileNotFoundError, TypeError) as e:
            logger.error(f"Error loading security config: {e}. Using defaults.")
            self._create_default_security_config()
    
    def _create_default_security_config(self) -> None:
        """Create default security configuration"""
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        self.settings = SecuritySettings()
        self._save_security_config()
        logger.info("Created default security configuration")
    
    def _save_security_config(self) -> bool:
        """Save security configuration to file"""
        try:
            config_dict = {
                'require_confirmation': self.settings.require_confirmation,
                'password_protected_commands': self.settings.password_protected_commands,
                'safe_mode': self.settings.safe_mode,
                'password_hash': self.settings.password_hash,
                'failed_attempts': self.settings.failed_attempts,
                'max_failed_attempts': self.settings.max_failed_attempts,
                'lockout_duration': self.settings.lockout_duration
            }
            
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(config_dict, f, indent=2)
            
            logger.info("Security configuration saved successfully")
            return True
        
        except Exception as e:
            logger.error(f"Error saving security config: {e}")
            return False
    
    def set_password(self, password: str) -> bool:
        """
        Set password for protected commands
        
        Args:
            password: Plain text password
            
        Returns:
            True if password was set successfully
        """
        if not password or len(password.strip()) < 4:
            logger.warning("Password must be at least 4 characters long")
            return False
        
        # Hash the password
        password_hash = hashlib.sha256(password.encode()).hexdigest()
        self.settings.password_hash = password_hash
        self.settings.failed_attempts = 0
        
        return self._save_security_config()
    
    def verify_password(self, password: str) -> bool:
        """
        Verify password for authentication
        
        Args:
            password: Plain text password to verify
            
        Returns:
            True if password is correct
        """
        if not self.settings.password_hash:
            logger.warning("No password set for verification")
            return False
        
        password_hash = hashlib.sha256(password.encode()).hexdigest()
        
        if password_hash == self.settings.password_hash:
            self.settings.failed_attempts = 0
            self.authenticated_session = True
            self._save_security_config()
            logger.info("Password verification successful")
            return True
        else:
            self.settings.failed_attempts += 1
            self._save_security_config()
            logger.warning(f"Password verification failed. Attempts: {self.settings.failed_attempts}")
            
            if self.settings.failed_attempts >= self.settings.max_failed_attempts:
                logger.warning("Maximum failed attempts reached. Consider implementing lockout.")
            
            return False
    
    def is_command_allowed(self, intent: str) -> bool:
        """
        Check if a command is allowed based on current security settings
        
        Args:
            intent: Command intent to check
            
        Returns:
            True if command is allowed
        """
        # In safe mode, only allow safe commands
        if self.settings.safe_mode:
            allowed = intent in self.safe_mode_commands
            if not allowed:
                logger.info(f"Command '{intent}' blocked by safe mode")
            return allowed
        
        # Normal mode - all commands allowed unless specifically restricted
        return True
    
    def requires_password(self, intent: str) -> bool:
        """
        Check if a command requires password authentication
        
        Args:
            intent: Command intent to check
            
        Returns:
            True if password is required
        """
        return intent in self.settings.password_protected_commands and self.settings.password_hash is not None
    
    def requires_confirmation(self, intent: str) -> bool:
        """
        Check if a command requires user confirmation
        
        Args:
            intent: Command intent to check
            
        Returns:
            True if confirmation is required
        """
        if not self.settings.require_confirmation:
            return False
        
        # Commands that always require confirmation
        critical_commands = {
            "system_shutdown", "system_restart", "delete_file", 
            "empty_recycle_bin", "batch_file_operation"
        }
        
        return intent in critical_commands
    
    def request_confirmation(self, intent: str, details: str, confirmation_id: str) -> str:
        """
        Request user confirmation for a critical operation
        
        Args:
            intent: Command intent
            details: Details about the operation
            confirmation_id: Unique ID for this confirmation request
            
        Returns:
            Confirmation message for the user
        """
        self.pending_confirmations[confirmation_id] = {
            'intent': intent,
            'details': details,
            'timestamp': logger.info.__globals__.get('time', __import__('time')).time()
        }
        
        return f"Are you sure you want to {details}? Say 'yes confirm {confirmation_id}' to proceed or 'no cancel {confirmation_id}' to cancel."
    
    def process_confirmation(self, response: str) -> tuple[bool, Optional[str]]:
        """
        Process user confirmation response
        
        Args:
            response: User's confirmation response
            
        Returns:
            Tuple of (confirmed, confirmation_id)
        """
        response = response.lower().strip()
        
        # Extract confirmation ID from response
        if "yes confirm" in response:
            parts = response.split()
            if len(parts) >= 3:
                confirmation_id = parts[2]
                if confirmation_id in self.pending_confirmations:
                    del self.pending_confirmations[confirmation_id]
                    return True, confirmation_id
        
        elif "no cancel" in response or "cancel" in response:
            parts = response.split()
            if len(parts) >= 3:
                confirmation_id = parts[2]
                if confirmation_id in self.pending_confirmations:
                    del self.pending_confirmations[confirmation_id]
                    return False, confirmation_id
        
        return False, None
    
    def clear_expired_confirmations(self, timeout_seconds: int = 60) -> None:
        """
        Clear confirmation requests that have expired
        
        Args:
            timeout_seconds: Timeout for confirmation requests
        """
        import time
        current_time = time.time()
        expired_ids = []
        
        for conf_id, conf_data in self.pending_confirmations.items():
            if current_time - conf_data['timestamp'] > timeout_seconds:
                expired_ids.append(conf_id)
        
        for conf_id in expired_ids:
            del self.pending_confirmations[conf_id]
            logger.info(f"Expired confirmation request: {conf_id}")
    
    def enable_safe_mode(self) -> bool:
        """
        Enable safe mode with limited command access
        
        Returns:
            True if safe mode was enabled successfully
        """
        self.settings.safe_mode = True
        success = self._save_security_config()
        if success:
            logger.info("Safe mode enabled")
        return success
    
    def disable_safe_mode(self) -> bool:
        """
        Disable safe mode (requires authentication if password is set)
        
        Returns:
            True if safe mode was disabled successfully
        """
        self.settings.safe_mode = False
        success = self._save_security_config()
        if success:
            logger.info("Safe mode disabled")
        return success
    
    def add_protected_command(self, intent: str) -> bool:
        """
        Add a command to the password protection list
        
        Args:
            intent: Command intent to protect
            
        Returns:
            True if command was added successfully
        """
        if intent not in self.settings.password_protected_commands:
            self.settings.password_protected_commands.append(intent)
            return self._save_security_config()
        return True
    
    def remove_protected_command(self, intent: str) -> bool:
        """
        Remove a command from the password protection list
        
        Args:
            intent: Command intent to unprotect
            
        Returns:
            True if command was removed successfully
        """
        if intent in self.settings.password_protected_commands:
            self.settings.password_commands.remove(intent)
            return self._save_security_config()
        return True
    
    def get_security_status(self) -> Dict[str, any]:
        """
        Get current security status
        
        Returns:
            Dictionary with security status information
        """
        return {
            'safe_mode': self.settings.safe_mode,
            'password_protected': self.settings.password_hash is not None,
            'confirmation_required': self.settings.require_confirmation,
            'authenticated_session': self.authenticated_session,
            'protected_commands_count': len(self.settings.password_protected_commands),
            'pending_confirmations': len(self.pending_confirmations),
            'failed_attempts': self.settings.failed_attempts
        }
    
    def reset_authentication(self) -> None:
        """Reset authentication session"""
        self.authenticated_session = False
        logger.info("Authentication session reset")
    
    def update_security_setting(self, setting: str, value: any) -> bool:
        """
        Update a security setting
        
        Args:
            setting: Setting name to update
            value: New value for the setting
            
        Returns:
            True if setting was updated successfully
        """
        if hasattr(self.settings, setting):
            setattr(self.settings, setting, value)
            return self._save_security_config()
        return False