# Wizard Voice Assistant - User Manual

## Table of Contents

1. [Introduction](#introduction)
2. [Getting Started](#getting-started)
3. [Basic Usage](#basic-usage)
4. [Voice Commands](#voice-commands)
5. [Configuration](#configuration)
6. [Advanced Features](#advanced-features)
7. [Troubleshooting](#troubleshooting)
8. [Tips and Best Practices](#tips-and-best-practices)

## Introduction

Wizard is a professional-grade AI voice assistant designed to provide comprehensive voice-controlled functionality for your computer. Unlike cloud-based assistants, Wizard operates entirely offline, ensuring your privacy while delivering powerful features including:

- **System Control**: Launch applications, manage windows, control system functions
- **Media Management**: Control volume, playback, and media applications
- **File Operations**: Search, create, move, and manage files and folders
- **Productivity Tools**: Timers, reminders, notes, and calendar management
- **Information Services**: Weather, news, calculations, and knowledge queries
- **Smart Home Integration**: Control IoT devices and smart home systems
- **Entertainment**: Jokes, games, music recommendations, and interactive content
- **Automation**: Custom routines and scheduled tasks

## Getting Started

### First Launch

1. **Start Wizard**: Run `python start_wizard.py` or use the desktop shortcut
2. **Initial Setup**: If this is your first time, Wizard will guide you through basic configuration
3. **Wake Word**: Say "Hey Wizard" or "Wizard" to activate listening mode
4. **First Command**: Try saying "What time is it?" or "Hello Wizard"

### Understanding the Interface

Wizard operates primarily through voice interaction, but provides visual feedback:

- **Listening Indicator**: Shows when Wizard is actively listening
- **Status Messages**: Displays command results and system status
- **Configuration Interface**: Accessible through the configuration tool

### Basic Interaction Flow

1. **Activation**: Say your wake word ("Hey Wizard" or "Wizard")
2. **Command**: Speak your command clearly
3. **Processing**: Wizard processes and executes the command
4. **Response**: Wizard provides audio and/or visual feedback
5. **Standby**: Returns to listening for the next wake word

## Basic Usage

### Wake Words and Activation

Wizard uses wake words to know when you want to interact:

- **Default Wake Words**: "Hey Wizard", "Wizard"
- **Custom Wake Words**: Configure your own in settings
- **Sensitivity**: Adjust detection sensitivity for your environment

**Example Interactions:**
```
You: "Hey Wizard"
Wizard: "Yes, how can I help you?"
You: "What time is it?"
Wizard: "It's 3:45 PM"
```

### Speaking to Wizard

**Best Practices:**
- Speak clearly and at normal volume
- Use natural language - no need for robotic commands
- Wait for Wizard to finish responding before the next command
- Be specific when possible (e.g., "Open Chrome" vs "Open browser")

**Natural Language Examples:**
- "Set a timer for 10 minutes"
- "Remind me to call John at 3 PM"
- "Play some music"
- "What's the weather like?"
- "Open my documents folder"

## Voice Commands

### System Control

**Application Management:**
- "Open [application name]" - Launch applications
- "Close [application name]" - Close applications
- "Switch to [application]" - Switch between windows
- "Minimize/Maximize window" - Window control

**System Operations:**
- "Shut down computer" - System shutdown (with confirmation)
- "Restart computer" - System restart (with confirmation)
- "Lock screen" - Lock the computer
- "Take a screenshot" - Capture screen

**Examples:**
```
"Open Calculator"
"Close Chrome"
"Minimize this window"
"Lock my computer"
```

### Media and Volume Control

**Volume Control:**
- "Set volume to [number]" - Set specific volume level
- "Volume up/down" - Adjust volume incrementally
- "Mute/Unmute" - Toggle audio mute

**Media Playback:**
- "Play music" - Start music playback
- "Pause/Resume" - Control playback
- "Next/Previous song" - Navigate tracks
- "Open Spotify" - Launch music applications

**Examples:**
```
"Set volume to 50"
"Turn the volume up"
"Play some jazz music"
"Skip this song"
```

### File Management

**File Operations:**
- "Find [filename]" - Search for files
- "Open [filename]" - Open specific files
- "Create folder [name]" - Create new folders
- "Delete [filename]" - Delete files (with confirmation)

**Navigation:**
- "Open Documents folder" - Navigate to folders
- "Show recent files" - Display recent files
- "What's in this folder?" - List folder contents

**Examples:**
```
"Find my presentation"
"Open the budget spreadsheet"
"Create a folder called Projects"
"Show me recent documents"
```

### Productivity Features

**Timers and Reminders:**
- "Set timer for [duration]" - Create countdown timers
- "Remind me to [task] at [time]" - Schedule reminders
- "Set alarm for [time]" - Create alarms
- "Cancel timer" - Stop active timers

**Notes and Tasks:**
- "Take a note: [content]" - Voice-to-text notes
- "Add to my todo list: [task]" - Task management
- "Read my notes" - Review saved notes
- "What's on my todo list?" - List tasks

**Examples:**
```
"Set a timer for 25 minutes"
"Remind me to call the dentist at 2 PM"
"Take a note: Meeting with Sarah tomorrow"
"Add buy groceries to my todo list"
```

### Information and Knowledge

**Time and Date:**
- "What time is it?" - Current time
- "What's today's date?" - Current date
- "What day is it?" - Day of the week

**Calculations:**
- "Calculate [expression]" - Mathematical calculations
- "What's [number] percent of [number]?" - Percentage calculations
- "Convert [amount] [unit] to [unit]" - Unit conversions

**Knowledge Queries:**
- "Define [word]" - Word definitions
- "Tell me about [topic]" - General knowledge
- "What's the capital of [country]?" - Factual questions

**Examples:**
```
"What time is it?"
"Calculate 15 percent of 200"
"Convert 100 fahrenheit to celsius"
"Define artificial intelligence"
```

### Entertainment

**Games and Fun:**
- "Tell me a joke" - Random jokes
- "Flip a coin" - Coin flip game
- "Roll a dice" - Dice roll
- "Give me a fun fact" - Interesting trivia

**Recommendations:**
- "Recommend a movie" - Movie suggestions
- "Suggest some music" - Music recommendations
- "Tell me a riddle" - Interactive riddles

**Examples:**
```
"Tell me a joke"
"Flip a coin"
"Recommend a good comedy movie"
"Give me a fun fact about space"
```

## Configuration

### Basic Settings

Access configuration through:
- **Interactive Menu**: Run `python configure.py`
- **Configuration File**: Edit `config/wizard_config.json`
- **Voice Commands**: "Change settings" or "Open configuration"

### Key Configuration Options

**Assistant Identity:**
- Assistant name (default: "Wizard")
- Wake words and phrases
- Response personality and style

**Voice Settings:**
- Voice gender (male/female/neutral)
- Speech speed (0.5-2.0)
- Volume level (0.0-1.0)

**Security Settings:**
- Confirmation requirements for critical operations
- Safe mode (limited command access)
- Password protection for restricted commands

**Application Paths:**
- Custom paths for frequently used applications
- Default applications for file types
- Integration preferences

### Example Configuration

```json
{
  "assistant_name": "Wizard",
  "wake_words": ["Hey Wizard", "Wizard"],
  "voice": {
    "gender": "female",
    "speed": 1.0,
    "volume": 0.8
  },
  "security": {
    "require_confirmation": true,
    "safe_mode": false
  },
  "applications": {
    "browser": "C:\\Program Files\\Google\\Chrome\\chrome.exe",
    "music_player": "spotify"
  }
}
```

## Advanced Features

### Custom Routines

Create multi-step routines for common tasks:

**Morning Routine:**
```
"Good morning" triggers:
- Weather report
- News headlines
- Calendar for today
- Open email and calendar apps
```

**Work Setup:**
```
"Start work" triggers:
- Open development tools
- Set focus mode
- Start productivity timer
- Play background music
```

### Smart Home Integration

Control compatible smart devices:
- Smart lights and switches
- Thermostats and climate control
- Smart locks and security systems
- Entertainment systems

**Examples:**
```
"Turn on the living room lights"
"Set temperature to 72 degrees"
"Lock the front door"
"Turn on the TV"
```

### Automation and Scheduling

**Scheduled Tasks:**
- Daily reminders and notifications
- Automatic backups and maintenance
- Recurring calendar events
- System optimization routines

**Batch Operations:**
- Multiple file operations
- Bulk application management
- System cleanup routines

### Learning and Personalization

Wizard learns from your interactions to:
- Improve command recognition
- Personalize responses
- Suggest relevant actions
- Optimize performance

## Troubleshooting

### Common Issues

**Wizard Not Responding:**
1. Check microphone permissions
2. Verify audio input device
3. Restart Wizard application
4. Check system resources

**Poor Voice Recognition:**
1. Reduce background noise
2. Speak more clearly
3. Adjust microphone sensitivity
4. Retrain voice model if available

**Application Launch Failures:**
1. Verify application paths in configuration
2. Check file permissions
3. Update application database
4. Use full application paths

**Performance Issues:**
1. Close unnecessary applications
2. Check system resources (CPU, memory)
3. Restart Wizard
4. Update to latest version

### Getting Help

**Log Files:**
- Check `logs/wizard.log` for detailed information
- Error logs in `logs/wizard_errors.log`
- Enable debug mode for verbose logging

**Support Resources:**
- Documentation in `docs/` folder
- FAQ section for common questions
- Community forums and discussions
- Issue tracker for bug reports

## Tips and Best Practices

### Optimal Usage

**Environment Setup:**
- Use in quiet environment when possible
- Position microphone appropriately
- Ensure stable system performance
- Keep Wizard updated

**Command Efficiency:**
- Learn common command patterns
- Use specific application names
- Combine related commands when possible
- Create custom routines for frequent tasks

**Privacy and Security:**
- Review security settings regularly
- Use confirmation for critical operations
- Keep sensitive data encrypted
- Monitor system access logs

### Customization Tips

**Personalization:**
- Customize wake words for your preference
- Adjust voice settings for comfort
- Configure application shortcuts
- Create personal routines

**Performance Optimization:**
- Disable unused features
- Optimize audio settings
- Regular system maintenance
- Monitor resource usage

### Advanced Usage

**Power User Features:**
- Command chaining and sequences
- Advanced automation rules
- Custom plugin development
- Integration with external systems

**Productivity Enhancement:**
- Workflow automation
- Context-aware responses
- Intelligent suggestions
- Performance analytics

---

## Conclusion

Wizard Voice Assistant is designed to enhance your productivity and provide seamless voice control over your computer. This manual covers the essential features and usage patterns, but Wizard's capabilities continue to expand through updates and community contributions.

For the latest information, additional features, and community support, visit the project documentation and community resources.

**Happy voice computing with Wizard!** 🧙‍♂️