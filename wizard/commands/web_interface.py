"""
Web Interface Module for Wizard Voice Assistant

This module handles web searches, browser automation, and online content access.
Provides functionality for Google searches, YouTube video searches, and browser control.
"""

import os
import json
import webbrowser
import requests
from typing import List, Dict, Optional, Tuple
from urllib.parse import quote_plus, urljoin, urlparse
import time
from datetime import datetime, timedelta
import re
from bs4 import BeautifulSoup
import sqlite3
import threading

from ..utils.logger import WizardLogger
from ..utils.config_manager import ConfigManager


class WebInterface:
    """
    Handles web search functionality and browser integration.
    
    Features:
    - Web search using search engines
    - Browser automation for opening websites
    - YouTube video search and playback
    - Google Images search
    - Local caching of search results
    """
    
    def __init__(self, config_manager: ConfigManager, logger: WizardLogger):
        """
        Initialize the Web Interface.
        
        Args:
            config_manager: Configuration manager instance
            logger: WizardLogger instance for logging operations
        """
        self.config = config_manager
        self.logger = logger
        self.cache_dir = os.path.join(os.path.dirname(__file__), '..', 'data', 'web_cache')
        self.search_engines = {
            'google': 'https://www.google.com/search?q={}',
            'bing': 'https://www.bing.com/search?q={}',
            'duckduckgo': 'https://duckduckgo.com/?q={}'
        }
        self.youtube_search_url = 'https://www.youtube.com/results?search_query={}'
        self.google_images_url = 'https://www.google.com/search?tbm=isch&q={}'
        
        # Create cache directory if it doesn't exist
        os.makedirs(self.cache_dir, exist_ok=True)
        
        # Initialize cache database
        self.cache_db_path = os.path.join(self.cache_dir, 'search_cache.db')
        self._init_cache_database()
        
        # Initialize search cache
        self.search_cache = self._load_cache()
        
        # Request session for better performance
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        
        # Local search index for offline functionality
        self.local_search_index = {}
        self._load_local_search_index()
        
        self.logger.info("Web Interface initialized successfully")
    
    def _load_cache(self) -> Dict:
        """Load search cache from file."""
        cache_file = os.path.join(self.cache_dir, 'search_cache.json')
        try:
            if os.path.exists(cache_file):
                with open(cache_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            self.logger.error(f"Error loading search cache: {e}")
        return {}
    
    def _init_cache_database(self) -> None:
        """Initialize SQLite database for caching search results."""
        try:
            conn = sqlite3.connect(self.cache_db_path)
            cursor = conn.cursor()
            
            # Create tables for different types of cached content
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS search_results (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    query TEXT NOT NULL,
                    engine TEXT NOT NULL,
                    results TEXT NOT NULL,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(query, engine)
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS youtube_results (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    query TEXT NOT NULL,
                    video_data TEXT NOT NULL,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(query)
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS image_results (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    query TEXT NOT NULL,
                    image_data TEXT NOT NULL,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(query)
                )
            ''')
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            self.logger.error(f"Error initializing cache database: {e}")
    
    def _load_local_search_index(self) -> None:
        """Load local search index for offline functionality."""
        try:
            index_file = os.path.join(self.cache_dir, 'local_search_index.json')
            if os.path.exists(index_file):
                with open(index_file, 'r', encoding='utf-8') as f:
                    self.local_search_index = json.load(f)
            else:
                # Create basic local search index with common topics
                self.local_search_index = {
                    'programming': {
                        'title': 'Programming and Software Development',
                        'content': 'Programming is the process of creating computer software using programming languages.',
                        'keywords': ['coding', 'software', 'development', 'computer', 'algorithm']
                    },
                    'python': {
                        'title': 'Python Programming Language',
                        'content': 'Python is a high-level, interpreted programming language known for its simplicity and readability.',
                        'keywords': ['programming', 'language', 'code', 'script', 'development']
                    },
                    'artificial intelligence': {
                        'title': 'Artificial Intelligence (AI)',
                        'content': 'AI is the simulation of human intelligence in machines programmed to think and learn.',
                        'keywords': ['machine learning', 'neural networks', 'automation', 'technology']
                    },
                    'machine learning': {
                        'title': 'Machine Learning',
                        'content': 'Machine learning is a subset of AI that enables computers to learn without explicit programming.',
                        'keywords': ['ai', 'algorithms', 'data', 'training', 'models']
                    }
                }
                self._save_local_search_index()
        except Exception as e:
            self.logger.error(f"Error loading local search index: {e}")
            self.local_search_index = {}
    
    def _save_local_search_index(self) -> None:
        """Save local search index to file."""
        try:
            index_file = os.path.join(self.cache_dir, 'local_search_index.json')
            with open(index_file, 'w', encoding='utf-8') as f:
                json.dump(self.local_search_index, f, indent=2, ensure_ascii=False)
        except Exception as e:
            self.logger.error(f"Error saving local search index: {e}")
    
    def _search_local_index(self, query: str) -> List[Dict]:
        """Search the local index for offline results."""
        results = []
        query_lower = query.lower()
        
        for topic, data in self.local_search_index.items():
            # Check if query matches topic or keywords
            if (query_lower in topic.lower() or 
                topic.lower() in query_lower or
                any(keyword.lower() in query_lower for keyword in data.get('keywords', []))):
                
                results.append({
                    'title': data['title'],
                    'content': data['content'],
                    'source': 'local_index',
                    'relevance': self._calculate_relevance(query_lower, topic, data)
                })
        
        # Sort by relevance
        results.sort(key=lambda x: x['relevance'], reverse=True)
        return results[:5]  # Return top 5 results
    
    def _calculate_relevance(self, query: str, topic: str, data: Dict) -> float:
        """Calculate relevance score for local search results."""
        score = 0.0
        
        # Exact topic match
        if query == topic.lower():
            score += 10.0
        elif query in topic.lower():
            score += 5.0
        elif topic.lower() in query:
            score += 3.0
        
        # Keyword matches
        keywords = data.get('keywords', [])
        for keyword in keywords:
            if keyword.lower() in query:
                score += 2.0
        
        # Content matches
        content = data.get('content', '').lower()
        query_words = query.split()
        for word in query_words:
            if word in content:
                score += 1.0
        
        return score
    
    def _fetch_web_results(self, query: str, engine: str = 'google') -> List[Dict]:
        """Fetch actual web search results with parsing."""
        try:
            if engine not in self.search_engines:
                engine = 'google'
            
            search_url = self.search_engines[engine]
            
            # For Google, we'll use a different approach to get results
            if engine == 'google':
                return self._fetch_google_results(query)
            elif engine == 'bing':
                return self._fetch_bing_results(query)
            else:
                return self._fetch_duckduckgo_results(query)
                
        except Exception as e:
            self.logger.error(f"Error fetching web results: {e}")
            return []
    
    def _fetch_google_results(self, query: str) -> List[Dict]:
        """Fetch and parse Google search results."""
        try:
            # Use Google Custom Search API alternative or scraping
            # For demo purposes, we'll simulate results
            search_url = f"https://www.google.com/search?q={quote_plus(query)}"
            
            # In a real implementation, you might use:
            # - Google Custom Search API
            # - Web scraping with proper headers
            # - Alternative search APIs
            
            # Simulated results for demo
            results = [
                {
                    'title': f"Search results for: {query}",
                    'url': search_url,
                    'snippet': f"Find information about {query} on Google.",
                    'source': 'google'
                }
            ]
            
            return results
            
        except Exception as e:
            self.logger.error(f"Error fetching Google results: {e}")
            return []
    
    def _fetch_bing_results(self, query: str) -> List[Dict]:
        """Fetch and parse Bing search results."""
        try:
            search_url = f"https://www.bing.com/search?q={quote_plus(query)}"
            
            results = [
                {
                    'title': f"Bing search: {query}",
                    'url': search_url,
                    'snippet': f"Search for {query} on Bing.",
                    'source': 'bing'
                }
            ]
            
            return results
            
        except Exception as e:
            self.logger.error(f"Error fetching Bing results: {e}")
            return []
    
    def _fetch_duckduckgo_results(self, query: str) -> List[Dict]:
        """Fetch and parse DuckDuckGo search results."""
        try:
            search_url = f"https://duckduckgo.com/?q={quote_plus(query)}"
            
            results = [
                {
                    'title': f"DuckDuckGo search: {query}",
                    'url': search_url,
                    'snippet': f"Privacy-focused search for {query}.",
                    'source': 'duckduckgo'
                }
            ]
            
            return results
            
        except Exception as e:
            self.logger.error(f"Error fetching DuckDuckGo results: {e}")
            return []
    
    def _cache_search_results(self, query: str, engine: str, results: List[Dict]) -> None:
        """Cache search results in database."""
        try:
            conn = sqlite3.connect(self.cache_db_path)
            cursor = conn.cursor()
            
            results_json = json.dumps(results)
            
            cursor.execute('''
                INSERT OR REPLACE INTO search_results (query, engine, results)
                VALUES (?, ?, ?)
            ''', (query, engine, results_json))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            self.logger.error(f"Error caching search results: {e}")
    
    def _get_cached_search_results(self, query: str, engine: str) -> Optional[List[Dict]]:
        """Get cached search results from database."""
        try:
            conn = sqlite3.connect(self.cache_db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT results, timestamp FROM search_results
                WHERE query = ? AND engine = ?
                ORDER BY timestamp DESC LIMIT 1
            ''', (query, engine))
            
            result = cursor.fetchone()
            conn.close()
            
            if result:
                results_json, timestamp = result
                # Check if cache is still valid (24 hours)
                cache_time = datetime.fromisoformat(timestamp)
                if datetime.now() - cache_time < timedelta(hours=24):
                    return json.loads(results_json)
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error getting cached search results: {e}")
            return None
    
    def _save_cache(self) -> None:
        """Save search cache to file."""
        cache_file = os.path.join(self.cache_dir, 'search_cache.json')
        try:
            with open(cache_file, 'w', encoding='utf-8') as f:
                json.dump(self.search_cache, f, indent=2, ensure_ascii=False)
        except Exception as e:
            self.logger.error(f"Error saving search cache: {e}")
    
    def _is_cache_valid(self, timestamp: str, max_age_hours: int = 24) -> bool:
        """Check if cached result is still valid."""
        try:
            cache_time = datetime.fromisoformat(timestamp)
            return datetime.now() - cache_time < timedelta(hours=max_age_hours)
        except:
            return False
    
    def search_web(self, query: str, engine: str = 'google', use_cache: bool = True, offline_fallback: bool = True) -> Dict:
        """
        Perform web search using specified search engine with enhanced functionality.
        
        Args:
            query: Search query string
            engine: Search engine to use ('google', 'bing', 'duckduckgo')
            use_cache: Whether to use cached results if available
            offline_fallback: Whether to use local search index if online search fails
            
        Returns:
            Dictionary containing search results and metadata
        """
        try:
            self.logger.info(f"Performing web search: '{query}' using {engine}")
            
            # Check cache first
            if use_cache:
                cached_results = self._get_cached_search_results(query, engine)
                if cached_results:
                    self.logger.info("Returning cached search results")
                    return {
                        'query': query,
                        'engine': engine,
                        'results': cached_results,
                        'timestamp': datetime.now().isoformat(),
                        'source': 'cache',
                        'success': True
                    }
            
            # Try to fetch live web results
            web_results = []
            try:
                web_results = self._fetch_web_results(query, engine)
                if web_results:
                    # Cache the results
                    self._cache_search_results(query, engine, web_results)
            except Exception as e:
                self.logger.warning(f"Failed to fetch live web results: {e}")
            
            # If no web results and offline fallback is enabled, use local index
            if not web_results and offline_fallback:
                self.logger.info("Using local search index for offline results")
                local_results = self._search_local_index(query)
                if local_results:
                    web_results = local_results
            
            # If still no results, create a basic search URL result
            if not web_results:
                if engine not in self.search_engines:
                    engine = 'google'
                
                search_url = self.search_engines[engine].format(quote_plus(query))
                web_results = [
                    {
                        'title': f"Search results for: {query}",
                        'url': search_url,
                        'snippet': f"Opening web search for '{query}' in your default browser.",
                        'source': engine
                    }
                ]
            
            result = {
                'query': query,
                'engine': engine,
                'results': web_results,
                'timestamp': datetime.now().isoformat(),
                'source': 'live' if not offline_fallback else 'mixed',
                'success': True,
                'total_results': len(web_results)
            }
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error performing web search: {e}")
            return {
                'query': query,
                'engine': engine,
                'error': str(e),
                'success': False,
                'timestamp': datetime.now().isoformat()
            }
    
    def open_website(self, url_or_query: str) -> bool:
        """
        Open a website in the default browser.
        If it's not a direct URL, it uses a smart search to find the site.
        
        Args:
            url_or_query: URL to open or website name to find
            
        Returns:
            True if successful, False otherwise
        """
        try:
            self.logger.info(f"Opening: {url_or_query}")
            
            # 1. Check if it's already a full URL
            if url_or_query.startswith(('http://', 'https://')):
                webbrowser.open(url_or_query)
                return True
            
            # 2. Check if it looks like a domain name (contains . and no spaces)
            if '.' in url_or_query and ' ' not in url_or_query:
                url = 'https://' + url_or_query
                webbrowser.open(url)
                return True
            
            # 3. If it's a name or query, use "I'm Feeling Lucky" to go directly to the site
            # This is great for "open apple website", "open my bank", etc.
            search_url = f"https://www.google.com/search?q={quote_plus(url_or_query)}&btnI=1"
            self.logger.info(f"Using 'I'm Feeling Lucky' for: {url_or_query}")
            webbrowser.open(search_url)
            return True
            
        except Exception as e:
            self.logger.error(f"Error opening {url_or_query}: {e}")
            return False
    
    def search_youtube(self, query: str, open_browser: bool = True, get_video_info: bool = False) -> Dict:
        """
        Search for videos on YouTube with enhanced functionality.
        
        Args:
            query: Search query for YouTube videos
            open_browser: Whether to open the search results in browser
            get_video_info: Whether to attempt to get video information
            
        Returns:
            Dictionary containing search information and video data
        """
        try:
            self.logger.info(f"Searching YouTube for: '{query}'")
            
            # Check cache first
            cached_videos = self._get_cached_youtube_results(query)
            if cached_videos:
                self.logger.info("Returning cached YouTube results")
                result = {
                    'query': query,
                    'videos': cached_videos,
                    'timestamp': datetime.now().isoformat(),
                    'source': 'cache',
                    'success': True
                }
                
                if open_browser:
                    search_url = self.youtube_search_url.format(quote_plus(query))
                    webbrowser.open(search_url)
                    result['browser_opened'] = True
                
                return result
            
            search_url = self.youtube_search_url.format(quote_plus(query))
            
            # Try to get video information if requested
            video_data = []
            if get_video_info:
                try:
                    video_data = self._fetch_youtube_video_info(query)
                except Exception as e:
                    self.logger.warning(f"Could not fetch video info: {e}")
            
            # If no video data, create basic result
            if not video_data:
                video_data = [
                    {
                        'title': f"YouTube search: {query}",
                        'url': search_url,
                        'description': f"Search results for '{query}' on YouTube",
                        'duration': 'Unknown',
                        'views': 'Unknown',
                        'channel': 'Various'
                    }
                ]
            
            result = {
                'query': query,
                'search_url': search_url,
                'videos': video_data,
                'timestamp': datetime.now().isoformat(),
                'source': 'live',
                'success': True,
                'total_videos': len(video_data)
            }
            
            # Cache the results
            self._cache_youtube_results(query, video_data)
            
            if open_browser:
                webbrowser.open(search_url)
                result['browser_opened'] = True
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error searching YouTube: {e}")
            return {
                'query': query,
                'error': str(e),
                'success': False,
                'timestamp': datetime.now().isoformat()
            }
    
    def _fetch_youtube_video_info(self, query: str) -> List[Dict]:
        """Fetch YouTube video information (simulated for offline operation)."""
        # In a real implementation, you might use:
        # - YouTube Data API
        # - Web scraping with BeautifulSoup
        # - youtube-dl or yt-dlp libraries
        
        # Simulated video data for demo
        video_data = [
            {
                'title': f"Top video about {query}",
                'url': f"https://www.youtube.com/watch?v=example1",
                'description': f"Learn about {query} in this comprehensive video tutorial.",
                'duration': "10:30",
                'views': "1.2M views",
                'channel': "Educational Channel"
            },
            {
                'title': f"{query} - Complete Guide",
                'url': f"https://www.youtube.com/watch?v=example2",
                'description': f"Everything you need to know about {query}.",
                'duration': "15:45",
                'views': "850K views",
                'channel': "Tutorial Hub"
            }
        ]
        
        return video_data
    
    def _cache_youtube_results(self, query: str, video_data: List[Dict]) -> None:
        """Cache YouTube search results."""
        try:
            conn = sqlite3.connect(self.cache_db_path)
            cursor = conn.cursor()
            
            video_json = json.dumps(video_data)
            
            cursor.execute('''
                INSERT OR REPLACE INTO youtube_results (query, video_data)
                VALUES (?, ?)
            ''', (query, video_json))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            self.logger.error(f"Error caching YouTube results: {e}")
    
    def _get_cached_youtube_results(self, query: str) -> Optional[List[Dict]]:
        """Get cached YouTube results."""
        try:
            conn = sqlite3.connect(self.cache_db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT video_data, timestamp FROM youtube_results
                WHERE query = ?
                ORDER BY timestamp DESC LIMIT 1
            ''', (query,))
            
            result = cursor.fetchone()
            conn.close()
            
            if result:
                video_json, timestamp = result
                # Check if cache is still valid (6 hours for video content)
                cache_time = datetime.fromisoformat(timestamp)
                if datetime.now() - cache_time < timedelta(hours=6):
                    return json.loads(video_json)
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error getting cached YouTube results: {e}")
            return None
    
    def search_google_images(self, query: str, open_browser: bool = True, get_image_info: bool = False) -> Dict:
        """
        Search for images on Google Images with enhanced functionality.
        
        Args:
            query: Search query for images
            open_browser: Whether to open the search results in browser
            get_image_info: Whether to attempt to get image information
            
        Returns:
            Dictionary containing search information and image data
        """
        try:
            self.logger.info(f"Searching Google Images for: '{query}'")
            
            # Check cache first
            cached_images = self._get_cached_image_results(query)
            if cached_images:
                self.logger.info("Returning cached image results")
                result = {
                    'query': query,
                    'images': cached_images,
                    'timestamp': datetime.now().isoformat(),
                    'source': 'cache',
                    'success': True
                }
                
                if open_browser:
                    search_url = self.google_images_url.format(quote_plus(query))
                    webbrowser.open(search_url)
                    result['browser_opened'] = True
                
                return result
            
            search_url = self.google_images_url.format(quote_plus(query))
            
            # Try to get image information if requested
            image_data = []
            if get_image_info:
                try:
                    image_data = self._fetch_image_info(query)
                except Exception as e:
                    self.logger.warning(f"Could not fetch image info: {e}")
            
            # If no image data, create basic result
            if not image_data:
                image_data = [
                    {
                        'title': f"Images of {query}",
                        'url': search_url,
                        'description': f"Google Images search results for '{query}'",
                        'thumbnail_url': None,
                        'source_site': 'Google Images',
                        'dimensions': 'Various'
                    }
                ]
            
            result = {
                'query': query,
                'search_url': search_url,
                'images': image_data,
                'timestamp': datetime.now().isoformat(),
                'source': 'live',
                'success': True,
                'total_images': len(image_data)
            }
            
            # Cache the results
            self._cache_image_results(query, image_data)
            
            if open_browser:
                webbrowser.open(search_url)
                result['browser_opened'] = True
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error searching Google Images: {e}")
            return {
                'query': query,
                'error': str(e),
                'success': False,
                'timestamp': datetime.now().isoformat()
            }
    
    def _fetch_image_info(self, query: str) -> List[Dict]:
        """Fetch image information (simulated for offline operation)."""
        # In a real implementation, you might use:
        # - Google Custom Search API with image search
        # - Web scraping with BeautifulSoup
        # - Alternative image search APIs
        
        # Simulated image data for demo
        image_data = [
            {
                'title': f"High quality {query} image",
                'url': f"https://example.com/images/{query.replace(' ', '_')}_1.jpg",
                'description': f"Professional photo of {query}",
                'thumbnail_url': f"https://example.com/thumbs/{query.replace(' ', '_')}_1_thumb.jpg",
                'source_site': "Stock Photos",
                'dimensions': "1920x1080"
            },
            {
                'title': f"{query} illustration",
                'url': f"https://example.com/images/{query.replace(' ', '_')}_2.jpg",
                'description': f"Artistic illustration of {query}",
                'thumbnail_url': f"https://example.com/thumbs/{query.replace(' ', '_')}_2_thumb.jpg",
                'source_site': "Art Gallery",
                'dimensions': "1280x720"
            }
        ]
        
        return image_data
    
    def _cache_image_results(self, query: str, image_data: List[Dict]) -> None:
        """Cache image search results."""
        try:
            conn = sqlite3.connect(self.cache_db_path)
            cursor = conn.cursor()
            
            image_json = json.dumps(image_data)
            
            cursor.execute('''
                INSERT OR REPLACE INTO image_results (query, image_data)
                VALUES (?, ?)
            ''', (query, image_json))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            self.logger.error(f"Error caching image results: {e}")
    
    def _get_cached_image_results(self, query: str) -> Optional[List[Dict]]:
        """Get cached image results."""
        try:
            conn = sqlite3.connect(self.cache_db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT image_data, timestamp FROM image_results
                WHERE query = ?
                ORDER BY timestamp DESC LIMIT 1
            ''', (query,))
            
            result = cursor.fetchone()
            conn.close()
            
            if result:
                image_json, timestamp = result
                # Check if cache is still valid (12 hours for image content)
                cache_time = datetime.fromisoformat(timestamp)
                if datetime.now() - cache_time < timedelta(hours=12):
                    return json.loads(image_json)
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error getting cached image results: {e}")
            return None
    
    def get_popular_websites(self) -> List[Dict]:
        """
        Get a list of popular websites for quick access.
        
        Returns:
            List of popular website dictionaries
        """
        return [
            {'name': 'Google', 'url': 'https://www.google.com'},
            {'name': 'YouTube', 'url': 'https://www.youtube.com'},
            {'name': 'Wikipedia', 'url': 'https://www.wikipedia.org'},
            {'name': 'GitHub', 'url': 'https://www.github.com'},
            {'name': 'Stack Overflow', 'url': 'https://stackoverflow.com'},
            {'name': 'Reddit', 'url': 'https://www.reddit.com'},
            {'name': 'Twitter', 'url': 'https://www.twitter.com'},
            {'name': 'Facebook', 'url': 'https://www.facebook.com'},
            {'name': 'LinkedIn', 'url': 'https://www.linkedin.com'},
            {'name': 'Amazon', 'url': 'https://www.amazon.com'}
        ]
    
    def clear_cache(self) -> bool:
        """
        Clear the search cache.
        
        Returns:
            True if successful, False otherwise
        """
        try:
            self.search_cache = {}
            self._save_cache()
            self.logger.info("Search cache cleared successfully")
            return True
        except Exception as e:
            self.logger.error(f"Error clearing cache: {e}")
            return False
    
    def get_cache_stats(self) -> Dict:
        """
        Get statistics about the search cache.
        
        Returns:
            Dictionary containing cache statistics
        """
        try:
            conn = sqlite3.connect(self.cache_db_path)
            cursor = conn.cursor()
            
            # Get search results count
            cursor.execute('SELECT COUNT(*) FROM search_results')
            search_count = cursor.fetchone()[0]
            
            # Get YouTube results count
            cursor.execute('SELECT COUNT(*) FROM youtube_results')
            youtube_count = cursor.fetchone()[0]
            
            # Get image results count
            cursor.execute('SELECT COUNT(*) FROM image_results')
            image_count = cursor.fetchone()[0]
            
            conn.close()
            
            return {
                'total_entries': len(self.search_cache),
                'search_results': search_count,
                'youtube_results': youtube_count,
                'image_results': image_count,
                'local_index_entries': len(self.local_search_index),
                'cache_size_mb': self._get_cache_size_mb(),
                'database_size_mb': self._get_database_size_mb()
            }
            
        except Exception as e:
            self.logger.error(f"Error getting cache stats: {e}")
            return {
                'total_entries': len(self.search_cache),
                'search_results': 0,
                'youtube_results': 0,
                'image_results': 0,
                'local_index_entries': len(self.local_search_index),
                'cache_size_mb': self._get_cache_size_mb(),
                'database_size_mb': 0.0
            }
    
    def _get_database_size_mb(self) -> float:
        """Get database size in megabytes."""
        try:
            if os.path.exists(self.cache_db_path):
                size_bytes = os.path.getsize(self.cache_db_path)
                return round(size_bytes / (1024 * 1024), 2)
        except:
            pass
        return 0.0
    
    def add_to_local_index(self, topic: str, title: str, content: str, keywords: List[str] = None) -> bool:
        """
        Add an entry to the local search index.
        
        Args:
            topic: Topic identifier
            title: Title of the content
            content: Content description
            keywords: List of keywords for searching
            
        Returns:
            True if successful, False otherwise
        """
        try:
            if keywords is None:
                keywords = []
            
            self.local_search_index[topic.lower()] = {
                'title': title,
                'content': content,
                'keywords': keywords,
                'added_date': datetime.now().isoformat()
            }
            
            self._save_local_search_index()
            self.logger.info(f"Added '{topic}' to local search index")
            return True
            
        except Exception as e:
            self.logger.error(f"Error adding to local index: {e}")
            return False
    
    def search_with_fallback(self, query: str, engine: str = 'google') -> Dict:
        """
        Perform search with automatic fallback to local index if online search fails.
        
        Args:
            query: Search query
            engine: Preferred search engine
            
        Returns:
            Search results with fallback information
        """
        try:
            # Try online search first
            result = self.search_web(query, engine, use_cache=True, offline_fallback=False)
            
            if result['success'] and result.get('results'):
                return result
            
            # Fallback to local search
            self.logger.info("Online search failed, using local fallback")
            local_results = self._search_local_index(query)
            
            if local_results:
                return {
                    'query': query,
                    'engine': 'local_index',
                    'results': local_results,
                    'timestamp': datetime.now().isoformat(),
                    'source': 'local_fallback',
                    'success': True,
                    'total_results': len(local_results),
                    'fallback_used': True
                }
            else:
                return {
                    'query': query,
                    'engine': engine,
                    'results': [],
                    'timestamp': datetime.now().isoformat(),
                    'source': 'none',
                    'success': False,
                    'error': 'No results found online or locally'
                }
                
        except Exception as e:
            self.logger.error(f"Error in search with fallback: {e}")
            return {
                'query': query,
                'engine': engine,
                'error': str(e),
                'success': False,
                'timestamp': datetime.now().isoformat()
            }
    
    def get_search_suggestions(self, partial_query: str) -> List[str]:
        """
        Get search suggestions based on partial query.
        
        Args:
            partial_query: Partial search query
            
        Returns:
            List of suggested search terms
        """
        suggestions = []
        partial_lower = partial_query.lower()
        
        # Check local index for matches
        for topic in self.local_search_index.keys():
            if partial_lower in topic or topic.startswith(partial_lower):
                suggestions.append(topic.title())
        
        # Add common search suggestions
        common_suggestions = [
            "programming tutorial",
            "python programming",
            "machine learning",
            "artificial intelligence",
            "web development",
            "data science",
            "software engineering",
            "computer science"
        ]
        
        for suggestion in common_suggestions:
            if partial_lower in suggestion.lower() and suggestion not in suggestions:
                suggestions.append(suggestion)
        
        return suggestions[:10]  # Return top 10 suggestions
    
    def _get_cache_size_mb(self) -> float:
        """Get cache size in megabytes."""
        try:
            cache_file = os.path.join(self.cache_dir, 'search_cache.json')
            if os.path.exists(cache_file):
                size_bytes = os.path.getsize(cache_file)
                return round(size_bytes / (1024 * 1024), 2)
        except:
            pass
        return 0.0