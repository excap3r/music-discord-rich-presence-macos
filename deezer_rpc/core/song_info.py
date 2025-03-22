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

# For macOS MediaPlayer import
try:
    from MediaPlayer import MPRemoteCommandCenter
    MEDIA_PLAYER_AVAILABLE = True
except ImportError:
    MEDIA_PLAYER_AVAILABLE = False


class SongInfo:
    """Stores information about a song"""
    
    def __init__(self, title=None, artist=None, album=None, album_cover=None, artist_image=None, 
                 song_link=None, duration=0, elapsed=0, playing=False):
        # Ensure proper Unicode encoding for text fields
        self.title = self._ensure_unicode(title) or "Not playing"
        self.artist = self._ensure_unicode(artist) or "Open Deezer and play a song"
        self.album = self._ensure_unicode(album)
        self.album_cover = album_cover
        self.artist_image = artist_image
        self.song_link = song_link
        self.duration = duration
        self.elapsed = elapsed
        self.playing = playing
    
    def _ensure_unicode(self, text):
        """Ensure the text is properly encoded as Unicode"""
        if text is None:
            return None
        
        # Convert non-string types to string
        if not isinstance(text, str):
            try:
                if isinstance(text, bytes):
                    return text.decode('utf-8')
                return str(text)
            except Exception:
                return str(text)
        
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
                    except Exception:
                        return '[?]'
                
                # Find and replace all Unicode escape sequences
                text = re.sub(r'\\U[0-9a-fA-F]{4,8}|\\u[0-9a-fA-F]{4}', replace_unicode_escapes, text)
            return text
        except Exception:
            # If there's an encoding issue, strip problematic characters
            return text.replace('\\U', 'U').replace('\\u', 'u')
    
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
                    return text.decode('utf-8')
                return str(text)
            except Exception:
                return str(text)
        
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
                    except Exception:
                        return '[?]'
                
                # Find and replace all Unicode escape sequences
                text = re.sub(r'\\U[0-9a-fA-F]{4,8}|\\u[0-9a-fA-F]{4}', replace_unicode_escapes, text)
            return text
        except Exception:
            # If there's an encoding issue, strip problematic characters
            return text.replace('\\U', 'U').replace('\\u', 'u')
    
    def check_deezer_is_running(self):
        """Check if Deezer is running"""
        try:
            result = subprocess.run(["pgrep", "-i", "Deezer"], 
                                  capture_output=True, text=True)
            return result.returncode == 0
        except Exception as e:
            self.logger.error(f"Error checking if Deezer is running: {e}")
            return False
    
    def get_now_playing(self):
        """Get the currently playing song information using nowplaying-cli"""
        try:
            # Run nowplaying-cli get-raw to get all available information
            result = subprocess.run(["nowplaying-cli", "get-raw"], 
                                  capture_output=True, text=True, check=True, encoding='utf-8')
            
            # Parse the output into a dictionary
            info = {}
            raw_output = result.stdout.strip()
            
            # Check if there's any output
            if not raw_output:
                return None
                
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
                
                # Try to handle Unicode escape sequences
                if '\\u' in value or '\\U' in value:
                    value = self._ensure_unicode(value)
                
                # Add to our info dictionary
                info[key] = value
            
            # Extract the relevant information
            song_info = {
                "title": info.get("kMRMediaRemoteNowPlayingInfoTitle", "Unknown"),
                "artist": info.get("kMRMediaRemoteNowPlayingInfoArtist", "Unknown"),
                "album": info.get("kMRMediaRemoteNowPlayingInfoAlbum", "Unknown"),
                "duration": info.get("kMRMediaRemoteNowPlayingInfoDuration", "0"),
                "elapsed": info.get("kMRMediaRemoteNowPlayingInfoElapsedTime", "0"),
                "playing": True if info.get("kMRMediaRemoteNowPlayingInfoPlaybackRate", "0") != "0" else False
            }
            
            return song_info
            
        except subprocess.CalledProcessError as e:
            self.logger.error(f"Error executing nowplaying-cli: {e}")
            return None
        except Exception as e:
            self.logger.error(f"Unexpected error getting now playing info: {e}")
            return None
    
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
        # Ensure query is properly URL encoded
        try:
            # Ensure song title and artist name are properly encoded
            song_title = self._ensure_unicode(song_title)
            artist_name = self._ensure_unicode(artist_name)
            
            # Encode the artist name and song title to handle special characters
            query_artist = artist_name.encode('utf-8', 'ignore').decode('utf-8')
            query_title = song_title.encode('utf-8', 'ignore').decode('utf-8')
            query = f"{query_artist} {query_title}"
            
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
                
                # Create song info object with now playing data
                song_info = SongInfo(
                    title=song_title,
                    artist=artist_name,
                    album=song.get("album", {}).get("title", "Unknown"),
                    album_cover=album_cover,
                    artist_image=artist_image,
                    song_link=song["link"]
                )
                
                # Cache the result for future use
                self.song_cache[cache_key] = song_info
                
                return song_info
                
        except requests.RequestException as e:
            self.logger.error(f"Failed to fetch song info: {e}")
        except UnicodeError as e:
            self.logger.error(f"Unicode encoding error when fetching song info: {e}")

        # Create basic info for failed requests
        basic_info = SongInfo(title=song_title, artist=artist_name)
        
        # Cache even the basic info to avoid repeated API calls
        self.song_cache[cache_key] = basic_info
        
        return basic_info
    
    def get_current_song_info(self, window_title=None):
        """Get current song info using nowplaying-cli
        
        Args:
            window_title (str, optional): Window title (not used in new implementation)
            
        Returns:
            SongInfo: Song information object
        """
        # First check if Deezer is running
        if not self.check_deezer_is_running():
            self.logger.debug("Deezer is not running")
            self.last_song_key = None
            return SongInfo()
        
        # Get song info using nowplaying-cli
        now_playing_data = self.get_now_playing()
        
        if not now_playing_data:
            self.logger.debug("No song information available")
            self.last_song_key = None
            return SongInfo()
        
        song_title = now_playing_data["title"]
        artist_name = now_playing_data["artist"]
        
        # Create a cache key for this song
        current_key = f"{song_title}::{artist_name}"
        
        # If it's a new song, get the API data
        if current_key != self.last_song_key or current_key not in self.song_cache:
            song_info = self.get_song_via_api(song_title, artist_name)
            self.last_song_key = current_key
        else:
            # Use cached song info
            song_info = self.song_cache[current_key]
        
        # Update with real-time media info (duration, elapsed, playing state)
        try:
            song_info.duration = float(now_playing_data["duration"])
            song_info.elapsed = float(now_playing_data["elapsed"])
            song_info.playing = now_playing_data["playing"]
            song_info.album = now_playing_data["album"]
        except (ValueError, TypeError) as e:
            self.logger.error(f"Error parsing song duration/elapsed time: {e}")
        
        # Log the progress if a song is playing
        if song_info.is_playing():
            progress = (song_info.elapsed / song_info.duration * 100) if song_info.duration > 0 else 0
            status = "▶️ Playing" if song_info.playing else "⏸️ Paused"
            try:
                self.logger.debug(f"{status}: {song_info.artist} - {song_info.title} [{song_info.album}]")
                self.logger.debug(f"Progress: {int(song_info.elapsed)}/{int(song_info.duration)}s ({progress:.1f}%)")
            except UnicodeEncodeError:
                # In case of encoding issues, try a safer encoding
                artist = song_info.artist.encode('utf-8', errors='replace').decode('utf-8')
                title = song_info.title.encode('utf-8', errors='replace').decode('utf-8')
                album = song_info.album.encode('utf-8', errors='replace').decode('utf-8') if song_info.album else "Unknown"
                self.logger.debug(f"{status}: {artist} - {title} [{album}]")
                self.logger.debug(f"Progress: {int(song_info.elapsed)}/{int(song_info.duration)}s ({progress:.1f}%)")
        else:
            self.logger.debug("💤 No song playing detected")
        
        return song_info 