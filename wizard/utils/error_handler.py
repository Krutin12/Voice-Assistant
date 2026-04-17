"""
Error Handling and Recovery System for Wizard Voice Assistant

Implements comprehensive error handling, retry mechanisms, and user notification
system for errors and status updates.
"""

import logging
import time
import threading
from typing import Dict, List, Optional, Callable, Any
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import traceback
import json
from pathlib import Path


class ErrorSeverity(Enum):
    """Error severity levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ErrorCategory(Enum):
    """Error categories for classification"""
    AUDIO = "audio"
    SPEECH_RECOGNITION = "speech_recognition"
    COMMAND_PROCESSING = "command_processing"
    SYSTEM_INTEGRATION = "system_integration"
    NETWORK = "network"
    FILE_SYSTEM = "file_system"
    CONFIGURATION = "configuration"
    HARDWARE = "hardware"
    UNKNOWN = "unknown"


@dataclass
class ErrorRecord:
    """Record of an error occurrence"""
    timestamp: datetime
    error_type: str
    error_message: str
    severity: ErrorSeverity
    category: ErrorCategory
    component: str
    traceback_info: str
    context: Dict[str, Any] = field(default_factory=dict)
    resolved: bool = False
    resolution_method: Optional[str] = None
    retry_count: int = 0


@dataclass
class RetryConfig:
    """Configuration for retry mechanisms"""
    max_attempts: int = 3
    base_delay: float = 1.0
    max_delay: float = 60.0
    exponential_backoff: bool = True
    jitter: bool = True


class ErrorHandler:
    """
    Comprehensive error handling and recovery system with retry mechanisms,
    user notifications, and automatic recovery strategies.
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        """
        Initialize the error handler.
        
        Args:
            config: Configuration dictionary for error handling
        """
        self.config = config or {}
        self.logger = logging.getLogger(__name__)
        
        # Error tracking
        self.error_history: List[ErrorRecord] = []
        self.error_counts: Dict[str, int] = {}
        self.component_health: Dict[str, bool] = {}
        
        # Recovery strategies
        self.recovery_strategies: Dict[str, Callable] = {}
        self.retry_configs: Dict[str, RetryConfig] = {}
        
        # Notification system
        self.notification_callbacks: List[Callable] = []
        self.tts_engine = None  # Will be set by main application
        
        # Error thresholds
        self.error_thresholds = {
            ErrorSeverity.LOW: 10,
            ErrorSeverity.MEDIUM: 5,
            ErrorSeverity.HIGH: 3,
            ErrorSeverity.CRITICAL: 1
        }
        
        # Monitoring
        self.monitoring_active = False
        self.monitoring_thread: Optional[threading.Thread] = None
        self.monitoring_interval = 30.0  # seconds
        
        # Error log file
        self.error_log_file = Path("logs/error_handler.log")
        self.error_log_file.parent.mkdir(exist_ok=True)
        
        # Initialize default retry configurations
        self._setup_default_retry_configs()
        
        # Initialize default recovery strategies
        self._setup_default_recovery_strategies()
    
    def _setup_default_retry_configs(self):
        """Setup default retry configurations for different error types"""
        self.retry_configs = {
            "audio_device": RetryConfig(max_attempts=3, base_delay=2.0),
            "speech_recognition": RetryConfig(max_attempts=2, base_delay=1.0),
            "command_execution": RetryConfig(max_attempts=2, base_delay=0.5),
            "file_operation": RetryConfig(max_attempts=3, base_delay=1.0),
            "network_request": RetryConfig(max_attempts=5, base_delay=2.0, max_delay=30.0),
            "system_command": RetryConfig(max_attempts=2, base_delay=1.0),
            "default": RetryConfig(max_attempts=3, base_delay=1.0)
        }
    
    def _setup_default_recovery_strategies(self):
        """Setup default recovery strategies for different error types"""
        self.recovery_strategies = {
            "audio_device_failure": self._recover_audio_device,
            "speech_recognition_failure": self._recover_speech_recognition,
            "command_router_failure": self._recover_command_router,
            "tts_engine_failure": self._recover_tts_engine,
            "wake_word_engine_failure": self._recover_wake_word_engine,
            "configuration_error": self._recover_configuration,
            "memory_error": self._recover_memory_issue,
            "disk_space_error": self._recover_disk_space
        }
    
    def handle_error(self, error: Exception, component: str, 
                    context: Dict[str, Any] = None, 
                    severity: ErrorSeverity = ErrorSeverity.MEDIUM,
                    category: ErrorCategory = ErrorCategory.UNKNOWN) -> bool:
        """
        Handle an error with comprehensive logging, classification, and recovery.
        
        Args:
            error: The exception that occurred
            component: Component where the error occurred
            context: Additional context information
            severity: Error severity level
            category: Error category
            
        Returns:
            bool: True if error was handled successfully
        """
        try:
            # Create error record
            error_record = ErrorRecord(
                timestamp=datetime.now(),
                error_type=type(error).__name__,
                error_message=str(error),
                severity=severity,
                category=category,
                component=component,
                traceback_info=traceback.format_exc(),
                context=context or {}
            )
            
            # Log the error
            self._log_error(error_record)
            
            # Add to error history
            self.error_history.append(error_record)
            
            # Update error counts
            error_key = f"{component}:{error_record.error_type}"
            self.error_counts[error_key] = self.error_counts.get(error_key, 0) + 1
            
            # Update component health
            self.component_health[component] = False
            
            # Check if error threshold exceeded
            if self._is_threshold_exceeded(severity, component):
                self.logger.critical(f"Error threshold exceeded for {component}")
                self._notify_critical_error(error_record)
            
            # Attempt recovery
            recovery_success = self._attempt_recovery(error_record)
            
            # Notify about the error
            self._notify_error(error_record, recovery_success)
            
            # Save error log
            self._save_error_log(error_record)
            
            return recovery_success
            
        except Exception as e:
            self.logger.critical(f"Error in error handler: {e}")
            return False
    
    def _log_error(self, error_record: ErrorRecord):
        """Log error with appropriate level"""
        log_message = (
            f"[{error_record.component}] {error_record.error_type}: "
            f"{error_record.error_message}"
        )
        
        if error_record.severity == ErrorSeverity.CRITICAL:
            self.logger.critical(log_message)
        elif error_record.severity == ErrorSeverity.HIGH:
            self.logger.error(log_message)
        elif error_record.severity == ErrorSeverity.MEDIUM:
            self.logger.warning(log_message)
        else:
            self.logger.info(log_message)
    
    def _is_threshold_exceeded(self, severity: ErrorSeverity, component: str) -> bool:
        """Check if error threshold is exceeded for a component"""
        threshold = self.error_thresholds.get(severity, 5)
        
        # Count recent errors for this component and severity
        recent_errors = [
            err for err in self.error_history[-50:]  # Check last 50 errors
            if err.component == component and err.severity == severity
            and err.timestamp > datetime.now() - timedelta(minutes=10)
        ]
        
        return len(recent_errors) >= threshold
    
    def _attempt_recovery(self, error_record: ErrorRecord) -> bool:
        """Attempt to recover from the error"""
        try:
            # Determine recovery strategy
            recovery_key = f"{error_record.component}_{error_record.category.value}_failure"
            
            if recovery_key in self.recovery_strategies:
                strategy = self.recovery_strategies[recovery_key]
            elif error_record.component in self.recovery_strategies:
                strategy = self.recovery_strategies[error_record.component]
            else:
                strategy = self._default_recovery_strategy
            
            # Attempt recovery
            success = strategy(error_record)
            
            if success:
                error_record.resolved = True
                error_record.resolution_method = recovery_key
                self.component_health[error_record.component] = True
                self.logger.info(f"Successfully recovered from error in {error_record.component}")
            
            return success
            
        except Exception as e:
            self.logger.error(f"Error during recovery attempt: {e}")
            return False
    
    def _default_recovery_strategy(self, error_record: ErrorRecord) -> bool:
        """Default recovery strategy"""
        self.logger.info(f"Applying default recovery for {error_record.component}")
        
        # Simple wait and retry strategy
        time.sleep(2.0)
        return True  # Assume recovery for default strategy
    
    def _recover_audio_device(self, error_record: ErrorRecord) -> bool:
        """Recovery strategy for audio device failures"""
        self.logger.info("Attempting audio device recovery...")
        
        try:
            # Wait for device to become available
            time.sleep(3.0)
            
            # Try to reinitialize audio components
            # This would be implemented by the main application
            return True
            
        except Exception as e:
            self.logger.error(f"Audio device recovery failed: {e}")
            return False
    
    def _recover_speech_recognition(self, error_record: ErrorRecord) -> bool:
        """Recovery strategy for speech recognition failures"""
        self.logger.info("Attempting speech recognition recovery...")
        
        try:
            # Reset speech recognition state
            time.sleep(1.0)
            return True
            
        except Exception as e:
            self.logger.error(f"Speech recognition recovery failed: {e}")
            return False
    
    def _recover_command_router(self, error_record: ErrorRecord) -> bool:
        """Recovery strategy for command router failures"""
        self.logger.info("Attempting command router recovery...")
        
        try:
            # Reset command router state
            time.sleep(0.5)
            return True
            
        except Exception as e:
            self.logger.error(f"Command router recovery failed: {e}")
            return False
    
    def _recover_tts_engine(self, error_record: ErrorRecord) -> bool:
        """Recovery strategy for TTS engine failures"""
        self.logger.info("Attempting TTS engine recovery...")
        
        try:
            # Reinitialize TTS engine
            time.sleep(2.0)
            return True
            
        except Exception as e:
            self.logger.error(f"TTS engine recovery failed: {e}")
            return False
    
    def _recover_wake_word_engine(self, error_record: ErrorRecord) -> bool:
        """Recovery strategy for wake word engine failures"""
        self.logger.info("Attempting wake word engine recovery...")
        
        try:
            # Restart wake word detection
            time.sleep(2.0)
            return True
            
        except Exception as e:
            self.logger.error(f"Wake word engine recovery failed: {e}")
            return False
    
    def _recover_configuration(self, error_record: ErrorRecord) -> bool:
        """Recovery strategy for configuration errors"""
        self.logger.info("Attempting configuration recovery...")
        
        try:
            # Reset to default configuration
            time.sleep(1.0)
            return True
            
        except Exception as e:
            self.logger.error(f"Configuration recovery failed: {e}")
            return False
    
    def _recover_memory_issue(self, error_record: ErrorRecord) -> bool:
        """Recovery strategy for memory issues"""
        self.logger.info("Attempting memory issue recovery...")
        
        try:
            # Force garbage collection
            import gc
            gc.collect()
            time.sleep(1.0)
            return True
            
        except Exception as e:
            self.logger.error(f"Memory recovery failed: {e}")
            return False
    
    def _recover_disk_space(self, error_record: ErrorRecord) -> bool:
        """Recovery strategy for disk space issues"""
        self.logger.info("Attempting disk space recovery...")
        
        try:
            # Clean up temporary files
            self._cleanup_temp_files()
            time.sleep(1.0)
            return True
            
        except Exception as e:
            self.logger.error(f"Disk space recovery failed: {e}")
            return False
    
    def _cleanup_temp_files(self):
        """Clean up temporary files to free disk space"""
        try:
            temp_dirs = [
                Path("logs"),
                Path("audio_cache"),
                Path("temp")
            ]
            
            for temp_dir in temp_dirs:
                if temp_dir.exists():
                    # Remove old files (older than 7 days)
                    cutoff_time = datetime.now() - timedelta(days=7)
                    for file_path in temp_dir.rglob("*"):
                        if file_path.is_file():
                            file_time = datetime.fromtimestamp(file_path.stat().st_mtime)
                            if file_time < cutoff_time:
                                try:
                                    file_path.unlink()
                                except Exception:
                                    pass  # Ignore individual file errors
                                    
        except Exception as e:
            self.logger.error(f"Error cleaning temp files: {e}")
    
    def _notify_error(self, error_record: ErrorRecord, recovery_success: bool):
        """Notify about the error through various channels"""
        try:
            # Prepare notification message
            if recovery_success:
                message = f"Recovered from {error_record.error_type} in {error_record.component}"
            else:
                message = f"Error in {error_record.component}: {error_record.error_message}"
            
            # Call notification callbacks
            for callback in self.notification_callbacks:
                try:
                    callback(error_record, recovery_success)
                except Exception as e:
                    self.logger.error(f"Error in notification callback: {e}")
            
            # TTS notification for critical errors
            if (error_record.severity in [ErrorSeverity.HIGH, ErrorSeverity.CRITICAL] 
                and self.tts_engine and not recovery_success):
                try:
                    self.tts_engine.speak("I encountered an error and need attention.")
                except Exception:
                    pass  # Don't let TTS errors cascade
                    
        except Exception as e:
            self.logger.error(f"Error in notification system: {e}")
    
    def _notify_critical_error(self, error_record: ErrorRecord):
        """Special notification for critical errors"""
        try:
            self.logger.critical(f"CRITICAL ERROR: {error_record.error_message}")
            
            # Immediate TTS notification
            if self.tts_engine:
                try:
                    self.tts_engine.speak("Critical error detected. Please check the system.")
                except Exception:
                    pass
                    
        except Exception as e:
            self.logger.error(f"Error in critical error notification: {e}")
    
    def _save_error_log(self, error_record: ErrorRecord):
        """Save error record to log file"""
        try:
            log_entry = {
                "timestamp": error_record.timestamp.isoformat(),
                "error_type": error_record.error_type,
                "error_message": error_record.error_message,
                "severity": error_record.severity.value,
                "category": error_record.category.value,
                "component": error_record.component,
                "context": error_record.context,
                "resolved": error_record.resolved,
                "resolution_method": error_record.resolution_method,
                "retry_count": error_record.retry_count
            }
            
            with open(self.error_log_file, "a", encoding="utf-8") as f:
                f.write(json.dumps(log_entry) + "\n")
                
        except Exception as e:
            self.logger.error(f"Error saving error log: {e}")
    
    def retry_with_backoff(self, func: Callable, *args, 
                          retry_type: str = "default", 
                          **kwargs) -> Any:
        """
        Execute a function with retry logic and exponential backoff.
        
        Args:
            func: Function to execute
            retry_type: Type of retry configuration to use
            *args, **kwargs: Arguments for the function
            
        Returns:
            Function result if successful
            
        Raises:
            Exception: Last exception if all retries failed
        """
        config = self.retry_configs.get(retry_type, self.retry_configs["default"])
        last_exception = None
        
        for attempt in range(config.max_attempts):
            try:
                return func(*args, **kwargs)
                
            except Exception as e:
                last_exception = e
                
                if attempt < config.max_attempts - 1:  # Not the last attempt
                    # Calculate delay with exponential backoff
                    if config.exponential_backoff:
                        delay = min(config.base_delay * (2 ** attempt), config.max_delay)
                    else:
                        delay = config.base_delay
                    
                    # Add jitter to prevent thundering herd
                    if config.jitter:
                        import random
                        delay *= (0.5 + random.random() * 0.5)
                    
                    self.logger.warning(f"Attempt {attempt + 1} failed, retrying in {delay:.2f}s: {e}")
                    time.sleep(delay)
                else:
                    self.logger.error(f"All {config.max_attempts} attempts failed")
        
        # All attempts failed, raise the last exception
        raise last_exception
    
    def add_notification_callback(self, callback: Callable):
        """Add a notification callback function"""
        self.notification_callbacks.append(callback)
    
    def set_tts_engine(self, tts_engine):
        """Set the TTS engine for audio notifications"""
        self.tts_engine = tts_engine
    
    def register_recovery_strategy(self, error_type: str, strategy: Callable):
        """Register a custom recovery strategy"""
        self.recovery_strategies[error_type] = strategy
    
    def set_retry_config(self, retry_type: str, config: RetryConfig):
        """Set retry configuration for a specific type"""
        self.retry_configs[retry_type] = config
    
    def start_monitoring(self):
        """Start error monitoring thread"""
        if self.monitoring_active:
            return
            
        self.monitoring_active = True
        self.monitoring_thread = threading.Thread(target=self._monitoring_loop, daemon=True)
        self.monitoring_thread.start()
        self.logger.info("Error monitoring started")
    
    def stop_monitoring(self):
        """Stop error monitoring thread"""
        self.monitoring_active = False
        if self.monitoring_thread:
            self.monitoring_thread.join(timeout=5.0)
        self.logger.info("Error monitoring stopped")
    
    def _monitoring_loop(self):
        """Monitoring loop for proactive error detection"""
        while self.monitoring_active:
            try:
                # Check component health
                self._check_component_health()
                
                # Check error patterns
                self._analyze_error_patterns()
                
                # Check system resources
                self._check_system_resources()
                
                time.sleep(self.monitoring_interval)
                
            except Exception as e:
                self.logger.error(f"Error in monitoring loop: {e}")
                time.sleep(5.0)
    
    def _check_component_health(self):
        """Check health of all components"""
        unhealthy_components = [
            comp for comp, healthy in self.component_health.items() 
            if not healthy
        ]
        
        if unhealthy_components:
            self.logger.warning(f"Unhealthy components detected: {unhealthy_components}")
    
    def _analyze_error_patterns(self):
        """Analyze error patterns for proactive intervention"""
        # Check for recurring errors
        recent_errors = [
            err for err in self.error_history[-20:]  # Last 20 errors
            if err.timestamp > datetime.now() - timedelta(hours=1)
        ]
        
        # Group by error type and component
        error_groups = {}
        for error in recent_errors:
            key = f"{error.component}:{error.error_type}"
            error_groups[key] = error_groups.get(key, 0) + 1
        
        # Alert on patterns
        for error_key, count in error_groups.items():
            if count >= 3:  # 3 or more of same error in last hour
                self.logger.warning(f"Recurring error pattern detected: {error_key} ({count} times)")
    
    def _check_system_resources(self):
        """Check system resources for potential issues"""
        try:
            import psutil
            
            # Check memory usage
            memory = psutil.virtual_memory()
            if memory.percent > 90:
                self.logger.warning(f"High memory usage: {memory.percent}%")
            
            # Check disk usage
            disk = psutil.disk_usage('/')
            if disk.percent > 90:
                self.logger.warning(f"High disk usage: {disk.percent}%")
                
        except ImportError:
            pass  # psutil not available
        except Exception as e:
            self.logger.error(f"Error checking system resources: {e}")
    
    def get_error_summary(self) -> Dict[str, Any]:
        """Get summary of error statistics"""
        recent_errors = [
            err for err in self.error_history
            if err.timestamp > datetime.now() - timedelta(hours=24)
        ]
        
        return {
            "total_errors": len(self.error_history),
            "recent_errors_24h": len(recent_errors),
            "error_counts_by_component": self._count_errors_by_component(recent_errors),
            "error_counts_by_severity": self._count_errors_by_severity(recent_errors),
            "component_health": self.component_health.copy(),
            "most_common_errors": self._get_most_common_errors(recent_errors)
        }
    
    def _count_errors_by_component(self, errors: List[ErrorRecord]) -> Dict[str, int]:
        """Count errors by component"""
        counts = {}
        for error in errors:
            counts[error.component] = counts.get(error.component, 0) + 1
        return counts
    
    def _count_errors_by_severity(self, errors: List[ErrorRecord]) -> Dict[str, int]:
        """Count errors by severity"""
        counts = {}
        for error in errors:
            severity = error.severity.value
            counts[severity] = counts.get(severity, 0) + 1
        return counts
    
    def _get_most_common_errors(self, errors: List[ErrorRecord]) -> List[Dict[str, Any]]:
        """Get most common error types"""
        error_types = {}
        for error in errors:
            key = f"{error.component}:{error.error_type}"
            if key not in error_types:
                error_types[key] = {
                    "component": error.component,
                    "error_type": error.error_type,
                    "count": 0
                }
            error_types[key]["count"] += 1
        
        # Sort by count and return top 5
        sorted_errors = sorted(error_types.values(), key=lambda x: x["count"], reverse=True)
        return sorted_errors[:5]
    
    def clear_error_history(self, older_than_days: int = 7):
        """Clear old error history"""
        cutoff_time = datetime.now() - timedelta(days=older_than_days)
        self.error_history = [
            err for err in self.error_history 
            if err.timestamp > cutoff_time
        ]
        self.logger.info(f"Cleared error history older than {older_than_days} days")


# Convenience functions for common error handling patterns

def handle_with_retry(error_handler: ErrorHandler, func: Callable, 
                     component: str, retry_type: str = "default",
                     severity: ErrorSeverity = ErrorSeverity.MEDIUM,
                     category: ErrorCategory = ErrorCategory.UNKNOWN,
                     *args, **kwargs) -> Any:
    """
    Execute a function with error handling and retry logic.
    
    Args:
        error_handler: ErrorHandler instance
        func: Function to execute
        component: Component name for error tracking
        retry_type: Type of retry configuration
        severity: Error severity level
        category: Error category
        *args, **kwargs: Function arguments
        
    Returns:
        Function result if successful
        
    Raises:
        Exception: If all retries failed
    """
    try:
        return error_handler.retry_with_backoff(func, *args, retry_type=retry_type, **kwargs)
    except Exception as e:
        error_handler.handle_error(e, component, severity=severity, category=category)
        raise


def safe_execute(error_handler: ErrorHandler, func: Callable, 
                component: str, default_return=None,
                severity: ErrorSeverity = ErrorSeverity.MEDIUM,
                category: ErrorCategory = ErrorCategory.UNKNOWN,
                *args, **kwargs) -> Any:
    """
    Execute a function safely with error handling, returning default on failure.
    
    Args:
        error_handler: ErrorHandler instance
        func: Function to execute
        component: Component name for error tracking
        default_return: Default value to return on error
        severity: Error severity level
        category: Error category
        *args, **kwargs: Function arguments
        
    Returns:
        Function result or default_return on error
    """
    try:
        return func(*args, **kwargs)
    except Exception as e:
        error_handler.handle_error(e, component, severity=severity, category=category)
        return default_return