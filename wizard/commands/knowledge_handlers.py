"""
Knowledge Command Handlers for Wizard Voice Assistant

This module contains command handlers for knowledge-related voice commands.
Integrates with the OfflineKnowledge system to provide offline information access.
"""

import re
from typing import Dict, Any, List, Optional, Tuple

from ..data.offline_knowledge import OfflineKnowledge
from ..utils.logger import WizardLogger
from ..utils.config_manager import ConfigManager


class KnowledgeHandlers:
    """
    Handles voice commands related to knowledge queries, definitions, and information lookup.
    
    Supported commands:
    - Wikipedia searches ("tell me about cats", "what is artificial intelligence")
    - Dictionary definitions ("define computer", "what does hello mean")
    - Spell checking ("how do you spell necessary", "spell check receive")
    - Currency conversion ("convert 100 dollars to euros", "how much is 50 pounds in yen")
    """
    
    def __init__(self, config_manager: ConfigManager, logger: WizardLogger):
        """
        Initialize knowledge command handlers.
        
        Args:
            config_manager: Configuration manager instance
            logger: WizardLogger instance
        """
        self.config = config_manager
        self.logger = logger
        self.knowledge = OfflineKnowledge(config_manager, logger)
        
        # Command patterns for knowledge operations
        self.wikipedia_patterns = [
            r"tell me about (.+)",
            r"what is (.+)",
            r"who is (.+)",
            r"explain (.+)",
            r"information about (.+)",
            r"wikipedia (.+)"
        ]
        
        self.definition_patterns = [
            r"define (.+)",
            r"what does (.+) mean",
            r"meaning of (.+)",
            r"definition of (.+)"
        ]
        
        self.spell_check_patterns = [
            r"how do you spell (.+)",
            r"spell (.+)",
            r"spelling of (.+)",
            r"spell check (.+)"
        ]
        
        self.currency_patterns = [
            r"convert (\d+(?:\.\d+)?) (\w+) to (\w+)",
            r"how much is (\d+(?:\.\d+)?) (\w+) in (\w+)",
            r"(\d+(?:\.\d+)?) (\w+) to (\w+)",
            r"exchange (\d+(?:\.\d+)?) (\w+) for (\w+)"
        ]
        
        self.logger.info("Knowledge handlers initialized successfully")
    
    def handle_wikipedia_search(self, command_text: str, entities: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle Wikipedia search commands.
        
        Args:
            command_text: The original command text
            entities: Extracted entities from the command
            
        Returns:
            Response dictionary with Wikipedia information
        """
        try:
            # Extract topic from command
            topic = self._extract_query(command_text, self.wikipedia_patterns)
            
            if not topic:
                return {
                    'success': False,
                    'message': "I couldn't understand what topic you want to learn about. Please try again.",
                    'speak': True
                }
            
            # Search Wikipedia cache
            article = self.knowledge.search_wikipedia(topic)
            
            if article and article.get('found'):
                # Truncate summary for speech if too long
                summary = article['summary']
                if len(summary) > 300:
                    summary = summary[:300] + "..."
                
                response_message = f"Here's what I found about {topic}: {summary}"
                
                return {
                    'success': True,
                    'message': response_message,
                    'speak': True,
                    'data': article
                }
            else:
                # Provide basic response when article not found
                response_message = f"I don't have information about '{topic}' in my offline knowledge base. You might want to search the web for more details."
                
                return {
                    'success': False,
                    'message': response_message,
                    'speak': True
                }
                
        except Exception as e:
            self.logger.error(f"Error handling Wikipedia search: {e}")
            return {
                'success': False,
                'message': "I encountered an error while searching for information.",
                'speak': True
            }
    
    def handle_definition_request(self, command_text: str, entities: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle word definition requests.
        
        Args:
            command_text: The original command text
            entities: Extracted entities from the command
            
        Returns:
            Response dictionary with word definition
        """
        try:
            # Extract word from command
            word = self._extract_query(command_text, self.definition_patterns)
            
            if not word:
                return {
                    'success': False,
                    'message': "I couldn't understand which word you want me to define. Please try again.",
                    'speak': True
                }
            
            # Get definition
            definition_result = self.knowledge.get_definition(word)
            
            if definition_result and definition_result.get('found'):
                response_parts = [f"The word '{word}' means: {definition_result['definition']}"]
                
                if definition_result.get('part_of_speech'):
                    response_parts.append(f"It's a {definition_result['part_of_speech']}.")
                
                if definition_result.get('example'):
                    response_parts.append(f"For example: {definition_result['example']}")
                
                response_message = " ".join(response_parts)
                
                return {
                    'success': True,
                    'message': response_message,
                    'speak': True,
                    'data': definition_result
                }
            else:
                response_message = f"I don't have a definition for '{word}' in my dictionary. You might want to search the web for its meaning."
                
                return {
                    'success': False,
                    'message': response_message,
                    'speak': True
                }
                
        except Exception as e:
            self.logger.error(f"Error handling definition request: {e}")
            return {
                'success': False,
                'message': "I encountered an error while looking up the definition.",
                'speak': True
            }
    
    def handle_spell_check(self, command_text: str, entities: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle spell checking requests.
        
        Args:
            command_text: The original command text
            entities: Extracted entities from the command
            
        Returns:
            Response dictionary with spelling information
        """
        try:
            # Extract word from command
            word = self._extract_query(command_text, self.spell_check_patterns)
            
            if not word:
                return {
                    'success': False,
                    'message': "I couldn't understand which word you want me to spell check. Please try again.",
                    'speak': True
                }
            
            # Check spelling
            spell_result = self.knowledge.spell_check(word)
            
            if spell_result['correct']:
                response_message = f"The word '{word}' is spelled correctly: {word.upper()}."
                
                return {
                    'success': True,
                    'message': response_message,
                    'speak': True,
                    'data': spell_result
                }
            else:
                if spell_result['suggestions']:
                    suggestions_text = ", ".join(spell_result['suggestions'][:3])
                    response_message = f"The word '{word}' might be misspelled. Did you mean: {suggestions_text}?"
                else:
                    response_message = f"I couldn't find '{word}' in my dictionary and don't have spelling suggestions."
                
                return {
                    'success': True,
                    'message': response_message,
                    'speak': True,
                    'data': spell_result
                }
                
        except Exception as e:
            self.logger.error(f"Error handling spell check: {e}")
            return {
                'success': False,
                'message': "I encountered an error while checking the spelling.",
                'speak': True
            }
    
    def handle_currency_conversion(self, command_text: str, entities: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle currency conversion requests.
        
        Args:
            command_text: The original command text
            entities: Extracted entities from the command
            
        Returns:
            Response dictionary with currency conversion
        """
        try:
            # Extract conversion details from command
            conversion_data = self._extract_currency_conversion(command_text)
            
            if not conversion_data:
                return {
                    'success': False,
                    'message': "I couldn't understand the currency conversion request. Please try saying something like 'convert 100 dollars to euros'.",
                    'speak': True
                }
            
            amount, from_currency, to_currency = conversion_data
            
            # Perform conversion
            conversion_result = self.knowledge.convert_currency(amount, from_currency, to_currency)
            
            if conversion_result and conversion_result.get('success'):
                converted_amount = conversion_result['converted_amount']
                rate = conversion_result['rate']
                
                response_message = f"{amount} {from_currency} equals {converted_amount} {to_currency}. The exchange rate is {rate:.4f}."
                
                return {
                    'success': True,
                    'message': response_message,
                    'speak': True,
                    'data': conversion_result
                }
            else:
                response_message = f"I don't have exchange rate information for converting {from_currency} to {to_currency}."
                
                return {
                    'success': False,
                    'message': response_message,
                    'speak': True
                }
                
        except Exception as e:
            self.logger.error(f"Error handling currency conversion: {e}")
            return {
                'success': False,
                'message': "I encountered an error while converting the currency.",
                'speak': True
            }
    
    def _extract_query(self, command_text: str, patterns: List[str]) -> Optional[str]:
        """
        Extract query from command text using regex patterns.
        
        Args:
            command_text: The command text to parse
            patterns: List of regex patterns to try
            
        Returns:
            Extracted query string or None if not found
        """
        command_lower = command_text.lower().strip()
        
        for pattern in patterns:
            match = re.search(pattern, command_lower)
            if match:
                query = match.group(1).strip()
                if query:
                    return query
        
        return None
    
    def _extract_currency_conversion(self, command_text: str) -> Optional[Tuple[float, str, str]]:
        """
        Extract currency conversion details from command.
        
        Args:
            command_text: The command text to parse
            
        Returns:
            Tuple of (amount, from_currency, to_currency) or None if not found
        """
        command_lower = command_text.lower().strip()
        
        # Currency name mappings
        currency_names = {
            'dollar': 'USD', 'dollars': 'USD', 'usd': 'USD',
            'euro': 'EUR', 'euros': 'EUR', 'eur': 'EUR',
            'pound': 'GBP', 'pounds': 'GBP', 'gbp': 'GBP',
            'yen': 'JPY', 'jpy': 'JPY',
            'canadian dollar': 'CAD', 'canadian dollars': 'CAD', 'cad': 'CAD',
            'australian dollar': 'AUD', 'australian dollars': 'AUD', 'aud': 'AUD',
            'swiss franc': 'CHF', 'swiss francs': 'CHF', 'chf': 'CHF',
            'yuan': 'CNY', 'cny': 'CNY',
            'rupee': 'INR', 'rupees': 'INR', 'inr': 'INR'
        }
        
        for pattern in self.currency_patterns:
            match = re.search(pattern, command_lower)
            if match:
                try:
                    amount = float(match.group(1))
                    from_curr = match.group(2).lower()
                    to_curr = match.group(3).lower()
                    
                    # Convert currency names to codes
                    from_currency = currency_names.get(from_curr, from_curr.upper())
                    to_currency = currency_names.get(to_curr, to_curr.upper())
                    
                    return (amount, from_currency, to_currency)
                except (ValueError, IndexError):
                    continue
        
        return None
    
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
            "what does hello mean",
            "how do you spell necessary",
            "spell check receive",
            "convert 100 dollars to euros",
            "how much is 50 pounds in yen"
        ]