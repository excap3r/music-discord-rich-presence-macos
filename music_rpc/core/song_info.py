"""
Song information retrieval functionality for Music RPC.

This module provides classes and utilities for retrieving, processing, and
storing information about songs from various music players and web APIs.
It handles detection of currently playing songs and enriches the data with
album art and other metadata.
"""
import re
import subprocess
import requests
import sys
import os
import unicodedata
from typing import Dict, Optional, Any
from urllib.parse import quote

from ..config.settings import Config
from ..logging.handlers import Logger

# For macOS MediaPlayer import
try:
    from MediaPlayer import MPRemoteCommandCenter
    MEDIA_PLAYER_AVAILABLE = True
except ImportError:
    MEDIA_PLAYER_AVAILABLE = False


class SongInfo:
    """Stores information about a song.
    
    This class serves as a data container for song information retrieved from
    music players and web APIs. It includes methods for handling and normalizing
    text data to ensure proper Unicode encoding.
    """
    
    def __init__(self, 
                 title: Optional[str] = None, 
                 artist: Optional[str] = None, 
                 album: Optional[str] = None, 
                 album_cover: Optional[str] = None, 
                 artist_image: Optional[str] = None, 
                 song_link: Optional[str] = None, 
                 duration: int = 0, 
                 elapsed: int = 0, 
                 playing: bool = False, 
                 player: Optional[str] = None,
                 position: Optional[int] = None,
                 start_time: Optional[int] = None,
                 end_time: Optional[int] = None,
                 album_art_url: Optional[str] = None) -> None:
        """Initialize a new SongInfo instance.
        
        Args:
            title: The title of the song
            artist: The artist/performer of the song
            album: The album the song belongs to
            album_cover: URL to album cover image
            artist_image: URL to artist image
            song_link: URL to play the song online
            duration: Total duration of the song in seconds
            elapsed: Elapsed time of the song in seconds
            playing: Whether the song is currently playing
            player: The name of the music player (e.g., "Deezer", "Music")
            position: Current playback position in seconds (alternative to elapsed)
            start_time: Epoch timestamp when the song started playing
            end_time: Epoch timestamp when the song will end
            album_art_url: Alternative URL for album art (used by Discord)
        """
        # Ensure proper Unicode encoding for text fields
        self.title = self._ensure_unicode(title) or "Not playing"
        self.artist = self._ensure_unicode(artist) or "Unknown Artist"
        self.album = self._ensure_unicode(album)
        self.album_cover = album_cover
        self.artist_image = artist_image
        self.song_link = song_link
        self.duration = duration
        self.elapsed = elapsed
        self.playing = playing
        self.player = self._ensure_unicode(player)
        self.position = position or elapsed  # Position is an alternative to elapsed
        self.start_time = start_time
        self.end_time = end_time
        self.album_art_url = album_art_url or album_cover  # Use appropriate field for Discord
    
    def _ensure_unicode(self, text: Any) -> Optional[str]:
        """Ensure the text is properly encoded as Unicode.
        
        Handles various text encodings and Unicode escape sequences to ensure
        consistent text representation.
        
        Args:
            text: The text to process, which can be a string, bytes, or other type
            
        Returns:
            Properly encoded Unicode string or None if input was None
        """
        if text is None:
            return None
        
        # Convert non-string types to string
        if not isinstance(text, str):
            try:
                if isinstance(text, bytes):
                    return text.decode('utf-8', 'replace')
                return str(text)
            except Exception as e:
                # Return a simple string representation on error
                return str(text)
        
        # Handle Unicode escape sequences like \u010C for Č
        if '\\u' in text:
            try:
                # Replace Unicode escape sequences with actual Unicode characters
                pattern = r'\\u([0-9a-fA-F]{4})'
                
                def replace_unicode(match: re.Match) -> str:
                    hex_val = match.group(1)
                    return chr(int(hex_val, 16))
                
                text = re.sub(pattern, replace_unicode, text)
            except Exception:
                pass
        
        # Handle 4-byte Unicode characters
        if '\\U' in text:
            try:
                pattern = r'\\U([0-9a-fA-F]{8})'
                
                def replace_unicode_long(match: re.Match) -> str:
                    hex_val = match.group(1)
                    return chr(int(hex_val, 16))
                
                text = re.sub(pattern, replace_unicode_long, text)
            except Exception:
                pass
        
        # Normalize Unicode characters to ensure consistent representation
        try:
            text = unicodedata.normalize('NFC', text)
        except Exception:
            pass
            
        return text
    
    def is_playing(self) -> bool:
        """Check if a song is actually playing.
        
        Returns:
            True if the song is currently playing, False otherwise
        """
        return self.title != "Not playing" and self.playing


class SongInfoRetriever:
    """Retrieves song information from various sources.
    
    This class is responsible for detecting currently playing songs from
    various music players, and enriching the song information with metadata
    from web APIs such as album art and song links.
    """
    
    def __init__(self, config: Config, logger: Logger) -> None:
        """Initialize the song information retriever.
        
        Args:
            config: Configuration object with API endpoints and settings
            logger: Logger instance for logging messages and errors
        """
        self.config = config
        self.logger = logger
        # Cache for song information to avoid duplicate API calls
        self.song_cache: Dict[str, SongInfo] = {}
        self.last_song_key: Optional[str] = None
        
        # Initialize session for API requests
        self.session = requests.Session()
        # Set a reasonable timeout for API requests
        self.session.request = lambda method, url, **kwargs: requests.Session.request(
            self.session, method, url, timeout=10, **kwargs
        )
        
        # Set up user agent for API requests
        self.user_agent = f"MusicRPC/{config.VERSION}"
        self.default_headers = {
            "User-Agent": self.user_agent
        }
        
        self.logger.info("SongInfoRetriever initialized")
    
    def _ensure_unicode(self, text):
        """Ensure the text is properly encoded as Unicode"""
        if text is None:
            return None
        
        # Convert non-string types to string
        if not isinstance(text, str):
            try:
                if isinstance(text, bytes):
                    return text.decode('utf-8', 'replace')
                return str(text)
            except Exception:
                return str(text)
        
        # Handle Unicode escape sequences like \u010C for Č
        if '\\u' in text:
            try:
                # Replace Unicode escape sequences with actual Unicode characters
                pattern = r'\\u([0-9a-fA-F]{4})'
                
                def replace_unicode(match):
                    hex_val = match.group(1)
                    return chr(int(hex_val, 16))
                
                text = re.sub(pattern, replace_unicode, text)
            except Exception:
                pass
        
        # Handle 4-byte Unicode characters
        if '\\U' in text:
            try:
                pattern = r'\\U([0-9a-fA-F]{8})'
                
                def replace_unicode_long(match):
                    hex_val = match.group(1)
                    return chr(int(hex_val, 16))
                
                text = re.sub(pattern, replace_unicode_long, text)
            except Exception:
                pass
        
        # Normalize Unicode characters to ensure consistent representation
        try:
            text = unicodedata.normalize('NFC', text)
        except Exception:
            pass
            
        return text
    
    def check_now_playing(self) -> Optional[SongInfo]:
        """Check if music is currently playing using system APIs.
        
        Returns:
            SongInfo object with basic information about the playing song,
            or None if no song is playing
        """
        try:
            # Call the actual info retrieval method
            song_info = self.get_now_playing()
            
            # Make sure we're always returning a SongInfo object or None, never a boolean
            if isinstance(song_info, bool):
                if song_info:
                    # If we just know music is playing but don't have details,
                    # return a minimal SongInfo object
                    return SongInfo(
                        title="Unknown Song",
                        artist="Unknown Artist",
                        playing=True,
                        player="Unknown Player"
                    )
                else:
                    # If no music is playing, return a non-playing SongInfo
                    return SongInfo(
                        title=None,
                        artist=None,
                        playing=False,
                        player=None
                    )
            
            # If song_info is already a SongInfo object, return it
            return song_info
        except Exception as e:
            self.logger.error(f"Error checking now playing: {e}")
            # Return a basic SongInfo object with playing=False on error
            return SongInfo(
                title=None,
                artist=None,
                playing=False,
                player=None
            )
    
    def get_now_playing(self) -> Optional[SongInfo]:
        """Get the currently playing song information using nowplaying-cli
        
        Returns:
            SongInfo object with information about the currently playing song,
            or None if no song is playing
        """
        try:
            # Run nowplaying-cli get-raw to get all available information
            # Force UTF-8 encoding for both input and output
            env = os.environ.copy()
            env['PYTHONIOENCODING'] = 'utf-8'
            env['LC_ALL'] = 'en_US.UTF-8'
            env['LANG'] = 'en_US.UTF-8'
            
            # First try to find nowplaying-cli in the PATH
            nowplaying_cli = "nowplaying-cli"
            
            # In frozen app, check if nowplaying-cli is in bin directory relative to executable
            if getattr(sys, 'frozen', False):
                bin_dir = os.path.join(os.path.dirname(sys.executable), 'bin')
                custom_nowplaying_cli = os.path.join(bin_dir, 'nowplaying-cli')
                if os.path.exists(custom_nowplaying_cli):
                    nowplaying_cli = custom_nowplaying_cli
                    self.logger.info(f"Using bundled nowplaying-cli: {custom_nowplaying_cli}")
            
            self.logger.info(f"Running nowplaying-cli: {nowplaying_cli}")
            
            # Use the simpler 'get' command to retrieve specific fields
            # This avoids having to parse complex property list format
            result = subprocess.run(
                [nowplaying_cli, "get", "title", "artist", "album"], 
                capture_output=True, 
                text=True,
                env=env
            )
            
            if result.returncode != 0:
                # If command failed, log the error and return a non-playing SongInfo
                self.logger.error(f"nowplaying-cli failed with exit code {result.returncode}: {result.stderr}")
                return SongInfo(playing=False, player=None)
            
            # Process the output - should be simple text with each value on a new line
            lines = [line.strip() for line in result.stdout.strip().split('\n') if line.strip()]
            
            # Check if we got any output
            if not lines:
                self.logger.info("No song playing according to nowplaying-cli")
                return SongInfo(playing=False, player=None)
            
            # Extract the values based on position
            title = lines[0] if len(lines) > 0 else None
            artist = lines[1] if len(lines) > 1 else None
            album = lines[2] if len(lines) > 2 else None
            
            # Get additional info for duration and playback state
            # Check if the player is playing
            playback_result = subprocess.run(
                [nowplaying_cli, "get-raw"],
                capture_output=True,
                text=True,
                env=env
            )
            
            # Default values
            duration = 0
            position = 0
            is_playing = False
            
            # If we get valid output, try to extract playback info
            if playback_result.returncode == 0 and playback_result.stdout.strip():
                raw_output = playback_result.stdout.strip()
                
                # Simple check if playback rate is mentioned and positive
                is_playing = "kMRMediaRemoteNowPlayingInfoPlaybackRate = 1" in raw_output
                
                # Try to extract duration and position if available
                try:
                    # Look for duration
                    duration_match = re.search(r'kMRMediaRemoteNowPlayingInfoDuration = (\d+(?:\.\d+)?)', raw_output)
                    if duration_match:
                        duration = float(duration_match.group(1))
                    
                    # Look for elapsed time
                    elapsed_match = re.search(r'kMRMediaRemoteNowPlayingInfoElapsedTime = "?(\d+(?:\.\d+)?)"?', raw_output)
                    if elapsed_match:
                        position = float(elapsed_match.group(1))
                except Exception as e:
                    self.logger.warning(f"Failed to extract duration/position: {e}")
            
            # If title is still None or empty after all attempts, no song is playing
            if not title:
                self.logger.info("No title found, assuming no song is playing")
                return SongInfo(playing=False, player=None)
            
            # Determine player
            player = None
            
            # Try to identify the player
            if self._detect_deezer():
                player = "Deezer"
            elif artist and "Music" in artist:
                player = "Apple Music"
            else:
                player = self._identify_player()
            
            self.logger.info(f"Player client name: {player}")
            
            # Create SongInfo object
            song_info = SongInfo(
                title=title,
                artist=artist,
                album=album,
                duration=duration,
                elapsed=position,
                playing=is_playing if title else False,
                player=player
            )
            
            return song_info
            
        except Exception as e:
            self.logger.error(f"Error getting now playing info: {e}")
            return SongInfo(playing=False, player=None)
    
    def get_song_via_api(self, song_title, artist_name, player_name=None):
        """Get song details from music API
        
        Args:
            song_title (str): Song title
            artist_name (str): Artist name
            player_name (str, optional): Name of the music player
            
        Returns:
            SongInfo: Song information object
        """
        # Create a cache key from title and artist
        cache_key = f"{song_title}::{artist_name}"
        
        # If we already have this song in cache, return the cached version
        if cache_key in self.song_cache:
            # Update player name if we have a new one
            if player_name and not self.song_cache[cache_key].player:
                self.song_cache[cache_key].player = player_name
            return self.song_cache[cache_key]
        
        # Otherwise fetch from API
        try:
            # Ensure song title and artist name are properly encoded
            song_title = self._ensure_unicode(song_title)
            artist_name = self._ensure_unicode(artist_name)
            
            self.logger.debug(f"Searching for: '{song_title}' by '{artist_name}'")
            
            # Try multiple music APIs for best results
            song_details = None
            
            # Check if the song contains Czech characters
            has_czech = self._contains_czech_chars(song_title) or self._contains_czech_chars(artist_name)
            if has_czech:
                self.logger.debug("Detected Czech characters in song title or artist name")
            
            # Try Deezer API search
            try:
                # Standard approach - try with artist and title first
                song_details = self._search_deezer(artist_name, song_title, player_name)
                
                # If that fails, try searching by title only
                if not song_details or not song_details.get("album_cover") or song_details["album_cover"] == "music_logo":
                    self.logger.debug("Trying title-only search as fallback")
                    title_only_details = self._search_deezer("", song_title, player_name)
                    
                    # If we got album art from the title-only search, use those results
                    if title_only_details and title_only_details.get("album_cover") and title_only_details["album_cover"] != "music_logo":
                        song_details = title_only_details
                
                # For songs with Czech characters, try removing diacritics as a fallback
                if has_czech and (not song_details or not song_details.get("album_cover") or song_details["album_cover"] == "music_logo"):
                    self.logger.debug("Trying search without diacritics for Czech song")
                    normalized_title = self._remove_diacritics(song_title)
                    normalized_artist = self._remove_diacritics(artist_name)
                    
                    normalized_result = self._search_deezer(normalized_artist, normalized_title, player_name)
                    if normalized_result and normalized_result.get("album_cover") and normalized_result["album_cover"] != "music_logo":
                        song_details = normalized_result
            except Exception as e:
                self.logger.error(f"Error searching Deezer API: {e}")
            
            # If we couldn't get details from any API, create basic song info
            if not song_details:
                now_playing_data = self.get_now_playing()
                
                # Get duration and elapsed time from now_playing_data
                duration = 0
                elapsed = 0
                player = player_name
                
                # Check if now_playing_data is a SongInfo object
                if now_playing_data and isinstance(now_playing_data, SongInfo):
                    duration = now_playing_data.duration or 0
                    elapsed = now_playing_data.elapsed or 0
                    player = player_name or now_playing_data.player
                
                song_details = {
                    "title": song_title,
                    "artist": artist_name,
                    "album_cover": "music_logo",
                    "artist_image": "music_icon",
                    "song_link": None,
                    "duration": float(duration),
                    "elapsed": float(elapsed),
                    "playing": True,
                    "player": player
                }
            
            # Create song info object with now playing data
            song_info = SongInfo(
                title=song_details["title"],
                artist=song_details["artist"],
                album=None,
                album_cover=song_details["album_cover"],
                artist_image=song_details["artist_image"],
                song_link=song_details["song_link"],
                duration=song_details["duration"],
                elapsed=song_details["elapsed"],
                playing=song_details["playing"],
                player=song_details["player"]
            )
            
            # Cache the result
            self.song_cache[cache_key] = song_info
            return song_info
            
        except Exception as e:
            self.logger.error(f"Error fetching song info: {e}")
            
            # Return a basic song info object if we couldn't get any details
            return SongInfo(
                title=song_title,
                artist=artist_name,
                playing=True,
                player=player_name
            )
    
    def _search_deezer(self, artist_name, song_title, player_name=None):
        """Search the Deezer API for song details
        
        Args:
            artist_name (str): Artist name
            song_title (str): Song title
            player_name (str, optional): Name of the music player
            
        Returns:
            dict: Song details or None if not found
        """
        try:
            # Prepare the query for the API request
            # If artist is provided, include it in the search, otherwise just search by title
            query_text = ""
            
            # If artist name has special characters, try a more general search
            if artist_name and self._contains_czech_chars(artist_name):
                # Just use a space between artist and title for special characters
                query_text = f"{artist_name} {song_title}"
            elif artist_name:
                # For regular text, use a more specific search format
                query_text = f'artist:"{artist_name}" track:"{song_title}"'
            else:
                # If no artist, just search by track title
                query_text = f'track:"{song_title}"'
                
            # Build the URL with proper query parameters
            api_url = f"{self.config.DEEZER_API_SEARCH_URL}?q={quote(query_text)}"
            self.logger.debug(f"Calling Deezer API: {api_url}")
            
            headers = {
                'Accept-Charset': 'utf-8',
                'Accept': 'application/json',
                'User-Agent': 'MusicRPC/2.0'  # Add user agent to avoid possible blocks
            }
            
            response = requests.get(
                api_url,
                headers=headers,
                timeout=5  # Add timeout to prevent hanging
            )
            response.raise_for_status()
            
            # Ensure JSON data is decoded with UTF-8
            response.encoding = 'utf-8'
            data = response.json()
            
            # Log the API response for debugging
            result_count = len(data.get('data', []))
            self.logger.debug(f"Deezer API found {result_count} results for query: {query_text}")
            
            if data.get("data") and len(data["data"]) > 0:
                song = data["data"][0]
                now_playing_data = self.get_now_playing()
                
                # Process song information from API
                api_title = self._ensure_unicode(song.get("title", song_title))
                api_artist = self._ensure_unicode(song.get("artist", {}).get("name", artist_name))
                
                # Get album cover URL and make sure it's accessible
                album_cover = None
                if self.config.USE_ALBUM_ART and song.get("album", {}).get("cover_medium"):
                    album_cover_url = song["album"]["cover_medium"]
                    try:
                        # Verify the album cover URL is accessible
                        cover_response = requests.head(
                            album_cover_url,
                            timeout=3,
                            headers={'User-Agent': 'MusicRPC/2.0'}
                        )
                        if cover_response.status_code == 200:
                            album_cover = album_cover_url
                            self.logger.debug(f"Album cover URL: {album_cover}")
                        else:
                            self.logger.debug(f"Album cover not accessible: {cover_response.status_code}")
                    except Exception as e:
                        self.logger.error(f"Error checking album cover URL: {e}")
                
                # Get artist image URL
                artist_image = None
                if self.config.USE_ALBUM_ART and song.get("artist", {}).get("picture_small"):
                    artist_image_url = song["artist"]["picture_small"]
                    try:
                        # Verify the artist image URL is accessible
                        image_response = requests.head(
                            artist_image_url,
                            timeout=3,
                            headers={'User-Agent': 'MusicRPC/2.0'}
                        )
                        if image_response.status_code == 200:
                            artist_image = artist_image_url
                            self.logger.debug(f"Artist image URL: {artist_image}")
                        else:
                            self.logger.debug(f"Artist image not accessible: {image_response.status_code}")
                    except Exception as e:
                        self.logger.error(f"Error checking artist image URL: {e}")
                
                # Get duration and elapsed time from now_playing_data
                duration = 0
                elapsed = 0
                player = player_name
                
                # Check if now_playing_data is a SongInfo object
                if now_playing_data and isinstance(now_playing_data, SongInfo):
                    duration = now_playing_data.duration or 0
                    elapsed = now_playing_data.elapsed or 0
                    player = player_name or now_playing_data.player
                
                return {
                    "title": api_title,
                    "artist": api_artist,
                    "album_cover": album_cover or "music_logo",
                    "artist_image": artist_image or "music_icon",
                    "song_link": song["link"],
                    "duration": float(duration),
                    "elapsed": float(elapsed),
                    "playing": True,
                    "player": player
                }
            
            # If no results found
            return None
        
        except Exception as e:
            self.logger.error(f"Error in Deezer API search: {e}")
            return None
    
    def _contains_czech_chars(self, text):
        """Check if text contains Czech-specific characters
        
        Args:
            text (str): Text to check
            
        Returns:
            bool: True if Czech characters are found
        """
        if not text:
            return False
            
        # List of Czech-specific characters
        czech_chars = 'ěščřžýáíéúůťďňóĚŠČŘŽÝÁÍÉÚŮŤĎŇÓ'
        
        return any(c in czech_chars for c in text)
    
    def _get_artist_aliases(self, artist_name):
        """Get possible aliases for artist names
        
        Args:
            artist_name: Artist name
            
        Returns:
            list: Possible artist name variations
        """
        # Default just returns the original name
        aliases = [artist_name]
        
        # Add specific aliases for known Czech artists
        artist_lower = artist_name.lower()
        if "yzomandias" in artist_lower:
            aliases.extend(["Logic", "Yzomandias", "Milion+"])
        elif "viktor sheen" in artist_lower:
            aliases.extend(["Viktor Sheen", "Sheen"])
        elif "calin" in artist_lower:
            aliases.extend(["Calin", "Callin"])
        elif "nik tendo" in artist_lower:
            aliases.extend(["Nik Tendo", "Milion+"])
        elif "hasan" in artist_lower:
            aliases.extend(["Hasan", "Hasanbeatz"])
        
        return aliases
    
    def _get_known_artist_ids(self, artist_name):
        """Get known Deezer artist IDs for specific artists
        
        Args:
            artist_name: Artist name to check
            
        Returns:
            list: List of Deezer artist IDs
        """
        artist_lower = artist_name.lower()
        
        # Map of artist names to Deezer artist IDs
        artist_id_map = {
            "yzomandias": [8183745, 1483394],  # Yzomandias, Logic
            "viktor sheen": [14870999],
            "calin": [14858449],
            "nik tendo": [10597054],
            "hasan": [4446337],
            "pil c": [15392919]
        }
        
        # Check if artist name contains any of the keys
        artist_ids = []
        for key, ids in artist_id_map.items():
            if key in artist_lower:
                artist_ids.extend(ids)
                
        return artist_ids
    
    def _search_deezer_alternative(self, artist_name, song_title, player_name=None):
        """Alternative search method for songs with Czech characters
        
        Args:
            artist_name (str): Artist name
            song_title (str): Song title
            player_name (str, optional): Name of the music player
            
        Returns:
            dict: Song details or None if not found
        """
        try:
            # Get possible artist name aliases
            artist_aliases = self._get_artist_aliases(artist_name)
            
            # Try multiple search strategies for Czech songs
            
            # Strategy 0: For known Czech artists, try getting tracks by artist ID
            artist_ids = self._get_known_artist_ids(artist_name)
            if artist_ids:
                for artist_id in artist_ids:
                    try:
                        # Try direct artist lookup
                        artist_result = self._try_artist_tracks(
                            artist_id=artist_id,
                            song_title=song_title,
                            artist_name=artist_name,
                            player_name=player_name
                        )
                        if artist_result:
                            return artist_result
                    except Exception as e:
                        self.logger.error(f"Error searching by artist ID {artist_id}: {e}")
            
            # Strategy 1: Try each artist alias alone
            for alias in artist_aliases:
                artist_only_result = self._try_alternative_search(
                    query=alias, 
                    song_title=song_title, 
                    artist_name=artist_name, 
                    player_name=player_name,
                    description=f"artist-alias-{alias}"
                )
                if artist_only_result:
                    return artist_only_result
                
            # Strategy 2: Try with simplified title (first two meaningful words)
            words = song_title.split()
            search_terms = []
            
            # Get only the most important words (more than 2 characters)
            for word in words:
                if len(word) > 2 and word.lower() not in ('the', 'and', 'feat', 'ft.', 'featuring', 'v', 'na', 'se', 'si', 'do', 'od'):
                    search_terms.append(word)
                    if len(search_terms) >= 2:
                        break
                        
            if search_terms:
                simplified_title = ' '.join(search_terms)
                simplified_result = self._try_alternative_search(
                    query=simplified_title, 
                    song_title=song_title, 
                    artist_name=artist_name, 
                    player_name=player_name,
                    description="simplified-title"
                )
                if simplified_result:
                    return simplified_result
            
            # Strategy 3: Try with first word of title and each artist alias
            if words:
                first_word = words[0]
                for alias in artist_aliases:
                    first_word_result = self._try_alternative_search(
                        query=f"{first_word} {alias}", 
                        song_title=song_title, 
                        artist_name=artist_name, 
                        player_name=player_name,
                        description=f"first-word-and-alias-{alias}"
                    )
                    if first_word_result:
                        return first_word_result
            
            # Strategy 4: Try removing all diacritics from both title and artist
            normalized_title = self._remove_diacritics(song_title)
            normalized_artist = self._remove_diacritics(artist_name)
            
            normalized_result = self._try_alternative_search(
                query=f"{normalized_title} {normalized_artist}", 
                song_title=song_title, 
                artist_name=artist_name, 
                player_name=player_name,
                description="normalized-no-diacritics"
            )
            if normalized_result:
                return normalized_result
                
            # If all specialized searches fail, return None
            return None
            
        except Exception as e:
            self.logger.error(f"Error in alternative Deezer search: {e}")
            return None
    
    def _remove_diacritics(self, text):
        """Remove diacritical marks from text
        
        Args:
            text (str): Text with diacritics
            
        Returns:
            str: Text without diacritics
        """
        if not text:
            return ""
            
        try:
            # Normalize to decomposed form (separate letters from accents)
            normalized = unicodedata.normalize('NFD', text)
            # Remove all non-spacing marks (accents)
            return ''.join(c for c in normalized if unicodedata.category(c) != 'Mn')
        except Exception as e:
            self.logger.error(f"Error removing diacritics: {e}")
            return text
    
    def _try_artist_tracks(self, artist_id, song_title, artist_name, player_name):
        """Try to find a song in an artist's tracklist using artist ID
        
        Args:
            artist_id (int): Deezer artist ID
            song_title (str): Song title to look for
            artist_name (str): Original artist name
            player_name (str): Player name
            
        Returns:
            dict: Song details or None if not found
        """
        try:
            # Build URL to get artist tracks
            api_url = f"https://api.deezer.com/artist/{artist_id}/top?limit=50"
            self.logger.debug(f"Calling Deezer API with artist ID: {api_url}")
            
            headers = {
                'Accept-Charset': 'utf-8',
                'Accept': 'application/json',
                'User-Agent': 'MusicRPC/2.0'
            }
            
            response = requests.get(
                api_url,
                headers=headers,
                timeout=5
            )
            response.raise_for_status()
            
            # Ensure JSON data is decoded with UTF-8
            response.encoding = 'utf-8'
            data = response.json()
            
            # Process track list
            tracks = data.get("data", [])
            self.logger.debug(f"Found {len(tracks)} tracks for artist ID {artist_id}")
            
            # Normalize the title for comparison
            normalized_title = self._remove_diacritics(song_title.lower())
            
            # Find best matching track
            best_match = None
            highest_score = 0
            
            for track in tracks:
                track_title = track.get("title", "")
                normalized_track = self._remove_diacritics(track_title.lower())
                
                # Calculate simple match score
                score = 0
                
                # Check exact match first
                if normalized_track == normalized_title:
                    score = 100
                else:
                    # Check for partial matches (words in common)
                    title_words = set(normalized_title.split())
                    track_words = set(normalized_track.split())
                    common_words = title_words.intersection(track_words)
                    
                    # Score based on percentage of words in common
                    if title_words:
                        score = len(common_words) * 100 / len(title_words)
                
                # Update best match if found better score
                if score > highest_score:
                    highest_score = score
                    best_match = track
            
            # If we found a decent match and it has album art
            if best_match and highest_score > 30 and best_match.get("album", {}).get("cover_medium"):
                now_playing_data = self.get_now_playing()
                album_cover_url = best_match["album"]["cover_medium"]
                
                # Verify album cover URL is accessible
                cover_response = requests.head(
                    album_cover_url,
                    timeout=3,
                    headers={'User-Agent': 'MusicRPC/2.0'}
                )
                
                if cover_response.status_code == 200:
                    self.logger.debug(f"Found album cover from artist ID search with score {highest_score}: {album_cover_url}")
                    
                    # Get duration and elapsed time from now_playing_data
                    duration = 0
                    elapsed = 0
                    player = player_name
                    
                    # Check if now_playing_data is a SongInfo object
                    if now_playing_data and isinstance(now_playing_data, SongInfo):
                        duration = now_playing_data.duration or 0
                        elapsed = now_playing_data.elapsed or 0
                        player = player_name or now_playing_data.player
                    
                    # Return song details with found album art
                    return {
                        "title": song_title,  # Keep original title
                        "artist": artist_name,  # Keep original artist
                        "album_cover": album_cover_url,
                        "artist_image": "music_icon",
                        "song_link": best_match.get("link", ""),
                        "duration": float(duration),
                        "elapsed": float(elapsed),
                        "playing": True,
                        "player": player
                    }
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error searching by artist ID: {e}")
            return None
    
    def _try_alternative_search(self, query, song_title, artist_name, player_name, description=""):
        """Try a single alternative search query
        
        Args:
            query (str): Query to search
            song_title (str): Original song title
            artist_name (str): Original artist name
            player_name (str): Player name
            description (str): Description of search strategy for logging
            
        Returns:
            dict: Song details or None if not found
        """
        try:
            # Build the URL with proper query parameters
            api_url = f"{self.config.DEEZER_API_SEARCH_URL}?q={quote(query)}"
            self.logger.debug(f"Calling Deezer API with {description} search: {api_url}")
            
            headers = {
                'Accept-Charset': 'utf-8',
                'Accept': 'application/json',
                'User-Agent': 'MusicRPC/2.0'
            }
            
            response = requests.get(
                api_url,
                headers=headers,
                timeout=5
            )
            response.raise_for_status()
            
            # Ensure JSON data is decoded with UTF-8
            response.encoding = 'utf-8'
            data = response.json()
            
            # Log the API response for debugging
            result_count = len(data.get('data', []))
            self.logger.debug(f"Deezer API found {result_count} results for {description} search")
            
            if data.get("data") and len(data["data"]) > 0:
                song = data["data"][0]
                now_playing_data = self.get_now_playing()
                
                # Get album cover URL and make sure it's accessible
                album_cover = None
                if self.config.USE_ALBUM_ART and song.get("album", {}).get("cover_medium"):
                    album_cover_url = song["album"]["cover_medium"]
                    try:
                        # Verify the album cover URL is accessible
                        cover_response = requests.head(
                            album_cover_url,
                            timeout=3,
                            headers={'User-Agent': 'MusicRPC/2.0'}
                        )
                        if cover_response.status_code == 200:
                            album_cover = album_cover_url
                            self.logger.debug(f"Album cover URL from {description} search: {album_cover}")
                        else:
                            self.logger.debug(f"Album cover not accessible: {cover_response.status_code}")
                    except Exception as e:
                        self.logger.error(f"Error checking album cover URL: {e}")
                        
                # Get duration and elapsed time from now_playing_data
                duration = 0
                elapsed = 0
                player = player_name
                
                # Check if now_playing_data is a SongInfo object
                if now_playing_data and isinstance(now_playing_data, SongInfo):
                    duration = now_playing_data.duration or 0
                    elapsed = now_playing_data.elapsed or 0
                    player = player_name or now_playing_data.player
                
                # Keep original title and artist but use the found album art
                if album_cover:  # Only return if we actually found an album cover
                    return {
                        "title": song_title,  # Keep original title
                        "artist": artist_name,  # Keep original artist
                        "album_cover": album_cover,
                        "artist_image": "music_icon",
                        "song_link": song.get("link", ""),
                        "duration": float(duration),
                        "elapsed": float(elapsed),
                        "playing": True,
                        "player": player
                    }
            
            # If no results with album art found
            return None
            
        except Exception as e:
            self.logger.error(f"Error in {description} search: {e}")
            return None
    
    def get_current_song_info(self, window_title: Optional[str] = None) -> Optional[SongInfo]:
        """Get information about the currently playing song.
        
        This is the main method for retrieving song information. It first attempts
        to detect the currently playing song using various methods, and then enriches
        the information with metadata from web APIs.
        
        Args:
            window_title: Title of the music player window (optional)
            
        Returns:
            SongInfo object with details about the currently playing song,
            or None if no song is playing or an error occurred
        """
        try:
            self.logger.debug(f"Getting song info from window: {window_title}")
            
            # Try to get song info from the MediaPlayer API first (macOS)
            song_info = self.check_now_playing()
            
            # Make sure song_info is a SongInfo object and check if it's playing
            if song_info and isinstance(song_info, SongInfo) and song_info.is_playing():
                # Generate a cache key based on title, artist, and player
                cache_key = f"{song_info.title}|{song_info.artist}|{song_info.player}"
                
                # Check if we've already processed this song
                if cache_key in self.song_cache:
                    # Update the elapsed time for the cached song
                    cached_song = self.song_cache[cache_key]
                    cached_song.elapsed = song_info.elapsed
                    cached_song.playing = song_info.playing
                    
                    # Log that we're using cached data
                    self.logger.debug(f"Using cached song info for {song_info.title}")
                    
                    # Update the last song key reference
                    self.last_song_key = cache_key
                    
                    return cached_song
                
                # If we haven't processed this song before, try to get additional info
                try:
                    # Enhance with metadata from APIs
                    enhanced_info = self.get_song_via_api(
                        song_info.title, 
                        song_info.artist,
                        song_info.player
                    )
                    
                    if enhanced_info:
                        # Preserve the original player name and playback status
                        enhanced_info.player = song_info.player
                        enhanced_info.playing = song_info.playing
                        enhanced_info.elapsed = song_info.elapsed
                        enhanced_info.duration = song_info.duration or enhanced_info.duration
                        
                        # Store in cache
                        self.song_cache[cache_key] = enhanced_info
                        self.last_song_key = cache_key
                        
                        self.logger.info(f"Enhanced song info for {enhanced_info.title} by {enhanced_info.artist}")
                        return enhanced_info
                except Exception as e:
                    # Log the error but continue with the basic song info
                    self.logger.error(f"Error enhancing song info: {e}")
                
                # If enhancement failed, use the basic info
                self.song_cache[cache_key] = song_info
                self.last_song_key = cache_key
                return song_info
            
            # If no song is playing, return the basic song info
            return song_info
            
        except Exception as e:
            self.logger.error(f"Error getting current song info: {e}")
            
            # Return a default SongInfo object for a graceful fallback
            return SongInfo(
                title=None, 
                artist=None, 
                playing=False, 
                player="Unknown"
            )
    
    def _detect_deezer(self) -> bool:
        """Detect if Deezer is running.
        
        Returns:
            bool: True if Deezer is running, False otherwise
        """
        try:
            deezer_check = subprocess.run(
                ["pgrep", "-i", "Deezer"],
                capture_output=True,
                text=True,
                timeout=0.5
            )
            return bool(deezer_check.stdout.strip())
        except Exception as e:
            self.logger.error(f"Error checking for Deezer via pgrep: {e}")
            return False
    
    def _identify_player(self) -> Optional[str]:
        """Identify which music player is currently running.
        
        Returns:
            str: Name of the detected player, or None if no player is detected
        """
        # Check common music players
        players = ["Spotify", "Music", "iTunes", "VLC", "YouTube", "Tidal"]
        
        for app_name in players:
            try:
                app_check = subprocess.run(
                    ["pgrep", "-i", app_name],
                    capture_output=True,
                    text=True,
                    timeout=0.5
                )
                if app_check.stdout.strip():
                    self.logger.info(f"Detected {app_name} application running via pgrep")
                    return app_name
            except Exception as e:
                self.logger.error(f"Error checking for {app_name} via pgrep: {e}")
        
        return None 