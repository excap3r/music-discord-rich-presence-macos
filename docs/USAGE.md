# Deezer RPC Usage Guide

This document provides detailed instructions on how to use Deezer RPC.

## Installation

### Standard Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/deezer-rpc.git
cd deezer-rpc

# Install the package
pip install .
```

### Development Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/deezer-rpc.git
cd deezer-rpc

# Install in development mode
pip install -e .
```

## Basic Usage

After installation, you can run Deezer RPC in two ways:

### Using the Command Line

If you installed the package:

```bash
deezer-rpc
```

If you're running from the repository:

```bash
python main.py
```

### Application Behavior

1. When started, Deezer RPC will look for an open Deezer window
2. If found, it will begin tracking your currently playing music
3. Your Discord status will update to show the current song, artist, and remaining time
4. The application will continue running in the background until stopped (Ctrl+C)

## Configuration

The main configuration settings can be found in `deezer_rpc/config/settings.py`.

### Available Settings

- `DISCORD_CLIENT_ID`: Discord application client ID
- `DEFAULT_UPDATE_INTERVAL`: How often to check for song changes (in seconds)
- `ACTIVATE_DEEZER`: Whether to activate the Deezer window
- `USE_ALBUM_ART`: Whether to use album art from the Deezer API
- `LOG_LEVEL`: Logging detail level (DEBUG, INFO, WARNING, ERROR)

## Troubleshooting

### Common Issues

1. **Discord status not updating**
   - Ensure Discord is running and you've enabled game activity
   - Check that the Discord client ID is correct
   - Verify that Deezer is properly playing music

2. **Application crashes**
   - Check the log file for detailed error messages
   - Ensure all dependencies are installed correctly
   - Make sure your Python version is 3.6 or higher

3. **High resource usage**
   - Increase the update interval to reduce CPU usage
   - Check for conflicting applications

For more detailed troubleshooting, consult the log file at `deezer_rpc.log`. 