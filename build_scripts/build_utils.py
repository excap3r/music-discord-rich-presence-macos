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
    if os.path.exists('Music-Discord-Rich-Presence-Installer.dmg'):
        os.remove('Music-Discord-Rich-Presence-Installer.dmg')
    
    # Clean up any Info.plist files in the root directory
    if os.path.exists('Info.plist'):
        os.remove('Info.plist')
    
    # Clean up any __pycache__ directories to avoid conflicts
    for root, dirs, files in os.walk('.'):
        for dirname in dirs:
            if dirname == '__pycache__':
                pycache_path = os.path.join(root, dirname)
                print(f"Removing {pycache_path}")
                shutil.rmtree(pycache_path)
    
    # Clean up egg-info directories which can cause conflicts
    egg_info_dirs = [d for d in os.listdir('.') if d.endswith('.egg-info')]
    for egg_dir in egg_info_dirs:
        shutil.rmtree(egg_dir)
        
    # Force clean pip cache for this project
    try:
        subprocess.run(['pip', 'cache', 'remove', 'packaging'], check=False)
        subprocess.run(['pip', 'cache', 'remove', 'pypresence'], check=False)
        subprocess.run(['pip', 'cache', 'remove', 'rumps'], check=False)
    except Exception as e:
        print(f"Warning: Could not clean pip cache: {e}")


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
        str: Path to the created ICNS file or None if failed
    """
    print("Creating macOS icon file...")
    
    # Ensure we're working from the project root directory
    project_root = ensure_project_root()
    
    # Create a temporary directory for icon creation
    tmp_icon_dir = os.path.join(project_root, 'build', 'tmp_icons')
    os.makedirs(tmp_icon_dir, exist_ok=True)
    
    # Final icon path that will be returned
    icon_path = os.path.join(tmp_icon_dir, 'Discord_Music_RPC.icns')
    
    # Check for icon files in the assets directory
    assets_dir = os.path.join(project_root, 'assets')
    print(f"Looking for icon files in: {assets_dir}")
    
    # Check if we already have a pre-built icns file in assets
    if os.path.exists(os.path.join(assets_dir, 'music_rpc.icns')):
        shutil.copy(os.path.join(assets_dir, 'music_rpc.icns'), icon_path)
        print(f"Using pre-built music_rpc.icns from assets directory: {icon_path}")
        return icon_path
    
    # Copy PNG to temporary directory if it exists
    png_path = os.path.join(tmp_icon_dir, 'music_rpc.png')
    if os.path.exists(os.path.join(assets_dir, 'music_rpc.png')):
        shutil.copy(os.path.join(assets_dir, 'music_rpc.png'), png_path)
        print(f"Copied music_rpc.png from assets directory to {png_path}")
    elif os.path.exists('music_rpc.png'):
        shutil.copy('music_rpc.png', png_path)
        print(f"Copied music_rpc.png from root directory to {png_path}")
    else:
        print("WARNING: Cannot find music_rpc.png icon file. Default icon will be used.")
        # Create a simple placeholder icon if needed
        with open(png_path, 'wb') as f:
            f.write(b'P')  # Just to create a file, will be ignored by PyInstaller
        return None
    
    print(f"Using icon file: {png_path}")
    
    # Create a temporary iconset directory
    iconset_dir = os.path.join(tmp_icon_dir, 'Discord_Music_RPC.iconset')
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
                png_path,
                '--out', f'{iconset_dir}/icon_{size}x{size}.png'
            ])
            
            # Create 2x versions for Retina displays
            if size <= 512:
                subprocess.run([
                    'sips',
                    '-z', str(size), str(size),
                    png_path,
                    '--out', f'{iconset_dir}/icon_{size}x{size}@2x.png'
                ])
        
        # Use iconutil to create the icns file
        try:
            subprocess.run(['iconutil', '-c', 'icns', iconset_dir, '-o', icon_path], check=True)
            print(f"Successfully created Discord_Music_RPC.icns at {icon_path}")
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
    
    return icon_path if success else None


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
    <string>Music Discord Rich Presence</string>
    <key>CFBundleExecutable</key>
    <string>Music Discord Rich Presence</string>
    <key>CFBundleIconFile</key>
    <string>Discord_Music_RPC.icns</string>
    <key>CFBundleIdentifier</key>
    <string>com.jakubsladek.musicdiscordrpc</string>
    <key>CFBundleInfoDictionaryVersion</key>
    <string>6.0</string>
    <key>CFBundleName</key>
    <string>Music Discord Rich Presence</string>
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
    
    # Use the DMG name specified in the README
    dmg_name = "Music-Discord-Rich-Presence-Installer.dmg"
    dmg_path = os.path.abspath(os.path.join('dist', dmg_name))
    
    # Remove any existing DMG file
    if os.path.exists(dmg_path):
        os.remove(dmg_path)
    
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
    if os.path.exists(tmp_dir):
        shutil.rmtree(tmp_dir)
    os.makedirs(tmp_dir, exist_ok=True)
    
    # Copy the app to the temporary directory
    app_name = os.path.basename(app_path)
    try:
        shutil.copytree(app_path, os.path.join(tmp_dir, app_name), symlinks=True)
    except Exception as e:
        print(f"Error copying app to temporary directory: {e}")
        return False
    
    # Create the DMG command
    dmg_cmd = [
        'create-dmg',
        '--volname', 'Music Discord Rich Presence',
        '--window-pos', '200', '120',
        '--window-size', '800', '400',
        '--icon-size', '100',
        '--icon', app_name, '200', '200',
        '--app-drop-link', '600', '200',
        '--no-internet-enable',
        dmg_path,
        tmp_dir
    ]
    
    # Add volume icon if provided
    if icon_path and os.path.exists(icon_path):
        dmg_cmd.extend(['--volicon', icon_path])
    
    # Run the command
    print(f"Running DMG creation command: {' '.join(dmg_cmd)}")
    result = subprocess.run(dmg_cmd, capture_output=True, text=True)
    
    # Clean up the temporary directory
    try:
        shutil.rmtree(tmp_dir, ignore_errors=True)
    except Exception as e:
        print(f"Warning: Could not clean up temporary directory: {e}")
    
    if result.returncode == 0:
        if os.path.exists(dmg_path):
            print(f"DMG installer created successfully: {dmg_path}")
            # Copy the DMG to the root directory for easier access
            root_dmg_path = os.path.join(os.getcwd(), dmg_name)
            try:
                shutil.copy2(dmg_path, root_dmg_path)
                print(f"DMG also copied to: {root_dmg_path}")
            except Exception as e:
                print(f"Warning: Could not copy DMG to root directory: {e}")
            return True
        else:
            print(f"DMG creation command succeeded but DMG file not found at: {dmg_path}")
            print(f"create-dmg output: {result.stdout}")
            print(f"create-dmg errors: {result.stderr}")
            return False
    else:
        print(f"Failed to create DMG installer. Return code: {result.returncode}")
        print(f"create-dmg output: {result.stdout}")
        print(f"create-dmg errors: {result.stderr}")
        return False 