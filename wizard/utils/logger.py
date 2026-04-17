"""
Logging system for Wizard Voice Assistant
Provides configurable logging with file output and different log levels.
"""

import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Optional


class WizardLogger:
    """Custom logger for Wizard Voice Assistant"""
    
    def __init__(self, 
                 name: str = "wizard",
                 log_level: str = "INFO",
                 log_dir: str = "logs",
                 max_file_size: int = 10 * 1024 * 1024,  # 10MB
                 backup_count: int = 5):
        """
        Initialize the Wizard logger
        
        Args:
            name: Logger name
            log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
            log_dir: Directory for log files
            max_file_size: Maximum size of log file before rotation
            backup_count: Number of backup files to keep
        """
        self.name = name
        self.log_level = getattr(logging, log_level.upper(), logging.INFO)
        self.log_dir = Path(log_dir)
        self.max_file_size = max_file_size
        self.backup_count = backup_count
        
        self.logger = self._setup_logger()
    
    def _setup_logger(self) -> logging.Logger:
        """Set up the logger with file and console handlers"""
        # Create logger
        logger = logging.getLogger(self.name)
        logger.setLevel(self.log_level)
        
        # Clear existing handlers
        logger.handlers.clear()
        
        # Create log directory if it doesn't exist
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
        # Create formatters
        detailed_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(module)s:%(funcName)s:%(lineno)d - %(message)s'
        )
        
        simple_formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s'
        )
        
        # File handler for all logs
        log_file = self.log_dir / f"{self.name}.log"
        file_handler = logging.handlers.RotatingFileHandler(
            log_file,
            maxBytes=self.max_file_size,
            backupCount=self.backup_count,
            encoding='utf-8'
        )
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(detailed_formatter)
        
        # File handler for errors only
        error_log_file = self.log_dir / f"{self.name}_errors.log"
        error_file_handler = logging.handlers.RotatingFileHandler(
            error_log_file,
            maxBytes=self.max_file_size,
            backupCount=self.backup_count,
            encoding='utf-8'
        )
        error_file_handler.setLevel(logging.ERROR)
        error_file_handler.setFormatter(detailed_formatter)
        
        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(self.log_level)
        console_handler.setFormatter(simple_formatter)
        
        # Add handlers to logger
        logger.addHandler(file_handler)
        logger.addHandler(error_file_handler)
        logger.addHandler(console_handler)
        
        return logger
    
    def debug(self, message: str, *args, **kwargs) -> None:
        """Log debug message"""
        self.logger.debug(message, *args, **kwargs)
    
    def info(self, message: str, *args, **kwargs) -> None:
        """Log info message"""
        self.logger.info(message, *args, **kwargs)
    
    def warning(self, message: str, *args, **kwargs) -> None:
        """Log warning message"""
        self.logger.warning(message, *args, **kwargs)
    
    def error(self, message: str, *args, **kwargs) -> None:
        """Log error message"""
        self.logger.error(message, *args, **kwargs)
    
    def critical(self, message: str, *args, **kwargs) -> None:
        """Log critical message"""
        self.logger.critical(message, *args, **kwargs)
    
    def exception(self, message: str, *args, **kwargs) -> None:
        """Log exception with traceback"""
        self.logger.exception(message, *args, **kwargs)
    
    def set_level(self, level: str) -> None:
        """Change the logging level"""
        new_level = getattr(logging, level.upper(), logging.INFO)
        self.logger.setLevel(new_level)
        
        # Update console handler level
        for handler in self.logger.handlers:
            if isinstance(handler, logging.StreamHandler) and not isinstance(handler, logging.FileHandler):
                handler.setLevel(new_level)
    
    def log_system_info(self) -> None:
        """Log system information at startup"""
        import platform
        import sys
        
        self.info("=" * 50)
        self.info("Wizard Voice Assistant Starting")
        self.info("=" * 50)
        self.info(f"Python Version: {sys.version}")
        self.info(f"Platform: {platform.platform()}")
        self.info(f"Architecture: {platform.architecture()}")
        self.info(f"Processor: {platform.processor()}")
        self.info(f"Log Level: {logging.getLevelName(self.log_level)}")
        self.info("=" * 50)


# Import rotating file handler
import logging.handlers

# Global logger instance
_wizard_logger: Optional[WizardLogger] = None


def get_logger(name: str = "wizard", 
               log_level: str = "INFO",
               log_dir: str = "logs") -> WizardLogger:
    """Get or create the global Wizard logger instance"""
    global _wizard_logger
    
    if _wizard_logger is None:
        _wizard_logger = WizardLogger(name, log_level, log_dir)
    
    return _wizard_logger


def setup_logging(log_level: str = "INFO", log_dir: str = "logs") -> WizardLogger:
    """Set up logging for the Wizard application"""
    logger = get_logger("wizard", log_level, log_dir)
    logger.log_system_info()
    return logger