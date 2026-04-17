# Wizard Voice Assistant - Frequently Asked Questions (FAQ)

## General Questions

### What is Wizard Voice Assistant?

Wizard is a professional-grade AI voice assistant that runs entirely offline on your computer. It provides comprehensive voice-controlled functionality including system control, file management, productivity tools, entertainment, and smart home integration - all without sending your data to external servers.

### How is Wizard different from Alexa, Siri, or Google Assistant?

**Key Differences:**
- **Privacy**: Wizard operates completely offline - no data sent to cloud services
- **Customization**: Fully customizable and extensible
- **Open Source**: Transparent code you can inspect and modify
- **No Subscription**: Free to use with no recurring costs
- **Local Control**: Works without internet connection

### What can Wizard do?

Wizard can:
- Control your computer (open apps, manage windows, system operations)
- Manage files and folders
- Control media playback and volume
- Set timers, reminders, and alarms
- Take notes and manage tasks
- Answer questions and provide information
- Perform calculations and conversions
- Tell jokes and provide entertainment
- Control smart home devices
- Execute custom automation routines

### Is Wizard really free?

Yes! Wizard is completely free and open-source. There are no hidden costs, subscriptions, or premium features. You have full access to all functionality.

---

## Installation and Setup

### What are the system requirements?

**Minimum Requirements:**
- Python 3.8 or higher
- 4GB RAM
- 2GB free disk space
- Microphone and speakers/headphones
- Windows 10+, macOS 10.14+, or Linux (Ubuntu 18.04+)

**Recommended:**
- Python 3.9+
- 8GB RAM
- Dedicated USB microphone
- SSD storage

### How do I install Wizard?

**Quick Installation:**
```bash
# Clone or download the repository
cd wizard-voice-assistant

# Run quick install
python install.py

# Start Wizard
python start_wizard.py
```

**Full Installation with Configuration:**
```bash
# Run full setup
python setup.py

# This will:
# - Install dependencies
# - Run configuration wizard
# - Download required models
# - Set up startup integration
```

### Do I need an internet connection?

**Initial Setup**: Internet required to download dependencies and models

**Daily Use**: No internet required - Wizard works completely offline

**Optional Features**: Some features (web search, online weather) require internet but have offline alternatives

### Can I use Wizard on multiple computers?

Yes! You can install Wizard on as many computers as you like. Each installation can have its own configuration, or you can sync configurations across machines.

---

## Usage Questions

### How do I activate Wizard?

Say your wake word (default: "Hey Wizard" or "Wizard"). Wizard will respond and wait for your command. You can customize wake words in the configuration.

### What if Wizard doesn't hear me?

**Troubleshooting Steps:**
1. Check microphone is connected and working
2. Verify microphone permissions
3. Adjust wake word sensitivity in settings
4. Reduce background noise
5. Speak louder or move closer to microphone
6. Try different wake words

### Can I change Wizard's voice?

Yes! You can customize:
- Voice gender (male/female/neutral)
- Speech speed (0.5x to 2.0x)
- Volume level
- Voice engine (if multiple TTS engines installed)

Configure through: `python configure.py` or edit `config/wizard_config.json`

### How do I teach Wizard new commands?

**For Developers:**
Create custom command handlers in `wizard/commands/` directory. See the Developer Guide for details.

**For Users:**
Use the automation system to create custom routines that combine existing commands.

### Can Wizard understand different accents?

Wizard uses speech recognition models that support various accents. For best results:
- Use clear pronunciation
- Adjust recognition settings for your accent
- Consider training custom models for heavy accents

### What languages does Wizard support?

Currently, Wizard primarily supports English. However, the architecture supports multiple languages. You can:
- Configure speech recognition for other languages
- Add language-specific command handlers
- Contribute translations to the project

---

## Features and Capabilities

### Can Wizard control any application?

Wizard can control:
- **Built-in**: Applications in system PATH
- **Configured**: Applications with paths in configuration
- **Common Apps**: Pre-configured popular applications

To add new applications, update the configuration with application paths.

### Does Wizard work with smart home devices?

Yes! Wizard supports:
- Smart lights (Philips Hue, LIFX, etc.)
- Smart thermostats
- Smart locks
- Smart plugs
- Other devices via MQTT or compatible protocols

Configuration required for specific devices.

### Can Wizard send emails or messages?

Wizard can:
- Open email applications
- Create calendar events
- Take notes and reminders
- Execute scripts that send emails (with configuration)

Direct email/messaging integration requires additional setup.

### Can Wizard browse the web?

Wizard can:
- Open web browsers
- Navigate to specific URLs
- Search the web (requires internet)
- Access offline Wikipedia database
- Use cached web content

### How accurate is Wizard's speech recognition?

Accuracy depends on:
- **Microphone Quality**: Better microphones = better accuracy
- **Environment**: Quiet environments improve recognition
- **Speech Clarity**: Clear speech improves accuracy
- **Model Quality**: Better models = better recognition

Typical accuracy: 85-95% in good conditions

---

## Privacy and Security

### Is my data safe with Wizard?

Yes! Wizard:
- Processes all data locally
- Never sends data to external servers
- Stores data only on your computer
- Gives you full control over your data

### What data does Wizard collect?

Wizard stores locally:
- Configuration settings
- Voice command history (optional)
- Notes and reminders
- User preferences
- Application usage patterns (for learning)

All data stays on your computer. You can delete it anytime.

### Can I use Wizard in a secure environment?

Yes! Wizard is suitable for secure environments because:
- No external network communication required
- No cloud dependencies
- Transparent, auditable code
- Configurable security settings

### How do I protect sensitive commands?

Enable security features:
- Require confirmation for critical operations
- Enable safe mode (limited commands)
- Set password protection for restricted commands
- Configure command restrictions

---

## Troubleshooting

### Wizard isn't responding to my wake word

**Common Solutions:**
1. Check microphone is working
2. Verify Wizard is running
3. Increase wake word sensitivity
4. Reduce background noise
5. Try alternative wake words
6. Restart Wizard

See Troubleshooting Guide for detailed solutions.

### Commands aren't being recognized

**Try:**
1. Speak more clearly
2. Use exact command phrases from documentation
3. Check if application names are correct
4. Verify required applications are installed
5. Review command syntax in Command Reference

### Wizard is using too much CPU/memory

**Optimization:**
1. Reduce wake word detection sensitivity
2. Disable unused features
3. Close other applications
4. Restart Wizard periodically
5. Check for memory leaks in logs

### Audio quality is poor

**Improvements:**
1. Use better microphone
2. Adjust microphone position
3. Reduce background noise
4. Update audio drivers
5. Adjust audio settings in configuration

---

## Customization

### Can I change the assistant's name?

Yes! Edit configuration:
```json
{
  "assistant_name": "YourName"
}
```

Or run: `python configure.py`

### Can I create custom wake words?

Yes! Configure multiple wake words:
```json
{
  "wake_words": ["Hey Assistant", "Computer", "Jarvis"]
}
```

### How do I create custom routines?

**Example Morning Routine:**
```python
# In configuration or through voice commands
"Good morning" triggers:
- "What's the weather?"
- "What's my schedule today?"
- "Open email"
- "Play morning playlist"
```

See User Manual for detailed routine creation.

### Can I add custom responses?

Yes! Edit the AI Brain knowledge base or create custom command handlers. See Developer Guide for implementation details.

---

## Performance

### How much resources does Wizard use?

**Typical Usage:**
- CPU: 5-15% (idle), 20-40% (active)
- RAM: 200-500 MB
- Disk: 1-2 GB (including models)

**Factors Affecting Performance:**
- Wake word detection method
- Speech recognition model size
- Number of active features
- System specifications

### Can I run Wizard on a Raspberry Pi?

Yes, but with considerations:
- Use lightweight models
- Reduce feature set
- Optimize for ARM architecture
- Expect slower performance
- Minimum: Raspberry Pi 4 with 4GB RAM

### How can I improve response time?

**Optimization Tips:**
1. Use faster speech recognition models
2. Preload frequently used data
3. Enable caching
4. Reduce logging verbosity
5. Use SSD storage
6. Close unnecessary applications

---

## Development and Contribution

### Can I contribute to Wizard?

Yes! Contributions welcome:
- Bug reports and fixes
- New features
- Documentation improvements
- Translations
- Testing and feedback

See Contributing Guide for details.

### How do I report bugs?

1. Check existing issues first
2. Gather system information
3. Collect relevant log files
4. Create detailed bug report
5. Submit to issue tracker

Use the bug report template in Troubleshooting Guide.

### Can I create plugins for Wizard?

Yes! Wizard supports plugins. See Developer Guide for:
- Plugin architecture
- Creating custom plugins
- Plugin API reference
- Example plugins

### Is there a developer community?

Yes! Join:
- GitHub discussions
- Community forums
- Developer chat
- Contribution channels

---

## Advanced Features

### What is the AI Brain?

The AI Brain is Wizard's local knowledge base and response generation system. It:
- Stores facts and information
- Generates contextual responses
- Learns from interactions
- Maintains conversation context

All processing happens locally.

### Can Wizard learn from my usage?

Yes! Wizard can:
- Learn command preferences
- Adapt to your speech patterns
- Remember frequently used applications
- Personalize responses
- Optimize performance

Learning is optional and configurable.

### What automation features are available?

**Automation Options:**
- Custom routines (multi-command sequences)
- Scheduled tasks
- Conditional triggers
- Batch operations
- Event-based actions

### Can I integrate Wizard with other software?

Yes! Integration options:
- Command-line interface
- Python API
- Plugin system
- Configuration files
- Inter-process communication

---

## Comparison Questions

### Wizard vs. Commercial Assistants?

**Wizard Advantages:**
- Complete privacy (offline)
- No subscription costs
- Full customization
- Open source
- No vendor lock-in

**Commercial Advantages:**
- Larger knowledge bases
- More third-party integrations
- Professional support
- Regular updates
- Ecosystem integration

### Wizard vs. Other Open Source Assistants?

Wizard focuses on:
- Professional-grade features
- Comprehensive offline functionality
- Extensive documentation
- Active development
- User-friendly setup

### Should I use Wizard or a commercial assistant?

**Choose Wizard if you:**
- Value privacy and data control
- Want offline functionality
- Need customization
- Prefer open source
- Want no recurring costs

**Choose Commercial if you:**
- Need extensive third-party integrations
- Want professional support
- Prefer plug-and-play setup
- Need cloud synchronization
- Want ecosystem integration

---

## Future Development

### What features are planned?

**Roadmap includes:**
- Additional language support
- Improved AI capabilities
- More smart home integrations
- Mobile companion app
- Cloud sync (optional)
- Enhanced automation
- Better voice training

### How often is Wizard updated?

Updates depend on:
- Community contributions
- Bug reports
- Feature requests
- Security issues

Check repository for latest releases.

### Can I request features?

Yes! Submit feature requests:
1. Check existing requests
2. Describe use case
3. Explain benefits
4. Submit to issue tracker

Popular requests are prioritized.

---

## Getting Help

### Where can I find more information?

**Documentation:**
- User Manual (comprehensive guide)
- Command Reference (all commands)
- Developer Guide (extending Wizard)
- Troubleshooting Guide (problem solving)

**Community:**
- GitHub repository
- Discussion forums
- Issue tracker
- Community chat

### How do I get support?

**Self-Help:**
1. Read documentation
2. Check FAQ (this document)
3. Review troubleshooting guide
4. Search existing issues

**Community Support:**
1. Ask in forums
2. Submit issue report
3. Join community chat

**Professional Support:**
- Available for enterprise users
- Custom development services
- Training and consulting

### What if my question isn't answered here?

1. Search documentation
2. Check community forums
3. Ask in community chat
4. Submit question to issue tracker
5. Contact maintainers

---

## Miscellaneous

### Can I use Wizard commercially?

Yes! Wizard's license allows commercial use. Check the LICENSE file for specific terms.

### Is Wizard suitable for accessibility needs?

Yes! Wizard can help users with:
- Mobility limitations
- Visual impairments
- Repetitive strain injuries
- Other accessibility needs

Customization available for specific requirements.

### Can children use Wizard?

Yes, with supervision. Consider:
- Enabling safe mode
- Restricting certain commands
- Monitoring usage
- Age-appropriate content settings

### Does Wizard work offline completely?

Core features work offline:
- Voice recognition
- System control
- File management
- Calculations
- Entertainment
- Productivity tools

Optional online features:
- Web search
- Real-time weather
- News updates
- Online translations

### How do I uninstall Wizard?

**Complete Removal:**
```bash
# Remove application files
rm -rf wizard-voice-assistant/

# Remove configuration (optional)
rm -rf ~/.wizard/

# Remove startup entries (if configured)
# Windows: Remove from Registry
# macOS: Remove LaunchAgent
# Linux: Remove autostart entry
```

### Can I run multiple instances of Wizard?

Not recommended. Multiple instances may:
- Conflict for microphone access
- Cause confusion with wake words
- Waste system resources

Use one instance with comprehensive configuration instead.

---

## Still Have Questions?

If your question isn't answered here:

1. **Check Documentation**: Read the full documentation set
2. **Search Issues**: Look for similar questions in the issue tracker
3. **Ask Community**: Post in community forums or chat
4. **Contact Support**: Reach out through official channels

We're here to help make your Wizard experience great!