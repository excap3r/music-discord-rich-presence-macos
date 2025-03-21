"""
Main application class for Deezer RPC
"""
import os
import sys
import signal
import time


class DeezerRPCApp:
    """Main application class for Deezer RPC"""
    
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
        
        # Setup signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def _signal_handler(self, sig, frame):
        """Handle termination signals gracefully"""
        print("\n ┃ 🛑 Received termination signal. Shutting down...")
        self.shutdown()
        sys.exit(0)
    
    def print_app_initialization(self):
        """Print application initialization message"""
        print(" ┃ 🪧 Deezer RPC v" + self.config.VERSION)
    
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
        
        # Find Deezer windows
        deezer_windows = self.window_manager.find_deezer_windows()
        if not deezer_windows:
            print(" ┃ ⚠️ Deezer window not detected. Please open Deezer and start playing a track.")
            print(" ┃ 🔄 Retrying in 5 seconds...")
            
            # Try one more time after a delay
            time.sleep(5)
            deezer_windows = self.window_manager.find_deezer_windows()
            
            if not deezer_windows:
                print(" ┃ ❌ Deezer still not detected. Please make sure Deezer is running.")
                return False
        
        # Use the first window
        selected_window = deezer_windows[0]
        print(" ┃ ✅ Deezer detected")
        
        # Display update interval (without asking)
        print(f" ┃ ⏱️ Update interval: {self.config.update_interval} seconds")
        
        # Connect to Discord
        if not self.discord_manager.connect():
            return False
        
        print(" ┃ 🎶 Discord Rich Presence for Deezer activated")
        
        # Start the update loop
        self.discord_manager.run_update_loop(selected_window, self.song_info_retriever)
        
        return True
    
    def shutdown(self):
        """Clean shutdown of the application"""
        # Disconnect from Discord
        self.discord_manager.disconnect()
        print(" ┃ 👋 Shutdown complete. Goodbye!") 