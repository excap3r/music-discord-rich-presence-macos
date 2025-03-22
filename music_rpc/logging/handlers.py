"""
Logging utility for Music RPC.

This module provides a centralized logging system that handles both file
and console output with proper formatting and log rotation.
"""
import logging
import os
import sys
from logging.handlers import RotatingFileHandler
from typing import Dict, Optional, Any, Union


class Logger:
    """Centralized logging utility for the application.
    
    This class provides a unified interface for logging throughout the application
    with support for both file and console logging, configurable log levels,
    and automatic log rotation to prevent log files from growing too large.
    """
    
    def __init__(self, config: Any) -> None:
        """Initialize the logger with configuration.

        Args:
            config: Config object containing logging settings including
                   LOG_LEVEL, LOG_FILE, MAX_LOG_SIZE, and LOG_BACKUP_COUNT
        """
        self.config = config
        self.logger = self._setup_logger()
    
    def _setup_logger(self) -> logging.Logger:
        """Configure the logger with file and console handlers.
        
        Creates a logger with both file (with rotation) and console handlers,
        each with appropriate formatting and log levels based on configuration.
        
        Returns:
            logging.Logger: The configured logger instance
        """
        # Convert string level to logging level
        level_map: Dict[str, int] = {
            "DEBUG": logging.DEBUG,
            "INFO": logging.INFO,
            "WARNING": logging.WARNING,
            "ERROR": logging.ERROR,
            "CRITICAL": logging.CRITICAL
        }
        log_level = level_map.get(self.config.LOG_LEVEL, logging.INFO)
        
        # Create logger
        logger = logging.getLogger('music_rpc')
        logger.setLevel(log_level)
        
        # Prevent adding handlers multiple times if _setup_logger is called again
        if logger.hasHandlers():
            logger.handlers.clear()
        
        # Ensure log directory exists
        log_dir = os.path.dirname(os.path.abspath(self.config.LOG_FILE))
        if not os.path.exists(log_dir):
            try:
                os.makedirs(log_dir)
            except OSError as e:
                print(f"Error creating log directory: {e}")
                # Fall back to user home directory
                self.config.LOG_FILE = os.path.expanduser("~/music_rpc.log")
        
        try:
            # Add rotating file handler
            max_log_size = getattr(self.config, 'MAX_LOG_SIZE', 5 * 1024 * 1024)  # Default 5MB
            backup_count = getattr(self.config, 'LOG_BACKUP_COUNT', 3)  # Default 3 backups
            
            file_handler = RotatingFileHandler(
                self.config.LOG_FILE,
                maxBytes=max_log_size,
                backupCount=backup_count
            )
            file_handler.setLevel(log_level)
            file_formatter = logging.Formatter(
                "%(asctime)s - %(levelname)s - %(module)s - %(message)s"
            )
            file_handler.setFormatter(file_formatter)
            logger.addHandler(file_handler)
            
            # Add console handler with less verbose format
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setLevel(log_level)
            console_formatter = logging.Formatter("%(levelname)s: %(message)s")
            console_handler.setFormatter(console_formatter)
            logger.addHandler(console_handler)
            
        except Exception as e:
            print(f"Failed to setup logger: {e}")
            # Set up a basic console-only logger as fallback
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setLevel(logging.INFO)
            console_formatter = logging.Formatter("%(levelname)s: %(message)s")
            console_handler.setFormatter(console_formatter)
            logger.addHandler(console_handler)
        
        return logger
    
    def debug(self, message: str) -> None:
        """Log a debug message.
        
        Args:
            message: The debug message to log
        """
        self.logger.debug(message)
    
    def info(self, message: str) -> None:
        """Log an info message.
        
        Args:
            message: The info message to log
        """
        self.logger.info(message)
    
    def warning(self, message: str) -> None:
        """Log a warning message.
        
        Args:
            message: The warning message to log
        """
        self.logger.warning(message)
    
    def error(self, message: str) -> None:
        """Log an error message.
        
        Args:
            message: The error message to log
        """
        self.logger.error(message)
    
    def critical(self, message: str) -> None:
        """Log a critical message.
        
        Args:
            message: The critical message to log
        """
        self.logger.critical(message)
    
    def exception(self, message: str) -> None:
        """Log an exception message with traceback.
        
        Should only be called from an exception handler.
        
        Args:
            message: The exception message to log
        """
        self.logger.exception(message) 