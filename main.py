#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Music RPC - Discord Rich Presence for Music Players

This script is the main entry point for the application when run directly.
It handles environment setup, initialization, and launches the application.

Author: Jakub Sladek
Version: 2.0.0
"""
from typing import Optional, Any, Dict, Union, TextIO
import os
import sys
import io
import locale
import codecs
import traceback
import platform
import argparse

# Set environment variables for encoding
os.environ['PYTHONIOENCODING'] = 'utf-8'
os.environ['LANG'] = 'en_US.UTF-8'
os.environ['LC_ALL'] = 'en_US.UTF-8'
os.environ['PYTHONLEGACYWINDOWSFSENCODING'] = '0'

# Configure stdout and stderr to use UTF-8
if hasattr(sys.stdout, 'detach'):
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.detach())
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.detach())

# Set default encoding for Python strings
if hasattr(sys, 'setdefaultencoding'):
    sys.setdefaultencoding('utf-8')

# Get application base path - handle both script run and frozen app
if getattr(sys, 'frozen', False):
    # Running as compiled app bundle
    BASE_PATH = os.path.dirname(sys.executable)
    os.chdir(BASE_PATH)  # Set working directory to app location
    
    # Add Resources directory to path for macOS app bundle
    if platform.system() == 'Darwin':
        resources_path = os.path.abspath(os.path.join(
            os.path.dirname(sys.executable), 
            '..',
            'Resources'
        ))
        if os.path.exists(resources_path):
            sys.path.insert(0, resources_path)
        
        # Add bin directory to PATH for nowplaying-cli
        bin_path = os.path.join(BASE_PATH, 'bin')
        if os.path.exists(bin_path):
            os.environ['PATH'] = f"{bin_path}:{os.environ.get('PATH', '')}"
else:
    # Running as script
    BASE_PATH = os.path.dirname(os.path.abspath(__file__))

# Add the project root to the Python path
sys.path.insert(0, BASE_PATH)

# Setup logging
LOG_FILE = os.path.expanduser("~/Music_RPC.log")

# Parse command line arguments
parser = argparse.ArgumentParser(description='Music RPC - Discord Rich Presence for Music Players')
parser.add_argument('--verbose', '-v', action='store_true', help='Enable verbose logging (INFO level)')
parser.add_argument('--debug', '-d', action='store_true', help='Enable debug logging (DEBUG level)')
parser.add_argument('--config', type=str, help='Path to custom config file')
parser.add_argument('--disable-discord', action='store_true', help='Run without Discord integration')
parser.add_argument('--interval', type=int, help='Set update interval in seconds')
args = parser.parse_args()

# Helper function for quiet logging during startup
def quiet_log(message: str) -> None:
    """Log a message to the log file only, not to console.
    
    Args:
        message: The message to log
    """
    try:
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(message + "\n")
    except:
        # Fallback in case of encoding errors
        pass

# Standard logging function with console output
def log(message: str, console: bool = True) -> None:
    """Log a message to both console and log file.
    
    Args:
        message: The message to log
        console: Whether to also print to console
    """
    try:
        if console:
            print(message)
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(message + "\n")
    except:
        # Fallback in case of encoding errors
        pass

# Log startup info to file but not console by default
quiet_log(f"Music RPC starting at {os.getcwd()}")
quiet_log(f"Python version: {sys.version}")
quiet_log(f"Platform: {sys.platform}")
quiet_log(f"Base path: {BASE_PATH}")
quiet_log(f"System path: {sys.path}")
quiet_log(f"Environment PATH: {os.environ.get('PATH', 'Not set')}")

try:
    # Set locale for proper encoding
    quiet_log("Setting locale...")
    locale.setlocale(locale.LC_ALL, '')
    quiet_log(f"Locale set to: {locale.getlocale()}")
    
    # Log current encoding settings
    quiet_log(f"File system encoding: {sys.getfilesystemencoding()}")
    quiet_log(f"Default encoding: {sys.getdefaultencoding()}")
    quiet_log(f"Stdout encoding: {sys.stdout.encoding}")
except Exception as e:
    log(f"Error setting locale: {str(e)}")

# Check if nowplaying-cli is available
try:
    import subprocess
    result = subprocess.run(['which', 'nowplaying-cli'], 
                           capture_output=True, 
                           text=True)
    quiet_log(f"nowplaying-cli location: {result.stdout.strip() if result.returncode == 0 else 'Not found'}")
    
    # Check for a local binary too
    bin_path = os.path.join(BASE_PATH, 'bin', 'nowplaying-cli')
    if os.path.exists(bin_path):
        quiet_log(f"Found local nowplaying-cli at: {bin_path}")
        os.chmod(bin_path, 0o755)  # Ensure it's executable
except Exception as e:
    log(f"Error checking nowplaying-cli: {str(e)}")

# Import application modules
try:
    quiet_log("Importing modules...")
    from music_rpc.core.app import MusicRPCApp
    from music_rpc.config.settings import Config
    from music_rpc.logging.handlers import Logger
    from music_rpc.core.window_manager import WindowManager
    from music_rpc.core.song_info import SongInfoRetriever
    from music_rpc.core.discord_presence import DiscordPresenceManager
    quiet_log("Modules imported successfully")
except Exception as e:
    log(f"Error importing modules: {str(e)}")
    log(traceback.format_exc())
    sys.exit(1)

# Start the application
try:
    quiet_log("Starting application...")
    
    # Initialize configuration
    config = Config()
    if args.config:
        config.CONFIG_FILE = args.config
        config.load_config()
    
    # Set log level based on command line arguments
    if args.debug:
        config.LOG_LEVEL = "DEBUG"
    elif args.verbose:
        config.LOG_LEVEL = "INFO"
    
    quiet_log(f"Log level: {config.LOG_LEVEL}")
    
    # Update interval from command line if provided
    if args.interval:
        success, message = config.set_update_interval(args.interval)
        quiet_log(f"Setting interval from command line: {message}")
    
    # Initialize logger
    logger = Logger(config)
    
    # Now that the logger is configured, display a startup message
    logger.info("Music RPC v{} starting".format(config.VERSION))
    
    # Initialize core components with dependency injection
    window_manager = WindowManager(logger)
    
    song_info_retriever = SongInfoRetriever(config, logger)
    
    discord_manager = DiscordPresenceManager(config, logger)
    if args.disable_discord:
        logger.warning("Discord integration disabled via command line")
        discord_manager.enabled = False
    
    # Create the application
    app = MusicRPCApp(
        config=config,
        logger=logger,
        window_manager=window_manager,
        song_info_retriever=song_info_retriever,
        discord_manager=discord_manager
    )
    
    # Start the application
    logger.info("Starting application...")
    app.startup()
    logger.info("Application started successfully")
except Exception as e:
    log(f"Error starting application: {str(e)}")
    log(traceback.format_exc())
    sys.exit(1) 