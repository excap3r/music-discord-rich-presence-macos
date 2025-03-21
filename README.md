# Deezer RPC

<div align="center">

![Deezer RPC](deezer_rpc.png)

[![Python](https://img.shields.io/badge/Python-3.6%2B-blue)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-MIT-green)](LICENSE)
[![Discord](https://img.shields.io/badge/Discord-Rich%20Presence-7289DA)](https://discord.com/)
[![Deezer](https://img.shields.io/badge/Deezer-Music-EF5466)](https://www.deezer.com/)

*Show your Deezer music in Discord with style!*

</div>

## ✨ Overview

Deezer RPC is a lightweight application that displays your currently playing Deezer music on Discord through Rich Presence integration. Let your friends see what you're listening to in real-time with artist information, track titles, and timestamps.

## 🎵 Features

- **Real-time Music Display**: Shows your current Deezer tracks on Discord in real-time
- **Song Details**: Displays song title, artist name, and album
- **Time Tracking**: Shows elapsed time and duration of the current track
- **Automatic Detection**: Seamlessly detects when Deezer is active
- **Low Resource Usage**: Minimal impact on system performance
- **Cross-platform**: Works on macOS and Windows

## 📋 Requirements

- Python 3.6 or higher
- Deezer desktop application (installed and running)
- Discord desktop application (installed and running)
- Internet connection for Discord Rich Presence updates

## 🚀 Installation

### Easy Method

1. Clone this repository:
   ```bash
   git clone https://github.com/yourusername/deezer-rpc.git
   cd deezer-rpc
   ```

2. Install the required dependencies:
   ```bash
   pip install -r requirements.txt
   ```

### Virtual Environment (Recommended)

For a cleaner installation, use a virtual environment:

```bash
# Create a virtual environment
python -m venv venv

# Activate the virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

## 🎮 Usage

1. Ensure Discord is running and the "Display current activity as a status message" setting is enabled
2. Make sure Deezer is running and playing music
3. Launch Deezer RPC:
   ```bash
   python main.py
   ```

The application will run in the background and automatically update your Discord status with your current Deezer track information.

To stop the application, press `Ctrl+C` in the terminal window.

## ⚙️ Configuration

You can customize Deezer RPC by editing the configuration in `deezer_rpc/utils/config.py`:

| Setting | Description |
|---------|-------------|
| `UPDATE_INTERVAL` | How frequently to update Discord presence (in seconds) |
| `CLIENT_ID` | Discord application client ID |
| `LOG_LEVEL` | Logging detail level (DEBUG, INFO, WARNING, ERROR) |
| `SHOW_TIME_REMAINING` | Whether to display time remaining or elapsed |

## 🔍 Troubleshooting

- **Discord status not updating:**
  - Ensure both Discord and Deezer applications are running
  - Check that Discord's game activity setting is enabled in User Settings > Activity Status
  - Restart Discord if the Rich Presence doesn't appear after a few minutes

- **Application crashes:**
  - Check the log file `deezer_rpc.log` for detailed error messages
  - Make sure you've installed all dependencies with `pip install -r requirements.txt`
  - Ensure you're using Python 3.6 or higher

- **High CPU usage:**
  - Try increasing the update interval in the configuration file

## 🔄 Updating

To update to the latest version:

```bash
git pull
pip install -r requirements.txt
```

## 📜 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## ��‍💻 Author

**Jakub Sladek**

## 🤝 Contributing

Contributions, issues, and feature requests are welcome! Feel free to check the [issues page](https://github.com/yourusername/deezer-rpc/issues).

---

<div align="center">
Made with ❤️ for Deezer and Discord users
</div>
