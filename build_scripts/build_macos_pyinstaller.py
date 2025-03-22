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

# Import shared build utilities
from build_utils import (
    cleanup, 
    ensure_project_root, 
    create_icns, 
    create_info_plist,
    find_nowplaying_cli,
    ensure_nowplaying_cli,
    create_dmg
)


def build_app_pyinstaller():
    """Build the macOS application using PyInstaller"""
    print("Building macOS application with PyInstaller...")
    
    # Ensure we're working from the project root directory
    project_root = ensure_project_root()
    
    # Verify main.py exists in the current directory
    if not os.path.exists('main.py'):
        print(f"ERROR: main.py not found in {os.getcwd()}")
        return False
    
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
    
    # Make sure we have an icon file
    icon_path = "Music_RPC.icns"
    assets_dir = os.path.join(project_root, 'assets')
    
    # Check icon files in various locations
    if not os.path.exists(icon_path):
        if os.path.exists(os.path.join(assets_dir, 'music_rpc.icns')):
            shutil.copy(os.path.join(assets_dir, 'music_rpc.icns'), icon_path)
            print(f"Copied icon from {os.path.join(assets_dir, 'music_rpc.icns')}")
    
    # Prepare data files to include
    data_files = []
    
    # Check for PNG icon in various locations
    png_icon = None
    if os.path.exists('music_rpc.png'):
        png_icon = 'music_rpc.png'
    elif os.path.exists(os.path.join(assets_dir, 'music_rpc.png')):
        shutil.copy(os.path.join(assets_dir, 'music_rpc.png'), 'music_rpc.png')
        png_icon = 'music_rpc.png'
    
    if png_icon:
        data_files.append(f"--add-data={png_icon}:.")
        print(f"Adding data file: {png_icon}")
    
    # Add the ICNS file if it exists
    if os.path.exists(icon_path):
        data_files.append(f"--add-data={icon_path}:.")
        print(f"Adding data file: {icon_path}")
    
    # Build the app with PyInstaller
    pyinstaller_cmd = [
        "pyinstaller",
        "--clean",
        "--windowed",
        "--name=Music RPC"
    ]
    
    # Add icon if it exists
    if os.path.exists(icon_path):
        pyinstaller_cmd.append(f"--icon={icon_path}")
        print(f"Using icon: {icon_path}")
    
    # Add data files
    pyinstaller_cmd.extend(data_files)
    
    # Add other PyInstaller options
    pyinstaller_cmd.extend([
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
        "--collect-submodules=music_rpc",  # Updated from deezer_rpc to music_rpc
        "--osx-bundle-identifier=com.jakubsladek.musicrpc",
        "main.py"  # Main script path
    ])
    
    # Run PyInstaller
    print("Running PyInstaller command:")
    print(" ".join(pyinstaller_cmd))
    result = subprocess.run(pyinstaller_cmd, check=False)
    
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


def main():
    """Main build script function"""
    print("Starting PyInstaller macOS build...")
    
    # Clean up previous builds
    cleanup()
    
    # Create macOS icon file
    create_icns()
    
    # Build macOS app
    if build_app_pyinstaller():
        print("App built successfully!")
        
        # Create DMG installer
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