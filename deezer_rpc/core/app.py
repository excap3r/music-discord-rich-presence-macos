"""
Main application class for Music RPC
"""
import os
import sys
import signal
import time
import threading
import atexit
from deezer_rpc.core.tray_icon import create_tray_app, start_tray_app, get_tray_app


class DeezerRPCApp:
    """Main application class for Music RPC"""
    
    def __init__(self, config, logger, window_manager, song_info_retriever, discord_manager):
        """Initialize with dependencies
        
        Args:
            config: Config instance
            logger: Logger instance
            window_manager: WindowManager instance
            song_info_retriever: SongInfoRetriever instance
            discord_manager: DiscordPresenceManager instance
        """
        self.config = config
        self.logger = logger
        self.window_manager = window_manager
        self.song_info_retriever = song_info_retriever
        self.discord_manager = discord_manager
        self.tray_app = None
        self.running = False
        self.update_thread = None
        
        # Setup signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        
        # Register clean shutdown on exit
        atexit.register(self.shutdown)
    
    def _signal_handler(self, sig, frame):
        """Handle termination signals gracefully"""
        print("\n ┃ 🛑 Received termination signal. Shutting down...")
        self.shutdown()
        sys.exit(0)
    
    def print_app_initialization(self):
        """Print application initialization message"""
        print(" ┃ 🪧 Music RPC v" + self.config.VERSION)
    
    def get_update_interval_from_user(self):
        """Ask user for update interval
        
        Returns:
            bool: True if interval was updated, False otherwise
        """
        try:
            interval_input = input(f" ┃ ⏱️ Update interval in seconds (5-60, default {self.config.update_interval}): ").strip()
            if interval_input:
                success, message = self.config.set_update_interval(interval_input)
                print(f" ┃ ⏱️ {message}")
                return success
            return True
        except Exception as e:
            self.logger.error(f"Error getting update interval: {e}")
            return False
    
    def startup(self):
        """Start the application
        
        Returns:
            bool: True if startup was successful, False otherwise
        """
        self.print_app_initialization()
        
        # Check accessibility permissions
        if not self.window_manager.check_accessibility_permissions():
            return False
        
        # Initialize macOS tray icon on the main thread
        print(" ┃ 🖥️ Initializing macOS tray icon...")
        self.tray_app = create_tray_app(
            self.config,
            self.logger,
            self.discord_manager,
            self.song_info_retriever
        )
        
        # Start background operation in a separate thread
        self.running = True
        self.update_thread = threading.Thread(
            target=self._run_background_operations,
            daemon=True
        )
        self.update_thread.start()
        
        # Start the tray app on the main thread
        # This will block until the app quits
        print(" ┃ 🖥️ Starting tray app (press Ctrl+C to exit)...")
        start_tray_app()
        
        return True
    
    def _run_background_operations(self):
        """Run all background operations in a separate thread"""
        try:
            # First, try to detect the Deezer player directly (fastest path)
            deezer_window = self.window_manager._detect_deezer()
            if deezer_window:
                print(" ┃ ✅ Deezer detected directly")
                selected_window = deezer_window
                player_name = "Deezer"
                
                # Get initial song info
                song_info = self.song_info_retriever.get_current_song_info(selected_window.title)
                
                # Ensure player is set to Deezer
                song_info.player = "Deezer"
                
                # Connect to Discord with Deezer
                if not self.discord_manager.connect(player_name):
                    # Update tray to show Discord disconnected
                    tray_app = get_tray_app()
                    if tray_app:
                        tray_app.update_discord_status(False)
                    return
                
                # Update tray to show Discord connected
                tray_app = get_tray_app()
                if tray_app:
                    tray_app.update_discord_status(True)
                
                print(" ┃ 🎶 Discord Rich Presence for Deezer activated")
                print(f" ┃ ⏱️ Update interval: {self.config.update_interval} seconds")
                
                # Run the update loop
                self._run_update_loop(selected_window)
                return
            
            # If Deezer wasn't detected directly, follow the regular flow
            # Check if any music is playing
            music_playing = self.song_info_retriever.check_now_playing()
            if not music_playing:
                print(" ┃ ⚠️ No music playing detected. Please start playing music on any player.")
                print(" ┃ 🔄 Retrying in 5 seconds...")
                
                # Try one more time after a delay
                time.sleep(5)
                music_playing = self.song_info_retriever.check_now_playing()
                
                if not music_playing:
                    print(" ┃ ❌ Music playback not detected. Please start playing music to use this app.")
                    # Show a notification in the tray
                    tray_app = get_tray_app()
                    if tray_app:
                        tray_app.update_now_playing(self.song_info_retriever.get_current_song_info(None))
                        
                    # Keep polling for music activity instead of exiting
                    self._poll_for_music_activity()
                    return
            
            # Music is playing, get a window reference or None for system media controls
            selected_window = self.window_manager.get_active_media_window()
            print(" ┃ ✅ Music playback detected")
            
            # Display update interval (without asking)
            print(f" ┃ ⏱️ Update interval: {self.config.update_interval} seconds")
            
            # Get initial song info to detect the player
            song_info = self.song_info_retriever.get_current_song_info(selected_window.title if selected_window else None)
            
            # Check for Deezer specifically - this is our special focus
            player_name = song_info.player if song_info and song_info.is_playing() else None
            
            # If the player wasn't detected properly and Deezer is running, ensure it's set correctly
            if (not player_name or player_name == "Unknown Player") and selected_window and selected_window.app_name == "Deezer":
                player_name = "Deezer"
                print(" ┃ 🎵 Detected Deezer as the player")
                
                # Also update the song info player field
                song_info.player = "Deezer"
            
            # Connect to Discord with the detected player
            discord_connected = self.discord_manager.connect(player_name)
            
            # Update tray status based on Discord connection result
            tray_app = get_tray_app()
            if tray_app:
                tray_app.update_discord_status(discord_connected)
            
            # Check if this player is disabled but continue running for status display
            if not discord_connected:
                # Check if player is in disabled list
                if player_name and player_name in self.config.DISABLED_PLAYERS:
                    print(f" ┃ ℹ️ Running without Discord Rich Presence for {player_name}")
                    print(f" ┃ ℹ️ System tray will still show playback status")
                    self._run_update_loop(selected_window, discord_enabled=False)
                    return
                else:
                    # If Discord connection failed for other reasons
                    return
            
            print(" ┃ 🎶 Discord Rich Presence for Music activated")
            
            # Run the update loop with Discord enabled
            self._run_update_loop(selected_window, discord_enabled=True)
        except Exception as e:
            self.logger.error(f"Error in background operations: {e}")
    
    def _run_update_loop(self, window, discord_enabled=True):
        """Run the update loop to continuously update Discord presence and tray
        
        Args:
            window: MediaWindow object
            discord_enabled: Whether Discord updates should be attempted
        """
        if discord_enabled:
            print(" ┃ 🌟 Rich Presence active and tray icon available")
        else:
            print(" ┃ 🌟 Tray icon monitoring active")
        print(f" ┃ 📊 Update interval: {self.config.update_interval} seconds")
        
        try:
            # Initial update
            song_info = self.song_info_retriever.get_current_song_info(window.title if window else None)
            
            # Only update Discord if enabled
            if discord_enabled:
                self.discord_manager.update(song_info)
            
            # Update tray icon
            tray_app = get_tray_app()
            if tray_app:
                tray_app.update_now_playing(song_info)
        except Exception as error:
            self.logger.error(f"Error in initial update: {error}")
        
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
                        print(" ┃ ▶️ Playback started")
                    else:
                        print(" ┃ ⏹️ Playback stopped, hiding Discord presence")
                
                # Update tracking variable
                was_playing = is_now_playing
                
                # Check if we've switched players
                if last_player != current_player:
                    print(f" ┃ 🔄 Player changed from {last_player} to {current_player}")
                    
                    # Check if new player is disabled
                    is_disabled = current_player in self.config.DISABLED_PLAYERS if current_player else False
                    
                    # If we switched from disabled to enabled player
                    if currently_disabled and not is_disabled:
                        print(f" ┃ 🔄 Reconnecting Discord for {current_player}...")
                        discord_connected = self.discord_manager.connect(current_player)
                        
                        # Update discord_enabled flag
                        discord_enabled = discord_connected
                        
                        # Update tray status
                        tray_app = get_tray_app()
                        if tray_app:
                            tray_app.update_discord_status(discord_connected)
                    
                    # Update tracking variables
                    last_player = current_player
                    currently_disabled = is_disabled
                
                # Update Discord presence if enabled and not disabled player
                if discord_enabled and (not current_player or current_player not in self.config.DISABLED_PLAYERS):
                    self.discord_manager.update(song_info)
                
                # Update tray icon
                tray_app = get_tray_app()
                if tray_app:
                    tray_app.update_now_playing(song_info)
                
                # Use update interval to reduce CPU usage
                time.sleep(self.config.update_interval)
            except Exception as error:
                self.logger.error(f"Error in update loop: {error}")
                print(f" ┃ ⚠️ Error in update loop: {error}. Trying again in {self.config.update_interval} seconds.")
                time.sleep(self.config.update_interval)
    
    def _poll_for_music_activity(self):
        """Poll for music activity until something is detected
        
        This is used when no music is playing initially, to keep the app running
        and ready to display Discord rich presence when music starts.
        """
        print(" ┃ 🔄 Monitoring for music activity...")
        print(" ┃ ℹ️ Discord presence will be shown when music starts playing")
        
        # Make sure we clear any existing Discord presence
        try:
            # Clear any existing presence since no music is playing
            if self.discord_manager.connected:
                self.discord_manager.rpc.clear()
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
                    print(" ┃ 🔄 Still monitoring for music activity...")
                
                # Check if any music is now playing
                music_playing = self.song_info_retriever.check_now_playing()
                if music_playing:
                    print(" ┃ ✅ Music playback detected!")
                    
                    # Get the active window
                    selected_window = self.window_manager.get_active_media_window()
                    
                    # Get song info to identify the player
                    song_info = self.song_info_retriever.get_current_song_info(
                        selected_window.title if selected_window else None
                    )
                    
                    # Determine player name
                    player_name = song_info.player if song_info and song_info.is_playing() else None
                    
                    # Connect to Discord if this isn't a disabled player
                    if player_name and player_name not in self.config.DISABLED_PLAYERS:
                        discord_connected = self.discord_manager.connect(player_name)
                        
                        # Update tray status
                        tray_app = get_tray_app()
                        if tray_app:
                            tray_app.update_discord_status(discord_connected)
                            tray_app.update_now_playing(song_info)
                        
                        if discord_connected:
                            print(f" ┃ 🎶 Discord Rich Presence for {player_name} activated")
                            self._run_update_loop(selected_window, discord_enabled=True)
                            return
                    else:
                        # Handle disabled player case
                        print(f" ┃ ℹ️ Running without Discord Rich Presence for {player_name}")
                        print(f" ┃ ℹ️ System tray will still show playback status")
                        
                        # Update tray
                        tray_app = get_tray_app()
                        if tray_app:
                            tray_app.update_now_playing(song_info)
                            tray_app.update_discord_status(False)
                        
                        # Run update loop without Discord
                        self._run_update_loop(selected_window, discord_enabled=False)
                        return
            except Exception as e:
                self.logger.error(f"Error while polling for music activity: {e}")
    
    def shutdown(self):
        """Clean shutdown of the application"""
        if not self.running:
            return
            
        self.running = False
        
        # Disconnect from Discord
        if hasattr(self, 'discord_manager') and self.discord_manager:
            try:
                # Clear presence first to ensure it's not showing when app is closed
                if self.discord_manager.connected and self.discord_manager.rpc:
                    try:
                        self.discord_manager.rpc.clear()
                        print(" ┃ 💤 Discord presence cleared")
                    except Exception as e:
                        self.logger.error(f"Error clearing Discord presence during shutdown: {e}")
                
                # Now disconnect
                self.discord_manager.disconnect()
            except Exception as e:
                self.logger.error(f"Error disconnecting from Discord: {e}")
        
        # Update tray app status if it exists
        tray_app = get_tray_app()
        if tray_app:
            try:
                tray_app.update_discord_status(False)
            except Exception as e:
                self.logger.error(f"Error updating tray status: {e}")
            
        print(" ┃ 👋 Shutdown complete. Goodbye!") 