"""
Enhanced Knowledge Manager for Wizard Voice Assistant

This module provides a centralized interface for managing all knowledge-related
functionality including offline knowledge, AI brain, and knowledge handlers.
"""

from typing import Dict, Any, List, Optional
from .offline_knowledge import OfflineKnowledge
from .ai_brain import AIBrain
from .sample_knowledge_data import populate_sample_data
from .enhanced_knowledge_data import (
    populate_comprehensive_wikipedia_data,
    populate_comprehensive_dictionary_data,
    populate_comprehensive_currency_data
)
from ..commands.knowledge_handlers import KnowledgeHandlers
from ..utils.logger import WizardLogger
from ..utils.config_manager import ConfigManager


class EnhancedKnowledgeManager:
    """
    Centralized manager for all knowledge-related functionality.
    
    This class coordinates between:
    - Offline knowledge system (Wikipedia, dictionary, currency)
    - AI brain for intelligent responses
    - Knowledge command handlers
    """
    
    def __init__(self, config_manager: ConfigManager, logger: WizardLogger):
        """
        Initialize the Enhanced Knowledge Manager.
        
        Args:
            config_manager: Configuration manager instance
            logger: WizardLogger instance
        """
        self.config = config_manager
        self.logger = logger
        
        # Initialize knowledge components
        self.offline_knowledge = OfflineKnowledge(config_manager, logger)
        self.ai_brain = AIBrain()  # AIBrain only takes db_path parameter
        self.knowledge_handlers = KnowledgeHandlers(config_manager, logger)
        
        # Initialize knowledge data
        self._initialize_knowledge_data()
        
        self.logger.info("Enhanced Knowledge Manager initialized successfully")
    
    def _initialize_knowledge_data(self) -> None:
        """Initialize the knowledge system with comprehensive data."""
        try:
            # Check if we need to populate data
            stats = self.offline_knowledge.get_cache_stats()
            
            # If we have very few entries, populate with comprehensive data
            if stats['total_entries'] < 50:
                self.logger.info("Populating comprehensive knowledge data...")
                
                # Populate basic sample data first
                populate_sample_data(self.offline_knowledge)
                
                # Then add comprehensive data
                populate_comprehensive_wikipedia_data(self.offline_knowledge)
                populate_comprehensive_dictionary_data(self.offline_knowledge)
                populate_comprehensive_currency_data(self.offline_knowledge)
                
                self.logger.info("Comprehensive knowledge data populated successfully")
            else:
                self.logger.info(f"Knowledge system already has {stats['total_entries']} entries")
                
        except Exception as e:
            self.logger.error(f"Error initializing knowledge data: {e}")
    
    def search_knowledge(self, query: str, knowledge_type: str = 'auto') -> Dict[str, Any]:
        """
        Search for knowledge across all available sources.
        
        Args:
            query: Search query
            knowledge_type: Type of knowledge to search ('wikipedia', 'dictionary', 'auto')
            
        Returns:
            Dictionary containing search results
        """
        try:
            if knowledge_type == 'wikipedia' or knowledge_type == 'auto':
                # Try Wikipedia first
                wiki_result = self.offline_knowledge.search_wikipedia(query)
                if wiki_result and wiki_result.get('found'):
                    return {
                        'success': True,
                        'source': 'wikipedia',
                        'data': wiki_result,
                        'message': f"Found Wikipedia article about {query}"
                    }
            
            if knowledge_type == 'dictionary' or knowledge_type == 'auto':
                # Try dictionary lookup
                dict_result = self.offline_knowledge.get_definition(query)
                if dict_result and dict_result.get('found'):
                    return {
                        'success': True,
                        'source': 'dictionary',
                        'data': dict_result,
                        'message': f"Found definition for {query}"
                    }
            
            # If no specific knowledge found, use AI brain
            ai_response = self.ai_brain.process_query(query, {})
            if ai_response:
                return {
                    'success': True,
                    'source': 'ai_brain',
                    'data': {'response': ai_response},
                    'message': ai_response
                }
            
            return {
                'success': False,
                'message': f"No knowledge found for: {query}"
            }
            
        except Exception as e:
            self.logger.error(f"Error searching knowledge: {e}")
            return {
                'success': False,
                'error': str(e),
                'message': "Error occurred while searching knowledge"
            }
    
    def get_definition(self, word: str) -> Dict[str, Any]:
        """
        Get definition for a word.
        
        Args:
            word: Word to define
            
        Returns:
            Dictionary containing definition information
        """
        return self.offline_knowledge.get_definition(word)
    
    def spell_check(self, word: str) -> Dict[str, Any]:
        """
        Check spelling of a word.
        
        Args:
            word: Word to check
            
        Returns:
            Dictionary containing spell check results
        """
        return self.offline_knowledge.spell_check(word)
    
    def convert_currency(self, amount: float, from_currency: str, to_currency: str) -> Dict[str, Any]:
        """
        Convert currency.
        
        Args:
            amount: Amount to convert
            from_currency: Source currency
            to_currency: Target currency
            
        Returns:
            Dictionary containing conversion results
        """
        return self.offline_knowledge.convert_currency(amount, from_currency, to_currency)
    
    def add_wikipedia_article(self, title: str, summary: str, url: str = None, full_text: str = None) -> bool:
        """
        Add a Wikipedia article to the offline cache.
        
        Args:
            title: Article title
            summary: Article summary
            url: Article URL (optional)
            full_text: Full article text (optional)
            
        Returns:
            True if successful, False otherwise
        """
        return self.offline_knowledge.cache_wikipedia_article(title, summary, url, full_text)
    
    def add_dictionary_entry(self, word: str, definition: str, part_of_speech: str = None, 
                           example: str = None, synonyms: str = None) -> bool:
        """
        Add a dictionary entry.
        
        Args:
            word: Word to add
            definition: Word definition
            part_of_speech: Part of speech (optional)
            example: Usage example (optional)
            synonyms: Comma-separated synonyms (optional)
            
        Returns:
            True if successful, False otherwise
        """
        return self.offline_knowledge.add_definition(word, definition, part_of_speech, example, synonyms)
    
    def update_exchange_rate(self, base_currency: str, target_currency: str, rate: float) -> bool:
        """
        Update currency exchange rate.
        
        Args:
            base_currency: Base currency code
            target_currency: Target currency code
            rate: Exchange rate
            
        Returns:
            True if successful, False otherwise
        """
        return self.offline_knowledge.update_exchange_rate(base_currency, target_currency, rate)
    
    def get_supported_currencies(self) -> List[str]:
        """
        Get list of supported currency codes.
        
        Returns:
            List of currency codes
        """
        return self.offline_knowledge.get_supported_currencies()
    
    def search_with_ai_fallback(self, query: str) -> Dict[str, Any]:
        """
        Search knowledge with AI fallback for complex queries.
        
        Args:
            query: Search query
            
        Returns:
            Dictionary containing search results with AI enhancement
        """
        try:
            # First try standard knowledge search
            result = self.search_knowledge(query, 'auto')
            
            if result['success']:
                # Enhance with AI context if available
                if result['source'] in ['wikipedia', 'dictionary']:
                    ai_context = self.ai_brain.process_query(f"explain more about {query}", {})
                    if ai_context:
                        result['ai_enhancement'] = ai_context
                
                return result
            
            # If no knowledge found, try AI brain with more context
            ai_response = self.ai_brain.process_query(
                f"I need information about {query}. Please provide what you know.", 
                {'query_type': 'knowledge_search'}
            )
            
            if ai_response:
                return {
                    'success': True,
                    'source': 'ai_brain_enhanced',
                    'data': {'response': ai_response},
                    'message': ai_response
                }
            
            return {
                'success': False,
                'message': f"No information available for: {query}"
            }
            
        except Exception as e:
            self.logger.error(f"Error in AI fallback search: {e}")
            return {
                'success': False,
                'error': str(e),
                'message': "Error occurred during enhanced search"
            }
    
    def get_knowledge_stats(self) -> Dict[str, Any]:
        """
        Get statistics about the knowledge system.
        
        Returns:
            Dictionary containing knowledge statistics
        """
        try:
            offline_stats = self.offline_knowledge.get_cache_stats()
            ai_stats = self.ai_brain.get_stats() if hasattr(self.ai_brain, 'get_stats') else {}
            
            return {
                'offline_knowledge': offline_stats,
                'ai_brain': ai_stats,
                'total_knowledge_entries': offline_stats.get('total_entries', 0),
                'supported_currencies': len(self.get_supported_currencies())
            }
            
        except Exception as e:
            self.logger.error(f"Error getting knowledge stats: {e}")
            return {
                'offline_knowledge': {},
                'ai_brain': {},
                'total_knowledge_entries': 0,
                'supported_currencies': 0
            }
    
    def refresh_knowledge_data(self) -> bool:
        """
        Refresh and update knowledge data.
        
        Returns:
            True if successful, False otherwise
        """
        try:
            self.logger.info("Refreshing knowledge data...")
            
            # Re-populate comprehensive data
            populate_comprehensive_wikipedia_data(self.offline_knowledge)
            populate_comprehensive_dictionary_data(self.offline_knowledge)
            populate_comprehensive_currency_data(self.offline_knowledge)
            
            self.logger.info("Knowledge data refreshed successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Error refreshing knowledge data: {e}")
            return False
    
    def handle_voice_command(self, command_text: str, entities: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle voice commands related to knowledge queries.
        
        Args:
            command_text: The voice command text
            entities: Extracted entities from the command
            
        Returns:
            Response dictionary
        """
        try:
            command_lower = command_text.lower().strip()
            
            # Wikipedia search commands
            if any(phrase in command_lower for phrase in ['tell me about', 'what is', 'who is', 'explain', 'wikipedia']):
                return self.knowledge_handlers.handle_wikipedia_search(command_text, entities)
            
            # Definition commands
            elif any(phrase in command_lower for phrase in ['define', 'what does', 'meaning of', 'definition']):
                return self.knowledge_handlers.handle_definition_request(command_text, entities)
            
            # Spell check commands
            elif any(phrase in command_lower for phrase in ['spell', 'spelling']):
                return self.knowledge_handlers.handle_spell_check(command_text, entities)
            
            # Currency conversion commands
            elif any(phrase in command_lower for phrase in ['convert', 'exchange', 'currency']):
                return self.knowledge_handlers.handle_currency_conversion(command_text, entities)
            
            # General knowledge search
            else:
                result = self.search_with_ai_fallback(command_text)
                if result['success']:
                    return {
                        'success': True,
                        'message': result['message'],
                        'speak': True,
                        'data': result['data']
                    }
                else:
                    return {
                        'success': False,
                        'message': "I couldn't find information about that topic.",
                        'speak': True
                    }
                    
        except Exception as e:
            self.logger.error(f"Error handling voice command: {e}")
            return {
                'success': False,
                'message': "I encountered an error while processing your request.",
                'speak': True
            }
    
    def get_supported_commands(self) -> List[str]:
        """
        Get list of supported knowledge commands.
        
        Returns:
            List of example commands
        """
        return [
            "tell me about artificial intelligence",
            "what is machine learning",
            "define computer",
            "what does algorithm mean",
            "how do you spell necessary",
            "spell check receive",
            "convert 100 dollars to euros",
            "how much is 50 pounds in yen",
            "exchange 75 euros for dollars"
        ]