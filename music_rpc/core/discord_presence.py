"""
Discord Rich Presence integration for Music RPC.

This module provides functionality to connect to Discord's Rich Presence API
and update the user's Discord status with currently playing music information.
It handles different music players with their specific client IDs and ensures
proper connection management.
"""
import time
import re
import unicodedata
from typing import Optional, Dict, Any, Callable, Union, Tuple
from pypresence import Presence

from ..config.settings import Config
from ..logging.handlers import Logger


class DiscordPresenceManager:
    """Manages Discord Rich Presence updates for music players.
    
    This class handles the connection to Discord's Rich Presence API and updates
    the user's Discord status with information about the currently playing music.
    It supports different music players by using appropriate client IDs and
    handles reconnection when switching between different music players.
    """
    
    def __init__(self, config: Config, logger: Logger) -> None:
        """Initialize the Discord Presence Manager.
        
        Args:
            config: Config object with Discord client IDs and settings
            logger: Logger instance for logging events and errors
        """
        self.config = config
        self.logger = logger
        self.rpc: Optional[Presence] = None
        self.connected: bool = False
        self.last_title: Optional[str] = None
        self.current_client_id: Optional[str] = None
    
    def _get_client_id_for_player(self, player_name: Optional[str]) -> Optional[str]:
        """Get the appropriate Discord client ID for the specified player.
        
        Resolves the correct Discord application client ID to use based on the 
        player name, using the configuration's aliasing and normalization system.
        
        Args:
            player_name: Name of the music player
            
        Returns:
            The Discord client ID to use, or None if the player has Discord RPC disabled
        """
        # Use the config's get_client_id method which handles all the normalization and aliasing
        client_id = self.config.get_client_id(player_name)
        
        # Log the client ID resolution for debugging
        if player_name:
            self.logger.debug(f"Resolved Discord client ID for {player_name}: {client_id}")
        
        return client_id
    
    def connect(self, player_name: Optional[str] = None) -> bool:
        """Connect to Discord's Rich Presence API with the appropriate client ID.
        
        Establishes a connection to Discord using the appropriate client ID for
        the specified player. Handles reconnection if switching between different
        players and their respective client IDs.
        
        Args:
            player_name: Name of the music player to connect with
            
        Returns:
            True if connection successful, False otherwise
        """
        try:
            # Handle empty player name gracefully
            if not player_name:
                player_name = "Music"
                
            # Get the appropriate client ID
            client_id = self._get_client_id_for_player(player_name)
            
            # If client_id is None, this player has Discord RPC disabled
            if client_id is None:
                if self.connected:
                    self.disconnect()
                self.logger.info(f"Discord Rich Presence is disabled for {player_name}")
                self.logger.info(f"{player_name} has its own Discord integration")
                return False
            
            # If we're already connected with this client ID, no need to reconnect
            if self.connected and self.current_client_id == client_id:
                self.logger.debug(f"Already connected with client ID: {client_id}")
                return True
                
            # Disconnect if we're connected with a different client ID
            if self.connected:
                self.logger.info(f"Switching Discord client from {self.current_client_id} to {client_id}")
                self.disconnect()
            
            # Ensure a clean state before connecting
            self.rpc = None
            self.connected = False
            
            # Add a short delay to ensure Discord properly registers disconnection
            time.sleep(0.5)
            
            self.logger.info("Connecting to Discord...")
            self.rpc = Presence(client_id)
            self.rpc.connect()
            self.connected = True
            self.current_client_id = client_id
            self.logger.info("Connected to Discord Rich Presence")
            return True
        except Exception as error:
            self.logger.error(f"Failed to connect to Discord: {error}")
            # Reset state on error
            self.connected = False
            self.current_client_id = None
            self.rpc = None
            return False
    
    def update(self, song_info: 'SongInfo') -> bool:
        """Update Discord Rich Presence with current song information.
        
        Updates the user's Discord status with information about the currently
        playing song. Handles reconnection if the player has changed since the
        last update and clears the presence if no song is playing.
        
        Args:
            song_info: SongInfo object with current song details
            
        Returns:
            True if update successful, False otherwise
        """
        if not song_info:
            self.logger.debug("No song info provided for update")
            return False
            
        # Check if we need to reconnect with a different client ID
        if song_info.player and self.connected:
            client_id = self._get_client_id_for_player(song_info.player)
            if client_id != self.current_client_id:
                # Reconnect with the new client ID
                self.logger.info(f"Switching Discord client for {song_info.player}")
                self.disconnect()
                if not self.connect(song_info.player):
                    return False
        
        # Skip if this is a disabled player
        if song_info.player:
            client_id = self._get_client_id_for_player(song_info.player)
            if client_id is None:
                return False
        
        if not self.connected:
            # Try to connect if we're not already connected
            if not self.connect(song_info.player):
                self.logger.error("Attempted to update Discord presence without connection")
                return False
        
        # If not playing, clear the presence instead of showing idle status
        if not song_info.is_playing():
            try:
                self.logger.info("No song playing, hiding Discord presence")
                # Clear the presence by calling clear()
                if self.rpc:
                    self.rpc.clear()
                self.last_title = None
                return True
            except Exception as error:
                self.logger.error(f"Error clearing Discord presence: {error}")
                return False
        
        # Avoid unnecessary updates for the same song
        if song_info.title == self.last_title:
            self.logger.debug(f"Skipping update for same song: {song_info.title}")
            return True
            
        try:
            # Format text for Discord's display
            title = self._ensure_unicode_display(song_info.title or "Unknown")
            artist = self._ensure_unicode_display(song_info.artist or "Unknown Artist")
            player_name = song_info.player or "Music Player"
            
            # Store current title to avoid duplicate updates
            self.last_title = song_info.title
            
            # Prepare timestamps if available
            timestamps = {}
            if song_info.start_time and song_info.end_time:
                # Discord expects seconds since epoch for start and end
                current_time = int(time.time())
                # Calculate how long the song has been playing
                elapsed = song_info.position or 0  # Default to 0 if position is None
                # Set the start time to current time minus elapsed time
                start_time = current_time - elapsed
                # Calculate end time based on song duration
                duration = song_info.duration or 0  # Default to 0 if duration is None
                end_time = start_time + duration
                
                # Add timestamps to presence update if we have valid times
                if start_time < end_time:
                    timestamps = {
                        "start": start_time,
                        "end": end_time
                    }
            
            # Directly assign asset properties instead of using nested assets dictionary
            large_image = "music_icon"
            large_text = player_name
            
            # Use album art if available and enabled
            if song_info.album_art_url and self.config.USE_ALBUM_ART:
                large_image = song_info.album_art_url
                large_text = song_info.album or player_name
            
            # Prepare the update payload with proper format for pypresence
            # The 'assets' parameter is not used directly in pypresence 4.x+
            update_data = {
                "details": title[:128],      # Discord limits details to 128 characters
                "state": artist[:128],       # Discord limits state to 128 characters
                "large_image": large_image,  # Direct parameter instead of nested in assets
                "large_text": large_text     # Direct parameter instead of nested in assets
            }
            
            # Add timestamps if available
            if timestamps:
                if "start" in timestamps:
                    update_data["start"] = timestamps["start"]
                if "end" in timestamps:
                    update_data["end"] = timestamps["end"]
                
            # Send the update to Discord
            if self.rpc:
                self.rpc.update(**update_data)
                self.logger.info(f"Updated Discord presence: {title} by {artist}")
                return True
            else:
                self.logger.error("RPC client is None during update")
                return False
        except Exception as error:
            self.logger.error(f"Error updating Discord presence: {error}")
            # Try to reconnect if there was an error
            self.connected = False
            return False
    
    def run_update_loop(self, window: 'WindowManager', song_info_retriever: Callable) -> None:
        """Run a continuous update loop for Discord Rich Presence.
        
        This method is intended to be called in a background thread. It periodically
        retrieves song information and updates the Discord Rich Presence status.
        
        Args:
            window: WindowManager instance for detecting active windows
            song_info_retriever: Function to retrieve current song information
        """
        self.logger.info("Starting Discord presence update loop")
        
        try:
            while True:
                try:
                    # Get current song info from the retriever function
                    song_info = song_info_retriever()
                    
                    # Update Discord presence if we have song info
                    if song_info:
                        self.update(song_info)
                    else:
                        # If no song info, clear presence if we're connected
                        if self.connected and self.rpc:
                            try:
                                self.rpc.clear()
                                self.last_title = None
                            except Exception as clear_error:
                                self.logger.error(f"Error clearing presence: {clear_error}")
                    
                    # Sleep for a short interval before the next update
                    # This determines how responsive the presence updates are
                    time.sleep(5)
                except Exception as loop_error:
                    self.logger.error(f"Error in update loop: {loop_error}")
                    # Sleep a bit longer if an error occurred to avoid tight error loops
                    time.sleep(10)
        except KeyboardInterrupt:
            # Handle graceful shutdown on keyboard interrupt
            self.logger.info("Update loop interrupted, shutting down")
            self.disconnect()
    
    def disconnect(self) -> bool:
        """Disconnect from Discord Rich Presence.
        
        Closes the connection to Discord's Rich Presence API and resets the
        internal state.
        
        Returns:
            True if disconnect successful, False otherwise
        """
        if not self.connected:
            self.logger.debug("Already disconnected from Discord")
            return True
            
        try:
            if self.rpc:
                # Clear presence before disconnecting
                try:
                    self.rpc.clear()
                except Exception:
                    # Ignore errors when clearing on disconnect
                    pass
                    
                # Close connection
                self.rpc.close()
                self.logger.info("Disconnected from Discord Rich Presence")
            
            # Reset state
            self.connected = False
            self.current_client_id = None
            self.rpc = None
            self.last_title = None
            return True
        except Exception as error:
            self.logger.error(f"Error disconnecting from Discord: {error}")
            # Force reset state even if there was an error
            self.connected = False
            self.current_client_id = None
            self.rpc = None
            self.last_title = None
            return False
    
    def _ensure_unicode_display(self, text: Optional[str]) -> str:
        """Ensure text displays correctly in Discord by handling Unicode issues.
        
        Discord Rich Presence sometimes has issues with certain Unicode characters.
        This method processes the text to ensure it displays correctly.
        
        Args:
            text: The text to process
            
        Returns:
            Processed text safe for Discord display
        """
        if not text:
            return ""
            
        try:
            # Normalize Unicode characters
            normalized = unicodedata.normalize('NFC', text)
            
            # Replace problematic characters
            # Replace zero-width spaces and other invisible characters
            normalized = re.sub(r'[\u200B-\u200D\uFEFF]', '', normalized)
            
            # Handle emoji sequences and other complex Unicode characters
            # that might not display well in Discord's limited font support
            def replace_complex_chars(match: re.Match) -> str:
                char = match.group(0)
                # For characters outside BMP (Basic Multilingual Plane)
                # Discord might not handle them well
                if ord(char) > 0xFFFF:
                    return '?'  # Replace with a simple character
                return char
                
            # Find characters that might cause issues in Discord
            normalized = re.sub(r'[^\u0000-\uFFFF]', replace_complex_chars, normalized)
            
            # Handle escaped Unicode in strings like '\\u1234'
            def replace_unicode_escapes(match: re.Match) -> str:
                code = int(match.group(1), 16)
                # Ignore control characters
                if code < 32 or (127 <= code <= 159):
                    return ''
                try:
                    return chr(code)
                except ValueError:
                    return ''
            
            # Convert escaped Unicode sequences like "\\u1234" to actual characters
            normalized = re.sub(r'\\u([0-9a-fA-F]{4})', replace_unicode_escapes, normalized)
            
            # Limit the length to avoid Discord's truncation
            # Discord details and state fields are limited to 128 characters
            return normalized[:128]
        except Exception as e:
            self.logger.error(f"Error processing text for Discord: {e}")
            # Fallback to a simple version of the string
            return text[:128] if text else "" 