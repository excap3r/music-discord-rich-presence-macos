"""
Deezer music player detection implementation.

This module provides an implementation of the MusicPlayerDetector interface
specifically for the Deezer music player.
"""
import re
import subprocess
from typing import Optional, Dict, Any, Match
import os
import sys
import time

from .base import MusicPlayerDetector
from ..song_info import SongInfo
from ...config.settings import Config
from ...logging.handlers import Logger


class DeezerPlayerDetector(MusicPlayerDetector):
    """Deezer player detector implementation.
    
    This class implements detection and song information retrieval for the
    Deezer music player.
    """
    
    @property
    def player_name(self) -> str:
        """Get the name of the player.
        
        Returns:
            The string "Deezer" as the player name
        """
        return "Deezer"
    
    def is_running(self) -> bool:
        """Check if Deezer is currently running.
        
        This method checks if the Deezer application is running by looking
        for its process or window.
        
        Returns:
            True if Deezer is running, False otherwise
        """
        try:
            # On macOS, use the 'ps' command to check if Deezer is running
            if sys.platform == 'darwin':
                result = subprocess.run(
                    ["ps", "-A"],
                    capture_output=True,
                    text=True,
                    check=False
                )
                return "Deezer" in result.stdout
            
            # On Windows, check for Deezer window using a different approach
            # Note: This is a placeholder; Windows detection would need to be implemented
            return False
        except Exception as e:
            self.logger.error(f"Error checking if Deezer is running: {e}")
            return False
    
    def get_current_song(self) -> Optional[SongInfo]:
        """Get information about the currently playing song in Deezer.
        
        This method attempts to extract song information from the Deezer application.
        It may use AppleScript (on macOS) or other platform-specific methods.
        
        Returns:
            SongInfo object with details about the current song, or None if
            no song is playing or Deezer is not running
        """
        if not self.is_running():
            return None
        
        try:
            # On macOS, use AppleScript to get information from Deezer
            if sys.platform == 'darwin':
                # First, get Deezer's window title which may contain song info
                window_title = self._get_deezer_window_title()
                if window_title:
                    return self.extract_song_info_from_window(window_title)
            
            return None
        except Exception as e:
            self.logger.error(f"Error getting current song from Deezer: {e}")
            return None
    
    def _get_deezer_window_title(self) -> Optional[str]:
        """Get the title of the Deezer window.
        
        Returns:
            The window title of Deezer, or None if it couldn't be retrieved
        """
        try:
            # Use AppleScript to get the title of the Deezer window
            applescript = '''
            tell application "System Events"
                set frontApp to name of first application process whose frontmost is true
                set allProcesses to application processes
                set deezerProcess to a reference to (first application process whose name is "Deezer")
                try
                    tell process "Deezer"
                        set windowTitle to name of first window
                    end tell
                    return windowTitle
                on error
                    return "Deezer"
                end try
            end tell
            '''
            
            result = subprocess.run(
                ["osascript", "-e", applescript],
                capture_output=True,
                text=True,
                check=False
            )
            
            if result.returncode == 0 and result.stdout.strip():
                return result.stdout.strip()
            return None
        except Exception as e:
            self.logger.error(f"Error getting Deezer window title: {e}")
            return None
    
    def extract_song_info_from_window(self, window_title: str) -> Optional[SongInfo]:
        """Extract song information from a Deezer window title.
        
        Args:
            window_title: The title of the Deezer window to extract information from
            
        Returns:
            SongInfo object with details extracted from the window title,
            or None if no song information could be extracted
        """
        if not window_title or window_title == "Deezer":
            return None
        
        try:
            # Deezer window title format: "Song - Artist - Deezer"
            pattern = r"^(.*) - (.*) - Deezer$"
            match = re.match(pattern, window_title)
            
            if match:
                title = match.group(1).strip()
                artist = match.group(2).strip()
                
                return SongInfo(
                    title=title,
                    artist=artist,
                    playing=True,
                    player=self.player_name
                )
            else:
                self.logger.debug(f"Could not extract song info from Deezer window title: {window_title}")
                return None
        except Exception as e:
            self.logger.error(f"Error extracting song info from Deezer window title: {e}")
            return None 