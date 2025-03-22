#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Music RPC - Discord Rich Presence for Music Players

This script displays your currently playing music on Discord
using Rich Presence.

Author: Jakub Sladek
Version: 2.0.0
"""
import os
import sys
import io
import locale
import codecs
import traceback
import platform

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

# Setup logging
LOG_FILE = os.path.expanduser("~/Music_RPC.log")
def log(message):
    try:
        print(message)
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(message + "\n")
    except:
        # Fallback in case of encoding errors
        pass

log(f"Music RPC starting at {os.getcwd()}")
log(f"Python version: {sys.version}")
log(f"Platform: {sys.platform}")
log(f"Base path: {BASE_PATH}")
log(f"System path: {sys.path}")
log(f"Environment PATH: {os.environ.get('PATH', 'Not set')}")

try:
    # Set locale for proper encoding
    log("Setting locale...")
    locale.setlocale(locale.LC_ALL, '')
    log(f"Locale set to: {locale.getlocale()}")
    
    # Log current encoding settings
    log(f"File system encoding: {sys.getfilesystemencoding()}")
    log(f"Default encoding: {sys.getdefaultencoding()}")
    log(f"Stdout encoding: {sys.stdout.encoding}")
except Exception as e:
    log(f"Error setting locale: {str(e)}")

# Add the project root to the Python path
sys.path.insert(0, BASE_PATH)

# Check if nowplaying-cli is available
try:
    import subprocess
    result = subprocess.run(['which', 'nowplaying-cli'], 
                           capture_output=True, 
                           text=True)
    log(f"nowplaying-cli location: {result.stdout.strip() if result.returncode == 0 else 'Not found'}")
    
    # Check for a local binary too
    bin_path = os.path.join(BASE_PATH, 'bin', 'nowplaying-cli')
    if os.path.exists(bin_path):
        log(f"Found local nowplaying-cli at: {bin_path}")
        os.chmod(bin_path, 0o755)  # Ensure it's executable
except Exception as e:
    log(f"Error checking nowplaying-cli: {str(e)}")

# Import application modules
try:
    log("Importing modules...")
    from deezer_rpc.core.app import DeezerRPCApp
    from deezer_rpc.config.settings import Config
    from deezer_rpc.logging.handlers import Logger
    from deezer_rpc.core.window_manager import WindowManager
    from deezer_rpc.core.song_info import SongInfoRetriever
    from deezer_rpc.core.discord_presence import DiscordPresenceManager
    log("Modules imported successfully")
except Exception as e:
    log(f"Error importing modules: {str(e)}")
    log(traceback.format_exc())
    sys.exit(1)

# Start the application
try:
    log("Starting application...")
    
    # Initialize configuration
    config = Config()
    log("Config initialized")
    
    # Initialize logger
    logger = Logger(config)
    log("Logger initialized")
    
    # Initialize core components with dependency injection
    window_manager = WindowManager(logger)
    log("Window manager initialized")
    
    song_info_retriever = SongInfoRetriever(config, logger)
    log("Song info retriever initialized")
    
    discord_manager = DiscordPresenceManager(config, logger)
    log("Discord manager initialized")
    
    # Create the application
    app = DeezerRPCApp(
        config=config,
        logger=logger,
        window_manager=window_manager,
        song_info_retriever=song_info_retriever,
        discord_manager=discord_manager
    )
    log("Application instance created")
    
    # Start the application
    log("Starting application...")
    app.startup()
    log("Application started")
except Exception as e:
    log(f"Error starting application: {str(e)}")
    log(traceback.format_exc())
    sys.exit(1) 