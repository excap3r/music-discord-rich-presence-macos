"""
MacOS Tray Icon for Music RPC.

This module provides a system tray icon implementation for Music RPC on macOS
using the rumps library. It displays the currently playing song information and
allows the user to configure certain settings directly from the menu bar.
"""
import rumps
import threading
import os
import sys
import subprocess
import queue
import unicodedata
import re
from typing import Dict, Optional, Tuple, Any, Callable, Union, List

from ..config.settings import Config
from ..logging.handlers import Logger
from ..core.song_info import SongInfo
from ..core.discord_presence import DiscordPresenceManager
from ..core.song_info import SongInfoRetriever

# Global reference to the tray app instance
_tray_app_instance: Optional["MusicRPCTrayApp"] = None


class MusicRPCTrayApp(rumps.App):
    """Music RPC Tray Icon App for macOS.
    
    This class implements a system tray icon for Music RPC using the rumps library.
    It displays information about the currently playing song and Discord connection
    status, and provides menu options for configuring the application.
    """
    
    def __init__(self, config: Config, logger: Logger, discord_manager: DiscordPresenceManager, 
                 song_info_retriever: SongInfoRetriever) -> None:
        """Initialize the tray icon application.
        
        Args:
            config: Configuration object for application settings
            logger: Logger instance for logging messages and errors
            discord_manager: DiscordPresenceManager for Discord status updates
            song_info_retriever: SongInfoRetriever for getting current song info
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
        self.interval_options: Dict[int, rumps.MenuItem] = {}
        for interval in [5, 10, 30]:
            try:
                menu_item = rumps.MenuItem(
                    f"{interval}s",
                    callback=self.set_interval
                )
                # Set checkmark for current interval
                menu_item.state = 1 if interval == self.config.update_interval else 0
                self.interval_options[interval] = menu_item
                self.interval_submenu.add(menu_item)
            except Exception as e:
                self.logger.error(f"Error creating interval menu item {interval}s: {e}")
        
        # Add menu items
        try:
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
        except Exception as e:
            self.logger.error(f"Error setting up tray menu: {e}")
        
        # Create a queue for passing UI updates from background threads
        self.update_queue: queue.Queue = queue.Queue()
        
        # Setup timer for processing UI updates from the queue
        # This ensures UI updates happen on the main thread
        try:
            self.timer = rumps.Timer(self.process_ui_updates, 1)
            self.timer.start()
            self.logger.info("Tray icon initialized successfully")
        except Exception as e:
            self.logger.error(f"Error starting UI update timer: {e}")
    
    def _ensure_unicode_display(self, text: Optional[str]) -> str:
        """Ensure proper Unicode display for text in tray menu items.
        
        Processes text to ensure it displays correctly in the system tray menu,
        handling Unicode escape sequences and normalization.
        
        Args:
            text: Text to process
            
        Returns:
            Properly encoded text safe for display
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
                def replace_unicode_escapes(match: re.Match) -> str:
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
    
    def process_ui_updates(self, _: Any) -> None:
        """Process UI updates from the queue on the main thread.
        
        This method is called periodically by the rumps timer to process
        updates to the UI that have been queued from background threads.
        
        Args:
            _: Unused timer parameter
        """
        try:
            # Process all pending updates
            while not self.update_queue.empty():
                try:
                    update_type, data = self.update_queue.get_nowait()
                    
                    if update_type == "now_playing":
                        # Update now playing info
                        song_info = data
                        if song_info and song_info.is_playing():
                            # Process text to ensure proper Unicode display
                            title = self._ensure_unicode_display(song_info.title)
                            artist = self._ensure_unicode_display(song_info.artist)
                            player = self._ensure_unicode_display(song_info.player)
                            
                            # Truncate long titles for better display
                            if len(title) > 50:
                                title = title[:47] + "..."
                            if len(artist) > 50:
                                artist = artist[:47] + "..."
                            
                            # Update menu items
                            self.now_playing_item.title = f"Playing: {title}"
                            self.artist_item.title = f"Artist: {artist}"
                            self.player_item.title = f"Player: {player or 'Unknown'}"
                        else:
                            # Reset to default text when nothing is playing
                            self.now_playing_item.title = "Not playing"
                            self.artist_item.title = "No artist"
                            self.player_item.title = "No player detected"
                    
                    elif update_type == "discord_status":
                        # Update Discord connection status
                        connected = data
                        self.discord_status_item.title = f"Discord: {'Connected' if connected else 'Disconnected'}"
                
                except queue.Empty:
                    break
                except Exception as e:
                    self.logger.error(f"Error processing UI update: {e}")
                    
        except Exception as e:
            self.logger.error(f"Error in UI update timer callback: {e}")
    
    @rumps.clicked("About Music RPC")
    def about(self, _: Any) -> None:
        """Display information about the Music RPC application.
        
        Shows a window with the application name, version, and a brief description.
        
        Args:
            _: Unused parameter from rumps callback
        """
        try:
            version = self.config.VERSION
            about_text = f"Music RPC {version}\n\n" \
                         f"Display your currently playing music on Discord.\n" \
                         f"Supports multiple music players including Deezer, Tidal, and more."
            rumps.alert(title="About Music RPC", message=about_text)
        except Exception as e:
            self.logger.error(f"Error displaying about dialog: {e}")
    
    def set_interval(self, sender: rumps.MenuItem) -> None:
        """Set the update interval for Discord status updates.
        
        Updates the configuration with the new interval and refreshes
        the checkmarks in the interval submenu.
        
        Args:
            sender: The MenuItem that was clicked
        """
        try:
            # Extract the interval value from the menu item title
            interval_str = sender.title.replace("s", "")
            interval = int(interval_str)
            
            # Update the configuration
            success, message = self.config.set_update_interval(str(interval))
            
            if success:
                # Update checkmarks in the menu
                for option_interval, menu_item in self.interval_options.items():
                    menu_item.state = 1 if option_interval == interval else 0
                
                self.logger.info(f"Update interval set to {interval}s")
            else:
                # Show an error message if the interval couldn't be set
                rumps.alert(title="Error", message=f"Failed to set update interval: {message}")
                self.logger.error(f"Failed to set update interval: {message}")
        except Exception as e:
            self.logger.error(f"Error setting update interval: {e}")
            rumps.alert(title="Error", message=f"Failed to set update interval: {str(e)}")
    
    def update_now_playing(self, song_info: SongInfo) -> None:
        """Update the tray icon with the currently playing song information.
        
        This method is called from background threads and should not
        modify the UI directly, but instead queue the update.
        
        Args:
            song_info: Current song information to display
        """
        try:
            # Queue the update to be processed on the main thread
            self.update_queue.put(("now_playing", song_info))
        except Exception as e:
            self.logger.error(f"Error queueing now playing update: {e}")
    
    def update_discord_status(self, connected: bool) -> None:
        """Update the tray icon with Discord connection status.
        
        This method is called from background threads and should not
        modify the UI directly, but instead queue the update.
        
        Args:
            connected: Whether Discord is connected
        """
        try:
            # Queue the update to be processed on the main thread
            self.update_queue.put(("discord_status", connected))
        except Exception as e:
            self.logger.error(f"Error queueing Discord status update: {e}")


def get_tray_app() -> Optional[MusicRPCTrayApp]:
    """Get the global tray app instance if it exists.
    
    Returns:
        The global tray app instance, or None if not initialized
    """
    global _tray_app_instance
    return _tray_app_instance


def create_tray_app(config: Config, logger: Logger, 
                    discord_manager: DiscordPresenceManager, 
                    song_info_retriever: SongInfoRetriever) -> MusicRPCTrayApp:
    """Create and initialize the tray app.
    
    Args:
        config: Application configuration
        logger: Logger for recording events and errors
        discord_manager: DiscordPresenceManager instance
        song_info_retriever: SongInfoRetriever instance
        
    Returns:
        The initialized tray app instance
    """
    global _tray_app_instance
    
    try:
        # Create the tray app
        _tray_app_instance = MusicRPCTrayApp(
            config,
            logger,
            discord_manager,
            song_info_retriever
        )
        logger.info("Tray app created successfully")
        return _tray_app_instance
    except Exception as e:
        logger.error(f"Error creating tray app: {e}")
        raise


def start_tray_app(app: MusicRPCTrayApp) -> None:
    """Start the tray app in a separate thread.
    
    This is necessary because the tray app will block the main thread,
    and we need to run other operations in the background.
    
    Args:
        app: The tray app instance to start
    """
    try:
        # Create a daemon thread for the tray app
        tray_thread = threading.Thread(target=app.run)
        tray_thread.daemon = True
        tray_thread.start()
    except Exception as e:
        app.logger.error(f"Error starting tray app thread: {e}")
        raise 