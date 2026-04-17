"""
Offline Knowledge and Reference System for Wizard Voice Assistant

This module provides offline access to Wikipedia articles, dictionary definitions,
spell checking, and currency conversion without requiring internet connectivity.
"""

import os
import json
import sqlite3
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
import re

from ..utils.logger import WizardLogger
from ..utils.config_manager import ConfigManager


class OfflineKnowledge:
    """
    Manages offline knowledge base including Wikipedia articles, dictionary,
    and currency conversion data.
    
    Features:
    - Cached Wikipedia article summaries
    - Local dictionary for word definitions
    - Spell checking capabilities
    - Currency conversion with offline exchange rates
    """
    
    def __init__(self, config_manager: ConfigManager, logger: WizardLogger):
        """
        Initialize the offline knowledge system.
        
        Args:
            config_manager: Configuration manager instance
            logger: WizardLogger instance
        """
        self.config = config_manager
        self.logger = logger
        self.data_dir = os.path.join(os.path.dirname(__file__), 'knowledge_data')
        
        # Create data directory if it doesn't exist
        os.makedirs(self.data_dir, exist_ok=True)
        
        # Initialize database
        self.db_path = os.path.join(self.data_dir, 'knowledge.db')
        self._initialize_database()
        
        # Load dictionary and exchange rates
        self.dictionary = self._load_dictionary()
        self.exchange_rates = self._load_exchange_rates()
        
        self.logger.info("Offline Knowledge system initialized successfully")
    
    def _initialize_database(self) -> None:
        """Initialize SQLite database for knowledge storage."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Wikipedia articles cache table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS wikipedia_cache (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT UNIQUE NOT NULL,
                    summary TEXT NOT NULL,
                    full_text TEXT,
                    url TEXT,
                    cached_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    access_count INTEGER DEFAULT 0
                )
            ''')
            
            # Dictionary entries table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS dictionary (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    word TEXT UNIQUE NOT NULL,
                    definition TEXT NOT NULL,
                    part_of_speech TEXT,
                    example TEXT,
                    synonyms TEXT
                )
            ''')
            
            # Currency exchange rates table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS exchange_rates (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    base_currency TEXT NOT NULL,
                    target_currency TEXT NOT NULL,
                    rate REAL NOT NULL,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(base_currency, target_currency)
                )
            ''')
            
            conn.commit()
            conn.close()
            
            self.logger.info("Knowledge database initialized successfully")
            
        except Exception as e:
            self.logger.error(f"Error initializing knowledge database: {e}")
    
    def _load_dictionary(self) -> Dict[str, Dict]:
        """Load basic dictionary data."""
        # Basic dictionary with common words
        # In a real implementation, this would load from a comprehensive dictionary file
        basic_dict = {
            'hello': {
                'definition': 'A greeting or expression of goodwill',
                'part_of_speech': 'interjection',
                'example': 'Hello, how are you today?'
            },
            'computer': {
                'definition': 'An electronic device for storing and processing data',
                'part_of_speech': 'noun',
                'example': 'I use my computer for work every day.'
            },
            'artificial': {
                'definition': 'Made or produced by human beings rather than occurring naturally',
                'part_of_speech': 'adjective',
                'example': 'Artificial intelligence is transforming technology.'
            },
            'intelligence': {
                'definition': 'The ability to acquire and apply knowledge and skills',
                'part_of_speech': 'noun',
                'example': 'Human intelligence is remarkably adaptable.'
            },
            'assistant': {
                'definition': 'A person or device that helps or supports someone',
                'part_of_speech': 'noun',
                'example': 'The voice assistant answered my question.'
            }
        }
        
        # Try to load from file if exists
        dict_file = os.path.join(self.data_dir, 'dictionary.json')
        try:
            if os.path.exists(dict_file):
                with open(dict_file, 'r', encoding='utf-8') as f:
                    loaded_dict = json.load(f)
                    basic_dict.update(loaded_dict)
        except Exception as e:
            self.logger.error(f"Error loading dictionary file: {e}")
        
        return basic_dict
    
    def _load_exchange_rates(self) -> Dict[str, Dict[str, float]]:
        """Load currency exchange rates."""
        # Default exchange rates (as of a reference date)
        # In a real implementation, these would be updated periodically
        default_rates = {
            'USD': {
                'EUR': 0.85,
                'GBP': 0.73,
                'JPY': 110.0,
                'CAD': 1.25,
                'AUD': 1.35,
                'CHF': 0.92,
                'CNY': 6.45,
                'INR': 74.5
            },
            'EUR': {
                'USD': 1.18,
                'GBP': 0.86,
                'JPY': 129.5,
                'CAD': 1.47,
                'AUD': 1.59
            },
            'GBP': {
                'USD': 1.37,
                'EUR': 1.16,
                'JPY': 150.7,
                'CAD': 1.71
            }
        }
        
        # Try to load from file if exists
        rates_file = os.path.join(self.data_dir, 'exchange_rates.json')
        try:
            if os.path.exists(rates_file):
                with open(rates_file, 'r', encoding='utf-8') as f:
                    loaded_rates = json.load(f)
                    default_rates.update(loaded_rates)
        except Exception as e:
            self.logger.error(f"Error loading exchange rates file: {e}")
        
        return default_rates
    
    def search_wikipedia(self, topic: str) -> Optional[Dict]:
        """
        Search for Wikipedia article in cache.
        
        Args:
            topic: Topic to search for
            
        Returns:
            Dictionary with article information or None if not found
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Search for exact match first
            cursor.execute('''
                SELECT title, summary, url, cached_at, access_count
                FROM wikipedia_cache
                WHERE LOWER(title) = LOWER(?)
            ''', (topic,))
            
            result = cursor.fetchone()
            
            if result:
                # Update access count
                cursor.execute('''
                    UPDATE wikipedia_cache
                    SET access_count = access_count + 1
                    WHERE LOWER(title) = LOWER(?)
                ''', (topic,))
                conn.commit()
                
                article = {
                    'title': result[0],
                    'summary': result[1],
                    'url': result[2],
                    'cached_at': result[3],
                    'access_count': result[4] + 1,
                    'found': True
                }
                
                conn.close()
                self.logger.info(f"Found Wikipedia article for: {topic}")
                return article
            
            # Try partial match
            cursor.execute('''
                SELECT title, summary, url, cached_at, access_count
                FROM wikipedia_cache
                WHERE LOWER(title) LIKE LOWER(?)
                LIMIT 1
            ''', (f'%{topic}%',))
            
            result = cursor.fetchone()
            conn.close()
            
            if result:
                article = {
                    'title': result[0],
                    'summary': result[1],
                    'url': result[2],
                    'cached_at': result[3],
                    'access_count': result[4],
                    'found': True,
                    'partial_match': True
                }
                self.logger.info(f"Found partial Wikipedia match for: {topic}")
                return article
            
            self.logger.info(f"No Wikipedia article found for: {topic}")
            return None
            
        except Exception as e:
            self.logger.error(f"Error searching Wikipedia cache: {e}")
            return None
    
    def cache_wikipedia_article(self, title: str, summary: str, url: str = None, full_text: str = None) -> bool:
        """
        Cache a Wikipedia article for offline access.
        
        Args:
            title: Article title
            summary: Article summary
            url: Article URL (optional)
            full_text: Full article text (optional)
            
        Returns:
            True if successful, False otherwise
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT OR REPLACE INTO wikipedia_cache (title, summary, full_text, url)
                VALUES (?, ?, ?, ?)
            ''', (title, summary, full_text, url))
            
            conn.commit()
            conn.close()
            
            self.logger.info(f"Cached Wikipedia article: {title}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error caching Wikipedia article: {e}")
            return False
    
    def get_definition(self, word: str) -> Optional[Dict]:
        """
        Get dictionary definition for a word.
        
        Args:
            word: Word to define
            
        Returns:
            Dictionary with word definition or None if not found
        """
        word_lower = word.lower().strip()
        
        # Check in-memory dictionary first
        if word_lower in self.dictionary:
            self.logger.info(f"Found definition for: {word}")
            return {
                'word': word,
                'definition': self.dictionary[word_lower]['definition'],
                'part_of_speech': self.dictionary[word_lower].get('part_of_speech', ''),
                'example': self.dictionary[word_lower].get('example', ''),
                'found': True
            }
        
        # Check database
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT word, definition, part_of_speech, example, synonyms
                FROM dictionary
                WHERE LOWER(word) = LOWER(?)
            ''', (word,))
            
            result = cursor.fetchone()
            conn.close()
            
            if result:
                self.logger.info(f"Found definition in database for: {word}")
                return {
                    'word': result[0],
                    'definition': result[1],
                    'part_of_speech': result[2],
                    'example': result[3],
                    'synonyms': result[4],
                    'found': True
                }
            
        except Exception as e:
            self.logger.error(f"Error getting definition: {e}")
        
        self.logger.info(f"No definition found for: {word}")
        return None
    
    def add_definition(self, word: str, definition: str, part_of_speech: str = None, 
                      example: str = None, synonyms: str = None) -> bool:
        """
        Add a word definition to the dictionary.
        
        Args:
            word: Word to add
            definition: Word definition
            part_of_speech: Part of speech (optional)
            example: Usage example (optional)
            synonyms: Comma-separated synonyms (optional)
            
        Returns:
            True if successful, False otherwise
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT OR REPLACE INTO dictionary (word, definition, part_of_speech, example, synonyms)
                VALUES (?, ?, ?, ?, ?)
            ''', (word, definition, part_of_speech, example, synonyms))
            
            conn.commit()
            conn.close()
            
            self.logger.info(f"Added definition for: {word}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error adding definition: {e}")
            return False
    
    def spell_check(self, word: str) -> Dict:
        """
        Check spelling and suggest corrections.
        
        Args:
            word: Word to check
            
        Returns:
            Dictionary with spelling check results
        """
        word_lower = word.lower().strip()
        
        # Check if word exists in dictionary
        if word_lower in self.dictionary or self.get_definition(word):
            return {
                'word': word,
                'correct': True,
                'suggestions': []
            }
        
        # Generate suggestions using simple edit distance
        suggestions = self._get_spelling_suggestions(word_lower)
        
        return {
            'word': word,
            'correct': False,
            'suggestions': suggestions[:5]  # Top 5 suggestions
        }
    
    def _get_spelling_suggestions(self, word: str) -> List[str]:
        """Generate spelling suggestions for a word."""
        suggestions = []
        
        # Check all dictionary words for similar spellings
        for dict_word in self.dictionary.keys():
            if self._edit_distance(word, dict_word) <= 2:
                suggestions.append(dict_word)
        
        return sorted(suggestions, key=lambda w: self._edit_distance(word, w))
    
    def _edit_distance(self, s1: str, s2: str) -> int:
        """Calculate Levenshtein edit distance between two strings."""
        if len(s1) < len(s2):
            return self._edit_distance(s2, s1)
        
        if len(s2) == 0:
            return len(s1)
        
        previous_row = range(len(s2) + 1)
        for i, c1 in enumerate(s1):
            current_row = [i + 1]
            for j, c2 in enumerate(s2):
                insertions = previous_row[j + 1] + 1
                deletions = current_row[j] + 1
                substitutions = previous_row[j] + (c1 != c2)
                current_row.append(min(insertions, deletions, substitutions))
            previous_row = current_row
        
        return previous_row[-1]
    
    def convert_currency(self, amount: float, from_currency: str, to_currency: str) -> Optional[Dict]:
        """
        Convert currency using offline exchange rates.
        
        Args:
            amount: Amount to convert
            from_currency: Source currency code (e.g., 'USD')
            to_currency: Target currency code (e.g., 'EUR')
            
        Returns:
            Dictionary with conversion results or None if currencies not found
        """
        from_currency = from_currency.upper()
        to_currency = to_currency.upper()
        
        try:
            # Check if same currency
            if from_currency == to_currency:
                return {
                    'amount': amount,
                    'from_currency': from_currency,
                    'to_currency': to_currency,
                    'converted_amount': amount,
                    'rate': 1.0,
                    'success': True
                }
            
            # Get exchange rate
            rate = None
            
            if from_currency in self.exchange_rates:
                if to_currency in self.exchange_rates[from_currency]:
                    rate = self.exchange_rates[from_currency][to_currency]
            
            # Try reverse conversion
            if rate is None and to_currency in self.exchange_rates:
                if from_currency in self.exchange_rates[to_currency]:
                    rate = 1.0 / self.exchange_rates[to_currency][from_currency]
            
            if rate is None:
                self.logger.warning(f"Exchange rate not found for {from_currency} to {to_currency}")
                return None
            
            converted_amount = amount * rate
            
            self.logger.info(f"Converted {amount} {from_currency} to {converted_amount:.2f} {to_currency}")
            
            return {
                'amount': amount,
                'from_currency': from_currency,
                'to_currency': to_currency,
                'converted_amount': round(converted_amount, 2),
                'rate': rate,
                'success': True
            }
            
        except Exception as e:
            self.logger.error(f"Error converting currency: {e}")
            return None
    
    def update_exchange_rate(self, base_currency: str, target_currency: str, rate: float) -> bool:
        """
        Update exchange rate in the database.
        
        Args:
            base_currency: Base currency code
            target_currency: Target currency code
            rate: Exchange rate
            
        Returns:
            True if successful, False otherwise
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT OR REPLACE INTO exchange_rates (base_currency, target_currency, rate, updated_at)
                VALUES (?, ?, ?, CURRENT_TIMESTAMP)
            ''', (base_currency.upper(), target_currency.upper(), rate))
            
            conn.commit()
            conn.close()
            
            # Update in-memory cache
            if base_currency.upper() not in self.exchange_rates:
                self.exchange_rates[base_currency.upper()] = {}
            self.exchange_rates[base_currency.upper()][target_currency.upper()] = rate
            
            self.logger.info(f"Updated exchange rate: {base_currency} to {target_currency} = {rate}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error updating exchange rate: {e}")
            return False
    
    def get_supported_currencies(self) -> List[str]:
        """
        Get list of supported currency codes.
        
        Returns:
            List of currency codes
        """
        currencies = set()
        for base in self.exchange_rates.keys():
            currencies.add(base)
            currencies.update(self.exchange_rates[base].keys())
        return sorted(list(currencies))
    
    def get_cache_stats(self) -> Dict:
        """
        Get statistics about the knowledge cache.
        
        Returns:
            Dictionary containing cache statistics
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Count Wikipedia articles
            cursor.execute('SELECT COUNT(*) FROM wikipedia_cache')
            wiki_count = cursor.fetchone()[0]
            
            # Count dictionary entries
            cursor.execute('SELECT COUNT(*) FROM dictionary')
            dict_count = cursor.fetchone()[0]
            
            # Count exchange rates
            cursor.execute('SELECT COUNT(*) FROM exchange_rates')
            rates_count = cursor.fetchone()[0]
            
            conn.close()
            
            # Get cache file size
            cache_size_mb = self._get_cache_size_mb()
            
            return {
                'total_entries': wiki_count + dict_count + rates_count,
                'wikipedia_articles': wiki_count,
                'dictionary_entries': dict_count,
                'exchange_rates': rates_count,
                'cache_size_mb': cache_size_mb
            }
            
        except Exception as e:
            self.logger.error(f"Error getting cache stats: {e}")
            return {
                'total_entries': 0,
                'wikipedia_articles': 0,
                'dictionary_entries': 0,
                'exchange_rates': 0,
                'cache_size_mb': 0.0
            }
    
    def _get_cache_size_mb(self) -> float:
        """Get cache database size in megabytes."""
        try:
            if os.path.exists(self.db_path):
                size_bytes = os.path.getsize(self.db_path)
                return round(size_bytes / (1024 * 1024), 2)
        except:
            pass
        return 0.0