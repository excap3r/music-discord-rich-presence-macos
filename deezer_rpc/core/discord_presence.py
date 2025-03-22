"""
Discord Rich Presence integration
"""
import time
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
    
    def connect(self):
        """Connect to Discord
        
        Returns:
            bool: True if connection successful, False otherwise
        """
        try:
            print(" ┃ 🌟 Connecting to Discord...")
            self.rpc = Presence(self.config.DISCORD_CLIENT_ID)
            self.rpc.connect()
            self.connected = True
            print(" ┃ 🌟 Connected to Discord Rich Presence")
            return True
        except Exception as error:
            self.logger.error(f"Failed to connect to Discord: {error}")
            print(" ┃ ❌ Error: Unable to connect to Discord.")
            return False
    
    def update(self, song_info):
        """Update Discord Rich Presence with song info
        
        Args:
            song_info: SongInfo object with current song details
            
        Returns:
            bool: True if update successful, False otherwise
        """
        if not self.connected:
            self.logger.error("Attempted to update Discord presence without connection")
            return False
        
        # If not playing, set idle status
        if not song_info.is_playing():
            try:
                print(" ┃ 💤 No song playing")
                self.rpc.update(
                    details="Not playing",
                    state="Open Deezer and play a song",
                    large_image="deezer_logo",
                    large_text="Deezer",
                    small_image="deezer_icon",
                    small_text="Idle"
                )
                return True
            except Exception as error:
                self.logger.error(f"Error setting idle status: {error}")
                return False
        
        # Avoid unnecessary updates for the same song
        if self.last_title == song_info.title:
            return True
        
        try:
            # Ensure we have valid values for the RPC
            details = f"🎧 Listening to {song_info.title}"
            state = f"🎤 {song_info.artist}" if song_info.artist else "Unknown Artist"
            
            # Discord rich presence supports both built-in assets and full URLs
            # Determine which to use
            large_image = song_info.album_cover if song_info.album_cover else "deezer_logo"
            small_image = song_info.artist_image if song_info.artist_image else "deezer_icon"
            
            buttons = [{"label": "🎵 Listen on Deezer", "url": song_info.song_link}] if song_info.song_link else None
            
            # Only show essential update information
            try:
                # Ensure proper Unicode rendering for display
                title_display = self._ensure_unicode_display(song_info.title)
                artist_display = self._ensure_unicode_display(song_info.artist)
                print(f" ┃ 🎵 Now playing: {title_display} by {artist_display}")
            except UnicodeEncodeError:
                # Fallback if there's an encoding issue
                print(f" ┃ 🎵 Now playing: [Song title with special characters] by {song_info.artist}")
            
            update_data = {
                "details": details,
                "state": state,
                "large_image": large_image,
                "large_text": song_info.title if song_info.title else "Deezer",
                "small_image": small_image,
                "small_text": song_info.artist if song_info.artist else "Deezer"
            }
            
            # Add buttons if available
            if buttons:
                update_data["buttons"] = buttons
                
            # Try to update with all data including album art
            try:
                self.rpc.update(**update_data)
            except Exception as img_error:
                # If that fails, try again without external images
                self.logger.error(f"Error updating with album art: {img_error}, falling back to default images")
                
                # Use default images instead
                update_data["large_image"] = "deezer_logo"
                update_data["small_image"] = "deezer_icon"
                self.rpc.update(**update_data)
            
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
        if self.connected and self.rpc:
            try:
                self.rpc.close()
                self.connected = False
                print(" ┃ 👋 Disconnected from Discord Rich Presence")
            except Exception as error:
                self.logger.error(f"Error disconnecting from Discord: {error}")

    def _ensure_unicode_display(self, text):
        """Ensure Unicode display for text"""
        if text is None:
            return "Unknown"
            
        # Handle different text types
        if not isinstance(text, str):
            try:
                if isinstance(text, bytes):
                    return text.decode('utf-8')
                return str(text)
            except Exception as e:
                self.logger.error(f"Error converting text type: {e}")
                return "Unknown"
        
        # Process string with escape sequences
        try:
            # Check for Unicode escape sequences (raw string matching)
            if '\\u' in text or '\\U' in text:
                # Use a more direct approach to handle literal \U and \u sequences
                import re
                
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
            
            return text
        except Exception as e:
            self.logger.error(f"Error processing Unicode text: {e}")
            # Fallback to simple replacement
            text = text.replace('\\U', 'U').replace('\\u', 'u')
            return text 