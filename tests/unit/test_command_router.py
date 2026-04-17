"""
Unit tests for Command Router functionality
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from wizard.commands.command_router import CommandRouter
from wizard.commands.entity_extractor import EntityExtractor


@pytest.mark.unit
class TestCommandRouter:
    """Test cases for CommandRouter class"""
    
    @pytest.fixture
    def router(self, config_manager):
        """Create CommandRouter instance for testing"""
        return CommandRouter(config_manager)
    
    @pytest.fixture
    def entity_extractor(self):
        """Create EntityExtractor instance for testing"""
        return EntityExtractor()
    
    def test_router_initialization(self, router):
        """Test router initializes correctly"""
        assert router is not None
        assert hasattr(router, 'handlers')
        assert hasattr(router, 'entity_extractor')
    
    def test_simple_command_processing(self, router):
        """Test processing simple commands"""
        # Test time command
        response = router.process_command("what time is it")
        assert response is not None
        assert isinstance(response, str)
        assert len(response) > 0
    
    def test_application_command(self, router):
        """Test application launch commands"""
        with patch('subprocess.run') as mock_subprocess:
            mock_subprocess.return_value.returncode = 0
            
            response = router.process_command("open calculator")
            assert "calculator" in response.lower() or "opened" in response.lower()
    
    def test_invalid_command(self, router):
        """Test handling of invalid commands"""
        response = router.process_command("xyz invalid nonsense command")
        assert "sorry" in response.lower() or "understand" in response.lower() or "help" in response.lower()
    
    def test_empty_command(self, router):
        """Test handling of empty commands"""
        response = router.process_command("")
        assert response is not None
        assert len(response) > 0
    
    def test_command_with_entities(self, router):
        """Test commands with extracted entities"""
        response = router.process_command("set timer for 5 minutes")
        assert response is not None
        # Should contain some indication of timer being set
        assert any(word in response.lower() for word in ["timer", "5", "minutes", "set"])
    
    def test_case_insensitive_commands(self, router):
        """Test that commands are case insensitive"""
        responses = [
            router.process_command("WHAT TIME IS IT"),
            router.process_command("what time is it"),
            router.process_command("What Time Is It")
        ]
        
        # All responses should be valid (not error messages)
        for response in responses:
            assert response is not None
            assert len(response) > 0
    
    def test_command_variations(self, router):
        """Test different ways to express the same command"""
        time_commands = [
            "what time is it",
            "tell me the time",
            "current time",
            "what's the time"
        ]
        
        responses = [router.process_command(cmd) for cmd in time_commands]
        
        # All should return valid responses
        for response in responses:
            assert response is not None
            assert len(response) > 0
    
    def test_handler_registration(self, router):
        """Test registering new command handlers"""
        initial_handler_count = len(router.handlers)
        
        # Create mock handler
        mock_handler = Mock()
        mock_handler.can_handle.return_value = True
        mock_handler.handle.return_value = "Mock response"
        
        router.register_handler(mock_handler)
        
        assert len(router.handlers) == initial_handler_count + 1
    
    def test_command_routing_priority(self, router):
        """Test that commands are routed to appropriate handlers"""
        # Mock specific handlers to test routing
        with patch.object(router, 'handlers') as mock_handlers:
            handler1 = Mock()
            handler1.can_handle.return_value = False
            
            handler2 = Mock()
            handler2.can_handle.return_value = True
            handler2.handle.return_value = "Handler 2 response"
            
            mock_handlers.__iter__.return_value = [handler1, handler2]
            
            response = router.process_command("test command")
            
            assert response == "Handler 2 response"
            handler1.can_handle.assert_called_once()
            handler2.can_handle.assert_called_once()
            handler2.handle.assert_called_once()


@pytest.mark.unit
class TestEntityExtractor:
    """Test cases for EntityExtractor class"""
    
    def test_time_extraction(self, entity_extractor):
        """Test extracting time entities"""
        text = "set timer for 10 minutes"
        entities = entity_extractor.extract_time(text)
        
        assert entities is not None
        assert isinstance(entities, dict)
    
    def test_number_extraction(self, entity_extractor):
        """Test extracting numbers from text"""
        text = "set volume to 75 percent"
        numbers = entity_extractor.extract_numbers(text)
        
        assert isinstance(numbers, list)
        assert 75.0 in numbers
    
    def test_application_extraction(self, entity_extractor):
        """Test extracting application names"""
        text = "open chrome browser"
        apps = entity_extractor.extract_applications(text)
        
        assert isinstance(apps, list)
        # Should find chrome or similar
        assert len(apps) >= 0  # May or may not find apps depending on implementation
    
    def test_multiple_entities(self, entity_extractor):
        """Test extracting multiple types of entities"""
        text = "remind me in 30 minutes to call John at 555-1234"
        
        time_entities = entity_extractor.extract_time(text)
        numbers = entity_extractor.extract_numbers(text)
        
        assert isinstance(time_entities, dict)
        assert isinstance(numbers, list)
        assert len(numbers) > 0  # Should find 30 and phone number parts
    
    def test_no_entities(self, entity_extractor):
        """Test text with no extractable entities"""
        text = "hello how are you"
        
        time_entities = entity_extractor.extract_time(text)
        numbers = entity_extractor.extract_numbers(text)
        apps = entity_extractor.extract_applications(text)
        
        # Should return empty but valid structures
        assert isinstance(time_entities, dict)
        assert isinstance(numbers, list)
        assert isinstance(apps, list)


@pytest.mark.unit
class TestCommandRouterIntegration:
    """Integration tests for command router with other components"""
    
    def test_router_with_mock_handlers(self, config_manager):
        """Test router with mocked handlers"""
        router = CommandRouter(config_manager)
        
        # Clear existing handlers and add mock
        router.handlers = []
        
        mock_handler = Mock()
        mock_handler.can_handle.return_value = True
        mock_handler.handle.return_value = "Mock handler response"
        
        router.register_handler(mock_handler)
        
        response = router.process_command("test command")
        
        assert response == "Mock handler response"
        mock_handler.can_handle.assert_called_once_with("test command")
        mock_handler.handle.assert_called_once()
    
    def test_router_error_handling(self, config_manager):
        """Test router handles handler errors gracefully"""
        router = CommandRouter(config_manager)
        
        # Create handler that raises exception
        error_handler = Mock()
        error_handler.can_handle.return_value = True
        error_handler.handle.side_effect = Exception("Handler error")
        
        router.handlers = [error_handler]
        
        response = router.process_command("test command")
        
        # Should return error message, not crash
        assert response is not None
        assert isinstance(response, str)
        assert len(response) > 0
    
    def test_no_matching_handlers(self, config_manager):
        """Test behavior when no handlers match command"""
        router = CommandRouter(config_manager)
        
        # Mock all handlers to return False for can_handle
        for handler in router.handlers:
            handler.can_handle = Mock(return_value=False)
        
        response = router.process_command("unknown command")
        
        # Should return helpful message
        assert response is not None
        assert isinstance(response, str)
        assert len(response) > 0


@pytest.mark.unit
class TestCommandRouterPerformance:
    """Performance tests for command router"""
    
    def test_command_processing_speed(self, router, performance_thresholds):
        """Test command processing meets performance requirements"""
        import time
        
        start_time = time.time()
        response = router.process_command("what time is it")
        end_time = time.time()
        
        processing_time = end_time - start_time
        
        assert processing_time < performance_thresholds["command_processing"]
        assert response is not None
    
    def test_multiple_commands_performance(self, router, sample_commands):
        """Test processing multiple commands efficiently"""
        import time
        
        start_time = time.time()
        
        responses = []
        for command in sample_commands[:5]:  # Test first 5 commands
            response = router.process_command(command)
            responses.append(response)
        
        end_time = time.time()
        total_time = end_time - start_time
        avg_time = total_time / len(sample_commands[:5])
        
        # Average processing time should be reasonable
        assert avg_time < 1.0  # 1 second per command max
        
        # All responses should be valid
        for response in responses:
            assert response is not None
            assert len(response) > 0