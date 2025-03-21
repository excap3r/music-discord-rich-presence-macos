"""
Logging utility for Deezer RPC
"""
import logging


class Logger:
    """Centralized logging utility for the application"""
    
    def __init__(self, config):
        """Initialize the logger with configuration

        Args:
            config: Config object containing logging settings
        """
        self.config = config
        self._setup_logger()
    
    def _setup_logger(self):
        """Configure the logger with file and console handlers"""
        # Convert string level to logging level
        level_map = {
            "DEBUG": logging.DEBUG,
            "INFO": logging.INFO,
            "WARNING": logging.WARNING,
            "ERROR": logging.ERROR,
            "CRITICAL": logging.CRITICAL
        }
        log_level = level_map.get(self.config.LOG_LEVEL, logging.ERROR)
        
        # Configure the root logger
        logging.basicConfig(
            filename=self.config.LOG_FILE,
            level=log_level,
            format="%(asctime)s - %(levelname)s - %(message)s"
        )
        
        # Add console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(log_level)
        console_formatter = logging.Formatter("%(levelname)s: %(message)s")
        console_handler.setFormatter(console_formatter)
        logging.getLogger('').addHandler(console_handler)
    
    @staticmethod
    def debug(message):
        """Log a debug message"""
        logging.debug(message)
    
    @staticmethod
    def info(message):
        """Log an info message"""
        logging.info(message)
    
    @staticmethod
    def warning(message):
        """Log a warning message"""
        logging.warning(message)
    
    @staticmethod
    def error(message):
        """Log an error message"""
        logging.error(message)
    
    @staticmethod
    def critical(message):
        """Log a critical message"""
        logging.critical(message) 