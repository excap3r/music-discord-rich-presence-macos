"""
Configuration settings for Deezer RPC
"""


class Config:
    """Configuration class for storing global settings and constants"""
    
    # Discord application client ID
    DISCORD_CLIENT_ID = "1352674859670310992"
    
    # Version information
    VERSION = "2.0.0"
    
    # API endpoints
    DEEZER_API_SEARCH_URL = "https://api.deezer.com/search?q="
    
    # Default configuration
    DEFAULT_UPDATE_INTERVAL = 10  # Seconds between song checks
    ACTIVATE_DEEZER = False  # Whether to activate Deezer window
    USE_ALBUM_ART = True  # Whether to try using album art from API
    
    # Log configuration
    LOG_FILE = "deezer_rpc.log"
    LOG_LEVEL = "ERROR"  # Can be DEBUG, INFO, WARNING, ERROR, CRITICAL
    
    def __init__(self):
        # User configurable settings (can be modified at runtime)
        self.update_interval = self.DEFAULT_UPDATE_INTERVAL
    
    def set_update_interval(self, interval):
        """Set the update interval with validation"""
        try:
            interval_value = int(interval)
            if 5 <= interval_value <= 60:
                self.update_interval = interval_value
                return True, f"Update interval set to {interval_value} seconds"
            else:
                return False, f"Invalid interval. Using default {self.update_interval} seconds"
        except ValueError:
            return False, f"Invalid input. Using default {self.update_interval} seconds" 