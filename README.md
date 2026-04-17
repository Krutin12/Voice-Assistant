# Wizard Voice Assistant 🧠🎤

A comprehensive offline-first AI Windows voice assistant built with Python, Tkinter, and Flask. Control apps, websites, MS Office, files, reminders, alarms, and system tasks using voice.

## Project Overview
⚙️ Works offline for many features with deep Windows automation.
💬 Speech recognition + text-to-speech for natural interaction.
🚀 A personal AI assistant that simplifies daily laptop use.

## Project Structure

```
wizard/
├── __init__.py                 # Package initialization
├── main.py                     # Main application entry point
├── audio/                      # Audio processing modules
│   └── __init__.py
├── commands/                   # Command processing and routing
│   └── __init__.py
├── utils/                      # Utility functions and helpers
│   ├── __init__.py
│   ├── config_manager.py       # Configuration management
│   └── logger.py               # Logging system
└── data/                       # Data management and storage
    └── __init__.py

config/                         # Configuration files
logs/                          # Log files
requirements.txt               # Python dependencies
```

## Features

- **Offline-First**: Works without internet connection for core functionality
- **Configurable**: JSON-based configuration with validation
- **Comprehensive Logging**: Multi-level logging with file rotation
- **Modular Architecture**: Clean separation of concerns
- **Cross-Platform Support**: Optimized for Windows

## Installation

1. Clone the repository
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Run the application:
   ```bash
   python wizard/main.py
   ```

## Configuration

The system uses JSON configuration files stored in the `config/` directory. Configuration includes:

- Voice settings (gender, speed, pitch, volume)
- Wake words and assistant name
- Security settings and access control
- User preferences and personalization
- Application paths and integrations

## Logging

Logs are stored in the `logs/` directory with automatic rotation:
- `wizard.log` - All application logs
- `wizard_errors.log` - Error logs only

Log levels: DEBUG, INFO, WARNING, ERROR, CRITICAL
