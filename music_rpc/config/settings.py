"""
Configuration settings for Deezer RPC
"""
import os
import json
from typing import Dict, List, Tuple, Union, Optional, Any


class Config:
    """Configuration class for storing global settings and constants"""
    
    # Version information
    VERSION: str = "2.0.0"
    
    # API endpoints
    DEEZER_API_SEARCH_URL: str = "https://api.deezer.com/search?q="
    
    # Default Discord application client IDs
    DISCORD_CLIENT_ID: str = "1352843252067209368"  # Default client ID
    DEFAULT_DISCORD_CLIENT_IDS: Dict[str, str] = {
        "Deezer": "1352674859670310992",  # Deezer client ID
        "Music": "1352841157159288894",    # Apple Music client ID
        "iTunes": "1352841157159288894",   # iTunes uses same ID as Apple Music
        "Tidal": "1352842418327912529"   # Tidal client ID
    }
    
    # Player name aliases
    DEFAULT_PLAYER_ALIASES: Dict[str, str] = {
        "apple music": "Music",
        "music.app": "Music",
        "musicapp": "Music",
        "applemusic": "Music",
        "deezer": "Deezer",
        "itunes": "iTunes",
        "tidal": "Tidal"
    }
    
    # Default configuration
    DEFAULT_UPDATE_INTERVAL: int = 10  # Seconds between song checks
    ACTIVATE_DEEZER: bool = False  # Whether to activate Deezer window
    USE_ALBUM_ART: bool = True  # Whether to try using album art from API
    
    # Players with disabled Discord rich presence (they have their own solutions)
    DISABLED_PLAYERS: List[str] = ["Music"]  # Apple Music has its own Discord RPC solution
    
    # Log configuration
    LOG_FILE: str = os.path.expanduser("~/music_rpc.log")
    LOG_LEVEL: str = "WARNING"  # Can be DEBUG, INFO, WARNING, ERROR, CRITICAL
    MAX_LOG_SIZE: int = 5 * 1024 * 1024  # 5MB
    LOG_BACKUP_COUNT: int = 3
    
    # Config file path
    CONFIG_FILE: str = os.path.expanduser("~/Music_RPC_config.json")
    
    def __init__(self) -> None:
        """Initialize configuration with default values and load user settings."""
        # User configurable settings (can be modified at runtime)
        self.update_interval: int = self.DEFAULT_UPDATE_INTERVAL
        self.discord_client_ids: Dict[str, str] = self.DEFAULT_DISCORD_CLIENT_IDS.copy()
        self.player_aliases: Dict[str, str] = self.DEFAULT_PLAYER_ALIASES.copy()
        
        # Load config from file if it exists
        self.load_config()
    
    def set_update_interval(self, interval: Union[str, int]) -> Tuple[bool, str]:
        """Set the update interval with validation.
        
        Args:
            interval: The new interval value in seconds (5-60)
        
        Returns:
            A tuple of (success, message) where success is a boolean indicating
            if the update was successful, and message is a descriptive message.
        """
        try:
            interval_value = int(interval)
            if 5 <= interval_value <= 60:
                self.update_interval = interval_value
                self.save_config()
                return True, f"Update interval set to {interval_value} seconds"
            else:
                return False, f"Invalid interval. Using default {self.update_interval} seconds"
        except ValueError:
            return False, f"Invalid input. Using default {self.update_interval} seconds"
    
    def set_client_id(self, player_name: str, client_id: str) -> Tuple[bool, str]:
        """Set custom Discord client ID for a specific player.
        
        Args:
            player_name: The player name (e.g., "Deezer", "Spotify")
            client_id: The Discord application client ID
            
        Returns:
            A tuple of (success, message) where success is a boolean indicating
            if the update was successful, and message is a descriptive message.
        """
        if not player_name or not client_id:
            return False, "Player name and client ID are required"
        
        # Validate client ID (should be numeric)
        try:
            # Client IDs are numeric strings
            _ = int(client_id)
            self.discord_client_ids[player_name] = client_id
            self.save_config()
            return True, f"Discord client ID for {player_name} set to {client_id}"
        except ValueError:
            return False, f"Invalid client ID format: {client_id}"
    
    def get_client_id(self, player_name: Optional[str]) -> Optional[str]:
        """Get Discord client ID for a specific player.
        
        Args:
            player_name: The player name
            
        Returns:
            The client ID or default if not found, None if disabled
        """
        if not player_name:
            return self.DISCORD_CLIENT_ID
            
        # Normalize the player name (case insensitive)
        player_name_lower = player_name.lower()
        
        # Check if the normalized name is in aliases
        normalized_name = None
        if player_name_lower in self.player_aliases:
            normalized_name = self.player_aliases[player_name_lower]
        else:
            # Check direct match
            for configured_name in self.discord_client_ids:
                if configured_name.lower() == player_name_lower:
                    normalized_name = configured_name
                    break
        
        # Check if this player is disabled
        if normalized_name and normalized_name in self.DISABLED_PLAYERS:
            return None
            
        # Return appropriate client ID
        if normalized_name:
            return self.discord_client_ids.get(normalized_name, self.DISCORD_CLIENT_ID)
                
        # Return default
        return self.DISCORD_CLIENT_ID
    
    def add_player_alias(self, alias: str, normalized_name: str) -> Tuple[bool, str]:
        """Add a new player alias mapping.
        
        Args:
            alias: The alias name
            normalized_name: The normalized player name to map to
            
        Returns:
            A tuple of (success, message) where success is a boolean indicating
            if the update was successful, and message is a descriptive message.
        """
        if not alias or not normalized_name:
            return False, "Alias and normalized name are required"
            
        # Ensure normalized name exists in client IDs
        if normalized_name not in self.discord_client_ids:
            return False, f"Normalized name '{normalized_name}' not found in configured players"
            
        # Add the alias
        self.player_aliases[alias.lower()] = normalized_name
        self.save_config()
        return True, f"Added alias '{alias}' for '{normalized_name}'"
    
    def load_config(self) -> None:
        """Load configuration from JSON file.
        
        Attempts to load saved configuration from a JSON file. If the file does not exist
        or contains invalid data, falls back to default values.
        """
        try:
            if os.path.exists(self.CONFIG_FILE):
                with open(self.CONFIG_FILE, 'r', encoding='utf-8') as f:
                    config_data = json.load(f)
                    
                # Load update interval
                if 'update_interval' in config_data:
                    interval = config_data['update_interval']
                    if isinstance(interval, int) and 5 <= interval <= 60:
                        self.update_interval = interval
                
                # Load client IDs
                if 'discord_client_ids' in config_data and isinstance(config_data['discord_client_ids'], dict):
                    for player, client_id in config_data['discord_client_ids'].items():
                        # Validate each client ID
                        if player and client_id and isinstance(client_id, str):
                            try:
                                _ = int(client_id)  # Validate numeric format
                                self.discord_client_ids[player] = client_id
                            except ValueError:
                                pass  # Skip invalid client IDs
                
                # Load player aliases
                if 'player_aliases' in config_data and isinstance(config_data['player_aliases'], dict):
                    for alias, player in config_data['player_aliases'].items():
                        if alias and player and isinstance(alias, str) and isinstance(player, str):
                            self.player_aliases[alias.lower()] = player
                            
                # Load other settings
                if 'log_level' in config_data and isinstance(config_data['log_level'], str):
                    valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
                    if config_data['log_level'].upper() in valid_levels:
                        self.LOG_LEVEL = config_data['log_level'].upper()
                
                if 'log_file' in config_data and isinstance(config_data['log_file'], str):
                    self.LOG_FILE = os.path.expanduser(config_data['log_file'])
                    
                if 'disabled_players' in config_data and isinstance(config_data['disabled_players'], list):
                    self.DISABLED_PLAYERS = [
                        p for p in config_data['disabled_players'] 
                        if isinstance(p, str)
                    ]
        except (json.JSONDecodeError, OSError, KeyError) as e:
            # Log error but continue with defaults
            print(f"Error loading configuration: {e}")
    
    def save_config(self) -> None:
        """Save current configuration to JSON file.
        
        Attempts to save the current configuration to a JSON file. If unable to save,
        the error is logged but execution continues.
        """
        try:
            # Ensure the directory exists
            config_dir = os.path.dirname(self.CONFIG_FILE)
            if config_dir and not os.path.exists(config_dir):
                os.makedirs(config_dir)
                
            # Create config data structure
            config_data = {
                'update_interval': self.update_interval,
                'discord_client_ids': self.discord_client_ids,
                'player_aliases': self.player_aliases,
                'log_level': self.LOG_LEVEL,
                'log_file': self.LOG_FILE,
                'disabled_players': self.DISABLED_PLAYERS
            }
            
            # Write to file with pretty formatting
            with open(self.CONFIG_FILE, 'w', encoding='utf-8') as f:
                json.dump(config_data, f, indent=4)
        except (OSError, TypeError) as e:
            # Log error but continue
            print(f"Error saving configuration: {e}") 