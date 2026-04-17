"""
User Notification System for Wizard Voice Assistant

Provides comprehensive user notification capabilities for errors, status updates,
system events, and user feedback through multiple channels.
"""

import logging
import threading
import time
import queue
from typing import Dict, List, Optional, Callable, Any, Union
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import json
from pathlib import Path


class NotificationType(Enum):
    """Types of notifications"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    SUCCESS = "success"
    SYSTEM_STATUS = "system_status"
    COMMAND_FEEDBACK = "command_feedback"
    REMINDER = "reminder"
    ALERT = "alert"


class NotificationPriority(Enum):
    """Notification priority levels"""
    LOW = 1
    NORMAL = 2
    HIGH = 3
    URGENT = 4


class NotificationChannel(Enum):
    """Available notification channels"""
    VOICE = "voice"
    LOG = "log"
    CONSOLE = "console"
    FILE = "file"
    CALLBACK = "callback"


@dataclass
class Notification:
    """Notification message structure"""
    id: str
    type: NotificationType
    priority: NotificationPriority
    title: str
    message: str
    timestamp: datetime = field(default_factory=datetime.now)
    channels: List[NotificationChannel] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    expires_at: Optional[datetime] = None
    acknowledged: bool = False
    retry_count: int = 0
    max_retries: int = 3


@dataclass
class NotificationConfig:
    """Configuration for notification system"""
    enabled_channels: List[NotificationChannel] = field(default_factory=lambda: [
        NotificationChannel.VOICE, NotificationChannel.LOG
    ])
    voice_enabled: bool = True
    voice_priority_threshold: NotificationPriority = NotificationPriority.NORMAL
    log_level_mapping: Dict[NotificationType, str] = field(default_factory=lambda: {
        NotificationType.INFO: "INFO",
        NotificationType.WARNING: "WARNING", 
        NotificationType.ERROR: "ERROR",
        NotificationType.SUCCESS: "INFO",
        NotificationType.SYSTEM_STATUS: "INFO",
        NotificationType.COMMAND_FEEDBACK: "DEBUG",
        NotificationType.REMINDER: "INFO",
        NotificationType.ALERT: "WARNING"
    })
    max_queue_size: int = 1000
    notification_timeout: float = 30.0
    retry_delay: float = 5.0


class NotificationSystem:
    """
    Comprehensive notification system for user feedback and status updates
    with multiple delivery channels and priority handling.
    """
    
    def __init__(self, config: NotificationConfig = None):
        """
        Initialize the notification system.
        
        Args:
            config: Notification system configuration
        """
        self.config = config or NotificationConfig()
        self.logger = logging.getLogger(__name__)
        
        # Notification queue and processing
        self.notification_queue = queue.PriorityQueue(maxsize=self.config.max_queue_size)
        self.processing_thread: Optional[threading.Thread] = None
        self.running = False
        
        # Notification history and tracking
        self.notification_history: List[Notification] = []
        self.pending_notifications: Dict[str, Notification] = {}
        self.notification_counter = 0
        
        # External components
        self.tts_engine = None
        self.callback_handlers: Dict[NotificationType, List[Callable]] = {}
        
        # Status tracking
        self.system_status = {
            "last_update": datetime.now(),
            "component_status": {},
            "error_count": 0,
            "warning_count": 0
        }
        
        # Notification templates
        self.message_templates = self._load_message_templates()
        
        # File logging
        self.notification_log_file = Path("logs/notifications.log")
        self.notification_log_file.parent.mkdir(exist_ok=True)
    
    def _load_message_templates(self) -> Dict[str, str]:
        """Load message templates for different notification types"""
        return {
            "system_startup": "System is starting up...",
            "system_ready": "System is ready and listening for commands.",
            "system_shutdown": "System is shutting down. Goodbye!",
            "error_occurred": "An error occurred: {error_message}",
            "error_recovered": "Successfully recovered from error in {component}.",
            "command_executed": "Command executed successfully.",
            "command_failed": "Command failed: {error_message}",
            "wake_word_detected": "Wake word detected, listening...",
            "speech_recognized": "I heard: {text}",
            "speech_not_recognized": "I didn't catch that. Could you please repeat?",
            "low_confidence": "I'm not sure I understood correctly.",
            "component_failure": "{component} is not responding properly.",
            "component_recovered": "{component} has been restored.",
            "reminder_notification": "Reminder: {reminder_text}",
            "timer_expired": "Timer '{timer_name}' has expired.",
            "system_resource_warning": "System resources are running low: {resource_type}",
            "configuration_updated": "Configuration has been updated.",
            "unknown_command": "I don't understand that command. Try asking for help."
        }
    
    def start(self):
        """Start the notification processing system"""
        if self.running:
            return
            
        self.running = True
        self.processing_thread = threading.Thread(target=self._processing_loop, daemon=True)
        self.processing_thread.start()
        self.logger.info("Notification system started")
    
    def stop(self):
        """Stop the notification processing system"""
        if not self.running:
            return
            
        self.running = False
        
        # Add sentinel to wake up processing thread
        try:
            self.notification_queue.put((0, 0, None), timeout=1.0)
        except queue.Full:
            pass
        
        if self.processing_thread:
            self.processing_thread.join(timeout=5.0)
        
        self.logger.info("Notification system stopped")
    
    def _processing_loop(self):
        """Main notification processing loop"""
        while self.running:
            try:
                # Get next notification with timeout
                try:
                    queue_item = self.notification_queue.get(timeout=1.0)
                    
                    # Handle tuple format (priority, id, notification) or (priority, notification)
                    if len(queue_item) == 3:
                        priority, notification_id, notification = queue_item
                    else:
                        priority, notification = queue_item
                    
                    # Check for sentinel (shutdown signal)
                    if notification is None:
                        break
                        
                    # Process the notification
                    self._process_notification(notification)
                    
                except queue.Empty:
                    continue
                    
            except Exception as e:
                self.logger.error(f"Error in notification processing loop: {e}")
                time.sleep(1.0)
    
    def _process_notification(self, notification: Notification):
        """Process a single notification through all channels"""
        try:
            self.logger.debug(f"Processing notification: {notification.id}")
            
            # Check if notification has expired
            if notification.expires_at and datetime.now() > notification.expires_at:
                self.logger.debug(f"Notification {notification.id} has expired")
                return
            
            # Process through each channel
            success = False
            for channel in notification.channels:
                if channel in self.config.enabled_channels:
                    try:
                        if self._send_to_channel(notification, channel):
                            success = True
                    except Exception as e:
                        self.logger.error(f"Error sending notification to {channel.value}: {e}")
            
            # Handle retry logic
            if not success and notification.retry_count < notification.max_retries:
                notification.retry_count += 1
                self.logger.warning(f"Retrying notification {notification.id} (attempt {notification.retry_count})")
                
                # Re-queue with delay
                threading.Timer(
                    self.config.retry_delay,
                    lambda: self._requeue_notification(notification)
                ).start()
            else:
                # Mark as processed
                notification.acknowledged = True
                self.notification_history.append(notification)
                
                # Remove from pending
                if notification.id in self.pending_notifications:
                    del self.pending_notifications[notification.id]
            
        except Exception as e:
            self.logger.error(f"Error processing notification {notification.id}: {e}")
    
    def _send_to_channel(self, notification: Notification, channel: NotificationChannel) -> bool:
        """Send notification to a specific channel"""
        try:
            if channel == NotificationChannel.VOICE:
                return self._send_voice_notification(notification)
            elif channel == NotificationChannel.LOG:
                return self._send_log_notification(notification)
            elif channel == NotificationChannel.CONSOLE:
                return self._send_console_notification(notification)
            elif channel == NotificationChannel.FILE:
                return self._send_file_notification(notification)
            elif channel == NotificationChannel.CALLBACK:
                return self._send_callback_notification(notification)
            else:
                self.logger.warning(f"Unknown notification channel: {channel}")
                return False
                
        except Exception as e:
            self.logger.error(f"Error sending to channel {channel.value}: {e}")
            return False
    
    def _send_voice_notification(self, notification: Notification) -> bool:
        """Send notification via text-to-speech"""
        if not self.config.voice_enabled or not self.tts_engine:
            return False
            
        # Check priority threshold
        if notification.priority.value < self.config.voice_priority_threshold.value:
            return False
            
        try:
            # Use title for voice if message is too long
            text = notification.title if len(notification.message) > 100 else notification.message
            self.tts_engine.speak(text, async_mode=True)
            return True
            
        except Exception as e:
            self.logger.error(f"Error in voice notification: {e}")
            return False
    
    def _send_log_notification(self, notification: Notification) -> bool:
        """Send notification to log"""
        try:
            log_level = self.config.log_level_mapping.get(notification.type, "INFO")
            log_message = f"[{notification.type.value.upper()}] {notification.title}: {notification.message}"
            
            if log_level == "DEBUG":
                self.logger.debug(log_message)
            elif log_level == "INFO":
                self.logger.info(log_message)
            elif log_level == "WARNING":
                self.logger.warning(log_message)
            elif log_level == "ERROR":
                self.logger.error(log_message)
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error in log notification: {e}")
            return False
    
    def _send_console_notification(self, notification: Notification) -> bool:
        """Send notification to console"""
        try:
            timestamp = notification.timestamp.strftime("%H:%M:%S")
            print(f"[{timestamp}] {notification.title}: {notification.message}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error in console notification: {e}")
            return False
    
    def _send_file_notification(self, notification: Notification) -> bool:
        """Send notification to file"""
        try:
            log_entry = {
                "id": notification.id,
                "timestamp": notification.timestamp.isoformat(),
                "type": notification.type.value,
                "priority": notification.priority.value,
                "title": notification.title,
                "message": notification.message,
                "metadata": notification.metadata
            }
            
            with open(self.notification_log_file, "a", encoding="utf-8") as f:
                f.write(json.dumps(log_entry) + "\n")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error in file notification: {e}")
            return False
    
    def _send_callback_notification(self, notification: Notification) -> bool:
        """Send notification via registered callbacks"""
        try:
            callbacks = self.callback_handlers.get(notification.type, [])
            success = False
            
            for callback in callbacks:
                try:
                    callback(notification)
                    success = True
                except Exception as e:
                    self.logger.error(f"Error in notification callback: {e}")
            
            return success
            
        except Exception as e:
            self.logger.error(f"Error in callback notification: {e}")
            return False
    
    def _requeue_notification(self, notification: Notification):
        """Re-queue a notification for retry"""
        try:
            priority_value = 10 - notification.priority.value  # Higher priority = lower number
            # Use a tuple to ensure proper comparison
            self.notification_queue.put((priority_value, id(notification), notification), timeout=1.0)
        except queue.Full:
            self.logger.warning(f"Notification queue full, dropping notification {notification.id}")
    
    def notify(self, type: NotificationType, title: str, message: str = "",
              priority: NotificationPriority = NotificationPriority.NORMAL,
              channels: List[NotificationChannel] = None,
              metadata: Dict[str, Any] = None,
              expires_in_seconds: Optional[float] = None) -> str:
        """
        Send a notification through the system.
        
        Args:
            type: Type of notification
            title: Notification title
            message: Detailed message (optional)
            priority: Notification priority
            channels: Specific channels to use (optional)
            metadata: Additional metadata (optional)
            expires_in_seconds: Expiration time in seconds (optional)
            
        Returns:
            str: Notification ID
        """
        try:
            # Generate unique ID
            self.notification_counter += 1
            notification_id = f"notif_{self.notification_counter}_{int(time.time())}"
            
            # Use default channels if none specified
            if channels is None:
                channels = self.config.enabled_channels
            
            # Calculate expiration time
            expires_at = None
            if expires_in_seconds:
                expires_at = datetime.now() + timedelta(seconds=expires_in_seconds)
            elif self.config.notification_timeout > 0:
                expires_at = datetime.now() + timedelta(seconds=self.config.notification_timeout)
            
            # Create notification
            notification = Notification(
                id=notification_id,
                type=type,
                priority=priority,
                title=title,
                message=message or title,
                channels=channels,
                metadata=metadata or {},
                expires_at=expires_at
            )
            
            # Add to pending notifications
            self.pending_notifications[notification_id] = notification
            
            # Queue for processing
            priority_value = 10 - priority.value  # Higher priority = lower number
            self.notification_queue.put((priority_value, id(notification), notification), timeout=1.0)
            
            return notification_id
            
        except queue.Full:
            self.logger.error("Notification queue is full")
            return ""
        except Exception as e:
            self.logger.error(f"Error creating notification: {e}")
            return ""
    
    def notify_template(self, template_name: str, priority: NotificationPriority = NotificationPriority.NORMAL,
                       channels: List[NotificationChannel] = None, **kwargs) -> str:
        """
        Send a notification using a predefined template.
        
        Args:
            template_name: Name of the message template
            priority: Notification priority
            channels: Specific channels to use
            **kwargs: Template variables
            
        Returns:
            str: Notification ID
        """
        try:
            if template_name not in self.message_templates:
                self.logger.warning(f"Unknown notification template: {template_name}")
                return ""
            
            # Format template message
            message = self.message_templates[template_name].format(**kwargs)
            
            # Determine notification type from template name
            if "error" in template_name:
                type = NotificationType.ERROR
            elif "warning" in template_name:
                type = NotificationType.WARNING
            elif "success" in template_name or "ready" in template_name:
                type = NotificationType.SUCCESS
            else:
                type = NotificationType.INFO
            
            return self.notify(
                type=type,
                title=template_name.replace("_", " ").title(),
                message=message,
                priority=priority,
                channels=channels,
                metadata={"template": template_name, "template_vars": kwargs}
            )
            
        except Exception as e:
            self.logger.error(f"Error using notification template: {e}")
            return ""
    
    def notify_error(self, title: str, message: str = "", 
                    priority: NotificationPriority = NotificationPriority.HIGH,
                    **kwargs) -> str:
        """Convenience method for error notifications"""
        return self.notify(NotificationType.ERROR, title, message, priority, **kwargs)
    
    def notify_warning(self, title: str, message: str = "",
                      priority: NotificationPriority = NotificationPriority.NORMAL,
                      **kwargs) -> str:
        """Convenience method for warning notifications"""
        return self.notify(NotificationType.WARNING, title, message, priority, **kwargs)
    
    def notify_success(self, title: str, message: str = "",
                      priority: NotificationPriority = NotificationPriority.NORMAL,
                      **kwargs) -> str:
        """Convenience method for success notifications"""
        return self.notify(NotificationType.SUCCESS, title, message, priority, **kwargs)
    
    def notify_info(self, title: str, message: str = "",
                   priority: NotificationPriority = NotificationPriority.LOW,
                   **kwargs) -> str:
        """Convenience method for info notifications"""
        return self.notify(NotificationType.INFO, title, message, priority, **kwargs)
    
    def notify_system_status(self, component: str, status: str, healthy: bool = True) -> str:
        """Notify about system component status"""
        self.system_status["component_status"][component] = {
            "status": status,
            "healthy": healthy,
            "last_update": datetime.now()
        }
        
        priority = NotificationPriority.NORMAL if healthy else NotificationPriority.HIGH
        type = NotificationType.SUCCESS if healthy else NotificationType.WARNING
        
        return self.notify(
            type=type,
            title=f"{component} Status",
            message=f"{component}: {status}",
            priority=priority,
            metadata={"component": component, "healthy": healthy}
        )
    
    def update_system_status(self, error_count: int = None, warning_count: int = None):
        """Update overall system status"""
        if error_count is not None:
            self.system_status["error_count"] = error_count
        if warning_count is not None:
            self.system_status["warning_count"] = warning_count
        
        self.system_status["last_update"] = datetime.now()
    
    def acknowledge_notification(self, notification_id: str) -> bool:
        """Acknowledge a notification"""
        try:
            if notification_id in self.pending_notifications:
                self.pending_notifications[notification_id].acknowledged = True
                return True
            return False
        except Exception as e:
            self.logger.error(f"Error acknowledging notification: {e}")
            return False
    
    def set_tts_engine(self, tts_engine):
        """Set the TTS engine for voice notifications"""
        self.tts_engine = tts_engine
    
    def register_callback(self, notification_type: NotificationType, callback: Callable):
        """Register a callback for specific notification types"""
        if notification_type not in self.callback_handlers:
            self.callback_handlers[notification_type] = []
        self.callback_handlers[notification_type].append(callback)
    
    def unregister_callback(self, notification_type: NotificationType, callback: Callable):
        """Unregister a callback"""
        if notification_type in self.callback_handlers:
            try:
                self.callback_handlers[notification_type].remove(callback)
            except ValueError:
                pass
    
    def get_pending_notifications(self) -> List[Notification]:
        """Get list of pending notifications"""
        return list(self.pending_notifications.values())
    
    def get_notification_history(self, limit: int = 100) -> List[Notification]:
        """Get notification history"""
        return self.notification_history[-limit:]
    
    def get_system_status(self) -> Dict[str, Any]:
        """Get current system status"""
        return self.system_status.copy()
    
    def clear_old_notifications(self, older_than_hours: int = 24):
        """Clear old notifications from history"""
        cutoff_time = datetime.now() - timedelta(hours=older_than_hours)
        self.notification_history = [
            notif for notif in self.notification_history
            if notif.timestamp > cutoff_time
        ]
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get notification system statistics"""
        recent_notifications = [
            notif for notif in self.notification_history
            if notif.timestamp > datetime.now() - timedelta(hours=24)
        ]
        
        type_counts = {}
        priority_counts = {}
        
        for notif in recent_notifications:
            type_counts[notif.type.value] = type_counts.get(notif.type.value, 0) + 1
            priority_counts[notif.priority.value] = priority_counts.get(notif.priority.value, 0) + 1
        
        return {
            "total_notifications": len(self.notification_history),
            "recent_notifications_24h": len(recent_notifications),
            "pending_notifications": len(self.pending_notifications),
            "queue_size": self.notification_queue.qsize(),
            "notifications_by_type": type_counts,
            "notifications_by_priority": priority_counts,
            "system_status": self.system_status
        }


# Convenience functions for common notification patterns

def create_notification_system(tts_engine=None, voice_enabled: bool = True) -> NotificationSystem:
    """
    Create a notification system with default configuration.
    
    Args:
        tts_engine: TTS engine for voice notifications
        voice_enabled: Whether to enable voice notifications
        
    Returns:
        NotificationSystem: Configured notification system
    """
    config = NotificationConfig(voice_enabled=voice_enabled)
    system = NotificationSystem(config)
    
    if tts_engine:
        system.set_tts_engine(tts_engine)
    
    return system


def notify_command_result(notification_system: NotificationSystem, 
                         command: str, success: bool, message: str = "") -> str:
    """
    Notify about command execution result.
    
    Args:
        notification_system: Notification system instance
        command: Command that was executed
        success: Whether command succeeded
        message: Additional message
        
    Returns:
        str: Notification ID
    """
    if success:
        return notification_system.notify_success(
            title="Command Executed",
            message=f"Successfully executed: {command}. {message}".strip(),
            metadata={"command": command, "success": True}
        )
    else:
        return notification_system.notify_error(
            title="Command Failed", 
            message=f"Failed to execute: {command}. {message}".strip(),
            metadata={"command": command, "success": False}
        )


def notify_component_status(notification_system: NotificationSystem,
                          component: str, status: str, healthy: bool = True) -> str:
    """
    Notify about component status change.
    
    Args:
        notification_system: Notification system instance
        component: Component name
        status: Status description
        healthy: Whether component is healthy
        
    Returns:
        str: Notification ID
    """
    return notification_system.notify_system_status(component, status, healthy)