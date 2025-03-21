"""
Song information retrieval functionality
"""
import re
import subprocess
import requests

# For macOS MediaPlayer import
try:
    from MediaPlayer import MPRemoteCommandCenter
    MEDIA_PLAYER_AVAILABLE = True
except ImportError:
    MEDIA_PLAYER_AVAILABLE = False


class SongInfo:
    """Stores information about a song"""
    
    def __init__(self, title=None, artist=None, album_cover=None, artist_image=None, song_link=None):
        self.title = title or "Not playing"
        self.artist = artist or "Open Deezer and play a song"
        self.album_cover = album_cover
        self.artist_image = artist_image
        self.song_link = song_link
    
    def is_playing(self):
        """Check if a song is actually playing"""
        return self.title != "Not playing"


class SongInfoRetriever:
    """Retrieves song information from various sources"""
    
    def __init__(self, config, logger):
        """Initialize with config and logger
        
        Args:
            config: Config instance with API endpoints
            logger: Logger instance for logging
        """
        self.config = config
        self.logger = logger
        # Cache for song information to avoid duplicate API calls
        self.song_cache = {}
        self.last_song_key = None
    
    def format_deezer_title(self, raw_title):
        """Extract song title and artist from window title
        
        Args:
            raw_title (str): Raw window title
            
        Returns:
            tuple: (song_title, artist_name)
        """
        # If we have just the app name, return placeholder values
        if raw_title.lower() == "deezer":
            return "Not playing", "Open Deezer and play a song"
        
        # Check if it's in "Song - Artist" format
        if " - " in raw_title:
            title_parts = raw_title.split(" - ")
            if len(title_parts) >= 2:
                song_title = title_parts[0].strip()
                artist_name = title_parts[1].strip()
                return song_title, artist_name
        
        # Check if it's from AppleScript description format
        if "now playing" in raw_title.lower():
            match = re.search(r"now playing[:\s]+(.+?)\s+by\s+(.+?)(?:\s+on|$)", raw_title.lower())
            if match:
                song_title = match.group(1).strip()
                artist_name = match.group(2).strip()
                return song_title, artist_name
        
        # If we couldn't parse it in a known format, return the raw title and unknown
        return raw_title, "Unknown"
    
    def get_song_via_api(self, song_title, artist_name):
        """Get song details from Deezer API
        
        Args:
            song_title (str): Song title
            artist_name (str): Artist name
            
        Returns:
            SongInfo: Song information object
        """
        # Create a cache key from title and artist
        cache_key = f"{song_title}::{artist_name}"
        
        # If we already have this song in cache, return the cached version
        if cache_key in self.song_cache:
            return self.song_cache[cache_key]
        
        # Otherwise fetch from API
        query = f"{artist_name} {song_title}"
        try:
            response = requests.get(self.config.DEEZER_API_SEARCH_URL + query)
            response.raise_for_status()
            data = response.json()

            if data["data"]:
                song = data["data"][0]
                
                # Check if we should use album art from API
                if self.config.USE_ALBUM_ART:
                    album_cover = song["album"]["cover_medium"]
                    artist_image = song["artist"]["picture_small"]
                else:
                    # Use default assets instead
                    album_cover = "deezer_logo"
                    artist_image = "deezer_icon"
                
                # Create song info object
                song_info = SongInfo(
                    title=song_title,
                    artist=artist_name,
                    album_cover=album_cover,
                    artist_image=artist_image,
                    song_link=song["link"]
                )
                
                # Cache the result for future use
                self.song_cache[cache_key] = song_info
                
                return song_info
        except requests.RequestException as e:
            self.logger.error(f"Failed to fetch song info: {e}")

        # Create basic info for failed requests
        basic_info = SongInfo(title=song_title, artist=artist_name)
        
        # Cache even the basic info to avoid repeated API calls
        self.song_cache[cache_key] = basic_info
        
        return basic_info
    
    def get_now_playing_from_control_center(self):
        """Get Now Playing info from Control Center
        
        Returns:
            str: Now playing info or None
        """
        script = '''
        on run
            try
                tell application "System Events"
                    tell process "ControlCenter"
                        set nowPlayingText to ""
                        
                        set allElements to every UI element
                        repeat with anElement in allElements
                            set elemDesc to description of anElement
                            if elemDesc contains "Now Playing" or elemDesc contains "now playing" then
                                set nowPlayingText to elemDesc
                                exit repeat
                            end if
                        end repeat
                        
                        if nowPlayingText is not "" then
                            if nowPlayingText contains "Now playing " then
                                set theText to text from (offset of "Now playing " in nowPlayingText) + (length of "Now playing ") to end of nowPlayingText
                                if theText contains " by " then
                                    set songName to text from beginning of theText to ((offset of " by " in theText) - 1)
                                    set artistName to text from ((offset of " by " in theText) + 4) to end of theText
                                    if artistName contains " on " then
                                        set artistName to text from beginning of artistName to ((offset of " on " in artistName) - 1)
                                    end if
                                    return songName & " - " & artistName
                                end if
                            end if
                            return nowPlayingText
                        end if
                    end tell
                end tell
            end try
            return ""
        end run
        '''
        
        try:
            result = subprocess.run(
                ["osascript", "-e", script],
                capture_output=True,
                text=True
            )
            
            if result.stdout.strip():
                return result.stdout.strip()
        except Exception as e:
            self.logger.error(f"Error getting Control Center info: {e}")
            
        return None
    
    def get_deezer_direct_info(self):
        """Get direct info from Deezer app
        
        Returns:
            str: Song info or None
        """
        # First try using osascript to check if Deezer is playing
        script_check = '''
        on run
            set isRunning to false
            set isPlaying to false
            set trackInfo to ""
            
            try
                tell application "Deezer"
                    set isRunning to it is running
                    if isRunning then
                        try
                            set isPlaying to player state is playing
                            if isPlaying then
                                set trackInfo to "PLAYING: " & name of current track & " - " & artist of current track
                            else
                                set trackInfo to "NOT_PLAYING"
                            end if
                        on error errMsg
                            set trackInfo to "ERROR: " & errMsg
                        end try
                    else
                        set trackInfo to "NOT_RUNNING"
                    end if
                end tell
            on error errMsg
                set trackInfo to "SCRIPT_ERROR: " & errMsg
            end try
            
            return trackInfo
        end run
        '''
        
        try:
            result_check = subprocess.run(
                ["osascript", "-e", script_check],
                capture_output=True,
                text=True
            )
            
            if result_check.stdout.strip():
                if result_check.stdout.strip().startswith("PLAYING:"):
                    # Extract the song info from the status
                    song_info = result_check.stdout.strip().replace("PLAYING: ", "")
                    return song_info
        except Exception as e:
            self.logger.error(f"Error checking Deezer status: {e}")
        
        # Try original direct method
        script_direct = '''
        tell application "Deezer" 
            try
                if it is running then
                    try
                        set track_name to name of current track
                        set artist_name to artist of current track
                        
                        return track_name & " - " & artist_name
                    end try
                end if
            end try
        end tell
        '''
        
        try:
            result = subprocess.run(
                ["osascript", "-e", script_direct], 
                capture_output=True, 
                text=True
            )
            
            if result.stdout.strip():
                return result.stdout.strip()
                
        except Exception as e:
            self.logger.error(f"Error with direct script: {e}")
                
        # If direct methods fail, try System Events to get window title
        try:
            script_window = '''
            tell application "System Events"
                tell process "Deezer"
                    try
                        set windowTitle to name of window 1
                        return windowTitle
                    on error
                        return ""
                    end try
                end tell
            end tell
            '''
            
            result_window = subprocess.run(
                ["osascript", "-e", script_window],
                capture_output=True,
                text=True
            )
            
            if result_window.stdout.strip() and " - " in result_window.stdout.strip():
                return result_window.stdout.strip()
        except Exception as e:
            self.logger.error(f"Error with window title script: {e}")
            
        return None
    
    def get_current_song_info(self, window_title=None):
        """Try multiple methods to get current song info
        
        Args:
            window_title (str, optional): Window title if available
            
        Returns:
            SongInfo: Song information object
        """
        # First try direct method from Deezer app - highest priority
        direct_info = self.get_deezer_direct_info()
        if direct_info:
            song_title, artist_name = self.format_deezer_title(direct_info)
            
            # Create a cache key for this song
            current_key = f"{song_title}::{artist_name}"
            
            # If it's the same song as last time, use cached info
            if current_key == self.last_song_key and current_key in self.song_cache:
                return self.song_cache[current_key]
            
            # Otherwise, get info and update last song key
            self.last_song_key = current_key
            return self.get_song_via_api(song_title, artist_name)
        
        # If window title has song info, use it
        if window_title and " - " in window_title:
            song_title, artist_name = self.format_deezer_title(window_title)
            
            # Create a cache key for this song
            current_key = f"{song_title}::{artist_name}"
            
            # If it's the same song as last time, use cached info
            if current_key == self.last_song_key and current_key in self.song_cache:
                return self.song_cache[current_key]
            
            # Otherwise, get info and update last song key
            self.last_song_key = current_key
            return self.get_song_via_api(song_title, artist_name)
        
        # Then try Control Center as fallback
        now_playing = self.get_now_playing_from_control_center()
        if now_playing:
            song_title, artist_name = self.format_deezer_title(now_playing)
            
            # Create a cache key for this song
            current_key = f"{song_title}::{artist_name}"
            
            # If it's the same song as last time, use cached info
            if current_key == self.last_song_key and current_key in self.song_cache:
                return self.song_cache[current_key]
            
            # Otherwise, get info and update last song key
            self.last_song_key = current_key
            return self.get_song_via_api(song_title, artist_name)
        
        # Try window title one more time if it wasn't checked earlier
        if window_title:
            song_title, artist_name = self.format_deezer_title(window_title)
            
            # Create a cache key for this song
            current_key = f"{song_title}::{artist_name}"
            
            # If it's the same song as last time, use cached info
            if current_key == self.last_song_key and current_key in self.song_cache:
                return self.song_cache[current_key]
            
            # Otherwise, get info and update last song key
            self.last_song_key = current_key
            return self.get_song_via_api(song_title, artist_name)
        
        # If nothing was found, return default SongInfo
        print(" ┃ 💤 No song playing detected")
        self.last_song_key = None
        return SongInfo() 