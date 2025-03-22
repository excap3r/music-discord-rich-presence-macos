# Music RPC

![Music RPC](music_rpc.png)

Discord Rich Presence for Music Players on macOS.

## Contents

- [About](#about)
- [Features](#features)
- [Installation](#installation)
- [Usage](#usage)
- [Configuration](#configuration)
- [Troubleshooting](#troubleshooting)
- [Architecture](#architecture)
- [Development](#development)
- [Contributing](#contributing)
- [License](#license)

## About

Music RPC adds Discord Rich Presence integration for various music players on macOS. Show off what you're listening to with your Discord friends in style!

Originally created for Deezer, Music RPC now supports multiple music players including:
- Deezer
- Apple Music
- iTunes
- Tidal (with limited functionality)
- More players coming soon!

## Features

- 🎵 Discord Rich Presence integration for multiple music players
- 🖥️ macOS tray icon with current song information
- 🔄 Automatic player detection and song information retrieval
- 🎨 Shows album art and artist images when available via the Deezer API
- ⏱️ Adjustable update interval
- 🚀 Easy DMG installer
- 🌍 Full Unicode support including special characters
- 📋 Detailed logs for troubleshooting

## Installation

### Requirements

- macOS 10.13 or higher
- Discord desktop app
- Python 3.9+ (if installing from source)
- One of the supported music players

### Option 1: DMG Installer (Recommended)

1. Download the latest `Music-RPC-Installer.dmg` from the [Releases](https://github.com/yourusername/music-rpc/releases) page
2. Open the DMG file
3. Drag the Music RPC app to your Applications folder
4. Launch Music RPC from your Applications folder
5. You'll see the 🎵 icon in your menu bar when the app is running

### Option 2: Install from Source

1. Clone this repository:
   ```bash
   git clone https://github.com/yourusername/music-rpc.git
   cd music-rpc
   ```

2. Create a virtual environment (optional but recommended):
   ```bash
   python -m venv venv
   source venv/bin/activate  # On macOS
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Run the application:
   ```bash
   python main.py
   ```

### Option 3: Build Your Own DMG

1. Install dependencies:
   ```bash
   pip install -r requirements.txt pyinstaller dmgbuild
   ```

2. Build the macOS app and DMG:
   ```bash
   python build_scripts/build_macos_dmg.py
   ```

3. The DMG installer will be created in the `dist` directory

## Usage

### Getting Started

1. Launch Music RPC from your Applications folder
2. Grant Accessibility permissions when prompted
   - Required to detect music players and retrieve song information
   - Open System Settings > Privacy & Security > Accessibility
   - Ensure Music RPC is checked in the list
3. Start playing music in a supported player
4. Your Discord status will automatically update with the currently playing song

### Menu Bar Options

Music RPC operates through its menu bar icon (🎵). Click it to see:

- **Playing**: Shows the title of the currently playing song
- **Artist**: Shows the artist of the currently playing song
- **Player**: Shows which music player is currently active
- **Discord**: Shows the connection status to Discord
- **Update Interval**: Lets you change how often the status updates (5, 10, or 30 seconds)
- **About**: Shows information about the application
- **Quit**: Exits the application

### Discord Integration

To ensure Discord integration works properly:

1. Make sure Discord desktop app is running (browser version doesn't support Rich Presence)
2. In Discord, go to User Settings > Activity Settings
3. Ensure "Display current activity as a status message" is enabled

### Auto-Launch on Startup

To make Music RPC start automatically when you log in:

1. Open System Settings > General > Login Items
2. Click the + button
3. Browse to your Applications folder
4. Select Music RPC and click "Open"

## Configuration

### Configuration File

Music RPC stores its configuration in a JSON file:
- When installed via DMG: `~/Library/Application Support/Music RPC/config.json`
- When running from source: In the application directory

### Core Settings

| Setting | Description | Default | Possible Values |
|---------|-------------|---------|----------------|
| `update_interval` | How often to check for song changes (in seconds) | `10` | `5`, `10`, `30` |
| `enabled_players` | List of enabled music players | All available | List of player names |
| `debug_mode` | Enable verbose logging for troubleshooting | `false` | `true`, `false` |

### Discord Settings

| Setting | Description | Default | Possible Values |
|---------|-------------|---------|----------------|
| `discord_enabled` | Whether to enable Discord Rich Presence | `true` | `true`, `false` |
| `client_id` | Discord application client ID | Built-in default | Any valid client ID |
| `show_elapsed_time` | Show elapsed time in Discord status | `true` | `true`, `false` |
| `show_player_name` | Show music player name in Discord status | `true` | `true`, `false` |

### Command-Line Arguments

When running from source, the following arguments are available:

| Argument | Description |
|----------|-------------|
| `--debug` | Enable debug mode with verbose logging |
| `--config /path/to/config.json` | Use a custom configuration file |
| `--disable-discord` | Run without Discord integration |
| `--interval N` | Set update interval to N seconds |

Example:
```bash
python main.py --debug --interval 5
```

### Advanced Configuration

#### Custom Discord Client ID

If you want to use your own Discord application for Rich Presence:

1. Create a new application at the [Discord Developer Portal](https://discord.com/developers/applications)
2. Copy your application's Client ID
3. Set the `client_id` field in the configuration file
4. Add appropriate assets to your Discord application for album art display

#### Debug Logging

When troubleshooting issues, you can enable debug logging:

1. Set `debug_mode` to `true` in the configuration file, or use the `--debug` command-line argument
2. Restart the application
3. Check the `music_rpc.log` file for detailed logs

## Troubleshooting

### Common Issues

#### Discord status not updating
- Make sure Discord desktop app is running
- Check that "Display current activity as a status message" is enabled in Discord settings
- Verify that Music RPC has Accessibility permissions

#### Song not being detected
- Make sure you're using a supported music player
- Verify the music player is currently playing a song
- Check that Music RPC has Accessibility permissions

#### Application crashes or freezes
- Check the log file (`music_rpc.log`) for error messages
- Make sure you have the latest version of the app
- For macOS Sonoma and higher, ensure you've granted all necessary permissions

### Log File

The application creates a log file named `music_rpc.log` in the directory where the application is run. This file contains detailed information about the application's operation and can be helpful for troubleshooting issues.

### Uninstallation

#### If Installed via DMG
1. Open the Applications folder in Finder
2. Drag Music RPC to the Trash
3. Empty the Trash

#### If Installed from Source
1. If you used a virtual environment, simply delete the project folder
2. If you want to remove the Python dependencies:
   ```bash
   pip uninstall -r requirements.txt
   ```

## Architecture

Music RPC is built with a modular architecture that separates concerns and allows for easy extension:

### Core Components

- **App**: The main application controller that orchestrates all components
- **Player Detection**: Abstractions and implementations for detecting music players and retrieving song information
- **Discord Presence**: Manages the Discord Rich Presence connection and updates
- **Window Manager**: Detects and manages window titles for song information extraction
- **Song Info**: Processes and enriches song information from various sources

### UI Components

- **Tray Icon**: Provides a system tray icon with menu options and status display

### Project Structure

```
music-rpc/
├── music_rpc/              # Core package
│   ├── core/               # Core functionality
│   │   ├── app.py          # Main application class
│   │   ├── discord_presence.py  # Discord integration
│   │   ├── song_info.py    # Song info processing
│   │   ├── window_manager.py  # Window detection
│   │   └── player_detection/  # Player detection
│   │       ├── base.py     # Base interfaces
│   │       ├── deezer.py   # Deezer implementation
│   │       ├── apple_music.py  # Apple Music implementation
│   │       └── registry.py # Player registry
│   ├── ui/                 # UI components
│   │   └── tray_icon.py    # System tray icon
│   ├── config/             # Configuration
│   │   └── settings.py     # Settings management
│   └── logging/            # Logging setup
│       └── handlers.py     # Custom log handlers
├── main.py                 # Application entry point
├── build_scripts/          # Build scripts
├── assets/                 # Application assets
└── requirements.txt        # Dependencies
```

## Development

### Development Environment Setup

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/music-rpc.git
   cd music-rpc
   ```

2. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On macOS
   ```

3. Install development dependencies:
   ```bash
   pip install -r requirements.txt
   pip install pytest pytest-cov mypy black isort flake8
   ```

### Running in Development Mode

Run the application in debug mode for development:

```bash
python main.py --debug
```

### Adding Support for a New Music Player

1. Create a new file in `music_rpc/core/player_detection/` (e.g., `spotify.py`)
2. Implement the `MusicPlayerDetector` interface with player-specific detection logic:

```python
from .base import MusicPlayerDetector
from ..song_info import SongInfo
from typing import Optional

class SpotifyPlayerDetector(MusicPlayerDetector):
    @property
    def player_name(self) -> str:
        return "Spotify"
    
    def is_running(self) -> bool:
        # Implement detection logic for Spotify
        pass
    
    def get_current_song(self) -> Optional[SongInfo]:
        # Implement song information retrieval
        pass
        
    def extract_song_info_from_window(self, window_title: str) -> Optional[SongInfo]:
        # Parse window title for song info
        pass
```

3. Register your player in `registry.py`:

```python
from .spotify import SpotifyPlayerDetector

# In the initialize_player_registry function:
try:
    spotify_detector = SpotifyPlayerDetector(config, logger)
    registry.register_player(spotify_detector)
except Exception as e:
    logger.error(f"Failed to initialize Spotify player detector: {e}")
```

### Adding UI Features

To add new menu items or functionality to the tray icon:

1. Open `music_rpc/ui/tray_icon.py`
2. Add new menu items to the `__init__` method of `MusicRPCTrayApp`
3. Implement handler methods for the new menu items

Example:

```python
# Add to __init__ method
self.menu.append(rumps.MenuItem("My New Feature", callback=self.my_new_feature))

# Add a new method to handle the menu item click
def my_new_feature(self, sender: rumps.MenuItem) -> None:
    """Handle the My New Feature menu item."""
    try:
        # Implement your functionality here
        rumps.alert("New Feature", "New feature activated!")
    except Exception as e:
        self.logger.error(f"Error in my_new_feature: {e}")
```

### Building and Packaging

To create a standalone `.app` without the DMG:

```bash
python build_scripts/build_macos_app.py
```

### Testing

Run the test suite:

```bash
pytest
```

Run tests with coverage:

```bash
pytest --cov=music_rpc
```

### Code Style Guidelines

This project follows the PEP 8 style guide with some modifications:
- Line length: 100 characters
- Use type hints for all function parameters and return values
- Document all classes and methods with docstrings

Format your code with Black:
```bash
black music_rpc/
```

Check types with mypy:
```bash
mypy music_rpc/
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests and ensure they pass
5. Submit a pull request

Please follow the code style guidelines and include tests for new functionality.

## Future Improvements

1. Add support for more music players (Spotify, VLC, etc.)
2. Implement a proper GUI for configuration
3. Add support for Windows and Linux
4. Implement automated testing
5. Create platform-specific installers

## Credits

- Uses [pypresence](https://github.com/qwertyquerty/pypresence) for Discord integration
- Uses [rumps](https://github.com/jaredks/rumps) for macOS tray icon

## License

This project is licensed under the MIT License - see the LICENSE file for details.
