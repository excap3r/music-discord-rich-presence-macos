"""
Window manager for detecting and interacting with music player windows
"""
import subprocess
from AppKit import NSWorkspace


class MediaWindow:
    """Represents a media player window in macOS"""
    
    def __init__(self, title, app_name=None):
        """Initialize with window title and app name
        
        Args:
            title (str): The window title
            app_name (str, optional): The application name
        """
        self.title = title
        self.app_name = app_name or "Music Player"


class WindowManager:
    """Manages detection and interaction with media player windows"""
    
    def __init__(self, logger):
        """Initialize with logger
        
        Args:
            logger: Logger instance for logging messages
        """
        self.logger = logger
        # List of known media player bundle identifiers
        self.known_media_players = [
            "com.apple.Music",
            "com.spotify.client",
            "com.deezer.Deezer",  # Deezer's bundle ID
            "com.apple.iTunes",
            "org.videolan.vlc",
            "co.neptunes.Audirvana",
            "com.plexamp.plexamp"
        ]
        
        # Keep track of the last detected Deezer window
        self.last_deezer_window = None
    
    def get_active_media_window(self):
        """Find the current active media player window
        
        Returns:
            MediaWindow or None: The active media window if found
        """
        print(" ┃ 🔍 Detecting media player...")
        
        # First try to detect Deezer specifically as it might need special handling
        deezer_window = self._detect_deezer()
        if deezer_window:
            print(f" ┃ 🎵 Detected Deezer: {deezer_window.title}")
            self.last_deezer_window = deezer_window
            return deezer_window
        
        # First check if any music is playing via Apple Script
        media_info = self._get_media_info_via_applescript()
        if media_info and "title" in media_info and media_info["title"]:
            print(f" ┃ 🎵 Detected playing: {media_info['title']}")
            # If we suspect this might be Deezer but it wasn't identified
            if self.last_deezer_window and not media_info.get('app_name'):
                self.logger.info("Using last known Deezer window for player name")
                media_info['app_name'] = "Deezer"
            return MediaWindow(
                f"{media_info.get('title', 'Unknown')} - {media_info.get('artist', 'Unknown Artist')}",
                media_info.get('app_name', 'Media Player')
            )
        
        # If no music is playing, check for running music applications
        for player_id in self.known_media_players:
            app_running = self._check_app_running(player_id)
            if app_running:
                app_name = player_id.split('.')[-1]
                print(f" ┃ 🎵 Detected player: {app_name}")
                return MediaWindow(f"{app_name} (Not playing)", app_name)
        
        # Fallback to NSWorkspace method to find any music player
        try:
            ws = NSWorkspace.sharedWorkspace()
            running_apps = ws.runningApplications()
            
            for app in running_apps:
                app_name = app.localizedName()
                if app_name and any(media_name.lower() in app_name.lower() 
                                    for media_name in ["music", "spotify", "deezer", "itunes", "vlc", "player"]):
                    print(f" ┃ 🎵 Detected media player: {app_name}")
                    return MediaWindow(app_name, app_name)
                
        except Exception as e:
            self.logger.error(f"Error finding media windows: {e}")
        
        # If we found Deezer previously but couldn't detect it now, use the last known window
        if self.last_deezer_window:
            print(f" ┃ 🎵 Using last known Deezer window")
            return self.last_deezer_window
            
        # Return a generic window for system media controls if no specific player is detected
        return MediaWindow("System Media Controls", "Media Player")
    
    def _detect_deezer(self):
        """Specifically detect Deezer application
        
        Returns:
            MediaWindow or None: Deezer window if found
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
                    self.logger.info("Deezer is running (via pgrep)")
                    return MediaWindow("Deezer", "Deezer")
            except Exception as e:
                self.logger.error(f"Error checking Deezer process with pgrep: {e}")
            
            # Only try the bundle ID check if pgrep fails
            deezer_running = self._check_app_running("com.deezer.Deezer", timeout=1.0)
            if deezer_running:
                self.logger.info("Deezer is running (via bundle ID)")
                return MediaWindow("Deezer", "Deezer")
            
            return None
        except Exception as e:
            self.logger.error(f"Error in Deezer detection: {e}")
            return None
    
    def check_accessibility_permissions(self):
        """Check if Terminal has accessibility permissions on macOS
        
        Returns:
            bool: True if permissions are granted, False otherwise
        """
        print(" ┃ 🔐 Checking accessibility permissions...")
        
        # Simple AppleScript to test accessibility permissions
        test_script = '''
        tell application "System Events"
            return "Accessibility permissions are enabled"
        end tell
        '''
        
        try:
            result = subprocess.run(
                ["osascript", "-e", test_script],
                capture_output=True,
                text=True
            )
            
            if result.stderr and "not allowed assistive access" in result.stderr:
                self.logger.error("Accessibility permissions not granted")
                print("\n⚠️  ACCESSIBILITY PERMISSIONS REQUIRED  ⚠️")
                print("This app needs accessibility permissions to detect song information.")
                print("Please follow these steps:")
                print("1. Open System Settings > Privacy & Security > Accessibility")
                print("2. Add Terminal (or your Python IDE) to the list")
                print("3. Make sure it's enabled (checked)")
                print("4. Restart this application\n")
                return False
                
            return True
        except Exception as e:
            self.logger.error(f"Error checking accessibility permissions: {e}")
            return False
    
    def _check_app_running(self, bundle_id, timeout=2.0):
        """Check if an app with the given bundle ID is running
        
        Args:
            bundle_id (str): The bundle identifier (e.g., com.apple.Music)
            timeout (float): Timeout for the subprocess call
            
        Returns:
            bool: True if the app is running, False otherwise
        """
        try:
            # Optimized AppleScript to directly check for a specific bundle ID
            script = f'''
            tell application "System Events"
                return (bundle identifier of processes) contains "{bundle_id}"
            end tell
            '''
            
            result = subprocess.run(
                ["osascript", "-e", script],
                capture_output=True,
                text=True,
                timeout=timeout
            )
            
            return result.stdout.strip().lower() == 'true'
        except subprocess.TimeoutExpired:
            self.logger.error(f"Timeout checking if {bundle_id} is running")
            return False
        except Exception as e:
            self.logger.error(f"Error checking if {bundle_id} is running: {e}")
            return False
    
    def _get_media_info_via_applescript(self):
        """Get media info via AppleScript
        
        Returns:
            dict: Media information including title, artist, and app name
        """
        print(" ┃ 🔍 Getting media information...")
        
        # Try the macOS Media API first (works for any app using system media controls)
        script = '''
        on run
            set mediaInfo to {}
            
            -- Try Music app
            try
                tell application "Music"
                    if it is running then
                        if player state is playing then
                            set end of mediaInfo to {app_name:"Music", title:(get name of current track), artist:(get artist of current track), playing:true}
                            return mediaInfo
                        end if
                    end if
                end tell
            end try
            
            -- Try Spotify
            try
                tell application "Spotify"
                    if it is running then
                        if player state is playing then
                            set end of mediaInfo to {app_name:"Spotify", title:(get name of current track), artist:(get artist of current track), playing:true}
                            return mediaInfo
                        end if
                    end if
                end tell
            end try
            
            -- Try Deezer
            try
                tell application "Deezer"
                    if it is running then
                        try
                            tell application "System Events" to tell process "Deezer"
                                set windowTitle to name of window 1
                                if windowTitle contains " - " then
                                    set titleParts to my theSplit(windowTitle, " - ")
                                    set end of mediaInfo to {app_name:"Deezer", title:item 1 of titleParts, artist:item 2 of titleParts, playing:true}
                                    return mediaInfo
                                end if
                            end tell
                        end try
                    end if
                end tell
            end try
            
            -- Try system-wide nowPlaying
            try
                set currentTrack to do shell script "nowplaying-cli get-title"
                set currentArtist to do shell script "nowplaying-cli get-artist"
                set currentApp to do shell script "nowplaying-cli get-app"
                
                if currentTrack is not "" and currentArtist is not "" then
                    set end of mediaInfo to {app_name:currentApp, title:currentTrack, artist:currentArtist, playing:true}
                    return mediaInfo
                end if
            end try
            
            return {}
        end run
        
        on theSplit(theString, theDelimiter)
            set oldDelimiters to AppleScript's text item delimiters
            set AppleScript's text item delimiters to theDelimiter
            set theArray to every text item of theString
            set AppleScript's text item delimiters to oldDelimiters
            return theArray
        end theSplit
        '''
        
        try:
            result = subprocess.run(
                ["osascript", "-e", script],
                capture_output=True,
                text=True
            )
            
            output = result.stdout.strip()
            if not output or output == "{}":
                return None
            
            # Parse the AppleScript output
            # Format is typically {app_name:"App", title:"Title", artist:"Artist", playing:true}
            media_info = {}
            
            # Simple parser for the AppleScript record
            if output.startswith("{") and output.endswith("}"):
                # Remove the outer braces
                inner_content = output[1:-1].strip()
                
                # Split by commas outside of quotes
                parts = []
                current_part = ""
                in_quotes = False
                
                for char in inner_content:
                    if char == '"' and (not current_part or current_part[-1] != '\\'):
                        in_quotes = not in_quotes
                    
                    if char == ',' and not in_quotes:
                        parts.append(current_part.strip())
                        current_part = ""
                    else:
                        current_part += char
                
                if current_part:
                    parts.append(current_part.strip())
                
                # Extract key-value pairs
                for part in parts:
                    if ":" in part:
                        key, value = part.split(":", 1)
                        key = key.strip()
                        value = value.strip().strip('"')
                        media_info[key] = value
            
            if media_info:
                return media_info
                
        except Exception as e:
            self.logger.error(f"Error getting media info: {e}")
        
        return None 