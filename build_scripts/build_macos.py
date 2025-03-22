#!/usr/bin/env python3
"""
Build script for creating macOS app and DMG installer using py2app
"""
import os
import sys
import subprocess
import shutil
from setuptools import setup

# Import shared build utilities
from build_utils import (
    cleanup, 
    ensure_project_root, 
    create_icns, 
    create_dmg
)


def build_app_py2app():
    """Build the macOS app using py2app"""
    print("Building macOS application with py2app...")
    
    # Ensure we're in the project root directory
    ensure_project_root()
    
    # Verify main.py exists in the current directory
    if not os.path.exists('main.py'):
        print(f"ERROR: main.py not found in {os.getcwd()}")
        return False
    
    # Check for necessary icon files
    icns_file = 'Music_RPC.icns'
    if not os.path.exists(icns_file):
        # Try to convert from png if possible
        create_icns()
        
        # If still doesn't exist after trying to create it, we need to use a different name
        if not os.path.exists(icns_file) and os.path.exists('music_rpc.icns'):
            icns_file = 'music_rpc.icns'
        elif not os.path.exists(icns_file):
            print(f"WARNING: Icon file {icns_file} not found. App will use default icon.")
            icns_file = None
    
    # Setup py2app configuration
    APP = ['main.py']
    DATA_FILES = [
        ('', ['LICENSE']),
    ]
    
    # Add icon files to data files if they exist
    for icon_file in ['music_rpc.png', 'music_rpc.ico']:
        if os.path.exists(icon_file):
            DATA_FILES[0][1].append(icon_file)
    
    # Build py2app options
    OPTIONS = {
        'argv_emulation': False,  # Set to False to avoid issues with macOS
        'plist': {
            'LSUIElement': True,  # Makes the app a background app with only a menu bar icon
            'CFBundleName': 'Music RPC',
            'CFBundleDisplayName': 'Music RPC',
            'CFBundleIdentifier': 'com.jakubsladek.musicrpc',
            'CFBundleVersion': '2.0.0',
            'CFBundleShortVersionString': '2.0.0',
            'NSHumanReadableCopyright': 'Copyright © 2023 Jakub Sladek. All rights reserved.',
            'NSHighResolutionCapable': True,
            'NSPrincipalClass': 'NSApplication',
            'NSAppleScriptEnabled': True,
        },
        'packages': [
            'rumps', 
            'pypresence', 
            'requests', 
            'AppKit', 
            'music_rpc',  # Updated from deezer_rpc to music_rpc
            'music_rpc.core',
            'music_rpc.config',
            'music_rpc.logging',
            'music_rpc.utils'
        ],
        'includes': [
            'rumps', 
            'AppKit', 
            'Foundation', 
            'threading', 
            'queue',
            'atexit',
            'signal'
        ],
        # Exclude some modules to reduce size
        'excludes': ['tkinter', 'PyQt5', 'PyQt6', 'PySide2', 'PySide6', 'matplotlib', 'pandas', 'scipy', 'numpy'],
    }
    
    # Add iconfile option if icon exists
    if icns_file:
        OPTIONS['iconfile'] = icns_file
    
    # Run py2app
    sys.argv = [sys.argv[0], 'py2app']
    try:
        setup(
            app=APP,
            data_files=DATA_FILES,
            options={'py2app': OPTIONS},
            setup_requires=['py2app'],
        )
        
        # Fix permissions on the resulting app bundle
        app_path = 'dist/Music RPC.app'
        if os.path.exists(app_path):
            subprocess.run(['chmod', '-R', '755', app_path])
            print(f"Successfully built app: {app_path}")
            return True
        else:
            print("ERROR: App build failed - app bundle not found")
            return False
    except Exception as e:
        print(f"ERROR: py2app build failed: {e}")
        return False


def main():
    """Main build script function"""
    print("Starting py2app macOS build...")
    
    # Clean up previous builds
    cleanup()
    
    # Create macOS icon file
    create_icns()
    
    # Build macOS app
    if build_app_py2app():
        print("App built successfully!")
        
        # Build DMG installer
        app_path = os.path.abspath("dist/Music RPC.app")
        icon_path = "Music_RPC.icns" if os.path.exists("Music_RPC.icns") else None
        
        if create_dmg(app_path, icon_path):
            print("DMG installer created successfully!")
        else:
            print("App built successfully but DMG creation failed. The app is still available in the 'dist' directory.")
    else:
        print("Failed to build app.")


if __name__ == '__main__':
    main() 