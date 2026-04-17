"""
Batch Operation Handlers Module

This module provides command handlers for batch operations, auto-responses,
and user preference management.
"""

import logging
from typing import Dict, Any, List
from .command_router import Command, Response
from .batch_operations import BatchOperationSystem, BatchFileOperation

logger = logging.getLogger(__name__)


class BatchHandlers:
    """Handlers for batch operations and automation commands"""
    
    def __init__(self, config: Dict, batch_system: BatchOperationSystem = None):
        self.config = config
        self.batch_system = batch_system
        
        if not self.batch_system:
            self.batch_system = BatchOperationSystem(config)
    
    def handle_batch_file_operation(self, command: Command) -> Response:
        """Handle batch file operations"""
        try:
            operation_type = command.entities.get('operation_type', 'copy')
            source_pattern = command.entities.get('source_pattern', '')
            destination = command.entities.get('destination', '')
            recursive = command.entities.get('recursive', False)
            confirm_each = command.entities.get('confirm_each', True)
            dry_run = command.entities.get('dry_run', False)
            
            if not source_pattern:
                return Response(
                    text="Please specify the source files or pattern for the batch operation.",
                    error_message="No source pattern provided"
                )
            
            # Create batch operation
            operation = BatchFileOperation(
                operation_type=operation_type,
                source_pattern=source_pattern,
                destination=destination,
                recursive=recursive,
                confirm_each=confirm_each,
                dry_run=dry_run
            )
            
            # Execute the operation
            response = self.batch_system.execute_batch_file_operation(operation)
            return response
            
        except Exception as e:
            logger.error(f"Error handling batch file operation: {e}")
            return Response(
                text=f"Sorry, I encountered an error during the batch operation: {str(e)}",
                error_message=str(e)
            )
    
    def handle_auto_response_management(self, command: Command) -> Response:
        """Handle auto-response management commands"""
        try:
            action = command.entities.get('action', 'list')
            
            if action == 'list':
                auto_responses = list(self.batch_system.auto_responses.keys())
                if not auto_responses:
                    return Response(
                        text="No auto-responses are currently configured."
                    )
                
                response_text = "Configured auto-responses:\n"
                for name in auto_responses:
                    ar = self.batch_system.auto_responses[name]
                    status = "enabled" if ar.enabled else "disabled"
                    usage = ar.usage_count
                    response_text += f"• {name}: {ar.response_text[:50]}... ({status}, used {usage} times)\n"
                
                return Response(
                    text=response_text.strip(),
                    action_taken=True
                )
            
            elif action == 'add':
                name = command.entities.get('name', '')
                triggers = command.entities.get('triggers', [])
                response_text = command.entities.get('response_text', '')
                
                if not all([name, triggers, response_text]):
                    return Response(
                        text="To add an auto-response, please provide: name, trigger patterns, and response text.",
                        error_message="Missing required parameters"
                    )
                
                success = self.batch_system.add_auto_response(name, triggers, response_text)
                
                if success:
                    return Response(
                        text=f"Successfully added auto-response '{name}'.",
                        action_taken=True
                    )
                else:
                    return Response(
                        text=f"Failed to add auto-response '{name}'.",
                        error_message="Auto-response creation failed"
                    )
            
            else:
                return Response(
                    text="Available auto-response actions: list, add",
                    error_message="Unknown action"
                )
                
        except Exception as e:
            logger.error(f"Error handling auto-response management: {e}")
            return Response(
                text=f"Sorry, I encountered an error managing auto-responses: {str(e)}",
                error_message=str(e)
            )
    
    def handle_personalized_suggestions(self, command: Command) -> Response:
        """Handle requests for personalized suggestions"""
        try:
            context = command.entities.get('context', command.raw_text)
            suggestions = self.batch_system.get_personalized_suggestions(context)
            
            if not suggestions:
                return Response(
                    text="I don't have enough information about your preferences yet. Keep using me and I'll learn what you like!"
                )
            
            response_text = "Based on your usage patterns, here are some personalized suggestions:\n"
            for i, suggestion in enumerate(suggestions, 1):
                response_text += f"{i}. {suggestion}\n"
            
            return Response(
                text=response_text.strip(),
                action_taken=True
            )
            
        except Exception as e:
            logger.error(f"Error generating personalized suggestions: {e}")
            return Response(
                text=f"Sorry, I encountered an error generating suggestions: {str(e)}",
                error_message=str(e)
            )
    
    def handle_preference_management(self, command: Command) -> Response:
        """Handle user preference management"""
        try:
            action = command.entities.get('action', 'show')
            
            if action == 'show':
                # Show top preferences by category
                categories = ['applications', 'entertainment', 'audio', 'time_patterns', 'usage_patterns']
                response_text = "Your learned preferences:\n\n"
                
                for category in categories:
                    prefs = self.batch_system._get_top_preferences(category, 3)
                    if prefs:
                        response_text += f"{category.title()}:\n"
                        for pref in prefs:
                            confidence_pct = int(pref['confidence'] * 100)
                            response_text += f"• {pref['key']}: {pref['value']} ({confidence_pct}% confidence, used {pref['usage_count']} times)\n"
                        response_text += "\n"
                
                if len(response_text.strip()) == len("Your learned preferences:"):
                    response_text = "I haven't learned enough about your preferences yet. Keep using me and I'll start to understand what you like!"
                
                return Response(
                    text=response_text.strip(),
                    action_taken=True
                )
            
            elif action == 'clear':
                category = command.entities.get('category', 'all')
                
                if category == 'all':
                    self.batch_system.user_preferences.clear()
                    self.batch_system._save_user_preferences()
                    return Response(
                        text="All learned preferences have been cleared.",
                        action_taken=True
                    )
                else:
                    # Clear specific category
                    keys_to_remove = [k for k, v in self.batch_system.user_preferences.items() if v.category == category]
                    for key in keys_to_remove:
                        del self.batch_system.user_preferences[key]
                    
                    self.batch_system._save_user_preferences()
                    return Response(
                        text=f"Preferences for category '{category}' have been cleared.",
                        action_taken=True
                    )
            
            else:
                return Response(
                    text="Available preference actions: show, clear",
                    error_message="Unknown action"
                )
                
        except Exception as e:
            logger.error(f"Error handling preference management: {e}")
            return Response(
                text=f"Sorry, I encountered an error managing preferences: {str(e)}",
                error_message=str(e)
            )
    
    def handle_batch_status(self, command: Command) -> Response:
        """Handle batch system status queries"""
        try:
            status = self.batch_system.get_batch_operation_status()
            
            status_text = f"""Batch Operation System Status:
• Auto-responses: {status['auto_responses']} total ({status['enabled_auto_responses']} enabled)
• User preferences: {status['user_preferences']} learned
• Command history: {status['command_history_size']} commands recorded

Top Usage Patterns:"""
            
            for pref in status['top_preferences']:
                confidence_pct = int(pref['confidence'] * 100)
                status_text += f"\n• {pref['value']}: {confidence_pct}% confidence"
            
            return Response(
                text=status_text,
                action_taken=True
            )
            
        except Exception as e:
            logger.error(f"Error getting batch status: {e}")
            return Response(
                text=f"Sorry, I encountered an error getting system status: {str(e)}",
                error_message=str(e)
            )
    
    def check_auto_response(self, command_text: str) -> Response:
        """Check if command should trigger an auto-response"""
        return self.batch_system.check_auto_response(command_text)
    
    def record_command(self, command: Command, response: Response) -> None:
        """Record command for preference learning"""
        self.batch_system.record_command(command, response)


def register_batch_handlers(command_router, config: Dict) -> BatchHandlers:
    """
    Register all batch operation handlers with the command router
    
    Args:
        command_router: CommandRouter instance
        config: Configuration dictionary
        
    Returns:
        BatchHandlers instance
    """
    handlers = BatchHandlers(config)
    
    # Register handlers
    command_router.register_handler("batch_file_operation", handlers.handle_batch_file_operation)
    command_router.register_handler("auto_response_management", handlers.handle_auto_response_management)
    command_router.register_handler("personalized_suggestions", handlers.handle_personalized_suggestions)
    command_router.register_handler("preference_management", handlers.handle_preference_management)
    command_router.register_handler("batch_status", handlers.handle_batch_status)
    
    logger.info("Batch operation handlers registered successfully")
    return handlers