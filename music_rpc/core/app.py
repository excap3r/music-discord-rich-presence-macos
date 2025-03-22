"""
Main application class for Music RPC.

This module contains the primary application controller which orchestrates
all the components needed for Discord Rich Presence functionality.
"""
import os
import sys
import signal
from typing import Optional, Any, Dict, Union, Tuple
import time
import threading
import atexit
import traceback
from music_rpc.core.tray_icon import create_tray_app, start_tray_app, get_tray_app
from music_rpc.config.settings import Config
from music_rpc.logging.handlers import Logger
from music_rpc.core.window_manager import WindowManager
from music_rpc.core.song_info import SongInfoRetriever, SongInfo
from music_rpc.core.discord_presence import DiscordPresenceManager


class MusicRPCApp:
    """Main application class for Music RPC.
    
    This class serves as the central controller for the application, coordinating
    all components and managing the application lifecycle from startup to shutdown.
    It handles window detection, Discord connection, and continuous playback monitoring.
    """
    
    def __init__(self, 
                 config: Config, 
                 logger: Logger, 
                 window_manager: WindowManager, 
                 song_info_retriever: SongInfoRetriever, 
                 discord_manager: DiscordPresenceManager) -> None:
        """Initialize the application with its dependencies.
        
        Args:
            config: Configuration settings manager
            logger: Logging service for application events
            window_manager: Detects and manages media player windows
            song_info_retriever: Extracts song information from players
            discord_manager: Manages Discord Rich Presence updates
        """
        self.config = config
        self.logger = logger
        self.window_manager = window_manager
        self.song_info_retriever = song_info_retriever
        self.discord_manager = discord_manager
        self.tray_app = None
        self.running: bool = False
        self.update_thread: Optional[threading.Thread] = None
        
        # Setup signal handlers for graceful shutdown
        try:
            signal.signal(signal.SIGINT, self._signal_handler)
            signal.signal(signal.SIGTERM, self._signal_handler)
            self.logger.info("Signal handlers registered successfully")
        except Exception as e:
            self.logger.error(f"Failed to register signal handlers: {e}")
        
        # Register clean shutdown on exit
        try:
            atexit.register(self.shutdown)
            self.logger.info("Atexit handler registered successfully")
        except Exception as e:
            self.logger.error(f"Failed to register atexit handler: {e}")
    
    def _signal_handler(self, sig: int, frame: Any) -> None:
        """Handle termination signals gracefully.
        
        Args:
            sig: Signal number received
            frame: Current stack frame
        """
        try:
            self.logger.info(f"Received termination signal {sig}")
            print("\n ┃ 🛑 Received termination signal. Shutting down...")
            self.shutdown()
            sys.exit(0)
        except Exception as e:
            self.logger.critical(f"Failed to handle termination signal: {e}")
            # In case of critical failures during shutdown, force exit
            sys.exit(1)
    
    def print_app_initialization(self) -> None:
        """Print application initialization message with version number."""
        try:
            print(" ┃ 🪧 Music RPC v" + self.config.VERSION)
            self.logger.info(f"Application initialized with version {self.config.VERSION}")
        except Exception as e:
            self.logger.error(f"Error printing initialization message: {e}")
    
    def get_update_interval_from_user(self) -> bool:
        """Ask user for update interval and update configuration.
        
        Returns:
            bool: True if interval was successfully updated or left unchanged,
                 False if there was an error updating the interval
        """
        try:
            interval_input = input(f" ┃ ⏱️ Update interval in seconds (5-60, default {self.config.update_interval}): ").strip()
            if interval_input:
                success, message = self.config.set_update_interval(interval_input)
                print(f" ┃ ⏱️ {message}")
                self.logger.info(f"Update interval set to {self.config.update_interval}")
                return success
            return True
        except Exception as e:
            self.logger.error(f"Error getting update interval: {e}")
            print(f" ┃ ⚠️ Error setting update interval: {str(e)}. Using default value.")
            return False
    
    def startup(self) -> bool:
        """Start the application and all its components.
        
        This method initializes the tray icon, starts background threads for monitoring,
        and begins the main application loop.
        
        Returns:
            bool: True if startup was successful, False otherwise
        """
        try:
            self.print_app_initialization()
            
            # Check accessibility permissions
            self.logger.info("Checking accessibility permissions")
            if not self.window_manager.check_accessibility_permissions():
                self.logger.error("Accessibility permissions check failed")
                return False
            
            # Initialize macOS tray icon on the main thread
            self.logger.info("Initializing tray icon")
            print(" ┃ 🖥️ Initializing macOS tray icon...")
            
            try:
                self.tray_app = create_tray_app(
                    self.config,
                    self.logger,
                    self.discord_manager,
                    self.song_info_retriever
                )
                self.logger.info("Tray icon initialized successfully")
            except Exception as e:
                self.logger.error(f"Failed to initialize tray icon: {e}")
                print(f" ┃ ⚠️ Error initializing tray icon: {str(e)}. Continuing without tray icon.")
            
            # Start background operation in a separate thread
            self.running = True
            self.update_thread = threading.Thread(
                target=self._run_background_operations,
                daemon=True
            )
            
            try:
                self.update_thread.start()
                self.logger.info("Background thread started successfully")
            except Exception as e:
                self.logger.error(f"Failed to start background thread: {e}")
                print(f" ┃ ⚠️ Error starting background processes: {str(e)}.")
                return False
            
            # Start the tray app on the main thread
            # This will block until the app quits
            self.logger.info("Starting tray app (this will block the main thread)")
            print(" ┃ 🖥️ Starting tray app (press Ctrl+C to exit)...")
            
            try:
                start_tray_app(self.tray_app)
            except Exception as e:
                self.logger.error(f"Error in tray app: {e}")
                print(f" ┃ ⚠️ Error running tray app: {str(e)}.")
                return False
            
            return True
        except Exception as e:
            self.logger.critical(f"Critical error during startup: {e}\n{traceback.format_exc()}")
            print(f" ┃ 🛑 Critical error during startup: {str(e)}")
            return False
    
    def _run_background_operations(self) -> None:
        """Run all background operations in a separate thread.
        
        This method handles player detection, Discord connection, and initiates
        the update loop for continuous monitoring. It's designed to run as a background
        thread separate from the main UI thread.
        """
        try:
            self.logger.info("Starting background operations")
            
            # First, try to detect the Deezer player directly (fastest path)
            try:
                self.logger.info("Attempting to detect Deezer directly")
                deezer_window = self.window_manager._detect_deezer()
                
                if deezer_window:
                    self.logger.info("Deezer detected directly")
                    print(" ┃ ✅ Deezer detected directly")
                    selected_window = deezer_window
                    player_name = "Deezer"
                    
                    # Get initial song info
                    try:
                        song_info = self.song_info_retriever.get_current_song_info(selected_window.title)
                        song_info.player = "Deezer"  # Ensure player is set to Deezer
                    except Exception as e:
                        self.logger.error(f"Error getting initial song info: {e}")
                        song_info = None
                    
                    # Connect to Discord with Deezer
                    try:
                        discord_connected = self.discord_manager.connect(player_name)
                        if not discord_connected:
                            self.logger.warning("Failed to connect to Discord")
                            # Update tray to show Discord disconnected
                            self._update_tray_discord_status(False)
                            return
                    except Exception as e:
                        self.logger.error(f"Error connecting to Discord: {e}")
                        self._update_tray_discord_status(False)
                        return
                    
                    # Update tray to show Discord connected
                    self._update_tray_discord_status(True)
                    
                    print(" ┃ 🎶 Discord Rich Presence for Deezer activated")
                    print(f" ┃ ⏱️ Update interval: {self.config.update_interval} seconds")
                    
                    # Run the update loop
                    self._run_update_loop(selected_window)
                    return
            except Exception as e:
                self.logger.error(f"Error during direct Deezer detection: {e}")
            
            # If Deezer wasn't detected directly, follow the regular flow
            self.logger.info("Deezer not detected directly, checking for music playback")
            
            # Check if any music is playing
            try:
                music_playing = self.song_info_retriever.check_now_playing()
            except Exception as e:
                self.logger.error(f"Error checking for music playback: {e}")
                music_playing = False
            
            if not music_playing:
                self.logger.info("No music playback detected initially")
                print(" ┃ ⚠️ No music playing detected. Please start playing music on any player.")
                print(" ┃ 🔄 Retrying in 5 seconds...")
                
                # Try one more time after a delay
                time.sleep(5)
                
                try:
                    music_playing = self.song_info_retriever.check_now_playing()
                except Exception as e:
                    self.logger.error(f"Error checking for music playback (retry): {e}")
                    music_playing = False
                
                if not music_playing:
                    self.logger.info("Music playback still not detected, switching to polling mode")
                    print(" ┃ ❌ Music playback not detected. Please start playing music to use this app.")
                    
                    # Show a notification in the tray
                    try:
                        tray_app = get_tray_app()
                        if tray_app:
                            empty_song_info = self.song_info_retriever.get_current_song_info(None)
                            tray_app.update_now_playing(empty_song_info)
                    except Exception as e:
                        self.logger.error(f"Error updating tray with empty song info: {e}")
                    
                    # Keep polling for music activity instead of exiting
                    self._poll_for_music_activity()
                    return
            
            # Music is playing, get a window reference or None for system media controls
            try:
                selected_window = self.window_manager.get_active_media_window()
                self.logger.info(f"Active media window detected: {selected_window.title if selected_window else 'None'}")
            except Exception as e:
                self.logger.error(f"Error getting active media window: {e}")
                selected_window = None
            
            print(" ┃ ✅ Music playback detected")
            
            # Display update interval (without asking)
            print(f" ┃ ⏱️ Update interval: {self.config.update_interval} seconds")
            
            # Get initial song info to detect the player
            try:
                song_info = self.song_info_retriever.get_current_song_info(
                    selected_window.title if selected_window else None
                )
                self.logger.info(f"Initial song info: {song_info}")
            except Exception as e:
                self.logger.error(f"Error getting initial song info: {e}")
                song_info = None
            
            # Check for Deezer specifically - this is our special focus
            player_name = song_info.player if song_info and song_info.is_playing() else None
            
            # If the player wasn't detected properly and Deezer is running, ensure it's set correctly
            if ((not player_name or player_name == "Unknown Player") and 
                selected_window and selected_window.app_name == "Deezer"):
                player_name = "Deezer"
                self.logger.info("Setting player to Deezer based on window detection")
                print(" ┃ 🎵 Detected Deezer as the player")
                
                # Also update the song info player field
                if song_info:
                    song_info.player = "Deezer"
            
            # Connect to Discord with the detected player
            try:
                discord_connected = self.discord_manager.connect(player_name)
                self.logger.info(f"Discord connection result: {discord_connected}")
            except Exception as e:
                self.logger.error(f"Error connecting to Discord: {e}")
                discord_connected = False
            
            # Update tray status based on Discord connection result
            self._update_tray_discord_status(discord_connected)
            
            # Check if this player is disabled but continue running for status display
            if not discord_connected:
                # Check if player is in disabled list
                if player_name and player_name in self.config.DISABLED_PLAYERS:
                    self.logger.info(f"Running without Discord for disabled player: {player_name}")
                    print(f" ┃ ℹ️ Running without Discord Rich Presence for {player_name}")
                    print(f" ┃ ℹ️ System tray will still show playback status")
                    self._run_update_loop(selected_window, discord_enabled=False)
                    return
                else:
                    # If Discord connection failed for other reasons
                    self.logger.warning("Discord connection failed, cannot continue with presence updates")
                    return
            
            self.logger.info("Discord Rich Presence activated successfully")
            print(" ┃ 🎶 Discord Rich Presence for Music activated")
            
            # Run the update loop with Discord enabled
            self._run_update_loop(selected_window, discord_enabled=True)
        except Exception as e:
            self.logger.critical(f"Critical error in background operations: {e}\n{traceback.format_exc()}")
    
    def _update_tray_discord_status(self, connected: bool) -> None:
        """Update the tray icon to show Discord connection status.
        
        Args:
            connected: Whether Discord is connected
        """
        try:
            tray_app = get_tray_app()
            if tray_app:
                tray_app.update_discord_status(connected)
                self.logger.debug(f"Updated tray Discord status: {connected}")
        except Exception as e:
            self.logger.error(f"Error updating tray Discord status: {e}")
    
    def _run_update_loop(self, window: Optional[Any], discord_enabled: bool = True) -> None:
        """Run the update loop to continuously update Discord presence and tray.
        
        This is the main monitoring loop that periodically checks for song updates
        and updates Discord Rich Presence and the tray icon accordingly.
        
        Args:
            window: MediaWindow object or None for system media controls
            discord_enabled: Whether Discord updates should be attempted
        """
        if discord_enabled:
            print(" ┃ 🌟 Rich Presence active and tray icon available")
        else:
            print(" ┃ 🌟 Tray icon monitoring active")
        print(f" ┃ 📊 Update interval: {self.config.update_interval} seconds")
        
        song_info = None
        
        try:
            # Initial update
            self.logger.info("Getting initial song info for update loop")
            song_info = self.song_info_retriever.get_current_song_info(window.title if window else None)
            
            # Only update Discord if enabled
            if discord_enabled:
                try:
                    self.discord_manager.update(song_info)
                    self.logger.debug("Initial Discord presence update successful")
                except Exception as e:
                    self.logger.error(f"Error updating Discord presence: {e}")
            
            # Update tray icon
            try:
                tray_app = get_tray_app()
                if tray_app:
                    tray_app.update_now_playing(song_info)
                    self.logger.debug("Initial tray update successful")
            except Exception as e:
                self.logger.error(f"Error updating tray: {e}")
                
        except Exception as error:
            self.logger.error(f"Error in initial update: {error}")
            print(f" ┃ ⚠️ Error in initial update: {error}. Will retry in next cycle.")
        
        # Track the last detected player for transitions
        last_player = song_info.player if song_info else None
        currently_disabled = last_player in self.config.DISABLED_PLAYERS if last_player else False
        
        # Track playback state
        was_playing = song_info is not None and song_info.is_playing()
        
        # Main update loop
        while self.running:
            try:
                # Get window title, which may have changed
                window_title = window.title if window else None
                
                # Get current song info
                song_info = self.song_info_retriever.get_current_song_info(window_title)
                is_now_playing = song_info is not None and song_info.is_playing()
                current_player = song_info.player if song_info else None
                
                # Detect when playback state changes
                if was_playing != is_now_playing:
                    if is_now_playing:
                        self.logger.info("Playback started")
                        print(" ┃ ▶️ Playback started")
                    else:
                        self.logger.info("Playback stopped")
                        print(" ┃ ⏹️ Playback stopped, hiding Discord presence")
                
                # Update tracking variable
                was_playing = is_now_playing
                
                # Check if we've switched players
                if last_player != current_player:
                    self.logger.info(f"Player changed from {last_player} to {current_player}")
                    print(f" ┃ 🔄 Player changed from {last_player} to {current_player}")
                    
                    # Check if new player is disabled
                    is_disabled = current_player in self.config.DISABLED_PLAYERS if current_player else False
                    
                    # If we switched from disabled to enabled player
                    if currently_disabled and not is_disabled:
                        self.logger.info(f"Reconnecting Discord for newly enabled player: {current_player}")
                        print(f" ┃ 🔄 Reconnecting Discord for {current_player}...")
                        
                        try:
                            discord_connected = self.discord_manager.connect(current_player)
                            
                            # Update discord_enabled flag
                            discord_enabled = discord_connected
                            
                            # Update tray status
                            self._update_tray_discord_status(discord_connected)
                        except Exception as e:
                            self.logger.error(f"Error reconnecting to Discord: {e}")
                    
                    # Update tracking variables
                    last_player = current_player
                    currently_disabled = is_disabled
                
                # Update Discord presence if enabled and not disabled player
                if discord_enabled and (not current_player or current_player not in self.config.DISABLED_PLAYERS):
                    try:
                        self.discord_manager.update(song_info)
                        self.logger.debug(f"Updated Discord presence: {song_info}")
                    except Exception as e:
                        self.logger.error(f"Error updating Discord presence: {e}")
                
                # Update tray icon
                try:
                    tray_app = get_tray_app()
                    if tray_app:
                        tray_app.update_now_playing(song_info)
                        self.logger.debug(f"Updated tray icon: {song_info}")
                except Exception as e:
                    self.logger.error(f"Error updating tray icon: {e}")
                
                # Use update interval to reduce CPU usage
                time.sleep(self.config.update_interval)
            except Exception as error:
                self.logger.error(f"Error in update loop: {error}")
                print(f" ┃ ⚠️ Error in update loop: {error}. Trying again in {self.config.update_interval} seconds.")
                time.sleep(self.config.update_interval)
    
    def _poll_for_music_activity(self) -> None:
        """Poll for music activity until something is detected.
        
        This is used when no music is playing initially, to keep the app running
        and ready to display Discord rich presence when music starts.
        """
        self.logger.info("Starting music activity polling mode")
        print(" ┃ 🔄 Monitoring for music activity...")
        print(" ┃ ℹ️ Discord presence will be shown when music starts playing")
        
        # Make sure we clear any existing Discord presence
        try:
            # Clear any existing presence since no music is playing
            if self.discord_manager.connected:
                self.discord_manager.rpc.clear()
                self.logger.info("Cleared existing Discord presence")
                print(" ┃ 💤 Discord presence hidden until music starts playing")
        except Exception as e:
            self.logger.error(f"Error clearing Discord presence during polling: {e}")
        
        poll_count = 0
        
        while self.running:
            try:
                # Only check every 5 seconds to reduce CPU usage
                time.sleep(5)
                
                poll_count += 1
                if poll_count % 6 == 0:  # Log every 30 seconds
                    self.logger.debug("Still monitoring for music activity")
                    print(" ┃ 🔄 Still monitoring for music activity...")
                
                # Check if any music is now playing
                try:
                    music_playing = self.song_info_retriever.check_now_playing()
                except Exception as e:
                    self.logger.error(f"Error checking for music playback in polling loop: {e}")
                    continue
                
                if music_playing:
                    self.logger.info("Music playback detected during polling")
                    print(" ┃ ✅ Music playback detected!")
                    
                    # Get the active window
                    try:
                        selected_window = self.window_manager.get_active_media_window()
                    except Exception as e:
                        self.logger.error(f"Error getting active media window: {e}")
                        selected_window = None
                    
                    # Get song info to identify the player
                    try:
                        song_info = self.song_info_retriever.get_current_song_info(
                            selected_window.title if selected_window else None
                        )
                    except Exception as e:
                        self.logger.error(f"Error getting song info: {e}")
                        continue
                    
                    # Determine player name
                    player_name = song_info.player if song_info and song_info.is_playing() else None
                    
                    # Connect to Discord if this isn't a disabled player
                    if player_name and player_name not in self.config.DISABLED_PLAYERS:
                        try:
                            discord_connected = self.discord_manager.connect(player_name)
                            
                            # Update tray status
                            tray_app = get_tray_app()
                            if tray_app:
                                tray_app.update_discord_status(discord_connected)
                                tray_app.update_now_playing(song_info)
                            
                            if discord_connected:
                                self.logger.info(f"Discord Rich Presence activated for {player_name}")
                                print(f" ┃ 🎶 Discord Rich Presence for {player_name} activated")
                                self._run_update_loop(selected_window, discord_enabled=True)
                                return
                        except Exception as e:
                            self.logger.error(f"Error connecting to Discord: {e}")
                    else:
                        # Handle disabled player case
                        self.logger.info(f"Running without Discord for disabled player: {player_name}")
                        print(f" ┃ ℹ️ Running without Discord Rich Presence for {player_name}")
                        print(f" ┃ ℹ️ System tray will still show playback status")
                        
                        # Update tray
                        try:
                            tray_app = get_tray_app()
                            if tray_app:
                                tray_app.update_now_playing(song_info)
                                tray_app.update_discord_status(False)
                        except Exception as e:
                            self.logger.error(f"Error updating tray: {e}")
                        
                        # Run update loop without Discord
                        self._run_update_loop(selected_window, discord_enabled=False)
                        return
            except Exception as e:
                self.logger.error(f"Error while polling for music activity: {e}")
    
    def shutdown(self) -> None:
        """Perform a clean shutdown of the application.
        
        Handles Discord disconnection, presence clearing, and proper resource cleanup.
        This method is designed to be called both during normal exit and when
        handling termination signals.
        """
        if not self.running:
            return
        
        self.logger.info("Shutting down application")
        self.running = False
        
        # Disconnect from Discord
        if hasattr(self, 'discord_manager') and self.discord_manager:
            try:
                # Clear presence first to ensure it's not showing when app is closed
                if self.discord_manager.connected and self.discord_manager.rpc:
                    try:
                        self.discord_manager.rpc.clear()
                        self.logger.info("Discord presence cleared")
                        print(" ┃ 💤 Discord presence cleared")
                    except Exception as e:
                        self.logger.error(f"Error clearing Discord presence during shutdown: {e}")
                
                # Now disconnect
                self.discord_manager.disconnect()
                self.logger.info("Disconnected from Discord")
            except Exception as e:
                self.logger.error(f"Error disconnecting from Discord: {e}")
        
        # Update tray app status if it exists
        try:
            tray_app = get_tray_app()
            if tray_app:
                tray_app.update_discord_status(False)
                self.logger.info("Updated tray status for shutdown")
        except Exception as e:
            self.logger.error(f"Error updating tray status: {e}")
        
        self.logger.info("Shutdown completed")
        print(" ┃ 👋 Shutdown complete. Goodbye!") 