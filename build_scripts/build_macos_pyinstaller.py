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
    print(f"Creating Info.plist file at: {plist_path}")
    
    # Find and ensure nowplaying-cli
    nowplaying_cli_path = ensure_nowplaying_cli()
    if not nowplaying_cli_path:
        return False
    
    print(f"Found nowplaying-cli at: {nowplaying_cli_path}")
    
    # Create a bin directory if it doesn't exist
    bin_dir = "bin"
    if os.path.exists(bin_dir):
        shutil.rmtree(bin_dir)
    os.makedirs(bin_dir, exist_ok=True)
    
    # Copy nowplaying-cli to the bin directory
    local_nowplaying_cli = os.path.join(bin_dir, "nowplaying-cli")
    shutil.copy(nowplaying_cli_path, local_nowplaying_cli)
    os.chmod(local_nowplaying_cli, 0o755)  # Make executable
    print(f"Copied nowplaying-cli to: {local_nowplaying_cli}")
    
    # Create or find icon file
    icon_path = create_icns()
    if icon_path:
        print(f"Using icon file at: {icon_path}")
    else:
        print("No icon file found. Default icon will be used.")
    
    assets_dir = os.path.join(project_root, 'assets')
    
    # Prepare data files to include
    data_files = []
    
    # Check for PNG icon in various locations
    png_icon = None
    if os.path.exists('music_rpc.png'):
        png_icon = 'music_rpc.png'
    elif os.path.exists(os.path.join(assets_dir, 'music_rpc.png')):
        png_path = os.path.join('build', 'tmp_icons', 'music_rpc.png')
        os.makedirs(os.path.dirname(png_path), exist_ok=True)
        shutil.copy(os.path.join(assets_dir, 'music_rpc.png'), png_path)
        png_icon = png_path
    
    if png_icon:
        data_files.append(f"--add-data={png_icon}:.")
        print(f"Adding data file: {png_icon}")
    
    # Add the ICNS file if it exists
    if icon_path:
        data_files.append(f"--add-data={icon_path}:.")
        print(f"Adding data file: {icon_path}")
    
    # Build the app with PyInstaller
    pyinstaller_cmd = [
        "pyinstaller",
        "--clean",
        "--windowed",
        "--name=Music Discord Rich Presence",
        "--distpath=./dist",
        "--workpath=./build",
        "--noconfirm"
    ]
    
    # Add icon if it exists
    if icon_path:
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
        "--osx-bundle-identifier=com.jakubsladek.musicdiscordrpc",
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
    app_path = "dist/Music Discord Rich Presence.app"
    contents_path = os.path.join(app_path, "Contents")
    
    # Ensure contents directory exists
    os.makedirs(contents_path, exist_ok=True)
    
    # Copy Info.plist and ensure it has the right permissions
    shutil.copy("Info.plist", os.path.join(contents_path, "Info.plist"))
    os.chmod(os.path.join(contents_path, "Info.plist"), 0o644)
    print(f"Copied Info.plist to {os.path.join(contents_path, 'Info.plist')}")
    
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
    print(f"Ensured nowplaying-cli is in app bundle and executable: {app_nowplaying_cli}")
    
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
    echo "nowplaying-cli found and is executable" >> ~/Music_Discord_RPC_debug.log
else
    echo "ERROR: nowplaying-cli not found or not executable in $(dirname "$0")/bin" >> ~/Music_Discord_RPC_debug.log
    ls -la "$(dirname "$0")/bin" >> ~/Music_Discord_RPC_debug.log
fi

# Execute the actual application
exec "$(dirname "$0")/Music Discord Rich Presence.bin" "$@"
""")
    
    os.chmod(env_script_path, 0o755)
    print(f"Created environment settings script at {env_script_path}")
    
    # Rename the original executable and create a wrapper script
    macos_path = os.path.join(contents_path, "MacOS")
    original_executable_path = os.path.join(macos_path, "Music Discord Rich Presence")
    renamed_executable_path = os.path.join(macos_path, "Music Discord Rich Presence.bin")
    
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
        print("Created wrapper script for the executable")
    
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
echo "Starting Music Discord Rich Presence in debug mode..."
echo "System PATH: $PATH" > ~/Music_Discord_RPC_debug.log
echo "Checking for nowplaying-cli:" >> ~/Music_Discord_RPC_debug.log
if [ -x "$(dirname "$0")/bin/nowplaying-cli" ]; then
    echo "nowplaying-cli found and is executable" >> ~/Music_Discord_RPC_debug.log
    ls -la "$(dirname "$0")/bin" >> ~/Music_Discord_RPC_debug.log
else
    echo "ERROR: nowplaying-cli not found or not executable in $(dirname "$0")/bin" >> ~/Music_Discord_RPC_debug.log
    ls -la "$(dirname "$0")/bin" >> ~/Music_Discord_RPC_debug.log
fi

# Try to run the app with output redirected to debug log
./\"Music Discord Rich Presence\" >> ~/Music_Discord_RPC_debug.log 2>&1
""")
    
    os.chmod(run_script_path, 0o755)
    print(f"Created debug run script at {run_script_path}")
    
    print(f"Successfully built app: {app_path}")
    print("If the app doesn't start, try running the debug script inside the app bundle:")
    print(f"cd '{macos_path}' && ./debug_run.sh")
    print("Check ~/Music_Discord_RPC_debug.log for error messages")
    
    return True


def main():
    """Main build script function"""
    print("Starting PyInstaller macOS build...")
    
    # Clean up previous builds
    cleanup()
    
    # Build macOS app
    if build_app_pyinstaller():
        print("App built successfully!")
        
        # Create DMG installer
        app_path = os.path.abspath("dist/Music Discord Rich Presence.app")
        if not os.path.exists(app_path):
            print(f"ERROR: App not found at {app_path}. Cannot create DMG.")
            return
            
        icon_path = create_icns()  # Get the icon path
        
        if create_dmg(app_path, icon_path):
            print("DMG installer created successfully!")
            dmg_file = "Music-Discord-Rich-Presence-Installer.dmg"
            expected_locations = [
                os.path.join(os.getcwd(), 'dist', dmg_file),
                os.path.join(os.getcwd(), dmg_file)
            ]
            
            for location in expected_locations:
                if os.path.exists(location):
                    print(f"DMG installer is available at: {location}")
                    print(f"You can install it by double-clicking on {location}")
        else:
            print("App built successfully but DMG creation failed. The app is still available in the 'dist' directory.")
    else:
        print("Failed to build app.")


if __name__ == '__main__':
    main() 