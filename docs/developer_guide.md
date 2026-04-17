# Wizard Voice Assistant - Developer Guide

## Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Development Environment Setup](#development-environment-setup)
3. [Code Structure](#code-structure)
4. [Extending Wizard](#extending-wizard)
5. [Creating Custom Commands](#creating-custom-commands)
6. [Plugin Development](#plugin-development)
7. [API Reference](#api-reference)
8. [Testing](#testing)
9. [Contributing](#contributing)
10. [Best Practices](#best-practices)

---

## Architecture Overview

### System Design

Wizard follows a modular architecture with clear separation of concerns:

```
┌─────────────────────────────────────────────────────────────┐
│                    Main Application                         │
│                   (wizard/main.py)                          │
└─────────────────────┬───────────────────────────────────────┘
                      │
┌─────────────────────┴───────────────────────────────────────┐
│                Audio Processing Layer                       │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────────────┐   │
│  │ Wake Word   │ │   Speech    │ │   Text-to-Speech    │   │
│  │  Engine     │ │ Recognition │ │      Engine         │   │
│  └─────────────┘ └─────────────┘ └─────────────────────┘   │
└─────────────────────┬───────────────────────────────────────┘
                      │
┌─────────────────────┴───────────────────────────────────────┐
│               Command Processing Layer                      │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────────────┐   │
│  │  Command    │ │   Entity    │ │     AI Brain        │   │
│  │   Router    │ │  Extractor  │ │   (Knowledge)       │   │
│  └─────────────┘ └─────────────┘ └─────────────────────┘   │
└─────────────────────┬───────────────────────────────────────┘
                      │
┌─────────────────────┴───────────────────────────────────────┐
│                  Service Layer                              │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────────────┐   │
│  │   System    │ │    Media    │ │      File           │   │
│  │ Controller  │ │ Controller  │ │     Manager         │   │
│  └─────────────┘ └─────────────┘ └─────────────────────┘   │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────────────┐   │
│  │Productivity │ │ Smart Home  │ │   Entertainment     │   │
│  │  Manager    │ │ Controller  │ │     System          │   │
│  └─────────────┘ └─────────────┘ └─────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

### Core Components

1. **Audio Processing**: Handles wake word detection, speech recognition, and text-to-speech
2. **Command Processing**: Parses natural language and routes commands
3. **Service Layer**: Implements specific functionality (system control, media, files, etc.)
4. **Configuration Management**: Handles settings and user preferences
5. **Data Layer**: Manages local knowledge bases and user data

### Key Design Principles

- **Modularity**: Each component has a single responsibility
- **Extensibility**: Easy to add new commands and features
- **Offline-First**: All core functionality works without internet
- **Privacy**: No data sent to external services
- **Performance**: Optimized for real-time voice interaction

---

## Development Environment Setup

### Prerequisites

- Python 3.8 or higher
- Git for version control
- Audio input/output devices
- Platform-specific development tools

### Installation

1. **Clone Repository**:
```bash
git clone <repository-url>
cd wizard-voice-assistant
```

2. **Create Virtual Environment**:
```bash
python -m venv wizard_env
source wizard_env/bin/activate  # Linux/macOS
# or
wizard_env\Scripts\activate     # Windows
```

3. **Install Dependencies**:
```bash
pip install -r requirements.txt
pip install -r requirements-dev.txt  # Development dependencies
```

4. **Install Development Tools**:
```bash
pip install black flake8 pytest pytest-cov mypy
```

### Development Configuration

Create a development configuration file:

```json
{
  "assistant_name": "DevWizard",
  "wake_words": ["Hey Dev", "DevWizard"],
  "debug_mode": true,
  "log_level": "DEBUG",
  "development": {
    "auto_reload": true,
    "test_mode": false,
    "mock_audio": false
  }
}
```

---

## Code Structure

### Directory Layout

```
wizard-voice-assistant/
├── wizard/                     # Main application package
│   ├── __init__.py
│   ├── main.py                # Application entry point
│   ├── audio/                 # Audio processing components
│   │   ├── wake_word_engine.py
│   │   ├── speech_recognition.py
│   │   └── text_to_speech.py
│   ├── commands/              # Command handlers and routing
│   │   ├── command_router.py
│   │   ├── entity_extractor.py
│   │   ├── system_handlers.py
│   │   ├── media_handlers.py
│   │   └── ...
│   ├── data/                  # Data management and knowledge
│   │   ├── ai_brain.py
│   │   ├── knowledge_manager.py
│   │   └── ...
│   └── utils/                 # Utility modules
│       ├── config_manager.py
│       ├── logger.py
│       └── ...
├── config/                    # Configuration files
├── docs/                      # Documentation
├── tests/                     # Test suite
├── setup.py                   # Installation script
├── requirements.txt           # Dependencies
└── README.md
```

### Module Organization

**Audio Package** (`wizard/audio/`):
- `wake_word_engine.py`: Wake word detection
- `speech_recognition.py`: Speech-to-text conversion
- `text_to_speech.py`: Text-to-speech synthesis

**Commands Package** (`wizard/commands/`):
- `command_router.py`: Main command routing logic
- `entity_extractor.py`: Extract entities from commands
- `*_handlers.py`: Specific command implementations

**Data Package** (`wizard/data/`):
- `ai_brain.py`: AI response generation
- `knowledge_manager.py`: Local knowledge base
- `*_data.py`: Specific data modules

**Utils Package** (`wizard/utils/`):
- `config_manager.py`: Configuration management
- `logger.py`: Logging utilities
- `error_handler.py`: Error handling

---

## Extending Wizard

### Adding New Command Categories

1. **Create Handler Module**:

```python
# wizard/commands/custom_handlers.py
from typing import Dict, Any
from .base_handler import BaseHandler

class CustomHandler(BaseHandler):
    """Handler for custom commands"""
    
    def __init__(self):
        super().__init__()
        self.commands = {
            "custom_action": self.handle_custom_action,
            "another_action": self.handle_another_action
        }
    
    def handle_custom_action(self, entities: Dict[str, Any]) -> str:
        """Handle custom action command"""
        # Implementation here
        return "Custom action completed"
    
    def handle_another_action(self, entities: Dict[str, Any]) -> str:
        """Handle another custom action"""
        # Implementation here
        return "Another action completed"
    
    def can_handle(self, command: str) -> bool:
        """Check if this handler can process the command"""
        return any(keyword in command.lower() for keyword in self.commands.keys())
```

2. **Register Handler**:

```python
# wizard/commands/command_router.py
from .custom_handlers import CustomHandler

class CommandRouter:
    def __init__(self):
        # ... existing code ...
        self.handlers.append(CustomHandler())
```

### Adding New Data Sources

1. **Create Data Module**:

```python
# wizard/data/custom_data.py
import sqlite3
from typing import List, Dict, Any

class CustomDataManager:
    """Manage custom data source"""
    
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Initialize database schema"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS custom_data (
                    id INTEGER PRIMARY KEY,
                    category TEXT,
                    data TEXT,
                    metadata TEXT
                )
            """)
    
    def get_data(self, category: str) -> List[Dict[str, Any]]:
        """Retrieve data by category"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                "SELECT * FROM custom_data WHERE category = ?",
                (category,)
            )
            return [dict(row) for row in cursor.fetchall()]
    
    def add_data(self, category: str, data: str, metadata: str = None):
        """Add new data entry"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "INSERT INTO custom_data (category, data, metadata) VALUES (?, ?, ?)",
                (category, data, metadata)
            )
```

---

## Creating Custom Commands

### Command Structure

Commands in Wizard follow a consistent pattern:

1. **Intent Recognition**: Identify what the user wants to do
2. **Entity Extraction**: Extract parameters from the command
3. **Validation**: Ensure required parameters are present
4. **Execution**: Perform the requested action
5. **Response**: Provide feedback to the user

### Example: Custom Weather Command

```python
# wizard/commands/weather_handlers.py
import requests
from typing import Dict, Any, Optional
from .base_handler import BaseHandler

class WeatherHandler(BaseHandler):
    """Handle weather-related commands"""
    
    def __init__(self):
        super().__init__()
        self.patterns = {
            r"weather.*in\s+(\w+)": self.get_weather_for_city,
            r"what.*weather": self.get_current_weather,
            r"temperature.*(\w+)": self.get_temperature
        }
    
    def get_current_weather(self, entities: Dict[str, Any]) -> str:
        """Get weather for current location"""
        try:
            # Implementation for current location weather
            weather_data = self._fetch_weather_data()
            return f"Current weather: {weather_data['description']}, {weather_data['temperature']}°F"
        except Exception as e:
            return f"Sorry, I couldn't get the weather information: {str(e)}"
    
    def get_weather_for_city(self, entities: Dict[str, Any]) -> str:
        """Get weather for specific city"""
        city = entities.get('city')
        if not city:
            return "Please specify a city for the weather forecast"
        
        try:
            weather_data = self._fetch_weather_data(city)
            return f"Weather in {city}: {weather_data['description']}, {weather_data['temperature']}°F"
        except Exception as e:
            return f"Sorry, I couldn't get weather for {city}: {str(e)}"
    
    def _fetch_weather_data(self, city: Optional[str] = None) -> Dict[str, Any]:
        """Fetch weather data from local source or API"""
        # Implementation depends on your weather data source
        # This could be a local database, cached data, or API call
        pass
```

### Entity Extraction

```python
# wizard/commands/entity_extractor.py
import re
from typing import Dict, Any, List
from datetime import datetime, timedelta

class EntityExtractor:
    """Extract entities from natural language commands"""
    
    def extract_time(self, text: str) -> Dict[str, Any]:
        """Extract time-related entities"""
        entities = {}
        
        # Time patterns
        time_patterns = {
            r"(\d{1,2}):(\d{2})\s*(am|pm)?": "specific_time",
            r"in\s+(\d+)\s+(minutes?|hours?|seconds?)": "relative_time",
            r"(tomorrow|today|yesterday)": "relative_day"
        }
        
        for pattern, entity_type in time_patterns.items():
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                entities[entity_type] = match.groups()
        
        return entities
    
    def extract_numbers(self, text: str) -> List[float]:
        """Extract numeric values from text"""
        number_pattern = r"\b\d+(?:\.\d+)?\b"
        matches = re.findall(number_pattern, text)
        return [float(match) for match in matches]
    
    def extract_applications(self, text: str) -> List[str]:
        """Extract application names from text"""
        # Common application names and variations
        app_patterns = {
            r"\b(chrome|google chrome)\b": "chrome",
            r"\b(notepad|text editor)\b": "notepad",
            r"\b(calculator|calc)\b": "calculator",
            r"\b(spotify|music)\b": "spotify"
        }
        
        apps = []
        for pattern, app_name in app_patterns.items():
            if re.search(pattern, text, re.IGNORECASE):
                apps.append(app_name)
        
        return apps
```

---

## Plugin Development

### Plugin Architecture

Wizard supports a plugin system for extending functionality:

```python
# wizard/plugins/base_plugin.py
from abc import ABC, abstractmethod
from typing import Dict, Any, List

class BasePlugin(ABC):
    """Base class for Wizard plugins"""
    
    def __init__(self, name: str, version: str):
        self.name = name
        self.version = version
        self.enabled = True
    
    @abstractmethod
    def initialize(self, config: Dict[str, Any]) -> bool:
        """Initialize the plugin"""
        pass
    
    @abstractmethod
    def get_commands(self) -> List[str]:
        """Return list of commands this plugin handles"""
        pass
    
    @abstractmethod
    def handle_command(self, command: str, entities: Dict[str, Any]) -> str:
        """Handle a command"""
        pass
    
    def cleanup(self):
        """Cleanup resources when plugin is disabled"""
        pass
```

### Example Plugin

```python
# wizard/plugins/example_plugin.py
from .base_plugin import BasePlugin
from typing import Dict, Any, List

class ExamplePlugin(BasePlugin):
    """Example plugin demonstrating the plugin system"""
    
    def __init__(self):
        super().__init__("Example Plugin", "1.0.0")
        self.data = {}
    
    def initialize(self, config: Dict[str, Any]) -> bool:
        """Initialize the plugin"""
        try:
            # Plugin initialization code
            self.api_key = config.get('api_key')
            return True
        except Exception as e:
            print(f"Failed to initialize {self.name}: {e}")
            return False
    
    def get_commands(self) -> List[str]:
        """Return supported commands"""
        return [
            "example command",
            "test plugin",
            "plugin status"
        ]
    
    def handle_command(self, command: str, entities: Dict[str, Any]) -> str:
        """Handle plugin commands"""
        if "example command" in command.lower():
            return "Example plugin command executed!"
        elif "test plugin" in command.lower():
            return f"Plugin {self.name} v{self.version} is working!"
        elif "plugin status" in command.lower():
            return f"Plugin status: {'Enabled' if self.enabled else 'Disabled'}"
        else:
            return "Unknown plugin command"
```

### Plugin Manager

```python
# wizard/utils/plugin_manager.py
import os
import importlib
from typing import List, Dict, Any
from wizard.plugins.base_plugin import BasePlugin

class PluginManager:
    """Manage Wizard plugins"""
    
    def __init__(self, plugin_dir: str):
        self.plugin_dir = plugin_dir
        self.plugins: List[BasePlugin] = []
        self.load_plugins()
    
    def load_plugins(self):
        """Load all plugins from plugin directory"""
        if not os.path.exists(self.plugin_dir):
            return
        
        for filename in os.listdir(self.plugin_dir):
            if filename.endswith('.py') and not filename.startswith('__'):
                module_name = filename[:-3]
                try:
                    module = importlib.import_module(f'wizard.plugins.{module_name}')
                    plugin_class = getattr(module, f'{module_name.title()}Plugin')
                    plugin = plugin_class()
                    
                    if plugin.initialize({}):
                        self.plugins.append(plugin)
                        print(f"Loaded plugin: {plugin.name}")
                    
                except Exception as e:
                    print(f"Failed to load plugin {module_name}: {e}")
    
    def handle_command(self, command: str, entities: Dict[str, Any]) -> str:
        """Try to handle command with plugins"""
        for plugin in self.plugins:
            if plugin.enabled and command.lower() in [cmd.lower() for cmd in plugin.get_commands()]:
                return plugin.handle_command(command, entities)
        
        return None  # No plugin handled the command
```

---

## API Reference

### Core Classes

#### CommandRouter

```python
class CommandRouter:
    """Main command routing and processing"""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize router with configuration"""
    
    def process_command(self, text: str) -> str:
        """Process natural language command and return response"""
    
    def register_handler(self, handler: BaseHandler):
        """Register new command handler"""
    
    def get_available_commands(self) -> List[str]:
        """Get list of all available commands"""
```

#### BaseHandler

```python
class BaseHandler(ABC):
    """Base class for command handlers"""
    
    @abstractmethod
    def can_handle(self, command: str) -> bool:
        """Check if handler can process command"""
    
    @abstractmethod
    def handle(self, command: str, entities: Dict[str, Any]) -> str:
        """Process command and return response"""
```

#### ConfigManager

```python
class ConfigManager:
    """Manage application configuration"""
    
    def __init__(self, config_path: str):
        """Initialize with config file path"""
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value"""
    
    def set(self, key: str, value: Any):
        """Set configuration value"""
    
    def save(self):
        """Save configuration to file"""
```

### Audio Processing APIs

#### SpeechRecognizer

```python
class SpeechRecognizer:
    """Speech recognition interface"""
    
    def __init__(self, language: str = "en-US"):
        """Initialize with language setting"""
    
    def recognize(self, audio_data: bytes) -> Tuple[str, float]:
        """Recognize speech and return text with confidence"""
    
    def set_language(self, language: str):
        """Change recognition language"""
```

#### TextToSpeech

```python
class TextToSpeech:
    """Text-to-speech interface"""
    
    def __init__(self, voice: str = "default"):
        """Initialize with voice setting"""
    
    def speak(self, text: str):
        """Convert text to speech and play"""
    
    def save_to_file(self, text: str, filename: str):
        """Save speech to audio file"""
```

---

## Testing

### Test Structure

```
tests/
├── unit/                      # Unit tests
│   ├── test_command_router.py
│   ├── test_handlers.py
│   └── ...
├── integration/               # Integration tests
│   ├── test_voice_workflow.py
│   └── ...
├── fixtures/                  # Test data
│   ├── audio_samples/
│   └── config_samples/
└── conftest.py               # Test configuration
```

### Writing Tests

#### Unit Test Example

```python
# tests/unit/test_command_router.py
import pytest
from wizard.commands.command_router import CommandRouter
from wizard.utils.config_manager import ConfigManager

class TestCommandRouter:
    
    @pytest.fixture
    def router(self):
        config = ConfigManager("tests/fixtures/test_config.json")
        return CommandRouter(config.get_all())
    
    def test_process_simple_command(self, router):
        """Test processing a simple command"""
        response = router.process_command("what time is it")
        assert "time" in response.lower()
    
    def test_process_application_command(self, router):
        """Test application launch command"""
        response = router.process_command("open calculator")
        assert "calculator" in response.lower()
    
    def test_invalid_command(self, router):
        """Test handling of invalid commands"""
        response = router.process_command("xyz invalid command")
        assert "sorry" in response.lower() or "understand" in response.lower()
```

#### Integration Test Example

```python
# tests/integration/test_voice_workflow.py
import pytest
from unittest.mock import Mock, patch
from wizard.main import WizardApp

class TestVoiceWorkflow:
    
    @pytest.fixture
    def app(self):
        return WizardApp(test_mode=True)
    
    @patch('wizard.audio.speech_recognition.SpeechRecognizer.recognize')
    def test_complete_voice_workflow(self, mock_recognize, app):
        """Test complete voice interaction workflow"""
        # Mock speech recognition
        mock_recognize.return_value = ("what time is it", 0.95)
        
        # Process voice input
        response = app.process_voice_input(b"fake_audio_data")
        
        # Verify response
        assert response is not None
        assert "time" in response.lower()
```

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=wizard --cov-report=html

# Run specific test file
pytest tests/unit/test_command_router.py

# Run with verbose output
pytest -v

# Run integration tests only
pytest tests/integration/
```

---

## Contributing

### Development Workflow

1. **Fork Repository**: Create your own fork
2. **Create Branch**: `git checkout -b feature/new-feature`
3. **Make Changes**: Implement your feature or fix
4. **Write Tests**: Add appropriate test coverage
5. **Run Tests**: Ensure all tests pass
6. **Code Style**: Follow project coding standards
7. **Submit PR**: Create pull request with description

### Code Style Guidelines

#### Python Style

Follow PEP 8 with these additions:

```python
# Use type hints
def process_command(self, command: str) -> str:
    """Process command and return response"""
    pass

# Use docstrings for all public methods
def calculate_similarity(text1: str, text2: str) -> float:
    """
    Calculate similarity between two text strings.
    
    Args:
        text1: First text string
        text2: Second text string
    
    Returns:
        Similarity score between 0.0 and 1.0
    """
    pass

# Use meaningful variable names
user_command = "open calculator"
confidence_threshold = 0.8
```

#### Code Formatting

Use Black for code formatting:

```bash
black wizard/ tests/
```

Use flake8 for linting:

```bash
flake8 wizard/ tests/
```

### Documentation Standards

- All public APIs must have docstrings
- Use Google-style docstrings
- Include type hints for all function parameters
- Add examples for complex functions
- Update relevant documentation files

### Commit Message Format

```
type(scope): brief description

Longer description if needed

Fixes #issue_number
```

Types: `feat`, `fix`, `docs`, `style`, `refactor`, `test`, `chore`

---

## Best Practices

### Performance Optimization

1. **Lazy Loading**: Load components only when needed
2. **Caching**: Cache frequently accessed data
3. **Async Operations**: Use async for I/O operations
4. **Memory Management**: Clean up resources properly

### Error Handling

```python
import logging
from typing import Optional

logger = logging.getLogger(__name__)

def safe_operation(data: str) -> Optional[str]:
    """Perform operation with proper error handling"""
    try:
        # Operation logic here
        result = process_data(data)
        return result
    except ValueError as e:
        logger.warning(f"Invalid data format: {e}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error in safe_operation: {e}")
        return None
```

### Security Considerations

1. **Input Validation**: Validate all user inputs
2. **File Operations**: Use safe file paths
3. **System Commands**: Sanitize system command parameters
4. **Configuration**: Secure sensitive configuration data

### Logging Best Practices

```python
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

# Use appropriate log levels
logger.debug("Detailed debug information")
logger.info("General information")
logger.warning("Warning message")
logger.error("Error occurred")
logger.critical("Critical error")
```

### Configuration Management

```python
# Use environment variables for sensitive data
import os
from typing import Optional

def get_api_key() -> Optional[str]:
    """Get API key from environment or config"""
    return os.getenv('WIZARD_API_KEY') or config.get('api_key')

# Provide sensible defaults
def get_timeout() -> int:
    """Get timeout setting with default"""
    return config.get('timeout', 30)
```

---

This developer guide provides the foundation for extending and contributing to Wizard Voice Assistant. For specific implementation details, refer to the source code and inline documentation.