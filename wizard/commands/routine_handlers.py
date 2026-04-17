"""
Routine Handlers Module

This module provides command handlers for routine and automation functionality.
"""

import logging
from typing import Dict, Any, List
from .command_router import Command, Response
from .routine_engine import RoutineEngine

logger = logging.getLogger(__name__)


class RoutineHandlers:
    """Handlers for routine and automation commands"""
    
    def __init__(self, config: Dict, routine_engine: RoutineEngine = None):
        self.config = config
        self.routine_engine = routine_engine
        
        if not self.routine_engine:
            self.routine_engine = RoutineEngine(config)
    
    def handle_execute_routine(self, command: Command) -> Response:
        """Handle routine execution commands"""
        try:
            routine_name = command.entities.get('routine_name', '').lower()
            
            # Handle common routine triggers
            if not routine_name:
                text = command.raw_text.lower()
                if 'good morning' in text or 'morning routine' in text:
                    routine_name = 'good_morning'
                elif 'good night' in text or 'night routine' in text:
                    routine_name = 'good_night'
                elif 'work mode' in text or 'work routine' in text:
                    routine_name = 'work_mode'
                else:
                    return Response(
                        text="Please specify which routine you'd like to run. Available routines: good morning, good night, work mode.",
                        error_message="No routine specified"
                    )
            
            # Execute the routine
            response = self.routine_engine.execute_routine(routine_name)
            return response
            
        except Exception as e:
            logger.error(f"Error executing routine: {e}")
            return Response(
                text=f"Sorry, I encountered an error while executing the routine: {str(e)}",
                error_message=str(e)
            )
    
    def handle_create_routine(self, command: Command) -> Response:
        """Handle routine creation commands"""
        try:
            # Extract routine details from command
            routine_name = command.entities.get('routine_name', '')
            description = command.entities.get('description', '')
            steps_data = command.entities.get('steps', [])
            
            if not routine_name:
                return Response(
                    text="Please provide a name for the routine.",
                    error_message="No routine name provided"
                )
            
            if not steps_data:
                return Response(
                    text="Please provide steps for the routine. For example: 'Create routine morning with steps: check time, check weather, open chrome'",
                    error_message="No routine steps provided"
                )
            
            # Create the routine
            success = self.routine_engine.create_routine(routine_name, description, steps_data)
            
            if success:
                return Response(
                    text=f"Successfully created routine '{routine_name}' with {len(steps_data)} steps.",
                    action_taken=True
                )
            else:
                return Response(
                    text=f"Failed to create routine '{routine_name}'. Please check the routine details.",
                    error_message="Routine creation failed"
                )
                
        except Exception as e:
            logger.error(f"Error creating routine: {e}")
            return Response(
                text=f"Sorry, I encountered an error while creating the routine: {str(e)}",
                error_message=str(e)
            )
    
    def handle_list_routines(self, command: Command) -> Response:
        """Handle listing available routines"""
        try:
            routines = self.routine_engine.list_routines()
            
            if not routines:
                return Response(
                    text="No routines are currently available. You can create custom routines or use the default ones like 'good morning'."
                )
            
            # Format routine list
            routine_text = "Available routines:\n"
            for routine in routines:
                status = "enabled" if routine['enabled'] else "disabled"
                last_run = routine['last_executed'] if routine['last_executed'] else "never"
                routine_text += f"• {routine['name']}: {routine['description']} ({routine['steps']} steps, {status}, last run: {last_run})\n"
            
            return Response(
                text=routine_text.strip(),
                action_taken=True
            )
            
        except Exception as e:
            logger.error(f"Error listing routines: {e}")
            return Response(
                text=f"Sorry, I encountered an error while listing routines: {str(e)}",
                error_message=str(e)
            )
    
    def handle_schedule_routine(self, command: Command) -> Response:
        """Handle routine scheduling commands"""
        try:
            routine_name = command.entities.get('routine_name', '')
            schedule_type = command.entities.get('schedule_type', 'daily')
            schedule_time = command.entities.get('schedule_time', '')
            
            if not routine_name:
                return Response(
                    text="Please specify which routine to schedule.",
                    error_message="No routine name provided"
                )
            
            if not schedule_time:
                return Response(
                    text="Please specify when to run the routine. For example: 'Schedule good morning routine daily at 8:00'",
                    error_message="No schedule time provided"
                )
            
            # Schedule the routine
            success = self.routine_engine.schedule_routine(routine_name, schedule_type, schedule_time)
            
            if success:
                return Response(
                    text=f"Successfully scheduled routine '{routine_name}' to run {schedule_type} at {schedule_time}.",
                    action_taken=True
                )
            else:
                return Response(
                    text=f"Failed to schedule routine '{routine_name}'. Please check the routine name and schedule details.",
                    error_message="Routine scheduling failed"
                )
                
        except Exception as e:
            logger.error(f"Error scheduling routine: {e}")
            return Response(
                text=f"Sorry, I encountered an error while scheduling the routine: {str(e)}",
                error_message=str(e)
            )
    
    def handle_routine_status(self, command: Command) -> Response:
        """Handle routine status queries"""
        try:
            status = self.routine_engine.get_routine_status()
            
            status_text = f"""Routine Engine Status:
• Total routines: {status['total_routines']} ({status['enabled_routines']} enabled)
• Currently running: {status['running_routines']} routines
• Scheduled tasks: {status['scheduled_tasks']} ({status['enabled_tasks']} enabled)
• Scheduler: {'running' if status['scheduler_running'] else 'stopped'}"""
            
            return Response(
                text=status_text,
                action_taken=True
            )
            
        except Exception as e:
            logger.error(f"Error getting routine status: {e}")
            return Response(
                text=f"Sorry, I encountered an error while getting routine status: {str(e)}",
                error_message=str(e)
            )


def register_routine_handlers(command_router, config: Dict) -> RoutineHandlers:
    """
    Register all routine handlers with the command router
    
    Args:
        command_router: CommandRouter instance
        config: Configuration dictionary
        
    Returns:
        RoutineHandlers instance
    """
    handlers = RoutineHandlers(config)
    
    # Register handlers
    command_router.register_handler("execute_routine", handlers.handle_execute_routine)
    command_router.register_handler("create_routine", handlers.handle_create_routine)
    command_router.register_handler("list_routines", handlers.handle_list_routines)
    command_router.register_handler("schedule_routine", handlers.handle_schedule_routine)
    command_router.register_handler("routine_status", handlers.handle_routine_status)
    
    # Register common routine triggers
    command_router.register_handler("good_morning", handlers.handle_execute_routine)
    command_router.register_handler("good_night", handlers.handle_execute_routine)
    command_router.register_handler("work_mode", handlers.handle_execute_routine)
    
    logger.info("Routine handlers registered successfully")
    return handlers