"""
Command Integration Example

This module demonstrates how to integrate the command router with handlers
and shows the complete command processing pipeline.
"""

import sys
import logging
from pathlib import Path
from typing import Dict, Any

# Add the project root to Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from wizard.commands.command_router import CommandRouter, Command, Response
from wizard.utils.config_manager import ConfigManager

logger = logging.getLogger(__name__)


class CommandIntegrationExample:
    """
    Example integration showing how to use the command router with handlers
    """
    
    def __init__(self):
        # Load configuration
        config_manager = ConfigManager()
        self.config = config_manager.load_config()
        
        # Initialize command router
        self.router = CommandRouter(self.config.__dict__)
        
        # Register example handlers
        self._register_handlers()
    
    def _register_handlers(self):
        """Register command handlers for different intents"""
        
        # System control handlers
        self.router.register_handler("open_application", self._handle_open_application)
        self.router.register_handler("close_application", self._handle_close_application)
        self.router.register_handler("system_shutdown", self._handle_system_shutdown)
        
        # Volume control handlers
        self.router.register_handler("set_volume", self._handle_set_volume)
        self.router.register_handler("volume_up", self._handle_volume_up)
        self.router.register_handler("volume_down", self._handle_volume_down)
        
        # Media control handlers
        self.router.register_handler("play_music", self._handle_play_music)
        self.router.register_handler("pause_music", self._handle_pause_music)
        
        # Information handlers
        self.router.register_handler("what_time", self._handle_what_time)
        self.router.register_handler("calculate", self._handle_calculate)
        
        # File operations
        self.router.register_handler("search_files", self._handle_search_files)
        
        # Productivity
        self.router.register_handler("set_timer", self._handle_set_timer)
        
        # General queries
        self.router.register_handler("general_query", self._handle_general_query)
    
    def _handle_open_application(self, command: Command) -> Response:
        """Handle application opening commands"""
        app_name = command.entities.get("application", "unknown")
        
        # In a real implementation, this would actually launch the application
        logger.info(f"Opening application: {app_name}")
        
        return Response(
            text=f"Opening {app_name}",
            action_taken=True,
            context_updates={"last_opened_app": app_name}
        )
    
    def _handle_close_application(self, command: Command) -> Response:
        """Handle application closing commands"""
        app_name = command.entities.get("application", "unknown")
        
        # In a real implementation, this would actually close the application
        logger.info(f"Closing application: {app_name}")
        
        return Response(
            text=f"Closing {app_name}",
            action_taken=True,
            context_updates={"last_closed_app": app_name}
        )
    
    def _handle_system_shutdown(self, command: Command) -> Response:
        """Handle system shutdown commands"""
        # In a real implementation, this would require confirmation and actually shutdown
        logger.info("System shutdown requested")
        
        return Response(
            text="Are you sure you want to shutdown the computer? Please confirm.",
            action_taken=False,
            context_updates={"pending_action": "shutdown"}
        )
    
    def _handle_set_volume(self, command: Command) -> Response:
        """Handle volume setting commands"""
        volume_level = command.entities.get("volume_level", 50)
        
        # In a real implementation, this would actually set the system volume
        logger.info(f"Setting volume to {volume_level}%")
        
        return Response(
            text=f"Volume set to {volume_level} percent",
            action_taken=True,
            context_updates={"current_volume": volume_level}
        )
    
    def _handle_volume_up(self, command: Command) -> Response:
        """Handle volume up commands"""
        # In a real implementation, this would increase system volume
        logger.info("Increasing volume")
        
        return Response(
            text="Volume increased",
            action_taken=True
        )
    
    def _handle_volume_down(self, command: Command) -> Response:
        """Handle volume down commands"""
        # In a real implementation, this would decrease system volume
        logger.info("Decreasing volume")
        
        return Response(
            text="Volume decreased",
            action_taken=True
        )
    
    def _handle_play_music(self, command: Command) -> Response:
        """Handle music playback commands"""
        query = command.entities.get("query", "music")
        
        # In a real implementation, this would search and play music
        logger.info(f"Playing music: {query}")
        
        return Response(
            text=f"Playing {query}",
            action_taken=True,
            context_updates={"now_playing": query}
        )
    
    def _handle_pause_music(self, command: Command) -> Response:
        """Handle music pause commands"""
        # In a real implementation, this would pause current music
        logger.info("Pausing music")
        
        return Response(
            text="Music paused",
            action_taken=True,
            context_updates={"playback_state": "paused"}
        )
    
    def _handle_what_time(self, command: Command) -> Response:
        """Handle time query commands"""
        from datetime import datetime
        
        current_time = datetime.now().strftime("%I:%M %p")
        
        return Response(
            text=f"The current time is {current_time}",
            action_taken=True
        )
    
    def _handle_calculate(self, command: Command) -> Response:
        """Handle calculation commands"""
        # Simple calculation handling - in a real implementation this would be more robust
        numbers = command.entities.get("numbers", [])
        
        if len(numbers) >= 2:
            # Simple addition for demonstration
            result = sum(numbers)
            return Response(
                text=f"The result is {result}",
                action_taken=True
            )
        else:
            return Response(
                text="I need at least two numbers to calculate",
                action_taken=False
            )
    
    def _handle_search_files(self, command: Command) -> Response:
        """Handle file search commands"""
        query = command.entities.get("query", "")
        
        # In a real implementation, this would actually search files
        logger.info(f"Searching for files: {query}")
        
        return Response(
            text=f"Searching for files matching '{query}'",
            action_taken=True,
            context_updates={"last_search": query}
        )
    
    def _handle_set_timer(self, command: Command) -> Response:
        """Handle timer setting commands"""
        duration = command.entities.get("duration", 5)
        unit = command.entities.get("unit", "minute")
        
        # In a real implementation, this would actually set a timer
        logger.info(f"Setting timer for {duration} {unit}(s)")
        
        return Response(
            text=f"Timer set for {duration} {unit}{'s' if duration != 1 else ''}",
            action_taken=True,
            context_updates={"active_timer": f"{duration}_{unit}"}
        )
    
    def _handle_general_query(self, command: Command) -> Response:
        """Handle general knowledge queries"""
        query = command.entities.get("query", "")
        
        # In a real implementation, this would use the AI brain for responses
        logger.info(f"Processing general query: {query}")
        
        return Response(
            text=f"Let me think about {query}. This would be handled by the AI brain component.",
            action_taken=True,
            context_updates={"last_query": query}
        )
    
    def process_voice_command(self, voice_text: str) -> Response:
        """
        Complete pipeline for processing a voice command
        
        Args:
            voice_text: Raw voice command text
            
        Returns:
            Response object with result
        """
        logger.info(f"Processing voice command: {voice_text}")
        
        # Parse the command
        command = self.router.parse_command(voice_text)
        
        # Route to appropriate handler
        response = self.router.route_command(command)
        
        logger.info(f"Command processed - Intent: {command.intent}, Response: {response.text}")
        
        return response
    
    def get_system_status(self) -> Dict[str, Any]:
        """Get current system status and capabilities"""
        return {
            "supported_intents": self.router.get_supported_intents(),
            "registered_handlers": list(self.router.handlers.keys()),
            "known_applications": self.router.get_application_names(),
            "config_loaded": True
        }


def demo_command_processing():
    """Demonstrate the command processing pipeline"""
    print("=" * 60)
    print("WIZARD COMMAND PROCESSING INTEGRATION DEMO")
    print("=" * 60)
    
    # Initialize the integration
    integration = CommandIntegrationExample()
    
    # Show system status
    status = integration.get_system_status()
    print(f"\nSystem Status:")
    print(f"  Supported Intents: {len(status['supported_intents'])}")
    print(f"  Registered Handlers: {len(status['registered_handlers'])}")
    print(f"  Known Applications: {len(status['known_applications'])}")
    
    # Demo commands
    demo_commands = [
        "open chrome",
        "set volume to 75",
        "play my favorite playlist",
        "what time is it",
        "set timer for 10 minutes",
        "calculate 15 plus 25",
        "search for important documents",
        "shutdown computer"
    ]
    
    print(f"\nProcessing Demo Commands:")
    print("-" * 40)
    
    for cmd in demo_commands:
        print(f"\nUser: \"{cmd}\"")
        response = integration.process_voice_command(cmd)
        print(f"Wizard: {response.text}")
        if response.context_updates:
            print(f"Context: {response.context_updates}")
    
    print("\n" + "=" * 60)
    print("DEMO COMPLETED SUCCESSFULLY!")
    print("=" * 60)


if __name__ == "__main__":
    demo_command_processing()