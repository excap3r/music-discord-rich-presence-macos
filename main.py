#!/usr/bin/env python3
"""
Deezer RPC - Discord Rich Presence for Deezer Music Player

This script displays your currently playing Deezer track on Discord
using Rich Presence.

Author: Jakub Sladek
Version: 2.0.0
"""
import os
import sys

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import required modules
from deezer_rpc.utils.config import Config
from deezer_rpc.utils.logger import Logger
from deezer_rpc.core.window_manager import WindowManager
from deezer_rpc.core.song_info import SongInfoRetriever
from deezer_rpc.core.discord_presence import DiscordPresenceManager
from deezer_rpc.core.app import DeezerRPCApp


def main():
    """Main entry point for the application"""
    # Initialize configuration
    config = Config()
    
    # Initialize logger
    logger = Logger(config)
    
    # Initialize core components with dependency injection
    window_manager = WindowManager(logger)
    song_info_retriever = SongInfoRetriever(config, logger)
    discord_manager = DiscordPresenceManager(config, logger)
    
    # Create and start the application
    app = DeezerRPCApp(
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