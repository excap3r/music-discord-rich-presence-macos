# Music Discord Rich Presence for macOS

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![macOS](https://img.shields.io/badge/Platform-macOS-brightgreen.svg)](https://github.com/yourusername/music-rpc/releases)
[![Discord](https://img.shields.io/badge/Discord-Rich%20Presence-7289DA.svg)](https://discord.com/developers/docs/rich-presence/how-to)

**Show off what you're listening to with your Discord friends in style!**

[Download Latest Release](https://github.com/yourusername/music-rpc/releases) | [Report Issue](https://github.com/yourusername/music-rpc/issues) | [Contribute](https://github.com/yourusername/music-rpc/pulls)

---

## 📋 Contents

- [About](#-about)
- [Features](#-features)
- [Installation](#-installation)
- [Usage](#-usage)
- [Configuration](#-configuration)
- [Troubleshooting](#-troubleshooting)
- [Architecture](#-architecture)
- [Development](#-development)
- [Contributing](#-contributing)
- [Future Improvements](#-future-improvements)
- [Frequently Asked Questions](#-frequently-asked-questions)
- [Credits](#-credits)
- [License](#-license)

---

## 🔍 About

Music Discord Rich Presence for macOS adds Discord Rich Presence integration for various music players on macOS. Show off what you're listening to with your Discord friends in style!

Originally created for Deezer, this app now supports:
- 🎵 **Deezer**
- 🎵 **iTunes**
- 🎵 **Tidal**

> **Note about Apple Music**: Apple Music is no longer supported as it now has its own native Discord Rich Presence integration. This prevents conflicts and provides a better experience for Apple Music users.

Want support for another player? Feel free to [open an issue](https://github.com/yourusername/music-rpc/issues) to request it. New player support is considered based on user demand.

---

## ✨ Features

<table>
  <tr>
    <td>🎵</td>
    <td><b>Discord Rich Presence integration</b> for multiple music players</td>
  </tr>
  <tr>
    <td>🖥️</td>
    <td><b>macOS tray icon</b> with current song information</td>
  </tr>
  <tr>
    <td>🔄</td>
    <td><b>Automatic player detection</b> and song information retrieval</td>
  </tr>
  <tr>
    <td>🎨</td>
    <td>Shows <b>album art and artist images</b> when available via the Deezer API</td>
  </tr>
  <tr>
    <td>⏱️</td>
    <td><b>Adjustable update interval</b> for song status</td>
  </tr>
  <tr>
    <td>🚀</td>
    <td><b>Easy DMG installer</b> for quick setup</td>
  </tr>
  <tr>
    <td>🌍</td>
    <td><b>Full Unicode support</b> including special characters</td>
  </tr>
  <tr>
    <td>📋</td>
    <td><b>Detailed logs</b> for troubleshooting</td>
  </tr>
</table>

---

## 📥 Installation

### 📋 Requirements

- 🖥️ macOS 10.13 or higher
- 💬 Discord desktop app
- 🐍 Python 3.9+ (if installing from source)
- 🎵 One of the supported music players
- 🛠️ [nowplaying-cli](https://github.com/kirtan-shah/nowplaying-cli) (automatically included in the DMG installer)

### 🔐 System Permissions

<details>
<summary>Click to expand permission requirements</summary>

The app requires certain permissions to function properly:

#### 1️⃣ Accessibility 
Required to detect music players and read window titles
- Go to System Settings → Privacy & Security → Accessibility
- Add Music Discord Rich Presence to the list and enable it

#### 2️⃣ Automation (macOS Sonoma and higher)
- Go to System Settings → Privacy & Security → Automation
- Allow Music Discord Rich Presence to control "System Events"

#### 3️⃣ Screen Recording (may be required on some systems)
- In some cases, especially on macOS Sonoma, you may need to grant screen recording permissions
- Go to System Settings → Privacy & Security → Screen Recording
- Add Music Discord Rich Presence to the list and enable it

</details>

### 🔧 Prerequisites

If you're installing from source or building your own app, you'll need to install nowplaying-cli:

```bash
brew install kirtan-shah/tap/nowplaying-cli
```

This CLI tool is required for retrieving currently playing song information from macOS players.

### 💿 Installation Options

<details open>
<summary><b>Option 1: DMG Installer (Recommended)</b></summary>

1. Download the latest `Music-Discord-Rich-Presence-Installer.dmg` from the [Releases](https://github.com/yourusername/music-rpc/releases) page
2. Open the DMG file
3. Drag the Music Discord Rich Presence app to your Applications folder
4. Launch Music Discord Rich Presence from your Applications folder
5. You'll see the 🎵 icon in your menu bar when the app is running
</details>

<details>
<summary>Option 2: Install from Source</summary>

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
</details>

<details>
<summary>Option 3: Build Your Own DMG</summary>

1. Install dependencies:
   ```bash
   pip install -r requirements.txt pyinstaller dmgbuild
   ```

2. Build the macOS app and DMG:
   ```bash
   python build_scripts/build_macos_dmg.py
   ```

3. The DMG installer will be created in the `dist` directory
</details>

---

## 🎮 Usage

### 🚀 Quick Start Guide

1. ⬇️ Download and install the app
2. 🔐 Grant permissions when prompted
3. 🎵 Play music in a supported player
4. 💬 See your music status appear in Discord

### 🚀 Getting Started

1. Launch Music Discord Rich Presence from your Applications folder
2. Grant the required permissions when prompted:
   - Accessibility permissions for detecting music player windows
   - Automation permissions for interacting with system events
   - Screen Recording permissions if needed (on macOS Sonoma+)
3. Start playing music in a supported player
4. Your Discord status will automatically update with the currently playing song

### 🔍 How Song Detection Works

Music Discord Rich Presence uses two primary methods to detect and retrieve song information:

1. **nowplaying-cli**: The primary method uses the Media Remote API via nowplaying-cli to get detailed song information from the system's current media player.
2. **Process Detection**: The app checks which music player applications are currently running.

This multi-layered approach ensures reliable song detection across different players.

#### About nowplaying-cli

[nowplaying-cli](https://github.com/kirtan-shah/nowplaying-cli) is a command-line tool that accesses the macOS Media Remote API, allowing us to retrieve information about currently playing media from various players. The app uses this tool to:

- Get current song title, artist, and album
- Retrieve playback status (playing, paused)
- Get track duration and current position
- Identify which player is currently active

When the DMG installer is used, nowplaying-cli is included automatically in the application bundle. When running from source, you need to install it via Homebrew as described in the Prerequisites section.

### 📊 Menu Bar Options

Music Discord Rich Presence operates through its menu bar icon (🎵). Click it to see:

- **📝 Playing**: Shows the title of the currently playing song
- **👤 Artist**: Shows the artist of the currently playing song
- **🎵 Player**: Shows which music player is currently active
- **🔗 Discord**: Shows the connection status to Discord
- **⏱️ Update Interval**: Lets you change how often the status updates (5, 10, or 30 seconds)
- **ℹ️ About**: Shows information about the application
- **❌ Quit**: Exits the application

### 🔗 Discord Integration

To ensure Discord integration works properly:

1. Make sure Discord desktop app is running (browser version doesn't support Rich Presence)
2. In Discord, go to User Settings > Activity Settings
3. Ensure "Display current activity as a status message" is enabled

### ⏰ Auto-Launch on Startup

To make Music Discord Rich Presence start automatically when you log in:

1. Open System Settings > General > Login Items
2. Click the + button
3. Browse to your Applications folder
4. Select Music Discord Rich Presence and click "Open"

---

## ⚙️ Configuration

### 📄 Configuration File

Music Discord Rich Presence stores its configuration in a JSON file:
- When installed via DMG: `~/Library/Application Support/Music Discord Rich Presence/config.json`
- When running from source: In the application directory

### 🛠️ Core Settings

| Setting | Description | Default | Possible Values |
|---------|-------------|---------|----------------|
| `update_interval` | How often to check for song changes (in seconds) | `10` | `5`, `10`, `30` |
| `enabled_players` | List of enabled music players | All available | List of player names |
| `debug_mode` | Enable verbose logging for troubleshooting | `false` | `true`, `false` |

### 💬 Discord Settings

| Setting | Description | Default | Possible Values |
|---------|-------------|---------|----------------|
| `discord_enabled` | Whether to enable Discord Rich Presence | `true` | `true`, `false` |
| `client_id` | Discord application client ID | Built-in default | Any valid client ID |
| `show_elapsed_time` | Show elapsed time in Discord status | `true` | `true`, `false` |
| `show_player_name` | Show music player name in Discord status | `true` | `true`, `false` |

### 💻 Command-Line Arguments

When running from source, the following arguments are available:

| Argument | Description |
|----------|-------------|
| `--debug`, `-d` | Enable debug logging |
| `--verbose`, `-v` | Enable verbose logging (INFO level) |
| `--config /path/to/config.json` | Use a custom configuration file |
| `--disable-discord` | Run without Discord integration |
| `--interval N` | Set update interval to N seconds |

Example:
```bash
python main.py --debug --interval 5
```

### 🔧 Advanced Configuration

<details>
<summary>Custom Discord Client ID</summary>

If you want to use your own Discord application for Rich Presence:

1. Create a new application at the [Discord Developer Portal](https://discord.com/developers/applications)
2. Copy your application's Client ID
3. Set the `client_id` field in the configuration file
4. Add appropriate assets to your Discord application for album art display
</details>

<details>
<summary>Debug Logging</summary>

When troubleshooting issues, you can enable debug logging:

1. Set `debug_mode` to `true` in the configuration file, or use the `--debug` command-line argument
2. Restart the application
3. Check the `music_rpc.log` file for detailed logs
</details>

---

## ❓ Troubleshooting

### 🚫 Common Issues

<details>
<summary><b>Discord status not updating</b></summary>

- Make sure Discord desktop app is running
- Check that "Display current activity as a status message" is enabled in Discord settings
- Verify that Music Discord Rich Presence has Accessibility permissions
</details>

<details>
<summary><b>Song not being detected</b></summary>

- Make sure you're using a supported music player
- Verify the music player is currently playing a song
- Check that Music Discord Rich Presence has all required permissions
- Ensure nowplaying-cli is installed (if using the source version)
  ```bash
  which nowplaying-cli
  ```
- Try running nowplaying-cli manually to see if it detects your player:
  ```bash
  nowplaying-cli get
  ```
- If nowplaying-cli returns no output, try running it with root permissions (once) to fix any permissions issues:
  ```bash
  sudo nowplaying-cli get
  ```
</details>

<details>
<summary><b>nowplaying-cli not working</b></summary>

If you're getting errors related to nowplaying-cli, try these steps:
1. Reinstall nowplaying-cli: `brew reinstall kirtan-shah/tap/nowplaying-cli`
2. Run it manually to verify it works: `nowplaying-cli get`
3. Check permissions: `ls -la $(which nowplaying-cli)`
4. Make sure it's executable: `chmod +x $(which nowplaying-cli)`
5. If all else fails, try running once with sudo: `sudo nowplaying-cli get`
</details>

<details>
<summary><b>Application crashes or freezes</b></summary>

- Check the log file (`music_rpc.log`) for error messages
- Make sure you have the latest version of the app
- For macOS Sonoma and higher, ensure you've granted all necessary permissions
- Try reinstalling nowplaying-cli:
  ```bash
  brew reinstall kirtan-shah/tap/nowplaying-cli
  ```
</details>

### 📝 Log File

The application creates a log file named `music_rpc.log` in the directory where the application is run. This file contains detailed information about the application's operation and can be helpful for troubleshooting issues.

### 🗑️ Uninstallation

<details>
<summary>If Installed via DMG</summary>

1. Open the Applications folder in Finder
2. Drag Music Discord Rich Presence to the Trash
3. Empty the Trash
</details>

<details>
<summary>If Installed from Source</summary>

1. If you used a virtual environment, simply delete the project folder
2. If you want to remove the Python dependencies:
   ```bash
   pip uninstall -r requirements.txt
   ```
</details>

---

## 🏗️ Architecture

Music Discord Rich Presence for macOS is built with a modular architecture that separates concerns and allows for easy extension:

### 🧩 Core Components

- **🎮 App**: The main application controller that orchestrates all components
- **🔗 Discord Presence**: Manages the Discord Rich Presence connection and updates
- **🎵 Song Info**: Processes and enriches song information from various sources using nowplaying-cli

### 🎵 Song Information Retrieval

The `SongInfoRetriever` class handles all song detection using these methods:

1. **📱 Media Remote API**: Uses nowplaying-cli to access the macOS Media Remote API
2. **🔍 Process Detection**: Checks running processes to identify active media players
3. **🌐 API Enrichment**: Enhances song info with additional metadata from the Deezer API

### 📂 Project Structure

```
music-rpc/
├── music_rpc/              # Core package
│   ├── core/               # Core functionality
│   │   ├── app.py          # Main application class
│   │   ├── discord_presence.py  # Discord integration
│   │   └── song_info.py    # Song info processing
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

---

## 💻 Development

### 🔧 Development Environment Setup

<details>
<summary>Expand step-by-step setup instructions</summary>

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

4. Install nowplaying-cli:
   ```bash
   brew install kirtan-shah/tap/nowplaying-cli
   ```
</details>

### ▶️ Running in Development Mode

Run the application in debug mode for development:

```bash
python main.py --debug
```

You can also run with additional logging for troubleshooting:

```bash
python main.py --debug --verbose
```

### 🖌️ Adding UI Features

<details>
<summary>Example: Adding a new menu item</summary>

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
</details>

### 📦 Building and Packaging

<details>
<summary>Building the application</summary>

To create a standalone `.app` without the DMG:

```bash
python build_scripts/build_macos_app.py
```
</details>

### 🧪 Testing

<details>
<summary>Running tests</summary>

Run the test suite:

```bash
pytest
```

Run tests with coverage:

```bash
pytest --cov=music_rpc
```
</details>

### 📝 Code Style Guidelines

<details>
<summary>Style guide and formatting tools</summary>

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
</details>

### 💡 Development Tips

1. Use `--debug` flag for detailed logging during development
2. Review `song_info.py` to understand how song detection works
3. Check the log file regularly while developing new features
4. Test across different music players to ensure wide compatibility
5. Use type hints and docstrings for all new code

---

## 🤝 Contributing

<details>
<summary>How to contribute to this project</summary>

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests and ensure they pass
5. Submit a pull request

Please follow the code style guidelines and include tests for new functionality.
</details>

---

## 🔮 Future Improvements

### 🎯 Planned Features

<details open>
<summary><b>View our roadmap</b></summary>

1. **🎵 Enhanced Player Support**
   - Add support for more music players based on user requests
   - Improve detection reliability for existing players

2. **🎨 Better User Experience**
   - Implement a proper GUI for configuration
   - Add localization for multiple languages
   - Improve first-run experience with better permission guidance

3. **💻 Cross-Platform Support**
   - Develop Windows version with equivalent functionality
   - Create Linux version for popular distributions
   - Unify codebase for easier maintenance across platforms

4. **⚙️ Technical Improvements**
   - Implement automated testing and CI/CD pipeline
   - Optimize resource usage for lower system impact
   - Enhance song metadata retrieval with additional APIs

5. **🔗 Discord Integration**
   - Add support for custom buttons in Discord presence
   - Implement playlist sharing functionality
   - Add music recommendations feature
</details>

### 🗺️ Development Roadmap

<details>
<summary>Short, medium, and long-term plans</summary>

- **Short Term (Next Release)**
  - Improve song detection reliability
  - Add support for additional macOS players
  - Fix reported bugs and stability issues

- **Medium Term (3-6 months)**
  - Implement configuration GUI
  - Begin Windows version development
  - Add automated testing

- **Long Term (6+ months)**
  - Complete cross-platform support
  - Add advanced features (playlist sharing, recommendations)
  - Implement localization
</details>

---

## ❓ Frequently Asked Questions

### 🔍 General Questions

<details>
<summary><b>Why doesn't Apple Music work with this app?</b></summary>

Apple Music now has its own native Discord Rich Presence integration. To avoid conflicts and provide the best experience, we've disabled support for Apple Music in this app.
</details>

<details>
<summary><b>How does the app detect what I'm listening to?</b></summary>

The app uses multiple methods, primarily the nowplaying-cli tool that interfaces with the macOS Media Remote API to get information about currently playing media.
</details>

<details>
<summary><b>Will this work with browser-based players?</b></summary>

Currently, the app works best with desktop applications. Browser-based players like YouTube Music or Spotify Web may be detected in some cases but with limited information.
</details>

### ⚙️ Technical Questions

<details>
<summary><b>Does this app collect any personal data?</b></summary>

No. The app only reads information about your currently playing music and sends it to Discord's Rich Presence API. No data is collected or sent to any other servers.
</details>

<details>
<summary><b>Why does the app need Accessibility and Screen Recording permissions?</b></summary>

These permissions are required to detect music players when using the Media Remote API. The app never records your screen content.
</details>

<details>
<summary><b>How much system resources does this app use?</b></summary>

The app is designed to be lightweight. It typically uses less than 50MB of memory and minimal CPU. The update interval setting lets you control how often it checks for song changes.
</details>

<details>
<summary><b>Can I use my own Discord application?</b></summary>

Yes, you can configure a custom Discord client ID in the settings. This allows you to use your own Discord application with custom assets.
</details>

### 🔧 Troubleshooting FAQ

<details>
<summary><b>The app doesn't detect my player, what can I do?</b></summary>

Check that your player is supported and that you've granted all necessary permissions. Try running nowplaying-cli manually to see if it can detect your player.
</details>

<details>
<summary><b>My Discord status shows the wrong song information</b></summary>

There might be a delay in updates. Try adjusting the update interval in the settings to a lower value. If the problem persists, check if multiple media players are running simultaneously.
</details>

<details>
<summary><b>How do I completely uninstall the app?</b></summary>

Delete the app from your Applications folder. Additionally, you can remove the configuration file from `~/Library/Application Support/Music Discord Rich Presence/config.json`.
</details>

---

## 👏 Credits

- Uses [pypresence](https://github.com/qwertyquerty/pypresence) for Discord integration
- Uses [rumps](https://github.com/jaredks/rumps) for macOS tray icon
- Uses [nowplaying-cli](https://github.com/kirtan-shah/nowplaying-cli) for media detection

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

Made with ❤️ for music lovers and Discord users
