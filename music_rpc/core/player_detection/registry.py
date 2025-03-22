"""
Player registry initialization for Music RPC.

This module provides a function to initialize and register all available
player detectors with the player registry.
"""
from typing import Optional

from ...config.settings import Config
from ...logging.handlers import Logger
from .base import PlayerRegistry
from .deezer import DeezerPlayerDetector
from .apple_music import AppleMusicPlayerDetector


def initialize_player_registry(config: Config, logger: Logger) -> PlayerRegistry:
    """Initialize and configure the player registry with all available player detectors.
    
    This function creates a new PlayerRegistry instance and registers all implemented
    player detectors with it.
    
    Args:
        config: Application configuration
        logger: Logger for recording events and errors
        
    Returns:
        Configured PlayerRegistry instance with all available player detectors
    """
    # Create the registry
    registry = PlayerRegistry(config, logger)
    logger.info("Initializing player registry")
    
    # Register the Deezer player detector
    try:
        deezer_detector = DeezerPlayerDetector(config, logger)
        registry.register_player(deezer_detector)
    except Exception as e:
        logger.error(f"Failed to initialize Deezer player detector: {e}")
    
    # Register the Apple Music player detector
    try:
        apple_music_detector = AppleMusicPlayerDetector(config, logger)
        registry.register_player(apple_music_detector)
    except Exception as e:
        logger.error(f"Failed to initialize Apple Music player detector: {e}")
    
    # Additional player detectors can be registered here in the future
    
    return registry 