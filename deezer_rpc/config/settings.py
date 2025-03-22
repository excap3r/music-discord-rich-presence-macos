"""
Configuration settings for Deezer RPC
"""
import os
import json


class Config:
    """Configuration class for storing global settings and constants"""
    
    # Version information
    VERSION = "2.0.0"
    
    # API endpoints
    DEEZER_API_SEARCH_URL = "https://api.deezer.com/search?q="
    
    # Default Discord application client IDs
    DISCORD_CLIENT_ID = "1352843252067209368"  # Default client ID
    DEFAULT_DISCORD_CLIENT_IDS = {
        "Deezer": "1352674859670310992",  # Deezer client ID
        "Music": "1352841157159288894",    # Apple Music client ID
        "iTunes": "1352841157159288894",   # iTunes uses same ID as Apple Music
        "Tidal": "1352842418327912529"   # Tidal client ID
    }
    
    # Player name aliases
    DEFAULT_PLAYER_ALIASES = {
        "apple music": "Music",
        "music.app": "Music",
        "musicapp": "Music",
        "applemusic": "Music",
        "deezer": "Deezer",
        "itunes": "iTunes",
        "tidal": "Tidal"
    }
    
    # Default configuration
    DEFAULT_UPDATE_INTERVAL = 10  # Seconds between song checks
    ACTIVATE_DEEZER = False  # Whether to activate Deezer window
    USE_ALBUM_ART = True  # Whether to try using album art from API
    
    # Players with disabled Discord rich presence (they have their own solutions)
    DISABLED_PLAYERS = ["Music"]  # Apple Music has its own Discord RPC solution
    
    # Log configuration
    LOG_FILE = "deezer_rpc.log"
    LOG_LEVEL = "ERROR"  # Can be DEBUG, INFO, WARNING, ERROR, CRITICAL
    
    # Config file path
    CONFIG_FILE = os.path.expanduser("~/Music_RPC_config.json")
    
    def __init__(self):
        # User configurable settings (can be modified at runtime)
        self.update_interval = self.DEFAULT_UPDATE_INTERVAL
        self.discord_client_ids = self.DEFAULT_DISCORD_CLIENT_IDS.copy()
        self.player_aliases = self.DEFAULT_PLAYER_ALIASES.copy()
        
        # Load config from file if it exists
        self.load_config()
    
    def set_update_interval(self, interval):
        """Set the update interval with validation"""
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
    
    def set_client_id(self, player_name, client_id):
        """Set custom Discord client ID for a specific player
        
        Args:
            player_name (str): The player name (e.g., "Deezer", "Spotify")
            client_id (str): The Discord application client ID
            
        Returns:
            tuple: (bool, str) indicating success and message
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
    
    def get_client_id(self, player_name):
        """Get Discord client ID for a specific player
        
        Args:
            player_name (str): The player name
            
        Returns:
            str: The client ID or default if not found, None if disabled
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
    
    def add_player_alias(self, alias, normalized_name):
        """Add a new player alias mapping
        
        Args:
            alias (str): The alias name
            normalized_name (str): The normalized player name to map to
            
        Returns:
            tuple: (bool, str) indicating success and message
        """
        if not alias or not normalized_name:
            return False, "Alias and normalized name are required"
            
        # Ensure normalized name exists in client IDs
        if normalized_name not in self.discord_client_ids:
            return False, f"Normalized name '{normalized_name}' not found in configured players"
            
        self.player_aliases[alias.lower()] = normalized_name
        self.save_config()
        return True, f"Alias '{alias}' mapped to '{normalized_name}'"
    
    def load_config(self):
        """Load configuration from config file"""
        try:
            if os.path.exists(self.CONFIG_FILE):
                with open(self.CONFIG_FILE, "r") as f:
                    config_data = json.load(f)
                    
                    # Load update interval if available
                    if "update_interval" in config_data:
                        interval = config_data["update_interval"]
                        if 5 <= interval <= 60:
                            self.update_interval = interval
                    
                    # Load Discord client IDs if available
                    if "discord_client_ids" in config_data:
                        # Only update with valid client IDs
                        client_ids = config_data["discord_client_ids"]
                        if isinstance(client_ids, dict):
                            for player, client_id in client_ids.items():
                                # Validate client ID
                                try:
                                    _ = int(client_id)
                                    self.discord_client_ids[player] = client_id
                                except (ValueError, TypeError):
                                    # Skip invalid client IDs
                                    pass
                    
                    # Load player aliases if available
                    if "player_aliases" in config_data:
                        aliases = config_data["player_aliases"]
                        if isinstance(aliases, dict):
                            for alias, player in aliases.items():
                                self.player_aliases[alias.lower()] = player
        except Exception as e:
            print(f" ┃ ⚠️ Error loading config: {e}")
            # Continue with defaults
    
    def save_config(self):
        """Save configuration to config file"""
        try:
            config_data = {
                "update_interval": self.update_interval,
                "discord_client_ids": self.discord_client_ids,
                "player_aliases": self.player_aliases
            }
            
            with open(self.CONFIG_FILE, "w") as f:
                json.dump(config_data, f, indent=4)
                
            return True
        except Exception as e:
            print(f" ┃ ⚠️ Error saving config: {e}")
            return False 