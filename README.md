# Music Discord Rich Presence for macOS

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![macOS](https://img.shields.io/badge/Platform-macOS-brightgreen.svg)](https://github.com/excap3r/music-discord-rich-presence-macos/releases)
[![Discord](https://img.shields.io/badge/Discord-Rich%20Presence-7289DA.svg)](https://discord.com/developers/docs/rich-presence/how-to)

**Show off what you're listening to with your Discord friends in style!**

[Download Latest Release](https://github.com/excap3r/music-discord-rich-presence-macos/releases) | [Report Issue](https://github.com/excap3r/music-discord-rich-presence-macos/issues) | [Contribute](https://github.com/excap3r/music-discord-rich-presence-macos/pulls)

---

## 📋 Contents

- [About](#-about)
- [Features](#-features)
- [Installation](#-installation)
- [Usage](#-usage)
- [Troubleshooting](#-troubleshooting)
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

Want support for another player? Feel free to [open an issue](https://github.com/excap3r/music-discord-rich-presence-macos/issues) to request it.

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
</table>

---

## 📥 Installation

### 📋 Requirements

- 🖥️ macOS 10.13 or higher
- 💬 Discord desktop app
- 🎵 One of the supported music players

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

### 💿 Installation

1. Download the latest DMG from the [Releases](https://github.com/excap3r/music-discord-rich-presence-macos/releases) page
2. Open the DMG file
3. Drag the Music Discord Rich Presence app to your Applications folder
4. Launch Music Discord Rich Presence from your Applications folder
5. **Important:** On first launch, macOS may block the app with a message "Music Discord Rich Presence Not Opened" This is normal for apps not from the App Store.
   - Click "Done" on the warning popup
   - Open System Settings → Privacy & Security
   - Scroll down to find the message about the blocked app
   - Click "Open Anyway" button
   - Confirm in the next dialog by clicking "Open Anyway"
6. You'll see the 🎵 icon in your menu bar when the app is running

---

## 🎮 Usage

### 🚀 Quick Start

1. ⬇️ Download and install the app
2. 🔐 Grant permissions when prompted
3. 🎵 Play music in a supported player
4. 💬 See your music status appear in Discord

### 📊 Menu Bar Options

Click the menu bar icon (🎵) to see:

- **📝 Playing**: Shows the currently playing song
- **👤 Artist**: Shows the artist
- **🎵 Player**: Shows which music player is active
- **🔗 Discord**: Shows the connection status
- **⏱️ Update Interval**: Change how often the status updates (5, 10, or 30 seconds)
- **ℹ️ About**: Information about the application
- **❌ Quit**: Exit the application

### 🔗 Discord Setup

To ensure Discord integration works properly:

1. Make sure Discord desktop app is running
2. In Discord, go to User Settings > Activity Settings
3. Ensure "Display current activity as a status message" is enabled

### ⏰ Auto-Launch on Startup

To make the app start automatically when you log in:

1. Open System Settings > General > Login Items
2. Click the + button
3. Browse to your Applications folder
4. Select Music Discord Rich Presence and click "Open"

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
- Try running nowplaying-cli manually to see if it detects your player:
  ```bash
  nowplaying-cli get
  ```
</details>

<details>
<summary><b>Application crashes or freezes</b></summary>

- Check the log file (`music_rpc.log`) for error messages
- Make sure you have the latest version of the app
- For macOS Sonoma and higher, ensure you've granted all necessary permissions
</details>

### 🗑️ Uninstallation

1. Open the Applications folder in Finder
2. Drag Music Discord Rich Presence to the Trash
3. Empty the Trash

---

## ❓ Frequently Asked Questions

<details>
<summary><b>How does the app detect what I'm listening to?</b></summary>

The app uses macOS Media Remote API to get information about currently playing media.
</details>

<details>
<summary><b>Will this work with browser-based players?</b></summary>

Currently, the app works best with desktop applications. Browser-based players may be detected in some cases but with limited information.
</details>

<details>
<summary><b>Does this app collect any personal data?</b></summary>

No. The app only reads information about your currently playing music and sends it to Discord's Rich Presence API.
</details>

<details>
<summary><b>Why does the app need Accessibility and Screen Recording permissions?</b></summary>

These permissions are required to detect music players when using the Media Remote API.
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
