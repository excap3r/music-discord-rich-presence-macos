"""
Window manager for detecting and interacting with music player windows.

This module provides functionality for detecting active music player applications
on macOS systems and retrieving information about them. It uses Apple's NSWorkspace
and AppleScript to identify running music players and their current state.
"""
import subprocess
import time
from typing import Dict, List, Optional, Any, Union, Tuple
from AppKit import NSWorkspace

from ..logging.handlers import Logger


class MediaWindow:
    """Represents a media player window in macOS.
    
    This class stores information about a detected media player window,
    including its title and the name of the application it belongs to.
    """
    
    def __init__(self, title: str, app_name: Optional[str] = None) -> None:
        """Initialize a MediaWindow instance.
        
        Args:
            title: The window title or song information
            app_name: The application name (defaults to "Music Player" if not provided)
        """
        self.title = title
        self.app_name = app_name or "Music Player"


class WindowManager:
    """Manages detection and interaction with media player windows.
    
    This class provides methods to detect running music player applications
    on macOS and retrieve information about their current state and playback.
    It uses a combination of NSWorkspace, AppleScript, and subprocess calls
    to identify and interact with media players.
    """
    
    def __init__(self, logger: Logger) -> None:
        """Initialize the WindowManager with a logger.
        
        Args:
            logger: Logger instance for logging messages and errors
        """
        self.logger = logger
        
        # List of known media player bundle identifiers
        self.known_media_players: List[str] = [
            "com.apple.Music",
            "com.spotify.client",
            "com.deezer.Deezer",  # Deezer's bundle ID
            "com.apple.iTunes",
            "org.videolan.vlc",
            "co.neptunes.Audirvana",
            "com.plexamp.plexamp",
            "com.tidal.desktop"
        ]
        
        # Keep track of the last detected media player window
        self.last_media_window: Optional[MediaWindow] = None
    
    def get_active_media_window(self) -> Optional[MediaWindow]:
        """Find the currently active media player window.
        
        Attempts to detect active music players using multiple methods:
        1. Check for Deezer specifically
        2. Use AppleScript to check if any music is playing
        3. Check if any known media player applications are running
        4. Use NSWorkspace to find applications with media-related names
        
        Returns:
            MediaWindow object if a media player is found, None otherwise
        """
        self.logger.info("Detecting active media player")
        
        # First try to detect Deezer specifically as it might need special handling
        deezer_window = self._detect_deezer()
        if deezer_window:
            self.logger.info(f"Detected Deezer: {deezer_window.title}")
            self.last_media_window = deezer_window
            return deezer_window
        
        # Check if any music is playing via Apple Script
        media_info = self._get_media_info_via_applescript()
        if media_info and "title" in media_info and media_info["title"]:
            self.logger.info(f"Detected playing music: {media_info['title']}")
            
            # If we suspect this might be Deezer but it wasn't identified
            if self.last_media_window and not media_info.get('app_name'):
                if self.last_media_window.app_name == "Deezer":
                    self.logger.info("Using last known Deezer window for player name")
                    media_info['app_name'] = "Deezer"
            
            # Create a media window with the retrieved information
            window = MediaWindow(
                f"{media_info.get('title', 'Unknown')} - {media_info.get('artist', 'Unknown Artist')}",
                media_info.get('app_name', 'Media Player')
            )
            self.last_media_window = window
            return window
        
        # If no music is playing, check for running music applications
        for player_id in self.known_media_players:
            try:
                app_running = self._check_app_running(player_id)
                if app_running:
                    app_name = player_id.split('.')[-1]
                    # Capitalize app name for better display
                    app_name = app_name.capitalize()
                    self.logger.info(f"Detected player: {app_name} (not playing)")
                    window = MediaWindow(f"{app_name} (Not playing)", app_name)
                    self.last_media_window = window
                    return window
            except Exception as e:
                self.logger.error(f"Error checking if {player_id} is running: {e}")
        
        # Fallback to NSWorkspace method to find any music player
        try:
            ws = NSWorkspace.sharedWorkspace()
            running_apps = ws.runningApplications()
            
            for app in running_apps:
                app_name = app.localizedName()
                if app_name and any(media_name.lower() in app_name.lower() 
                                    for media_name in ["music", "spotify", "deezer", "itunes", "vlc", "tidal", "player"]):
                    self.logger.info(f"Detected media player via NSWorkspace: {app_name}")
                    window = MediaWindow(app_name, app_name)
                    self.last_media_window = window
                    return window
                
        except Exception as e:
            self.logger.error(f"Error finding media windows via NSWorkspace: {e}")
        
        # If we found a media player previously but couldn't detect it now, use the last known window
        if self.last_media_window:
            self.logger.info(f"Using last known media window: {self.last_media_window.app_name}")
            return self.last_media_window
            
        # Return a generic window for system media controls if no specific player is detected
        self.logger.info("No specific media player detected, using system media controls")
        return MediaWindow("System Media Controls", "Media Player")
    
    def _detect_deezer(self) -> Optional[MediaWindow]:
        """Specifically detect the Deezer application.
        
        Uses multiple methods to check if Deezer is running, including
        pgrep and NSWorkspace bundle identifier checks.
        
        Returns:
            MediaWindow object for Deezer if found, None otherwise
        """
        try:
            # Fast check: Use pgrep first (much faster than AppleScript)
            try:
                deezer_check = subprocess.run(
                    ["pgrep", "-i", "Deezer"],
                    capture_output=True,
                    encoding='utf-8',
                    timeout=0.5
                )
                if deezer_check.stdout.strip():
                    self.logger.debug("Deezer is running (via pgrep)")
                    return MediaWindow("Deezer", "Deezer")
            except subprocess.TimeoutExpired:
                self.logger.warning("Timeout checking Deezer process with pgrep")
            except Exception as e:
                self.logger.error(f"Error checking Deezer process with pgrep: {e}")
            
            # Only try the bundle ID check if pgrep fails
            deezer_running = self._check_app_running("com.deezer.Deezer", timeout=1.0)
            if deezer_running:
                self.logger.debug("Deezer is running (via bundle ID)")
                return MediaWindow("Deezer", "Deezer")
            
            return None
        except Exception as e:
            self.logger.error(f"Error in Deezer detection: {e}")
            return None
    
    def check_accessibility_permissions(self) -> bool:
        """Check if Terminal has accessibility permissions on macOS.
        
        Uses AppleScript to test if the current process has permission to
        use System Events, which is required for many window operations.
        
        Returns:
            True if permissions are granted, False otherwise
        """
        self.logger.info("Checking accessibility permissions")
        
        # Simple AppleScript to test accessibility permissions
        test_script = '''
        tell application "System Events"
            return "Accessibility permissions are enabled"
        end tell
        '''
        
        try:
            # Run the test script
            result = subprocess.run(
                ["osascript", "-e", test_script],
                capture_output=True,
                text=True,
                timeout=3.0
            )
            
            # Check if the script executed successfully
            if result.returncode == 0 and "enabled" in result.stdout:
                self.logger.info("Accessibility permissions are enabled")
                return True
            else:
                self.logger.warning("Accessibility permissions may not be enabled")
                if result.stderr:
                    self.logger.error(f"Permission error: {result.stderr.strip()}")
                return False
                
        except subprocess.TimeoutExpired:
            self.logger.error("Timeout checking accessibility permissions")
            return False
        except Exception as e:
            self.logger.error(f"Error checking accessibility permissions: {e}")
            return False
    
    def _check_app_running(self, bundle_id: str, timeout: float = 2.0) -> bool:
        """Check if an application with the specified bundle ID is running.
        
        Uses NSWorkspace to check if an application with the given
        bundle identifier is currently running.
        
        Args:
            bundle_id: The application's bundle identifier
            timeout: Maximum time to wait for the check to complete
            
        Returns:
            True if the application is running, False otherwise
            
        Raises:
            TimeoutError: If the check takes longer than the specified timeout
        """
        try:
            # Use NSWorkspace to check if the app is running
            start_time = time.time()
            ws = NSWorkspace.sharedWorkspace()
            
            # We'll keep trying until we timeout
            while time.time() - start_time < timeout:
                running_apps = ws.runningApplications()
                
                for app in running_apps:
                    if app.bundleIdentifier() == bundle_id:
                        return True
                
                # Sleep briefly to avoid high CPU usage
                time.sleep(0.1)
            
            # If we get here, the app was not found
            return False
            
        except Exception as e:
            self.logger.error(f"Error checking if {bundle_id} is running: {e}")
            return False
    
    def _get_media_info_via_applescript(self) -> Optional[Dict[str, str]]:
        """Get information about currently playing media using AppleScript.
        
        Executes an AppleScript to query various music players for information
        about the currently playing track.
        
        Returns:
            Dictionary with media information (title, artist, album, app_name) or None if no media is playing
        """
        # Try to get info from Music/iTunes first
        script = '''
        set playerList to {"Music", "iTunes", "Spotify"}
        set mediaInfo to {}
        
        repeat with playerName in playerList
            try
                tell application "System Events"
                    if (exists process playerName) and (exists application process playerName) then
                        tell application playerName
                            if player state is playing then
                                set mediaInfo to {title:name of current track, artist:artist of current track, album:album of current track, app_name:playerName}
                                exit repeat
                            end if
                        end tell
                    end if
                end tell
            on error errMsg
                -- Silently continue to the next player
            end try
        end repeat
        
        -- Check Deezer with a different approach since it has a different structure
        if mediaInfo is {} then
            try
                tell application "System Events"
                    if (exists process "Deezer") and (exists application process "Deezer") then
                        tell application "Deezer"
                            if player state is playing then
                                set mediaInfo to {title:current track, artist:current artist, album:current album, app_name:"Deezer"}
                            end if
                        end tell
                    end if
                end tell
            on error errMsg
                -- Silently continue
            end try
        end if
        
        return mediaInfo
        '''
        
        try:
            # Run the AppleScript
            result = subprocess.run(
                ["osascript", "-e", script],
                capture_output=True,
                text=True,
                timeout=3.0
            )
            
            # Process the result
            if result.returncode == 0 and result.stdout.strip():
                output = result.stdout.strip()
                
                # Parse the output into a dictionary
                media_info = {}
                if "title:" in output:
                    # Extract key-value pairs
                    pairs = output.split(", ")
                    for pair in pairs:
                        if ":" in pair:
                            key, value = pair.split(":", 1)
                            # Clean up keys and values
                            key = key.strip().replace("title", "title").replace("album of current track", "album").replace("artist of current track", "artist")
                            value = value.strip()
                            media_info[key] = value
                    
                    # Replace empty values with None
                    for key in media_info:
                        if not media_info[key]:
                            media_info[key] = None
                    
                    self.logger.debug(f"Retrieved media info via AppleScript: {media_info}")
                    return media_info
                
            # If we get here, no media is playing
            return None
                
        except subprocess.TimeoutExpired:
            self.logger.warning("Timeout getting media info via AppleScript")
            return None
        except Exception as e:
            self.logger.error(f"Error getting media info via AppleScript: {e}")
            return None 