#!/usr/bin/env python3
"""
Build script for creating macOS app using PyInstaller
"""
import os
import sys
import subprocess
import shutil
import time
import platform


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


def create_info_plist():
    """Create a custom Info.plist file for the application"""
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
    """Find the nowplaying-cli executable in the system"""
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
    """Ensure nowplaying-cli is installed and return its path"""
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


def build_app():
    """Build the macOS application using PyInstaller"""
    print("Building macOS application with PyInstaller...")
    
    # Create the Info.plist file
    plist_path = create_info_plist()
    print(f"Creating Info.plist file...")
    
    # Find and ensure nowplaying-cli
    nowplaying_cli_path = ensure_nowplaying_cli()
    if not nowplaying_cli_path:
        return False
    
    print(f"Found nowplaying-cli at: {nowplaying_cli_path}")
    
    # Create a bin directory if it doesn't exist
    bin_dir = "bin"
    if not os.path.exists(bin_dir):
        os.makedirs(bin_dir)
    
    # Copy nowplaying-cli to the bin directory
    local_nowplaying_cli = os.path.join(bin_dir, "nowplaying-cli")
    shutil.copy(nowplaying_cli_path, local_nowplaying_cli)
    os.chmod(local_nowplaying_cli, 0o755)  # Make executable
    
    # Build the app with PyInstaller
    result = subprocess.run(
        [
            "pyinstaller",
            "--clean",
            "--windowed",
            "--name=Music RPC",
            f"--icon=Music_RPC.icns",
            "--add-data=music_rpc.png:.",
            "--add-data=Music_RPC.icns:.",
            f"--add-binary={local_nowplaying_cli}:bin",
            "--hidden-import=rumps",
            "--hidden-import=Quartz",
            "--hidden-import=Cocoa",
            "--hidden-import=Foundation",
            "--hidden-import=AppKit",
            "--hidden-import=PyObjCTools",
            "--hidden-import=MediaPlayer",
            "--hidden-import=pypresence",
            "--hidden-import=requests",
            "--hidden-import=locale",
            "--hidden-import=io",
            "--hidden-import=codecs",
            "--hidden-import=re",
            "--hidden-import=subprocess",
            "--hidden-import=json",
            "--hidden-import=queue",
            "--hidden-import=threading",
            "--hidden-import=unicodedata",
            "--recursive-copy-metadata=pypresence",
            "--collect-submodules=deezer_rpc",
            "--osx-bundle-identifier=com.jakubsladek.musicrpc",
        ] + 
        ["main.py"],
        check=False,
    )
    
    if result.returncode != 0:
        print("Failed to build app.")
        return False
    
    # Manually copy the Info.plist to the app bundle
    app_path = "dist/Music RPC.app"
    contents_path = os.path.join(app_path, "Contents")
    
    # Ensure contents directory exists
    os.makedirs(contents_path, exist_ok=True)
    
    # Copy Info.plist and ensure it has the right permissions
    shutil.copy("Info.plist", os.path.join(contents_path, "Info.plist"))
    os.chmod(os.path.join(contents_path, "Info.plist"), 0o644)
    
    # Copy resources that might be needed
    resources_path = os.path.join(contents_path, "Resources")
    os.makedirs(resources_path, exist_ok=True)
    
    # Make sure the bin directory exists and nowplaying-cli is executable
    bin_path = os.path.join(contents_path, "MacOS", "bin")
    os.makedirs(bin_path, exist_ok=True)
    
    # Verify nowplaying-cli is in the bin directory and is executable
    app_nowplaying_cli = os.path.join(bin_path, "nowplaying-cli")
    if not os.path.exists(app_nowplaying_cli):
        # Copy it again if it's not there
        shutil.copy(nowplaying_cli_path, app_nowplaying_cli)
    os.chmod(app_nowplaying_cli, 0o755)  # Make executable
    
    # Create an environment settings script to ensure proper environment variables
    env_script_path = os.path.join(contents_path, "MacOS", "env_settings.sh")
    with open(env_script_path, 'w') as f:
        f.write("""#!/bin/bash
# Set environment variables for proper Unicode support
export PYTHONIOENCODING=utf-8
export LC_ALL=en_US.UTF-8
export LANG=en_US.UTF-8
export PATH="$(dirname "$0")/bin:$PATH"

# Check if nowplaying-cli exists and is executable
if [ -x "$(dirname "$0")/bin/nowplaying-cli" ]; then
    echo "nowplaying-cli found and is executable" >> ~/Music_RPC_debug.log
else
    echo "ERROR: nowplaying-cli not found or not executable in $(dirname "$0")/bin" >> ~/Music_RPC_debug.log
    ls -la "$(dirname "$0")/bin" >> ~/Music_RPC_debug.log
fi

# Execute the actual application
exec "$(dirname "$0")/Music RPC.bin" "$@"
""")
    
    os.chmod(env_script_path, 0o755)
    
    # Rename the original executable and create a wrapper script
    macos_path = os.path.join(contents_path, "MacOS")
    original_executable_path = os.path.join(macos_path, "Music RPC")
    renamed_executable_path = os.path.join(macos_path, "Music RPC.bin")
    
    if os.path.exists(original_executable_path):
        # Rename the original executable
        os.rename(original_executable_path, renamed_executable_path)
        
        # Create a wrapper script
        with open(original_executable_path, 'w') as f:
            f.write("""#!/bin/bash
# Environment setup wrapper script
cd "$(dirname "$0")"
./env_settings.sh
""")
        
        # Make it executable
        os.chmod(original_executable_path, 0o755)
    
    # Create a debug run script 
    run_script_path = os.path.join(macos_path, "debug_run.sh")
    with open(run_script_path, 'w') as f:
        f.write("""#!/bin/bash
# Debug script to help identify issues with the app
export PYTHONIOENCODING=utf-8
export LC_ALL=en_US.UTF-8
export LANG=en_US.UTF-8
export PATH="$(dirname "$0")/bin:$PATH"

cd "$(dirname "$0")"
echo "Starting Music RPC in debug mode..."
echo "System PATH: $PATH" > ~/Music_RPC_debug.log
echo "Checking for nowplaying-cli:" >> ~/Music_RPC_debug.log
if [ -x "$(dirname "$0")/bin/nowplaying-cli" ]; then
    echo "nowplaying-cli found and is executable" >> ~/Music_RPC_debug.log
    ls -la "$(dirname "$0")/bin" >> ~/Music_RPC_debug.log
else
    echo "ERROR: nowplaying-cli not found or not executable in $(dirname "$0")/bin" >> ~/Music_RPC_debug.log
    ls -la "$(dirname "$0")/bin" >> ~/Music_RPC_debug.log
fi

# Try to run the app with output redirected to debug log
./\"Music RPC\" >> ~/Music_RPC_debug.log 2>&1
""")
    
    os.chmod(run_script_path, 0o755)
    print(f"Created debug run script at {run_script_path}")
    
    print(f"Successfully built app: {app_path}")
    print("If the app doesn't start, try running the debug script inside the app bundle:")
    print(f"cd '{macos_path}' && ./debug_run.sh")
    print("Check ~/Music_RPC_debug.log for error messages")
    
    return True


def create_dmg():
    """Create a DMG installer for the app"""
    print("Creating DMG installer...")
    
    # Path to the app
    app_path = os.path.abspath("dist/Music RPC.app")
    
    # Check if app exists
    if not os.path.exists(app_path):
        print("App not found at:", app_path)
        return False
    
    # Use explicit DMG name 
    dmg_name = "Music-RPC-Installer.dmg"
    
    try:
        # Check if create-dmg is installed
        subprocess.run(['which', 'create-dmg'], check=True, capture_output=True)
    except subprocess.CalledProcessError:
        print("create-dmg not found. Installing via Homebrew...")
        subprocess.run(['brew', 'install', 'create-dmg'], check=True)
    
    # Prepare a temporary directory for DMG creation
    tmp_dir = os.path.abspath("dist/tmp_dmg")
    os.makedirs(tmp_dir, exist_ok=True)
    
    # Copy the app to the temporary directory
    shutil.copytree(app_path, os.path.join(tmp_dir, "Music RPC.app"), symlinks=True)
    
    # Create the DMG
    dmg_cmd = [
        'create-dmg',
        '--volname', 'Music RPC',
        '--volicon', 'Music_RPC.icns',
        '--window-pos', '200', '120',
        '--window-size', '800', '400',
        '--icon-size', '100',
        '--icon', 'Music RPC.app', '200', '200',
        '--app-drop-link', '600', '200',
        '--no-internet-enable',
        os.path.join('dist', dmg_name),
        tmp_dir
    ]
    
    result = subprocess.run(dmg_cmd)
    
    # Clean up the temporary directory
    shutil.rmtree(tmp_dir, ignore_errors=True)
    
    if result.returncode == 0:
        print(f"DMG installer created successfully: dist/{dmg_name}")
        return True
    else:
        print("Failed to create DMG installer.")
        return False


def main():
    """Main build script function"""
    # Clean up previous builds
    cleanup()
    
    # Create macOS icon file
    create_icns()
    
    # Build macOS app
    if build_app():
        print("App built successfully!")
        
        # Create DMG installer
        if create_dmg():
            print("DMG installer created successfully at: Music-RPC-Installer.dmg")
        else:
            print("App built successfully but DMG creation failed. The app is still available in the 'dist' directory.")
    else:
        print("Failed to build app.")


if __name__ == '__main__':
    main() 