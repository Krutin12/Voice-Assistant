"""
System Command Handlers

This module provides command handlers for system control operations
including application management, window control, and system operations.
"""

import logging
import sys
from pathlib import Path
from typing import Dict, Any

# Add project root to Python path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from wizard.commands.command_router import Command, Response
from wizard.commands.system_controller import SystemController

logger = logging.getLogger(__name__)


class SystemCommandHandlers:
    """
    Command handlers for system control operations
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize system command handlers
        
        Args:
            config: Configuration dictionary
        """
        self.config = config
        self.system_controller = SystemController(config)
        self.pending_confirmations = {}  # Store pending confirmation requests
    
    def handle_open_application(self, command: Command) -> Response:
        """
        Handle application opening commands
        
        Args:
            command: Parsed command object
            
        Returns:
            Response object with result
        """
        try:
            app_name = command.entities.get("application", "").strip()
            
            if not app_name:
                return Response(
                    text="Please specify which application you'd like me to open.",
                    action_taken=False
                )
            
            logger.info(f"Opening application: {app_name}")
            success, message = self.system_controller.open_application(app_name)
            
            if success:
                return Response(
                    text=f"Opening {app_name}.",
                    action_taken=True,
                    context_updates={"last_opened_app": app_name}
                )
            else:
                return Response(
                    text=f"I couldn't open {app_name}. {message}",
                    action_taken=False,
                    error_message=message
                )
                
        except Exception as e:
            logger.error(f"Error in handle_open_application: {e}")
            return Response(
                text=f"Sorry, I encountered an error while trying to open the application: {str(e)}",
                action_taken=False,
                error_message=str(e)
            )
    
    def handle_close_application(self, command: Command) -> Response:
        """
        Handle application closing commands
        
        Args:
            command: Parsed command object
            
        Returns:
            Response object with result
        """
        try:
            app_name = command.entities.get("application", "").strip()
            
            if not app_name:
                return Response(
                    text="Please specify which application you'd like me to close.",
                    action_taken=False
                )
            
            logger.info(f"Closing application: {app_name}")
            
            # Check if this is a confirmation for a previous close request
            confirmation_key = f"close_{app_name}_{command.user_id}"
            if confirmation_key in self.pending_confirmations:
                # User confirmed, proceed with force close
                success, message = self.system_controller.close_application(app_name, force=True)
                del self.pending_confirmations[confirmation_key]
                
                if success:
                    return Response(
                        text=f"Closed {app_name}. {message}",
                        action_taken=True,
                        context_updates={"last_closed_app": app_name}
                    )
                else:
                    return Response(
                        text=f"I couldn't close {app_name}. {message}",
                        action_taken=False,
                        error_message=message
                    )
            else:
                # First attempt - try graceful close
                success, message = self.system_controller.close_application(app_name, force=False)
                
                if success:
                    return Response(
                        text=f"Closed {app_name}. {message}",
                        action_taken=True,
                        context_updates={"last_closed_app": app_name}
                    )
                else:
                    # Store pending confirmation for force close
                    self.pending_confirmations[confirmation_key] = True
                    return Response(
                        text=f"I couldn't close {app_name} gracefully. Would you like me to force close it? Say 'close {app_name}' again to confirm.",
                        action_taken=False,
                        context_updates={"pending_confirmation": confirmation_key}
                    )
                    
        except Exception as e:
            logger.error(f"Error in handle_close_application: {e}")
            return Response(
                text=f"Sorry, I encountered an error while trying to close the application: {str(e)}",
                action_taken=False,
                error_message=str(e)
            )
    
    def handle_window_control(self, command: Command) -> Response:
        """
        Handle window control commands (minimize, maximize, etc.)
        
        Args:
            command: Parsed command object
            
        Returns:
            Response object with result
        """
        try:
            # Extract action from the command intent or entities
            action = None
            window_title = command.entities.get("window_title", None)
            
            # Determine action from intent
            if "minimize" in command.intent:
                action = "minimize"
            elif "maximize" in command.intent:
                action = "maximize"
            elif "restore" in command.intent:
                action = "restore"
            elif "close" in command.intent and "window" in command.raw_text:
                action = "close"
            else:
                # Try to extract action from raw text
                text_lower = command.raw_text.lower()
                if "minimize" in text_lower:
                    action = "minimize"
                elif "maximize" in text_lower:
                    action = "maximize"
                elif "restore" in text_lower:
                    action = "restore"
                elif "close" in text_lower:
                    action = "close"
            
            if not action:
                return Response(
                    text="Please specify what you'd like me to do with the window (minimize, maximize, restore, or close).",
                    action_taken=False
                )
            
            logger.info(f"Window control: {action}, target: {window_title}")
            success, message = self.system_controller.control_window(action, window_title)
            
            if success:
                return Response(
                    text=message,
                    action_taken=True,
                    context_updates={"last_window_action": action}
                )
            else:
                return Response(
                    text=f"I couldn't {action} the window. {message}",
                    action_taken=False,
                    error_message=message
                )
                
        except Exception as e:
            logger.error(f"Error in handle_window_control: {e}")
            return Response(
                text=f"Sorry, I encountered an error while controlling the window: {str(e)}",
                action_taken=False,
                error_message=str(e)
            )
    
    def handle_system_shutdown(self, command: Command) -> Response:
        """
        Handle system shutdown commands
        
        Args:
            command: Parsed command object
            
        Returns:
            Response object with result
        """
        try:
            # Check if this is a confirmation
            confirmation_key = f"shutdown_{command.user_id}"
            
            if confirmation_key in self.pending_confirmations:
                # User confirmed shutdown
                del self.pending_confirmations[confirmation_key]
                
                success, message = self.system_controller.system_shutdown(confirm=True)
                
                if success:
                    return Response(
                        text=message,
                        action_taken=True,
                        context_updates={"system_action": "shutdown"}
                    )
                else:
                    return Response(
                        text=f"I couldn't shutdown the system. {message}",
                        action_taken=False,
                        error_message=message
                    )
            else:
                # Request confirmation
                self.pending_confirmations[confirmation_key] = True
                return Response(
                    text="Are you sure you want to shutdown the computer? This will close all applications and turn off the system. Say 'shutdown computer' again to confirm.",
                    action_taken=False,
                    context_updates={"pending_confirmation": confirmation_key}
                )
                
        except Exception as e:
            logger.error(f"Error in handle_system_shutdown: {e}")
            return Response(
                text=f"Sorry, I encountered an error while trying to shutdown: {str(e)}",
                action_taken=False,
                error_message=str(e)
            )
    
    def handle_system_restart(self, command: Command) -> Response:
        """
        Handle system restart commands
        
        Args:
            command: Parsed command object
            
        Returns:
            Response object with result
        """
        try:
            # Check if this is a confirmation
            confirmation_key = f"restart_{command.user_id}"
            
            if confirmation_key in self.pending_confirmations:
                # User confirmed restart
                del self.pending_confirmations[confirmation_key]
                
                success, message = self.system_controller.system_restart(confirm=True)
                
                if success:
                    return Response(
                        text=message,
                        action_taken=True,
                        context_updates={"system_action": "restart"}
                    )
                else:
                    return Response(
                        text=f"I couldn't restart the system. {message}",
                        action_taken=False,
                        error_message=message
                    )
            else:
                # Request confirmation
                self.pending_confirmations[confirmation_key] = True
                return Response(
                    text="Are you sure you want to restart the computer? This will close all applications and restart the system. Say 'restart computer' again to confirm.",
                    action_taken=False,
                    context_updates={"pending_confirmation": confirmation_key}
                )
                
        except Exception as e:
            logger.error(f"Error in handle_system_restart: {e}")
            return Response(
                text=f"Sorry, I encountered an error while trying to restart: {str(e)}",
                action_taken=False,
                error_message=str(e)
            )
    
    def handle_system_lock(self, command: Command) -> Response:
        """
        Handle system lock commands
        
        Args:
            command: Parsed command object
            
        Returns:
            Response object with result
        """
        try:
            logger.info("Locking system")
            success, message = self.system_controller.system_lock()
            
            if success:
                return Response(
                    text=message,
                    action_taken=True,
                    context_updates={"system_action": "lock"}
                )
            else:
                return Response(
                    text=f"I couldn't lock the system. {message}",
                    action_taken=False,
                    error_message=message
                )
                
        except Exception as e:
            logger.error(f"Error in handle_system_lock: {e}")
            return Response(
                text=f"Sorry, I encountered an error while trying to lock the system: {str(e)}",
                action_taken=False,
                error_message=str(e)
            )
    
    def handle_system_logout(self, command: Command) -> Response:
        """
        Handle system logout commands
        
        Args:
            command: Parsed command object
            
        Returns:
            Response object with result
        """
        try:
            # Check if this is a confirmation
            confirmation_key = f"logout_{command.user_id}"
            
            if confirmation_key in self.pending_confirmations:
                # User confirmed logout
                del self.pending_confirmations[confirmation_key]
                
                success, message = self.system_controller.system_logout()
                
                if success:
                    return Response(
                        text=message,
                        action_taken=True,
                        context_updates={"system_action": "logout"}
                    )
                else:
                    return Response(
                        text=f"I couldn't logout. {message}",
                        action_taken=False,
                        error_message=message
                    )
            else:
                # Request confirmation
                self.pending_confirmations[confirmation_key] = True
                return Response(
                    text="Are you sure you want to logout? This will close all applications and end your session. Say 'logout' again to confirm.",
                    action_taken=False,
                    context_updates={"pending_confirmation": confirmation_key}
                )
                
        except Exception as e:
            logger.error(f"Error in handle_system_logout: {e}")
            return Response(
                text=f"Sorry, I encountered an error while trying to logout: {str(e)}",
                action_taken=False,
                error_message=str(e)
            )
    
    def handle_take_screenshot(self, command: Command) -> Response:
        """
        Handle screenshot commands
        
        Args:
            command: Parsed command object
            
        Returns:
            Response object with result
        """
        try:
            filename = command.entities.get("filename", None)
            
            logger.info(f"Taking screenshot, filename: {filename}")
            success, message = self.system_controller.take_screenshot(filename)
            
            if success:
                return Response(
                    text=f"Screenshot taken. {message}",
                    action_taken=True,
                    context_updates={"last_screenshot": message}
                )
            else:
                return Response(
                    text=f"I couldn't take a screenshot. {message}",
                    action_taken=False,
                    error_message=message
                )
                
        except Exception as e:
            logger.error(f"Error in handle_take_screenshot: {e}")
            return Response(
                text=f"Sorry, I encountered an error while taking a screenshot: {str(e)}",
                action_taken=False,
                error_message=str(e)
            )
    
    def handle_screen_recording(self, command: Command) -> Response:
        """
        Handle screen recording commands
        
        Args:
            command: Parsed command object
            
        Returns:
            Response object with result
        """
        try:
            filename = command.entities.get("filename", None)
            duration = command.entities.get("duration", 30)
            
            # Try to extract duration from numbers in the command
            numbers = command.entities.get("numbers", [])
            if numbers:
                duration = numbers[0]
            
            logger.info(f"Starting screen recording, filename: {filename}, duration: {duration}")
            success, message = self.system_controller.start_screen_recording(filename, duration)
            
            if success:
                return Response(
                    text=message,
                    action_taken=True,
                    context_updates={"recording_started": True, "recording_duration": duration}
                )
            else:
                return Response(
                    text=f"I couldn't start screen recording. {message}",
                    action_taken=False,
                    error_message=message
                )
                
        except Exception as e:
            logger.error(f"Error in handle_screen_recording: {e}")
            return Response(
                text=f"Sorry, I encountered an error while starting screen recording: {str(e)}",
                action_taken=False,
                error_message=str(e)
            )
    
    def handle_empty_recycle_bin(self, command: Command) -> Response:
        """
        Handle empty recycle bin commands
        
        Args:
            command: Parsed command object
            
        Returns:
            Response object with result
        """
        try:
            # Check if this is a confirmation
            confirmation_key = f"empty_recycle_bin_{command.user_id}"
            
            if confirmation_key in self.pending_confirmations:
                # User confirmed
                del self.pending_confirmations[confirmation_key]
                
                success, message = self.system_controller.empty_recycle_bin()
                
                if success:
                    return Response(
                        text=message,
                        action_taken=True,
                        context_updates={"system_action": "empty_recycle_bin"}
                    )
                else:
                    return Response(
                        text=f"I couldn't empty the recycle bin. {message}",
                        action_taken=False,
                        error_message=message
                    )
            else:
                # Request confirmation
                self.pending_confirmations[confirmation_key] = True
                return Response(
                    text="Are you sure you want to empty the recycle bin? This will permanently delete all items in the recycle bin. Say 'empty recycle bin' again to confirm.",
                    action_taken=False,
                    context_updates={"pending_confirmation": confirmation_key}
                )
                
        except Exception as e:
            logger.error(f"Error in handle_empty_recycle_bin: {e}")
            return Response(
                text=f"Sorry, I encountered an error while emptying the recycle bin: {str(e)}",
                action_taken=False,
                error_message=str(e)
            )
    
    def handle_get_running_apps(self, command: Command) -> Response:
        """
        Handle requests to list running applications
        
        Args:
            command: Parsed command object
            
        Returns:
            Response object with result
        """
        try:
            logger.info("Getting list of running applications")
            applications = self.system_controller.get_running_applications()
            
            if applications:
                # Filter to show only user applications (not system processes)
                user_apps = [app for app in applications if app['memory_mb'] > 10 and 
                           not app['name'].lower().startswith(('system', 'dwm', 'csrss', 'winlogon'))]
                
                if user_apps:
                    # Sort by memory usage and take top 10
                    user_apps.sort(key=lambda x: x['memory_mb'], reverse=True)
                    top_apps = user_apps[:10]
                    
                    app_list = []
                    for app in top_apps:
                        app_list.append(f"{app['name']} ({app['memory_mb']:.1f} MB)")
                    
                    response_text = f"Here are the top running applications: {', '.join(app_list)}"
                else:
                    response_text = "I found system processes running, but no major user applications."
            else:
                response_text = "I couldn't retrieve the list of running applications."
            
            return Response(
                text=response_text,
                action_taken=True,
                context_updates={"running_apps_count": len(applications)}
            )
            
        except Exception as e:
            logger.error(f"Error in handle_get_running_apps: {e}")
            return Response(
                text=f"Sorry, I encountered an error while getting running applications: {str(e)}",
                action_taken=False,
                error_message=str(e)
            )
    
    def handle_get_system_info(self, command: Command) -> Response:
        """
        Handle requests for system information
        
        Args:
            command: Parsed command object
            
        Returns:
            Response object with result
        """
        try:
            logger.info("Getting system information")
            system_info = self.system_controller.get_system_info()
            
            if system_info:
                response_parts = []
                response_parts.append(f"System: {system_info.get('platform', 'Unknown')}")
                response_parts.append(f"Processor: {system_info.get('processor', 'Unknown')}")
                response_parts.append(f"Memory: {system_info.get('memory_available_gb', 0):.1f} GB available of {system_info.get('memory_total_gb', 0):.1f} GB total")
                
                disk_info = system_info.get('disk_usage', {})
                if disk_info:
                    response_parts.append(f"Disk: {disk_info.get('free_gb', 0):.1f} GB free of {disk_info.get('total_gb', 0):.1f} GB total")
                
                response_text = ". ".join(response_parts)
            else:
                response_text = "I couldn't retrieve system information."
            
            return Response(
                text=response_text,
                action_taken=True,
                context_updates={"system_info_retrieved": True}
            )
            
        except Exception as e:
            logger.error(f"Error in handle_get_system_info: {e}")
            return Response(
                text=f"Sorry, I encountered an error while getting system information: {str(e)}",
                action_taken=False,
                error_message=str(e)
            )
    
    def register_handlers(self, router):
        """
        Register all system command handlers with the router
        
        Args:
            router: CommandRouter instance to register handlers with
        """
        # Application management
        router.register_handler("open_application", self.handle_open_application)
        router.register_handler("close_application", self.handle_close_application)
        
        # Window control
        router.register_handler("minimize_window", self.handle_window_control)
        router.register_handler("maximize_window", self.handle_window_control)
        router.register_handler("restore_window", self.handle_window_control)
        router.register_handler("close_window", self.handle_window_control)
        
        # System operations
        router.register_handler("system_shutdown", self.handle_system_shutdown)
        router.register_handler("system_restart", self.handle_system_restart)
        router.register_handler("system_lock", self.handle_system_lock)
        router.register_handler("system_logout", self.handle_system_logout)
        
        # Screenshot and recording
        router.register_handler("take_screenshot", self.handle_take_screenshot)
        router.register_handler("screen_recording", self.handle_screen_recording)
        
        # Recycle bin management
        router.register_handler("empty_recycle_bin", self.handle_empty_recycle_bin)
        
        # System information
        router.register_handler("get_running_apps", self.handle_get_running_apps)
        router.register_handler("get_system_info", self.handle_get_system_info)
        
        logger.info("System command handlers registered successfully")