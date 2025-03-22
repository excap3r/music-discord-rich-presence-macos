"""
MacOS Tray Icon for Music RPC
"""
import rumps
import threading
import os
import sys
import subprocess
import queue
import unicodedata
import re


class MusicRPCTrayApp(rumps.App):
    """Music RPC Tray Icon App for macOS"""
    
    def __init__(self, config, logger, discord_manager, song_info_retriever):
        """Initialize with dependencies
        
        Args:
            config: Config instance
            logger: Logger instance
            discord_manager: DiscordPresenceManager instance
            song_info_retriever: SongInfoRetriever instance
        """
        super(MusicRPCTrayApp, self).__init__(
            name="Music RPC",
            title="🎵",
            icon=None,  # We'll use emoji in title instead
            quit_button="Quit"
        )
        
        self.config = config
        self.logger = logger
        self.discord_manager = discord_manager
        self.song_info_retriever = song_info_retriever
        
        # Status items
        self.now_playing_item = rumps.MenuItem("Not playing")
        self.artist_item = rumps.MenuItem("No artist")
        self.player_item = rumps.MenuItem("No player detected")
        self.discord_status_item = rumps.MenuItem("Discord: Disconnected")
        
        # Update interval submenu
        self.interval_submenu = rumps.MenuItem("Update Interval")
        
        # Add common interval options with checkmarks - reduced to 3 options
        self.interval_options = {}
        for interval in [5, 10, 30]:
            menu_item = rumps.MenuItem(
                f"{interval}s",
                callback=self.set_interval
            )
            # Set checkmark for current interval
            menu_item.state = 1 if interval == self.config.update_interval else 0
            self.interval_options[interval] = menu_item
            self.interval_submenu.add(menu_item)
        
        # Add menu items
        self.menu = [
            self.now_playing_item,
            self.artist_item,
            self.player_item,
            None,  # Separator
            self.discord_status_item,
            self.interval_submenu,
            None,  # Separator
            rumps.MenuItem("About Music RPC", callback=self.about),
        ]
        
        # Create a queue for passing UI updates from background threads
        self.update_queue = queue.Queue()
        
        # Setup timer for processing UI updates from the queue
        # This ensures UI updates happen on the main thread
        self.timer = rumps.Timer(self.process_ui_updates, 1)
        self.timer.start()
    
    def _ensure_unicode_display(self, text):
        """Ensure proper Unicode display for text in tray menu items
        
        Args:
            text: Text to process
            
        Returns:
            str: Properly encoded text
        """
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
    
    def process_ui_updates(self, _):
        """Process UI updates from the queue on the main thread"""
        try:
            # Process all pending updates
            while not self.update_queue.empty():
                update_type, data = self.update_queue.get_nowait()
                
                if update_type == "now_playing":
                    # Update now playing info
                    song_info = data
                    if song_info.is_playing():
                        # Process text to ensure proper Unicode display
                        title = self._ensure_unicode_display(song_info.title)
                        artist = self._ensure_unicode_display(song_info.artist)
                        player_name = self._ensure_unicode_display(song_info.player) if song_info.player else "Unknown Player"
                        
                        self.now_playing_item.title = f"Now Playing: {title}"
                        self.artist_item.title = f"Artist: {artist}"
                        self.player_item.title = f"Player: {player_name}"
                        self.title = "🎵"
                    else:
                        self.now_playing_item.title = "Not Playing"
                        self.artist_item.title = "Start playing music to see details"
                        self.player_item.title = "No player detected"
                        self.title = "⏸"
                        
                elif update_type == "discord":
                    # Update Discord status
                    connected = data
                    if connected:
                        self.discord_status_item.title = "Discord: Connected ✅"
                    else:
                        self.discord_status_item.title = "Discord: Disconnected ❌"
                
                elif update_type == "interval":
                    # Update interval display and checkmarks
                    interval = data
                    # Update all checkmarks in the interval submenu
                    for int_value, menu_item in self.interval_options.items():
                        menu_item.state = 1 if int_value == interval else 0
                
                # Mark the task as done
                self.update_queue.task_done()
        except Exception as e:
            self.logger.error(f"Error processing UI updates: {e}")
    
    @rumps.clicked("About Music RPC")
    def about(self, _):
        """Show about dialog"""
        rumps.alert(
            title="About Music RPC",
            message=f"Music RPC v{self.config.VERSION}\n\n"
                    f"Discord Rich Presence for Music Players\n\n"
                    f"Originally created for Deezer, now supports any music player.",
            ok="OK"
        )
    
    def set_interval(self, sender):
        """Set update interval callback"""
        # Extract interval from menu item text
        try:
            interval = int(sender.title.replace("s", ""))
            success, message = self.config.set_update_interval(str(interval))
            if success:
                # Queue the UI update instead of directly changing the UI
                self.update_queue.put(("interval", interval))
                rumps.notification(
                    title="Music RPC",
                    subtitle="Update Interval Changed",
                    message=f"Now updating every {interval} seconds"
                )
        except Exception as e:
            self.logger.error(f"Error setting interval: {e}")
    
    def update_now_playing(self, song_info):
        """Queue update for now playing information
        
        Args:
            song_info: SongInfo object with current song details
        """
        self.update_queue.put(("now_playing", song_info))
    
    def update_discord_status(self, connected):
        """Queue update for Discord connection status
        
        Args:
            connected: Boolean indicating if connected to Discord
        """
        self.update_queue.put(("discord", connected))


# Global reference to the tray app
_global_tray_app = None

def get_tray_app():
    """Get the global tray app instance"""
    global _global_tray_app
    return _global_tray_app

def create_tray_app(config, logger, discord_manager, song_info_retriever):
    """Create the tray app - must be called from the main thread"""
    global _global_tray_app
    _global_tray_app = MusicRPCTrayApp(config, logger, discord_manager, song_info_retriever)
    return _global_tray_app

def start_tray_app():
    """Start the tray app - must be called from the main thread
    This function will not return until the app is quit"""
    global _global_tray_app
    if _global_tray_app:
        _global_tray_app.run() 