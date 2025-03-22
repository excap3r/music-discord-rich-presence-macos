#!/usr/bin/env python3
"""
Shared build utilities for macOS app build scripts
"""
import os
import subprocess
import shutil


def cleanup():
    """Clean up build artifacts from previous builds"""
    print("Cleaning up previous build artifacts...")
    dirs_to_clean = ['build', 'dist']
    for dir_name in dirs_to_clean:
        if os.path.exists(dir_name):
            shutil.rmtree(dir_name)
    
    # Also clean up any leftover .spec files
    spec_files = [f for f in os.listdir('.') if f.endswith('.spec')]
    for spec_file in spec_files:
        os.unlink(spec_file)
    
    # Clean up DMG files
    if os.path.exists('Music RPC.dmg'):
        os.remove('Music RPC.dmg')


def ensure_project_root():
    """Ensure we're working from the project root directory
    
    Returns:
        str: Path to the project root directory
    """
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir)  # Go up one level to project root
    os.chdir(project_root)
    print(f"Working directory: {os.getcwd()}")
    return project_root


def create_icns():
    """Create an .icns file from the PNG image for macOS app icon
    
    Returns:
        bool: True if icon created successfully, False otherwise
    """
    print("Creating macOS icon file...")
    
    # Ensure we're working from the project root directory
    project_root = ensure_project_root()
    
    # Check for icon files in the assets directory
    assets_dir = os.path.join(project_root, 'assets')
    print(f"Looking for icon files in: {assets_dir}")
    
    if os.path.exists(os.path.join(assets_dir, 'music_rpc.png')):
        shutil.copy(os.path.join(assets_dir, 'music_rpc.png'), 'music_rpc.png')
        print("Copied music_rpc.png from assets directory")
    
    if os.path.exists(os.path.join(assets_dir, 'music_rpc.ico')):
        shutil.copy(os.path.join(assets_dir, 'music_rpc.ico'), 'music_rpc.ico')
        print("Copied music_rpc.ico from assets directory")
    
    # Assets directory has a pre-built icns file we can use
    if os.path.exists(os.path.join(assets_dir, 'music_rpc.icns')):
        shutil.copy(os.path.join(assets_dir, 'music_rpc.icns'), 'Music_RPC.icns')
        print("Using pre-built music_rpc.icns from assets directory")
        return True
    
    # Verify we have the PNG file now
    if not os.path.exists('music_rpc.png'):
        print("WARNING: Cannot find music_rpc.png icon file. Default icon will be used.")
        # Create a simple placeholder icon if needed
        with open('music_rpc.png', 'wb') as f:
            f.write(b'P')  # Just to create a file, will be ignored by PyInstaller
        return False
    
    print(f"Found icon file: {os.path.abspath('music_rpc.png')}")
    
    # Create a temporary iconset directory
    iconset_dir = 'Music_RPC.iconset'
    if not os.path.exists(iconset_dir):
        os.makedirs(iconset_dir)
    
    try:
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
                subprocess.run([
                    'sips',
                    '-z', str(size), str(size),
                    'music_rpc.png',
                    '--out', f'{iconset_dir}/icon_{size}x{size}@2x.png'
                ])
        
        # Use iconutil to create the icns file
        try:
            subprocess.run(['iconutil', '-c', 'icns', iconset_dir], check=True)
            print("Successfully created Music_RPC.icns")
            success = True
        except subprocess.CalledProcessError:
            print(f"{iconset_dir}: Failed to generate ICNS.")
            success = False
    except Exception as e:
        print(f"Error creating icon: {e}")
        success = False
    
    # Clean up the iconset directory
    if os.path.exists(iconset_dir):
        shutil.rmtree(iconset_dir)
    
    return success


def create_info_plist():
    """Create a custom Info.plist file for the application
    
    Returns:
        str: Path to the created Info.plist file
    """
    print("Creating Info.plist file...")
    
    info_plist_content = """<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>CFBundleDevelopmentRegion</key>
    <string>English</string>
    <key>CFBundleDisplayName</key>
    <string>Music RPC</string>
    <key>CFBundleExecutable</key>
    <string>Music RPC</string>
    <key>CFBundleIconFile</key>
    <string>Music_RPC.icns</string>
    <key>CFBundleIdentifier</key>
    <string>com.jakubsladek.musicrpc</string>
    <key>CFBundleInfoDictionaryVersion</key>
    <string>6.0</string>
    <key>CFBundleName</key>
    <string>Music RPC</string>
    <key>CFBundlePackageType</key>
    <string>APPL</string>
    <key>CFBundleShortVersionString</key>
    <string>2.0.0</string>
    <key>CFBundleVersion</key>
    <string>2.0.0</string>
    <key>LSHasLocalizedDisplayName</key>
    <false/>
    <key>LSMinimumSystemVersion</key>
    <string>10.13</string>
    <key>LSUIElement</key>
    <true/>
    <key>NSAppleScriptEnabled</key>
    <true/>
    <key>NSHighResolutionCapable</key>
    <true/>
    <key>NSHumanReadableCopyright</key>
    <string>Copyright © 2023 Jakub Sladek. All rights reserved.</string>
    <key>NSPrincipalClass</key>
    <string>NSApplication</string>
    <key>NSRequiresAquaSystemAppearance</key>
    <false/>
</dict>
</plist>
"""
    
    with open('Info.plist', 'w', encoding='utf-8') as f:
        f.write(info_plist_content)
    
    return os.path.abspath('Info.plist')


def find_nowplaying_cli():
    """Find the nowplaying-cli executable in the system
    
    Returns:
        str: Path to the nowplaying-cli executable, or None if not found
    """
    try:
        result = subprocess.run(['which', 'nowplaying-cli'], 
                               capture_output=True, 
                               text=True, 
                               check=True)
        return result.stdout.strip()
    except Exception:
        common_paths = [
            '/opt/homebrew/bin/nowplaying-cli',
            '/usr/local/bin/nowplaying-cli',
            '/usr/bin/nowplaying-cli'
        ]
        for path in common_paths:
            if os.path.exists(path):
                return path
    return None


def ensure_nowplaying_cli():
    """Ensure nowplaying-cli is installed and return its path
    
    Returns:
        str: Path to the nowplaying-cli executable, or None if not found
    """
    nowplaying_cli_path = find_nowplaying_cli()
    
    if not nowplaying_cli_path:
        print("nowplaying-cli not found. Attempting to install with Homebrew...")
        try:
            subprocess.run(['brew', 'install', 'nowplaying-cli'], check=True)
            nowplaying_cli_path = find_nowplaying_cli()
        except Exception as e:
            print(f"Error installing nowplaying-cli: {e}")
    
    if not nowplaying_cli_path:
        print("ERROR: nowplaying-cli is required but could not be found or installed.")
        print("Please install it manually with: brew install nowplaying-cli")
        return None
    
    return nowplaying_cli_path


def create_dmg(app_path, icon_path=None):
    """Create a DMG installer for the app
    
    Args:
        app_path (str): Path to the app bundle
        icon_path (str, optional): Path to the icon file for the DMG
        
    Returns:
        bool: True if DMG creation was successful, False otherwise
    """
    print("Creating DMG installer...")
    
    # Check if app exists
    if not os.path.exists(app_path):
        print(f"App not found at: {app_path}")
        return False
    
    # Use explicit DMG name 
    dmg_name = "Music-RPC-Installer.dmg"
    
    try:
        # Check if create-dmg is installed
        subprocess.run(['which', 'create-dmg'], check=True, capture_output=True)
    except subprocess.CalledProcessError:
        print("create-dmg not found. Installing via Homebrew...")
        try:
            subprocess.run(['brew', 'install', 'create-dmg'], check=True)
        except Exception as e:
            print(f"Error installing create-dmg: {e}")
            return False
    
    # Prepare a temporary directory for DMG creation
    tmp_dir = os.path.abspath("dist/tmp_dmg")
    os.makedirs(tmp_dir, exist_ok=True)
    
    # Copy the app to the temporary directory
    app_name = os.path.basename(app_path)
    shutil.copytree(app_path, os.path.join(tmp_dir, app_name), symlinks=True)
    
    # Create the DMG command
    dmg_cmd = [
        'create-dmg',
        '--volname', 'Music RPC',
        '--window-pos', '200', '120',
        '--window-size', '800', '400',
        '--icon-size', '100',
        '--icon', app_name, '200', '200',
        '--app-drop-link', '600', '200',
        '--no-internet-enable',
        os.path.join('dist', dmg_name),
        tmp_dir
    ]
    
    # Add volume icon if provided
    if icon_path and os.path.exists(icon_path):
        dmg_cmd.extend(['--volicon', icon_path])
    
    # Run the command
    result = subprocess.run(dmg_cmd)
    
    # Clean up the temporary directory
    shutil.rmtree(tmp_dir, ignore_errors=True)
    
    if result.returncode == 0:
        print(f"DMG installer created successfully: dist/{dmg_name}")
        return True
    else:
        print("Failed to create DMG installer.")
        return False 