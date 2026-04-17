"""
Security Command Handlers for Wizard Voice Assistant

This module provides command handlers for security-related operations
including password management, safe mode control, and confirmation handling.
"""

import uuid
from typing import Dict, Any, Optional
# Add project root to Python path for imports
import sys
from pathlib import Path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))
from wizard.commands.command_router import Command, Response
from wizard.utils.security_module import SecurityModule
import logging

logger = logging.getLogger(__name__)


class SecurityHandlers:
    """Handles security-related voice commands"""
    
    def __init__(self, security_module: SecurityModule):
        self.security = security_module
    
    def handle_set_password(self, command: Command) -> Response:
        """Handle setting a security password"""
        password = command.entities.get('password')
        
        if not password:
            return Response(
                text="Please provide a password. For example, say 'set password to my secret phrase'",
                action_taken=False
            )
        
        success = self.security.set_password(password)
        
        if success:
            return Response(
                text="Security password has been set successfully. Protected commands will now require authentication.",
                action_taken=True
            )
        else:
            return Response(
                text="Failed to set password. Please ensure it's at least 4 characters long.",
                action_taken=False,
                error_message="Password validation failed"
            )
    
    def handle_authenticate(self, command: Command) -> Response:
        """Handle password authentication"""
        password = command.entities.get('password')
        
        if not password:
            return Response(
                text="Please provide your password for authentication.",
                action_taken=False
            )
        
        success = self.security.verify_password(password)
        
        if success:
            return Response(
                text="Authentication successful. You now have access to protected commands.",
                action_taken=True
            )
        else:
            attempts_left = self.security.settings.max_failed_attempts - self.security.settings.failed_attempts
            return Response(
                text=f"Authentication failed. You have {attempts_left} attempts remaining.",
                action_taken=False,
                error_message="Invalid password"
            )
    
    def handle_enable_safe_mode(self, command: Command) -> Response:
        """Handle enabling safe mode"""
        success = self.security.enable_safe_mode()
        
        if success:
            return Response(
                text="Safe mode enabled. Only basic commands are now available for security.",
                action_taken=True
            )
        else:
            return Response(
                text="Failed to enable safe mode.",
                action_taken=False,
                error_message="Safe mode activation failed"
            )
    
    def handle_disable_safe_mode(self, command: Command) -> Response:
        """Handle disabling safe mode"""
        # Check if authentication is required
        if self.security.settings.password_hash and not self.security.authenticated_session:
            return Response(
                text="Please authenticate first to disable safe mode. Say 'authenticate with password [your password]'",
                action_taken=False
            )
        
        success = self.security.disable_safe_mode()
        
        if success:
            return Response(
                text="Safe mode disabled. All commands are now available.",
                action_taken=True
            )
        else:
            return Response(
                text="Failed to disable safe mode.",
                action_taken=False,
                error_message="Safe mode deactivation failed"
            )
    
    def handle_security_status(self, command: Command) -> Response:
        """Handle security status inquiry"""
        status = self.security.get_security_status()
        
        status_text = f"""Security Status:
- Safe Mode: {'Enabled' if status['safe_mode'] else 'Disabled'}
- Password Protection: {'Enabled' if status['password_protected'] else 'Disabled'}
- Confirmation Required: {'Yes' if status['confirmation_required'] else 'No'}
- Current Session: {'Authenticated' if status['authenticated_session'] else 'Not Authenticated'}
- Protected Commands: {status['protected_commands_count']}
- Pending Confirmations: {status['pending_confirmations']}"""
        
        return Response(
            text=status_text,
            action_taken=True
        )
    
    def handle_confirmation_response(self, command: Command) -> Response:
        """Handle user confirmation responses"""
        confirmed, confirmation_id = self.security.process_confirmation(command.raw_text)
        
        if confirmation_id:
            if confirmed:
                return Response(
                    text=f"Confirmation received. Proceeding with the requested operation.",
                    action_taken=True,
                    context_updates={'confirmed_operation': confirmation_id}
                )
            else:
                return Response(
                    text="Operation cancelled as requested.",
                    action_taken=True
                )
        else:
            return Response(
                text="I didn't understand your confirmation response. Please say 'yes confirm [ID]' or 'no cancel [ID]'",
                action_taken=False
            )
    
    def handle_add_protected_command(self, command: Command) -> Response:
        """Handle adding a command to password protection"""
        command_name = command.entities.get('command_name')
        
        if not command_name:
            return Response(
                text="Please specify which command to protect. For example, 'protect command open application'",
                action_taken=False
            )
        
        success = self.security.add_protected_command(command_name)
        
        if success:
            return Response(
                text=f"Command '{command_name}' is now password protected.",
                action_taken=True
            )
        else:
            return Response(
                text=f"Failed to protect command '{command_name}'.",
                action_taken=False,
                error_message="Command protection failed"
            )
    
    def handle_remove_protected_command(self, command: Command) -> Response:
        """Handle removing a command from password protection"""
        command_name = command.entities.get('command_name')
        
        if not command_name:
            return Response(
                text="Please specify which command to unprotect. For example, 'unprotect command open application'",
                action_taken=False
            )
        
        success = self.security.remove_protected_command(command_name)
        
        if success:
            return Response(
                text=f"Command '{command_name}' is no longer password protected.",
                action_taken=True
            )
        else:
            return Response(
                text=f"Failed to unprotect command '{command_name}'.",
                action_taken=False,
                error_message="Command unprotection failed"
            )
    
    def handle_reset_security(self, command: Command) -> Response:
        """Handle resetting security settings"""
        # This is a critical operation that should require confirmation
        confirmation_id = str(uuid.uuid4())[:8]
        
        confirmation_msg = self.security.request_confirmation(
            "reset_security",
            "reset all security settings to defaults",
            confirmation_id
        )
        
        return Response(
            text=confirmation_msg,
            action_taken=False,
            context_updates={'pending_confirmation': confirmation_id}
        )
    
    def check_command_security(self, command: Command) -> tuple:
        """
        Check if a command passes security requirements
        
        Args:
            command: Command to check
            
        Returns:
            Tuple of (allowed, response_if_blocked)
        """
        # Clear expired confirmations
        self.security.clear_expired_confirmations()
        
        # Check if command is allowed in current mode
        if not self.security.is_command_allowed(command.intent):
            return False, Response(
                text=f"Command '{command.intent}' is not available in safe mode. Only basic commands are allowed.",
                action_taken=False,
                error_message="Command blocked by safe mode"
            )
        
        # Check if password is required
        if self.security.requires_password(command.intent):
            if not self.security.authenticated_session:
                return False, Response(
                    text=f"This command requires authentication. Please say 'authenticate with password [your password]' first.",
                    action_taken=False,
                    error_message="Authentication required"
                )
        
        # Check if confirmation is required
        if self.security.requires_confirmation(command.intent):
            confirmation_id = str(uuid.uuid4())[:8]
            
            # Generate confirmation message based on command
            details = self._get_confirmation_details(command)
            confirmation_msg = self.security.request_confirmation(
                command.intent,
                details,
                confirmation_id
            )
            
            return False, Response(
                text=confirmation_msg,
                action_taken=False,
                context_updates={'pending_confirmation': confirmation_id, 'original_command': command}
            )
        
        return True, None
    
    def _get_confirmation_details(self, command: Command) -> str:
        """Generate human-readable confirmation details for a command"""
        intent = command.intent
        entities = command.entities
        
        if intent == "system_shutdown":
            return "shut down the computer"
        elif intent == "system_restart":
            return "restart the computer"
        elif intent == "delete_file":
            target = entities.get('target', 'the file')
            return f"delete {target}"
        elif intent == "empty_recycle_bin":
            return "empty the recycle bin"
        elif intent == "batch_file_operation":
            operation = entities.get('operation_type', 'perform batch operation on')
            pattern = entities.get('source_pattern', 'files')
            return f"{operation} {pattern}"
        else:
            return f"execute {intent}"


def register_security_handlers(router, security_module: SecurityModule) -> None:
    """Register all security handlers with the command router"""
    handlers = SecurityHandlers(security_module)
    
    # Security management commands
    router.register_handler("set_password", handlers.handle_set_password)
    router.register_handler("authenticate", handlers.handle_authenticate)
    router.register_handler("enable_safe_mode", handlers.handle_enable_safe_mode)
    router.register_handler("disable_safe_mode", handlers.handle_disable_safe_mode)
    router.register_handler("security_status", handlers.handle_security_status)
    router.register_handler("confirmation_response", handlers.handle_confirmation_response)
    router.register_handler("add_protected_command", handlers.handle_add_protected_command)
    router.register_handler("remove_protected_command", handlers.handle_remove_protected_command)
    router.register_handler("reset_security", handlers.handle_reset_security)
    
    logger.info("Security handlers registered successfully")