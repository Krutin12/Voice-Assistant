"""
Pytest configuration and shared fixtures for Wizard Voice Assistant tests
"""

import pytest
import sys
import os
import tempfile
import json
from pathlib import Path
from unittest.mock import Mock, MagicMock

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from wizard.utils.config_manager import ConfigManager
from wizard.utils.logger import WizardLogger


@pytest.fixture
def temp_dir():
    """Create temporary directory for tests"""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield Path(temp_dir)


@pytest.fixture
def test_config():
    """Create test configuration"""
    return {
        "assistant_name": "TestWizard",
        "wake_words": ["Test Wizard", "TestWizard"],
        "voice": {
            "gender": "female",
            "speed": 1.0,
            "volume": 0.8
        },
        "security": {
            "require_confirmation": False,
            "safe_mode": True
        },
        "applications": {
            "calculator": "calc.exe",
            "notepad": "notepad.exe"
        },
        "test_mode": True
    }


@pytest.fixture
def config_manager(temp_dir, test_config):
    """Create test configuration manager"""
    config_file = temp_dir / "test_config.json"
    with open(config_file, 'w') as f:
        json.dump(test_config, f)
    
    return ConfigManager(str(config_file))


@pytest.fixture
def logger(temp_dir):
    """Create test logger"""
    log_file = temp_dir / "test.log"
    return WizardLogger(str(log_file), level="DEBUG")


@pytest.fixture
def mock_audio_input():
    """Mock audio input for testing"""
    mock = Mock()
    mock.read.return_value = b"fake_audio_data"
    mock.get_sample_size.return_value = 2
    mock.get_sample_rate.return_value = 44100
    return mock


@pytest.fixture
def mock_speech_recognizer():
    """Mock speech recognizer"""
    mock = Mock()
    mock.recognize.return_value = ("test command", 0.95)
    mock.adjust_for_ambient_noise = Mock()
    return mock


@pytest.fixture
def mock_tts_engine():
    """Mock text-to-speech engine"""
    mock = Mock()
    mock.say = Mock()
    mock.runAndWait = Mock()
    mock.getProperty.return_value = []
    mock.setProperty = Mock()
    return mock


@pytest.fixture
def sample_commands():
    """Sample commands for testing"""
    return [
        "what time is it",
        "open calculator",
        "set timer for 5 minutes",
        "what is artificial intelligence",
        "play music",
        "create folder test",
        "tell me a joke"
    ]


@pytest.fixture
def sample_entities():
    """Sample entities for testing"""
    return {
        "application": "calculator",
        "duration": "5 minutes",
        "folder_name": "test",
        "query": "artificial intelligence"
    }


@pytest.fixture(autouse=True)
def setup_test_environment(monkeypatch):
    """Set up test environment variables"""
    monkeypatch.setenv("WIZARD_TEST_MODE", "true")
    monkeypatch.setenv("WIZARD_LOG_LEVEL", "DEBUG")


class MockAudioDevice:
    """Mock audio device for testing"""
    
    def __init__(self, device_type="input"):
        self.device_type = device_type
        self.is_open = False
    
    def open(self):
        self.is_open = True
    
    def close(self):
        self.is_open = False
    
    def read(self, chunk_size):
        return b"0" * chunk_size
    
    def write(self, data):
        pass


@pytest.fixture
def mock_audio_devices():
    """Mock audio devices"""
    return {
        "input": MockAudioDevice("input"),
        "output": MockAudioDevice("output")
    }


# Test data fixtures
@pytest.fixture
def sample_knowledge_data():
    """Sample knowledge base data"""
    return {
        "facts": [
            {
                "question": "what is python",
                "answer": "Python is a programming language",
                "category": "technology"
            },
            {
                "question": "what is ai",
                "answer": "AI stands for Artificial Intelligence",
                "category": "technology"
            }
        ],
        "definitions": {
            "computer": "An electronic device for processing data",
            "algorithm": "A set of rules for solving problems"
        }
    }


@pytest.fixture
def sample_file_structure(temp_dir):
    """Create sample file structure for testing"""
    # Create directories
    (temp_dir / "documents").mkdir()
    (temp_dir / "downloads").mkdir()
    (temp_dir / "music").mkdir()
    
    # Create files
    (temp_dir / "documents" / "test.txt").write_text("Test document")
    (temp_dir / "documents" / "report.pdf").touch()
    (temp_dir / "downloads" / "file.zip").touch()
    (temp_dir / "music" / "song.mp3").touch()
    
    return temp_dir


# Performance testing fixtures
@pytest.fixture
def performance_thresholds():
    """Performance thresholds for testing"""
    return {
        "wake_word_detection": 0.5,  # seconds
        "command_processing": 1.0,   # seconds
        "response_generation": 0.5,  # seconds
        "memory_usage": 500,         # MB
        "cpu_usage": 50             # percentage
    }


# Integration test fixtures
@pytest.fixture
def integration_test_config():
    """Configuration for integration tests"""
    return {
        "test_duration": 30,  # seconds
        "command_interval": 2,  # seconds between commands
        "expected_accuracy": 0.85,  # minimum accuracy
        "max_response_time": 2.0   # maximum response time
    }


# Cleanup fixtures
@pytest.fixture(autouse=True)
def cleanup_after_test():
    """Cleanup after each test"""
    yield
    # Cleanup code here if needed
    pass


# Skip markers for different test types
def pytest_configure(config):
    """Configure pytest markers"""
    config.addinivalue_line(
        "markers", "unit: mark test as unit test"
    )
    config.addinivalue_line(
        "markers", "integration: mark test as integration test"
    )
    config.addinivalue_line(
        "markers", "performance: mark test as performance test"
    )
    config.addinivalue_line(
        "markers", "audio: mark test as requiring audio devices"
    )
    config.addinivalue_line(
        "markers", "slow: mark test as slow running"
    )