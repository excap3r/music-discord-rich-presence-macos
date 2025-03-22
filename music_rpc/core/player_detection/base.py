"""
Base interfaces for player detection and song information retrieval.

This module defines the abstract base classes and interfaces that all player
implementations must adhere to, ensuring consistent behavior across different
music player integrations.
"""
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any

from ...config.settings import Config
from ...logging.handlers import Logger
from ..song_info import SongInfo


class MusicPlayerDetector(ABC):
    """Base interface for music player detection.
    
    This abstract class defines the interface that all player detectors must implement.
    Player detectors are responsible for detecting if a specific music player is running
    and retrieving information about the currently playing song.
    """
    
    def __init__(self, config: Config, logger: Logger):
        """Initialize the player detector.
        
        Args:
            config: Application configuration
            logger: Logger for recording events and errors
        """
        self.config = config
        self.logger = logger
    
    @property
    @abstractmethod
    def player_name(self) -> str:
        """Get the name of the music player this detector handles.
        
        Returns:
            The name of the music player (e.g., "Deezer", "Apple Music")
        """
        pass
    
    @abstractmethod
    def is_running(self) -> bool:
        """Check if the music player is currently running.
        
        Returns:
            True if the player is running, False otherwise
        """
        pass
    
    @abstractmethod
    def get_current_song(self) -> Optional[SongInfo]:
        """Get information about the currently playing song.
        
        Returns:
            SongInfo object with details about the current song, or None if
            no song is playing or the player is not running
        """
        pass
    
    @abstractmethod
    def extract_song_info_from_window(self, window_title: str) -> Optional[SongInfo]:
        """Extract song information from a window title.
        
        This method is used when the player is detected through window titles
        rather than through direct API access.
        
        Args:
            window_title: The title of the window to extract information from
            
        Returns:
            SongInfo object with details extracted from the window title,
            or None if no song information could be extracted
        """
        pass


class PlayerRegistry:
    """Registry for managing available music player detectors.
    
    This class maintains a registry of all available player detectors and
    provides methods for detecting active players and retrieving song information.
    """
    
    def __init__(self, config: Config, logger: Logger):
        """Initialize the player registry.
        
        Args:
            config: Application configuration
            logger: Logger for recording events and errors
        """
        self.config = config
        self.logger = logger
        self.players: Dict[str, MusicPlayerDetector] = {}
    
    def register_player(self, player: MusicPlayerDetector) -> None:
        """Register a player detector with the registry.
        
        Args:
            player: The player detector to register
        """
        self.players[player.player_name] = player
        self.logger.info(f"Registered player detector: {player.player_name}")
    
    def get_active_player(self) -> Optional[MusicPlayerDetector]:
        """Find the first active music player.
        
        Returns:
            The first active player detector, or None if no players are active
        """
        for player_name, player in self.players.items():
            try:
                if player.is_running():
                    self.logger.debug(f"Found active player: {player_name}")
                    return player
            except Exception as e:
                self.logger.error(f"Error checking if {player_name} is running: {e}")
        
        self.logger.debug("No active players found")
        return None
    
    def get_player_by_name(self, name: str) -> Optional[MusicPlayerDetector]:
        """Get a player detector by name.
        
        Args:
            name: The name of the player to get
            
        Returns:
            The player detector with the given name, or None if not found
        """
        return self.players.get(name) 