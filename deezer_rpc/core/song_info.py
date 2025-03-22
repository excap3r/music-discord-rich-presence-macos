"""
Song information retrieval functionality
"""
import re
import subprocess
import requests
import json
import sys
import os
import time
import unicodedata
from urllib.parse import quote

# For macOS MediaPlayer import
try:
    from MediaPlayer import MPRemoteCommandCenter
    MEDIA_PLAYER_AVAILABLE = True
except ImportError:
    MEDIA_PLAYER_AVAILABLE = False


class SongInfo:
    """Stores information about a song"""
    
    def __init__(self, title=None, artist=None, album=None, album_cover=None, artist_image=None, 
                 song_link=None, duration=0, elapsed=0, playing=False, player=None):
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
    
    def is_playing(self):
        """Check if a song is actually playing"""
        return self.title != "Not playing" and self.playing


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
    
    def check_now_playing(self):
        """Check if anything is currently playing
        
        Returns:
            bool: True if music is playing, False otherwise
        """
        try:
            now_playing = self.get_now_playing()
            if now_playing and now_playing.get("title") and now_playing.get("title") != "Unknown":
                return now_playing.get("playing", False)
            return False
        except Exception as e:
            self.logger.error(f"Error checking now playing status: {e}")
            return False
    
    def get_now_playing(self):
        """Get the currently playing song information using nowplaying-cli"""
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
            
            result = subprocess.run(
                [nowplaying_cli, "get-raw"], 
                capture_output=True, 
                encoding='utf-8',  # Explicitly use UTF-8 encoding for output
                check=True,
                env=env
            )
            
            # Parse the output into a dictionary
            info = {}
            raw_output = result.stdout.strip()
            
            # Check if there's any output
            if not raw_output:
                return None
                
            # Log the raw output for debugging
            self.logger.debug(f"Raw nowplaying-cli output: {raw_output}")
                
            # Convert the output to a proper Python dictionary
            # Clean up the output by removing curly braces
            output_lines = raw_output.strip("{}\n").split("\n")
            
            for line in output_lines:
                line = line.strip()
                if not line or "=" not in line:
                    continue
                    
                # Split by the first equals sign
                key, value = line.split("=", 1)
                
                # Clean up the key and value
                key = key.strip()
                # Handle escaped unicode characters
                value = value.strip().strip('";')
                
                # Directly process Unicode escapes using our helper
                value = self._ensure_unicode(value)
                
                # Add to our info dictionary
                info[key] = value
            
            # Try to detect the player name
            # This is necessary because nowplaying-cli doesn't always provide client name
            player_name = info.get("kMRMediaRemoteNowPlayingInfoClientName", None)
            
            # If client name is not available, try to detect based on different approaches
            if not player_name:
                # First try to identify the player from known patterns
                content_identifier = info.get("kMRMediaRemoteNowPlayingInfoContentItemIdentifier")
                bundle_identifier = info.get("kMRMediaRemoteNowPlayingInfoBundleIdentifier")
                
                self.logger.info(f"Content identifier: {content_identifier}, Bundle identifier: {bundle_identifier}")
                
                # Identify player based on bundle/content identifier patterns
                if bundle_identifier:
                    if "apple" in bundle_identifier.lower() and "music" in bundle_identifier.lower():
                        player_name = "Music"
                    elif "spotify" in bundle_identifier.lower():
                        player_name = "Spotify"
                    elif "deezer" in bundle_identifier.lower():
                        player_name = "Deezer"
                    elif "vlc" in bundle_identifier.lower():
                        player_name = "VLC"
                    elif "itunes" in bundle_identifier.lower():
                        player_name = "iTunes"
                    elif "youtube" in bundle_identifier.lower():
                        player_name = "YouTube"
                
                # Try content identifier if bundle identifier didn't work
                if not player_name and content_identifier:
                    if "apple" in content_identifier.lower():
                        player_name = "Music"
                    elif "spotify" in content_identifier.lower():
                        player_name = "Spotify"
                    elif "deezer" in content_identifier.lower():
                        player_name = "Deezer"
                
                # If still no player name, check for Deezer specifically (fastest method)
                if not player_name:
                    try:
                        deezer_check = subprocess.run(
                            ["pgrep", "-i", "Deezer"],
                            capture_output=True,
                            encoding='utf-8',
                            timeout=0.5
                        )
                        if deezer_check.stdout.strip():
                            self.logger.info("Detected Deezer application running via pgrep (fast method)")
                            player_name = "Deezer"
                    except Exception as e:
                        self.logger.error(f"Error checking for Deezer via pgrep: {e}")
                
                # Check for Apple Music
                if not player_name:
                    try:
                        music_check = subprocess.run(
                            ["pgrep", "-i", "Music"],
                            capture_output=True,
                            encoding='utf-8',
                            timeout=0.5
                        )
                        if music_check.stdout.strip():
                            self.logger.info("Detected Apple Music application running via pgrep")
                            player_name = "Music"
                    except Exception as e:
                        self.logger.error(f"Error checking for Apple Music via pgrep: {e}")
                
                # Check for other common players if we still don't have a player name
                if not player_name:
                    for app_name in ["Spotify", "iTunes", "VLC", "YouTube"]:
                        try:
                            app_check = subprocess.run(
                                ["pgrep", "-i", app_name],
                                capture_output=True,
                                encoding='utf-8',
                                timeout=0.5
                            )
                            if app_check.stdout.strip():
                                self.logger.info(f"Detected {app_name} application running via pgrep")
                                player_name = app_name
                                break
                        except Exception as e:
                            self.logger.error(f"Error checking for {app_name} via pgrep: {e}")
                
                # Last resort: Try to get source app using nowplaying-cli source command
                if not player_name:
                    try:
                        source_result = subprocess.run(
                            [nowplaying_cli, "source"], 
                            capture_output=True,
                            encoding='utf-8',
                            timeout=1.0
                        )
                        source = source_result.stdout.strip()
                        self.logger.info(f"Playback source: {source}")
                        
                        # Map source to player name
                        if source:
                            source_lower = source.lower()
                            if "music" in source_lower or "apple" in source_lower:
                                player_name = "Music"
                            elif "spotify" in source_lower:
                                player_name = "Spotify"
                            elif "deezer" in source_lower:
                                player_name = "Deezer"
                            elif "itunes" in source_lower:
                                player_name = "iTunes"
                            elif "vlc" in source_lower:
                                player_name = "VLC"
                            elif "youtube" in source_lower:
                                player_name = "YouTube"
                            else:
                                # Just use the source name if we can't map it
                                player_name = source
                    except Exception as e:
                        self.logger.error(f"Error checking playback source: {e}")
            
            # Extract the relevant information
            song_info = {
                "title": info.get("kMRMediaRemoteNowPlayingInfoTitle", "Unknown"),
                "artist": info.get("kMRMediaRemoteNowPlayingInfoArtist", "Unknown"),
                "album": info.get("kMRMediaRemoteNowPlayingInfoAlbum", "Unknown"),
                "duration": info.get("kMRMediaRemoteNowPlayingInfoDuration", "0"),
                "elapsed": info.get("kMRMediaRemoteNowPlayingInfoElapsedTime", "0"),
                "playing": True if info.get("kMRMediaRemoteNowPlayingInfoPlaybackRate", "0") != "0" else False,
                "player": player_name
            }
            
            # DEBUG: Log the client name detection
            self.logger.info(f"Player client name: {player_name}")
            
            # One more pass to ensure all strings are properly encoded
            for key in ["title", "artist", "album", "player"]:
                if song_info.get(key):
                    song_info[key] = self._ensure_unicode(song_info[key])
                    
                    # Log the processed values to help with debugging
                    self.logger.debug(f"Processed {key}: {song_info[key]}")
            
            return song_info
            
        except subprocess.CalledProcessError as e:
            self.logger.error(f"Error executing nowplaying-cli: {e}")
            return None
        except Exception as e:
            self.logger.error(f"Unexpected error getting now playing info: {e}")
            return None
    
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
                song_details = {
                    "title": song_title,
                    "artist": artist_name,
                    "album_cover": "music_logo",
                    "artist_image": "music_icon",
                    "song_link": None,
                    "duration": float(now_playing_data.get("duration", 0)) if now_playing_data else 0,
                    "elapsed": float(now_playing_data.get("elapsed", 0)) if now_playing_data else 0,
                    "playing": True,
                    "player": player_name or (now_playing_data.get("player") if now_playing_data else None)
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
                
                return {
                    "title": api_title,
                    "artist": api_artist,
                    "album_cover": album_cover or "music_logo",
                    "artist_image": artist_image or "music_icon",
                    "song_link": song["link"],
                    "duration": float(now_playing_data.get("duration", 0)) if now_playing_data else 0,
                    "elapsed": float(now_playing_data.get("elapsed", 0)) if now_playing_data else 0,
                    "playing": True,
                    "player": player_name or (now_playing_data.get("player") if now_playing_data else None)
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
                    
                    # Return song details with found album art
                    return {
                        "title": song_title,  # Keep original title
                        "artist": artist_name,  # Keep original artist
                        "album_cover": album_cover_url,
                        "artist_image": "music_icon",
                        "song_link": best_match.get("link", ""),
                        "duration": float(now_playing_data.get("duration", 0)) if now_playing_data else 0,
                        "elapsed": float(now_playing_data.get("elapsed", 0)) if now_playing_data else 0,
                        "playing": True,
                        "player": player_name or (now_playing_data.get("player") if now_playing_data else None)
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
                        
                # Keep original title and artist but use the found album art
                if album_cover:  # Only return if we actually found an album cover
                    return {
                        "title": song_title,  # Keep original title
                        "artist": artist_name,  # Keep original artist
                        "album_cover": album_cover,
                        "artist_image": "music_icon",
                        "song_link": song.get("link", ""),
                        "duration": float(now_playing_data.get("duration", 0)) if now_playing_data else 0,
                        "elapsed": float(now_playing_data.get("elapsed", 0)) if now_playing_data else 0,
                        "playing": True,
                        "player": player_name or (now_playing_data.get("player") if now_playing_data else None)
                    }
            
            # If no results with album art found
            return None
            
        except Exception as e:
            self.logger.error(f"Error in {description} search: {e}")
            return None
    
    def get_current_song_info(self, window_title=None):
        """Get current song information from window title or system media
        
        Args:
            window_title (str, optional): Window title to parse for song info
            
        Returns:
            SongInfo: Song information object
        """
        # Try to get information from nowplaying-cli first (most reliable)
        now_playing = self.get_now_playing()
        
        if now_playing and now_playing.get("title") and now_playing.get("title") != "Unknown":
            # We have song info from nowplaying-cli
            title = now_playing.get("title")
            artist = now_playing.get("artist", "Unknown Artist")
            player = now_playing.get("player")
            
            # Create a cache key
            cache_key = f"{title}::{artist}"
            
            # Check if song is the same as the last one we processed (for caching)
            if cache_key == self.last_song_key and cache_key in self.song_cache:
                # Update just the elapsed time and player info
                cached_song = self.song_cache[cache_key]
                cached_song.elapsed = float(now_playing.get("elapsed", 0))
                cached_song.playing = now_playing.get("playing", True)
                # Update player name if it's available now
                if player and not cached_song.player:
                    cached_song.player = player
                return cached_song
            
            # Remember this song for later
            self.last_song_key = cache_key
            
            # Get enriched song information from API
            return self.get_song_via_api(title, artist, player)
        
        # Fallback: try to parse the window title if available
        elif window_title:
            # Different music players format their window titles differently
            player_name = None
            
            # Try to extract app name from window title first
            known_apps = ["Music", "Spotify", "Deezer", "iTunes", "VLC", "YouTube"]
            for app in known_apps:
                if app.lower() in window_title.lower():
                    player_name = app
                    break
            
            # Most common format: "Song Title - Artist Name"
            if " - " in window_title:
                parts = window_title.split(" - ", 1)
                title = parts[0].strip()
                artist = parts[1].strip() if len(parts) > 1 else "Unknown Artist"
                
                # Get enriched song information from API
                return self.get_song_via_api(title, artist, player_name)
            
            # Format: "Song Title by Artist Name"
            elif " by " in window_title:
                parts = window_title.split(" by ", 1)
                title = parts[0].strip()
                artist = parts[1].strip() if len(parts) > 1 else "Unknown Artist"
                
                # Get enriched song information from API
                return self.get_song_via_api(title, artist, player_name)
            
            # If no recognizable format, just use the window title as the song title
            else:
                title = window_title
                
                # Create a basic song info object
                return SongInfo(
                    title=title,
                    artist="Unknown Artist",
                    playing=False,  # We can't determine if it's playing from just the title
                    player=player_name
                )
        
        # If all else fails, return a not playing status
        return SongInfo(
            title="Not playing",
            artist="Open a music player and play a song",
            playing=False,
            player=None
        ) 