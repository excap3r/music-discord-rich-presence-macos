# Music RPC

![Music RPC](music_rpc.png)

Discord Rich Presence for Music Players on macOS.

## About

Music RPC adds Discord Rich Presence integration for any music player on macOS. Show off what you're listening to with your Discord friends in style!

Originally created for Deezer, Music RPC now supports **any music player** that works with macOS media controls, including:
- Apple Music
- Spotify
- Deezer
- iTunes
- VLC
- And many more!

## Features

- 🎵 Discord Rich Presence integration for any music player
- 🖥️ macOS tray icon with current song information
- 🔄 Automatic song detection via macOS media controls
- 🎨 Shows album art and artist images when available
- ⏱️ Adjustable update interval
- 🚀 Easy DMG installer
- 🌍 Full Unicode support including Czech characters
- 📋 Detailed logs for troubleshooting

## Special Notes

- **Apple Music Integration:** By default, Discord Rich Presence for Apple Music is disabled since Apple Music has its own native Discord integration. The app will still show Apple Music playback in the tray icon but won't duplicate Discord presence. This prevents conflicts with Apple's own solution.

## Screenshots

*Insert screenshots here*

## Installation

### Requirements

- macOS 10.13 or higher
- Discord desktop app
- Python 3.9+ (if installing from source)
- Any music player that works with macOS media controls

### Option 1: DMG Installer (Recommended)

1. Download the latest `Music-RPC-Installer.dmg` from the [Releases](https://github.com/yourusername/music-rpc/releases) page
2. Open the DMG file
3. Drag the Music RPC app to your Applications folder
4. Launch Music RPC from your Applications folder
5. You'll see the 🎵 icon in your menu bar when the app is running

### Option 2: Install from Source

1. Clone this repository:
   ```
   git clone https://github.com/yourusername/music-rpc.git
   cd music-rpc
   ```

2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

3. Run the application:
   ```
   python main.py
   ```

### Option 3: Build Your Own DMG

1. Clone this repository:
   ```
   git clone https://github.com/yourusername/music-rpc.git
   cd music-rpc
   ```

2. Install dependencies:
   ```
   pip install -r requirements.txt pyinstaller dmgbuild
   ```

3. Build the macOS app and DMG using PyInstaller:
   ```
   python build_macos_pyinstaller.py
   ```

4. The DMG installer will be created as `Music-RPC-Installer.dmg`

See [BUILD_NOTES.md](BUILD_NOTES.md) for detailed information about the build process.

## Usage

1. Start Music RPC (either from Applications or by running the script)
2. The app will appear as a 🎵 icon in your menu bar
3. Play music in any supported music player
4. Your Discord status will automatically update with the currently playing song
5. You can check the current song and Discord connection status in the menu bar

### Menu Bar Options

- **Now Playing**: Shows the current song title
- **Artist**: Shows the current artist
- **Player**: Shows the detected music player
- **Discord**: Shows Discord connection status
- **Update Interval**: Change how often the app updates (5, 10, or 30 seconds)
- **About**: Shows version information
- **Quit**: Exits the application

## Accessibility Permissions

On first run, Music RPC will request Accessibility permissions. These are required to detect what's playing in your music player.

To grant permissions:
1. Open System Settings > Privacy & Security > Accessibility
2. Add Music RPC to the list of allowed apps
3. Ensure the checkbox next to Music RPC is checked

## Troubleshooting

For detailed troubleshooting information, please refer to the [TROUBLESHOOTING.md](TROUBLESHOOTING.md) guide.

Common issues:

### Discord status not updating

- Make sure Discord is running
- Check that "Display current activity as a status message" is enabled in Discord settings
- Verify that the app has accessibility permissions

### Song not being detected

- Make sure your music player is supported and currently playing
- Try using a different music player that uses macOS media controls
- Check that the app has accessibility permissions

### Application freezes or crashes

- Make sure you have the latest version of the app
- If updating from an older version, you may need to restart Discord
- For macOS Sonoma and higher, ensure you've granted the necessary permissions

## Development

### Project Structure

```
music-rpc/
├── deezer_rpc/              # Core package (name kept for compatibility)
│   ├── core/                # Core functionality
│   │   ├── app.py           # Main application class
│   │   ├── discord_presence.py  # Discord integration
│   │   ├── song_info.py     # Music detection
│   │   ├── tray_icon.py     # macOS tray icon
│   │   └── window_manager.py  # Window detection
│   ├── config/              # Configuration
│   └── logging/             # Logging setup
├── main.py                  # Application entry point
├── build_macos_pyinstaller.py  # macOS build script using PyInstaller
├── debug_main.py            # Debug version of main.py with enhanced logging
├── test_tray.py             # Test script for tray functionality
├── BUILD_NOTES.md           # Detailed build information
├── TROUBLESHOOTING.md       # Troubleshooting guide
├── setup.py                 # Package setup
└── requirements.txt         # Dependencies
```

### Building from Source

To build the application from source:

1. Clone the repository
2. Install dependencies: `pip install -r requirements.txt pyinstaller dmgbuild`
3. Run the build script: `python build_macos_pyinstaller.py`

For detailed build instructions and options, see [BUILD_NOTES.md](BUILD_NOTES.md).

## Building Notes

The app is built using PyInstaller, which packages the Python application into a standalone executable. This approach provides better compatibility with modern macOS systems and ensures all dependencies are properly included.

For detailed information about the build process, see [BUILD_NOTES.md](BUILD_NOTES.md).

## Credits

- Created by [Jakub Sladek](https://github.com/yourusername)
- Originally developed for Deezer, now supporting all music players
- Uses [pypresence](https://github.com/qwertyquerty/pypresence) for Discord integration
- Uses [rumps](https://github.com/jaredks/rumps) for macOS tray integration
- Uses [nowplaying-cli](https://github.com/kirtan-shah/nowplaying-cli) for macOS media detection

## License

This project is licensed under the MIT License - see the LICENSE file for details.
