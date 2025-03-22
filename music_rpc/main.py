#!/usr/bin/env python3
"""
Music RPC - Discord Rich Presence for Music Players
Package entry point

This module provides the main entry point when the package is installed
and called using the 'music-rpc' command.
"""
from music_rpc.config.settings import Config
from music_rpc.logging.handlers import Logger
from music_rpc.core.window_manager import WindowManager
from music_rpc.core.song_info import SongInfoRetriever
from music_rpc.core.discord_presence import DiscordPresenceManager
from music_rpc.core.app import MusicRPCApp


def main() -> None:
    """Main entry point for the application.
    
    This function initializes all components using dependency injection pattern
    and starts the application. It's used as the entry point when the package
    is installed and run via the 'music-rpc' command.
    """
    # Initialize configuration
    config = Config()
    
    # Initialize logger
    logger = Logger(config)
    
    # Initialize core components with dependency injection
    window_manager = WindowManager(logger)
    song_info_retriever = SongInfoRetriever(config, logger)
    discord_manager = DiscordPresenceManager(config, logger)
    
    # Create and start the application
    app = MusicRPCApp(
        config=config,
        logger=logger,
        window_manager=window_manager,
        song_info_retriever=song_info_retriever,
        discord_manager=discord_manager
    )
    
    # Run the application
    app.startup()


if __name__ == "__main__":
    main() 