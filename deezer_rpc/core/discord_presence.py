"""
Discord Rich Presence integration
"""
import time
import re
import unicodedata
from pypresence import Presence


class DiscordPresenceManager:
    """Manages Discord Rich Presence updates"""
    
    def __init__(self, config, logger):
        """Initialize with config and logger
        
        Args:
            config: Config object with Discord client ID
            logger: Logger instance for logging
        """
        self.config = config
        self.logger = logger
        self.rpc = None
        self.connected = False
        self.last_title = None
        self.current_client_id = None
    
    def _get_client_id_for_player(self, player_name):
        """Get the appropriate Discord client ID for the player
        
        Args:
            player_name: Name of the music player
            
        Returns:
            str: Discord client ID to use
        """
        # Use the config's get_client_id method which handles all the normalization and aliasing
        client_id = self.config.get_client_id(player_name)
        
        # Log the client ID resolution for debugging
        if player_name:
            self.logger.debug(f"Resolved Discord client ID for {player_name}: {client_id}")
        
        return client_id
    
    def connect(self, player_name=None):
        """Connect to Discord
        
        Args:
            player_name: Name of the music player to connect with
            
        Returns:
            bool: True if connection successful, False otherwise
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
                print(f" ┃ ℹ️ Discord Rich Presence is disabled for {player_name}")
                print(f" ┃ ℹ️ {player_name} has its own Discord integration")
                return False
            
            # If we're already connected with this client ID, no need to reconnect
            if self.connected and self.current_client_id == client_id:
                self.logger.debug(f"Already connected with client ID: {client_id}")
                return True
                
            # Disconnect if we're connected with a different client ID
            if self.connected:
                print(f" ┃ 🔄 Switching Discord client from {self.current_client_id} to {client_id}...")
                self.disconnect()
            
            # Ensure a clean state before connecting
            self.rpc = None
            self.connected = False
            
            # Add a short delay to ensure Discord properly registers disconnection
            time.sleep(0.5)
            
            print(" ┃ 🌟 Connecting to Discord...")
            self.rpc = Presence(client_id)
            self.rpc.connect()
            self.connected = True
            self.current_client_id = client_id
            print(" ┃ 🌟 Connected to Discord Rich Presence")
            return True
        except Exception as error:
            self.logger.error(f"Failed to connect to Discord: {error}")
            print(" ┃ ❌ Error: Unable to connect to Discord.")
            # Reset state on error
            self.connected = False
            self.current_client_id = None
            self.rpc = None
            return False
    
    def update(self, song_info):
        """Update Discord Rich Presence with song info
        
        Args:
            song_info: SongInfo object with current song details
            
        Returns:
            bool: True if update successful, False otherwise
        """
        if not song_info:
            self.logger.debug("No song info provided for update")
            return False
            
        # Check if we need to reconnect with a different client ID
        if song_info.player and self.connected:
            client_id = self._get_client_id_for_player(song_info.player)
            if client_id != self.current_client_id:
                # Reconnect with the new client ID
                print(f" ┃ 🔄 Switching Discord client for {song_info.player}...")
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
                print(" ┃ 💤 No song playing, hiding Discord presence")
                # Clear the presence by calling clear()
                self.rpc.clear()
                self.last_title = None
                return True
            except Exception as error:
                self.logger.error(f"Error clearing Discord presence: {error}")
                return False
        
        # Avoid unnecessary updates for the same song
        if self.last_title == song_info.title:
            return True
        
        try:
            # Process all text fields to ensure proper encoding
            title = self._ensure_unicode_display(song_info.title)
            artist = self._ensure_unicode_display(song_info.artist)
            player = self._ensure_unicode_display(song_info.player) if song_info.player else "Music"
            
            # We can't set the activity type to "Listening" due to Discord API limitations
            # But we can make the text read "Listening to" to clarify the activity
            details = f"Listening to {title}"
            state = f"by {artist}" if artist else "Unknown Artist"
            
            # Discord rich presence supports both built-in assets and full URLs
            # Determine which to use for album art
            large_image = "music_logo"
            small_image = "music_icon"
            
            # Check if we have valid image URLs
            if song_info.album_cover and song_info.album_cover != "music_logo":
                if song_info.album_cover.startswith(('http://', 'https://')):
                    self.logger.debug(f"Using album cover URL: {song_info.album_cover}")
                    large_image = song_info.album_cover
                else:
                    self.logger.debug(f"Invalid album cover URL, using default: {song_info.album_cover}")
            else:
                self.logger.debug("No album cover available, using default")
            
            if song_info.artist_image and song_info.artist_image != "music_icon":
                if song_info.artist_image.startswith(('http://', 'https://')):
                    self.logger.debug(f"Using artist image URL: {song_info.artist_image}")
                    small_image = song_info.artist_image
                else:
                    self.logger.debug(f"Invalid artist image URL, using default: {song_info.artist_image}")
            
            # Prepare button if we have a song link
            buttons = [{"label": "🎵 Listen Now", "url": song_info.song_link}] if song_info.song_link else None
            
            # Only show essential update information
            try:
                # No need to re-encode for display since we already processed above
                print(f" ┃ 🎵 Now playing on {player}: {title} by {artist}")
            except UnicodeEncodeError:
                # Fallback if there's an encoding issue with the console
                print(f" ┃ 🎵 Now playing: [Song with special characters]")
            
            # Calculate timestamps for song progress
            current_time = int(time.time())
            start_time = current_time - int(song_info.elapsed)  # When the song started
            end_time = 0
            
            # Only set end timestamp if we have a valid duration
            if song_info.duration > 0:
                end_time = current_time + int(song_info.duration - song_info.elapsed)
                
            update_data = {
                "details": details,
                "state": state,
                "large_image": large_image,
                "large_text": title,
                "small_image": small_image,
                "small_text": artist,
                "start": start_time
            }
            
            # Add end timestamp if we have a valid duration
            if end_time > current_time:
                update_data["end"] = end_time
            
            # Add buttons if available
            if buttons:
                update_data["buttons"] = buttons
                
            # Try to update with all data including album art
            try:
                self.rpc.update(**update_data)
                self.logger.debug("Discord Rich Presence updated successfully with album art")
            except Exception as img_error:
                # If that fails, try again without external images
                self.logger.error(f"Error updating with album art: {img_error}, falling back to default images")
                
                # Use default images instead
                update_data["large_image"] = "music_logo"
                update_data["small_image"] = "music_icon"
                self.rpc.update(**update_data)
                self.logger.debug("Discord Rich Presence updated with default images")
            
            self.last_title = song_info.title
            return True
        except Exception as error:
            self.logger.error(f"Error updating Discord presence: {error}")
            print(f" ┃ ❌ Error updating Discord presence: {error}")
            return False
    
    def run_update_loop(self, window, song_info_retriever):
        """Run the update loop to continuously update Discord presence
        
        Args:
            window: DeezerWindow object
            song_info_retriever: SongInfoRetriever instance
        """
        print(" ┃ 🌟 Discord Rich Presence active")
        print(f" ┃ 📊 Update interval: {self.config.update_interval} seconds")
        print(" ┃ 💡 Press Ctrl+C to exit")
        
        try:
            # Initial update to set status
            window_title = window.title
            song_info = song_info_retriever.get_current_song_info(window_title)
            self.update(song_info)
        except Exception as error:
            self.logger.error(f"Error in initial update: {error}")
        
        # Main update loop
        while True:
            try:
                # Get song info using window title
                window_title = window.title
                
                # Get current song info (cached if it's the same song)
                song_info = song_info_retriever.get_current_song_info(window_title)
                
                # Update Discord presence (the update method already checks if song has changed)
                self.update(song_info)
                
                # Use update interval to reduce CPU usage
                time.sleep(self.config.update_interval)
            except Exception as error:
                self.logger.error(f"Error in update loop: {error}")
                print(f" ┃ ⚠️ Error in update loop: {error}. Trying again in {self.config.update_interval} seconds.")
                time.sleep(self.config.update_interval)
    
    def disconnect(self):
        """Disconnect from Discord Rich Presence"""
        if not self.connected and not self.rpc:
            # Already disconnected
            return
            
        try:
            print(" ┃ 👋 Disconnecting from Discord Rich Presence...")
            if self.rpc:
                self.rpc.close()
            self.connected = False
            self.current_client_id = None
            self.rpc = None
            print(" ┃ 👋 Disconnected from Discord Rich Presence")
        except Exception as error:
            self.logger.error(f"Error disconnecting from Discord: {error}")
            # Ensure we reset state even on error
            self.connected = False
            self.current_client_id = None
            self.rpc = None

    def _ensure_unicode_display(self, text):
        """Ensure Unicode display for text"""
        if text is None:
            return "Unknown"
            
        # Handle different text types
        if not isinstance(text, str):
            try:
                if isinstance(text, bytes):
                    return text.decode('utf-8', 'replace')
                return str(text)
            except Exception as e:
                self.logger.error(f"Error converting text type: {e}")
                return "Unknown"
        
        # Process string with escape sequences
        try:
            # Check for Unicode escape sequences
            if '\\u' in text or '\\U' in text:
                # Use a more direct approach to handle literal \U and \u sequences
                
                # Replace Unicode escape sequences with their character equivalents
                def replace_unicode_escapes(match):
                    try:
                        escape_seq = match.group(0)
                        # Convert to proper Python escape sequence and evaluate
                        if escape_seq.startswith('\\U'):
                            code_point = int(escape_seq[2:], 16)
                            return chr(code_point)
                        elif escape_seq.startswith('\\u'):
                            code_point = int(escape_seq[2:], 16)
                            return chr(code_point)
                        return escape_seq
                    except Exception as e:
                        self.logger.error(f"Failed to decode escape sequence {match.group(0)}: {e}")
                        return '[?]'
                
                # Find and replace all Unicode escape sequences
                text = re.sub(r'\\U[0-9a-fA-F]{4,8}|\\u[0-9a-fA-F]{4}', replace_unicode_escapes, text)
            
            # Normalize Unicode characters to ensure consistent representation
            try:
                text = unicodedata.normalize('NFC', text)
            except Exception as e:
                self.logger.error(f"Error normalizing Unicode: {e}")
            
            return text
        except Exception as e:
            self.logger.error(f"Error processing Unicode text: {e}")
            # Fallback to simple replacement
            text = text.replace('\\U', 'U').replace('\\u', 'u')
            return text 