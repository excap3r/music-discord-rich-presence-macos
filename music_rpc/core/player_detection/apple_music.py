"""
Apple Music player detection implementation.

This module provides an implementation of the MusicPlayerDetector interface
specifically for the Apple Music application on macOS.
"""
import re
import subprocess
import time
from typing import Optional, Dict, Any, Match, Tuple
import os
import sys

from .base import MusicPlayerDetector
from ..song_info import SongInfo
from ...config.settings import Config
from ...logging.handlers import Logger


class AppleMusicPlayerDetector(MusicPlayerDetector):
    """Apple Music player detector implementation.
    
    This class implements detection and song information retrieval for the
    Apple Music application on macOS.
    """
    
    @property
    def player_name(self) -> str:
        """Get the name of the player.
        
        Returns:
            The string "Apple Music" as the player name
        """
        return "Apple Music"
    
    def is_running(self) -> bool:
        """Check if Apple Music is currently running.
        
        This method checks if the Apple Music application is running by looking
        for its process or using AppleScript.
        
        Returns:
            True if Apple Music is running, False otherwise
        """
        try:
            # Only implement for macOS since Apple Music is macOS-specific
            if sys.platform != 'darwin':
                return False
            
            # Use AppleScript to check if Apple Music is running
            applescript = '''
            tell application "System Events"
                set isRunning to (exists (processes where name is "Music"))
                return isRunning
            end tell
            '''
            
            result = subprocess.run(
                ["osascript", "-e", applescript],
                capture_output=True,
                text=True,
                check=False
            )
            
            return result.returncode == 0 and result.stdout.strip().lower() == "true"
        except Exception as e:
            self.logger.error(f"Error checking if Apple Music is running: {e}")
            return False
    
    def get_current_song(self) -> Optional[SongInfo]:
        """Get information about the currently playing song in Apple Music.
        
        This method uses AppleScript to extract detailed song information
        from the Apple Music application.
        
        Returns:
            SongInfo object with details about the current song, or None if
            no song is playing or Apple Music is not running
        """
        if not self.is_running():
            return None
        
        try:
            # Get song information using AppleScript
            applescript = '''
            tell application "Music"
                if player state is playing then
                    set songInfo to {}
                    set end of songInfo to name of current track
                    set end of songInfo to artist of current track
                    set end of songInfo to album of current track
                    set end of songInfo to player position
                    set end of songInfo to duration of current track
                    set end of songInfo to "true"
                    return songInfo
                else
                    return {"Not playing", "", "", "0", "0", "false"}
                end if
            end tell
            '''
            
            result = subprocess.run(
                ["osascript", "-e", applescript],
                capture_output=True,
                text=True,
                check=False
            )
            
            if result.returncode == 0 and result.stdout.strip():
                # Parse the AppleScript result
                lines = result.stdout.strip().split(", ")
                if len(lines) >= 6:
                    # Extract song information from the AppleScript result
                    title = lines[0].replace('"', '').strip()
                    artist = lines[1].replace('"', '').strip()
                    album = lines[2].replace('"', '').strip()
                    
                    try:
                        position = float(lines[3])
                    except (ValueError, TypeError):
                        position = 0
                    
                    try:
                        duration = float(lines[4])
                    except (ValueError, TypeError):
                        duration = 0
                    
                    playing = lines[5].lower() == "true"
                    
                    # Create and return the SongInfo object
                    return SongInfo(
                        title=title,
                        artist=artist,
                        album=album,
                        elapsed=int(position),
                        duration=int(duration),
                        playing=playing,
                        player=self.player_name
                    )
            
            return None
        except Exception as e:
            self.logger.error(f"Error getting current song from Apple Music: {e}")
            return None
    
    def extract_song_info_from_window(self, window_title: str) -> Optional[SongInfo]:
        """Extract song information from an Apple Music window title.
        
        For Apple Music, we don't typically extract song info from window titles
        since we can get more detailed information using AppleScript directly.
        
        Args:
            window_title: The title of the window to extract information from
            
        Returns:
            None, as we use direct AppleScript access instead of window titles
        """
        # For Apple Music, we prefer the AppleScript method over window title extraction
        return None 