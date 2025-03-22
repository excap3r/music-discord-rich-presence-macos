#!/usr/bin/env python3
"""
Build script for creating macOS app and DMG installer
"""
import os
import sys
import subprocess
import shutil
from setuptools import setup


def cleanup():
    """Clean up build artifacts from previous builds"""
    print("Cleaning up previous build artifacts...")
    dirs_to_clean = ['build', 'dist']
    for dir_name in dirs_to_clean:
        if os.path.exists(dir_name):
            shutil.rmtree(dir_name)
    
    if os.path.exists('Music RPC.dmg'):
        os.remove('Music RPC.dmg')


def build_app():
    """Build the macOS app using py2app"""
    print("Building macOS application...")
    
    # Setup py2app configuration
    APP = ['main.py']
    DATA_FILES = [
        ('', ['LICENSE']),
        ('icons', ['music_rpc.png', 'music_rpc.ico']),
    ]
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
            'deezer_rpc',
            'deezer_rpc.core',
            'deezer_rpc.config',
            'deezer_rpc.logging',
            'deezer_rpc.utils'
        ],
        'iconfile': 'music_rpc.icns',
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
    
    # Run py2app
    sys.argv = [sys.argv[0], 'py2app']
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


def create_icns():
    """Create an .icns file from the PNG image for macOS app icon"""
    print("Creating macOS icon file...")
    
    # Rename the icon file
    if os.path.exists('deezer_rpc.png') and not os.path.exists('music_rpc.png'):
        shutil.copy('deezer_rpc.png', 'music_rpc.png')
    
    if os.path.exists('deezer_rpc.ico') and not os.path.exists('music_rpc.ico'):
        shutil.copy('deezer_rpc.ico', 'music_rpc.ico')
    
    # Create a temporary iconset directory
    iconset_dir = 'Music_RPC.iconset'
    if not os.path.exists(iconset_dir):
        os.makedirs(iconset_dir)
    
    # Generate different icon sizes
    icon_sizes = [16, 32, 64, 128, 256, 512, 1024]
    for size in icon_sizes:
        # Convert the PNG image to different sizes
        subprocess.run([
            'sips',
            '-z', str(size), str(size),
            'music_rpc.png',
            '--out', f'{iconset_dir}/icon_{size}x{size}.png'
        ])
        
        # Create 2x versions for Retina displays
        if size <= 512:
            double_size = size * 2
            subprocess.run([
                'sips',
                '-z', str(size), str(size),
                'music_rpc.png',
                '--out', f'{iconset_dir}/icon_{size}x{size}@2x.png'
            ])
    
    # Use iconutil to create the icns file
    subprocess.run(['iconutil', '-c', 'icns', iconset_dir])
    
    # Clean up the iconset directory
    shutil.rmtree(iconset_dir)


def build_dmg():
    """Build a DMG installer for the macOS app"""
    print("Building DMG installer...")
    
    # Check if the app exists
    if not os.path.exists('dist/Music RPC.app'):
        print("Error: Application not found in dist directory")
        return False
    
    # Create a settings file for dmgbuild
    with open('dmg_settings.py', 'w') as f:
        f.write('''
# DMG settings for Music RPC
app = defines.get('app', 'dist/Music RPC.app')
appname = defines.get('appname', 'Music RPC')
background = 'builtin-arrow'
format = 'UDBZ'
size = {'width': 600, 'height': 400}
symlinks = {'Applications': '/Applications'}
icon = 'music_rpc.icns'
files = [app]
badge_icon = 'music_rpc.icns'
icon_locations = {
    appname: (150, 200),
    'Applications': (450, 200)
}
window_rect = ((100, 100), (600, 400))
default_view = 'icon-view'
show_icon_preview = False
include_icon_view_settings = True
include_list_view_settings = False
arrange_by = None
grid_offset = (0, 0)
grid_spacing = 100
''')
    
    # Build the DMG
    result = subprocess.run([
        'dmgbuild',
        '-s', 'dmg_settings.py',
        'Music RPC',
        'Music RPC.dmg'
    ])
    
    # Clean up settings file
    os.remove('dmg_settings.py')
    
    return result.returncode == 0


def main():
    """Main build script function"""
    # Clean up previous builds
    cleanup()
    
    # Create macOS icon file
    create_icns()
    
    # Build macOS app
    build_app()
    
    # Build DMG installer
    if build_dmg():
        print("Build completed successfully!")
        print("The DMG installer is located at: Music RPC.dmg")
    else:
        print("DMG build failed. The app is still available in the 'dist' directory.")


if __name__ == '__main__':
    main() 