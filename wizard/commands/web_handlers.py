"""
Web Command Handlers for Wizard Voice Assistant

This module contains command handlers for web-related voice commands.
Integrates with the WebInterface to provide voice-controlled web functionality.
"""

import re
from typing import Dict, Any, List, Optional

from .web_interface import WebInterface
from ..utils.logger import WizardLogger
from ..utils.config_manager import ConfigManager


class WebHandlers:
    """
    Handles voice commands related to web searches and browser operations.
    
    Supported commands:
    - Web searches ("search for cats", "google python tutorial")
    - YouTube searches ("search youtube for music", "play video about cooking")
    - Image searches ("show me images of dogs", "search images for cars")
    - Website opening ("open google", "go to youtube")
    """
    
    def __init__(self, config_manager: ConfigManager, logger: WizardLogger):
        """
        Initialize web command handlers.
        
        Args:
            config_manager: Configuration manager instance
            logger: WizardLogger instance
        """
        self.config = config_manager
        self.logger = logger
        self.web_interface = WebInterface(config_manager, logger)
        
        # Command patterns for web operations
        self.search_patterns = [
            r"search (?:for |about )?(.+)",
            r"google (.+)",
            r"look up (.+)",
            r"find (?:information about |info about )?(.+)",
            r"web search (?:for )?(.+)",
            r"internet search (?:for )?(.+)"
        ]
        
        self.youtube_patterns = [
            r"search youtube (?:for )?(.+)",
            r"youtube (.+)",
            r"play video (?:about |of )?(.+)",
            r"find video (?:about |of )?(.+)",
            r"watch video (?:about |of )?(.+)",
            r"show me video (?:about |of )?(.+)"
        ]
        
        self.image_patterns = [
            r"search images (?:for |of )?(.+)",
            r"show me images (?:of |about )?(.+)",
            r"find pictures (?:of |about )?(.+)",
            r"google images (.+)",
            r"image search (?:for )?(.+)",
            r"pictures of (.+)"
        ]
        
        self.website_patterns = [
            r"open (.+)",
            r"go to (.+)",
            r"visit (.+)",
            r"navigate to (.+)",
            r"browse to (.+)",
            r"load (.+)"
        ]
        
        self.logger.info("Web handlers initialized successfully")
    
    def handle_web_search(self, command_text: str, entities: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle web search commands with enhanced functionality.
        
        Args:
            command_text: The original command text
            entities: Extracted entities from the command
            
        Returns:
            Response dictionary with search results
        """
        try:
            # Extract search query from command
            query = self._extract_search_query(command_text, self.search_patterns)
            
            if not query:
                return {
                    'success': False,
                    'message': "I couldn't understand what you want to search for. Please try again.",
                    'speak': True
                }
            
            # Determine search engine from command if specified
            engine = 'google'  # default
            command_lower = command_text.lower()
            if 'bing' in command_lower:
                engine = 'bing'
            elif 'duckduckgo' in command_lower or 'duck duck go' in command_lower:
                engine = 'duckduckgo'
            
            # Perform web search with enhanced functionality
            search_result = self.web_interface.search_web(query, engine, use_cache=True, offline_fallback=True)
            
            if search_result['success']:
                # Open the search in browser if we have a URL
                if search_result.get('results') and len(search_result['results']) > 0:
                    first_result = search_result['results'][0]
                    if 'url' in first_result:
                        self.web_interface.open_website(first_result['url'])
                    elif search_result.get('source') != 'local_index':
                        # Open search engine with query
                        search_engines = {
                            'google': f"https://www.google.com/search?q={query}",
                            'bing': f"https://www.bing.com/search?q={query}",
                            'duckduckgo': f"https://duckduckgo.com/?q={query}"
                        }
                        self.web_interface.open_website(search_engines.get(engine, search_engines['google']))
                
                # Create response message
                source_info = ""
                if search_result.get('source') == 'cache':
                    source_info = " (from cache)"
                elif search_result.get('source') == 'local_fallback':
                    source_info = " (from offline knowledge)"
                elif search_result.get('fallback_used'):
                    source_info = " (using offline fallback)"
                
                total_results = search_result.get('total_results', 0)
                response_message = f"I found {total_results} result{'s' if total_results != 1 else ''} for '{query}'{source_info}."
                
                if search_result.get('source') != 'local_index':
                    response_message += " I've opened the search results in your browser."
                
                return {
                    'success': True,
                    'message': response_message,
                    'speak': True,
                    'data': search_result
                }
            else:
                error_msg = search_result.get('error', 'Unknown error')
                return {
                    'success': False,
                    'message': f"I couldn't search for '{query}'. {error_msg}",
                    'speak': True
                }
                
        except Exception as e:
            self.logger.error(f"Error handling web search: {e}")
            return {
                'success': False,
                'message': "I encountered an error while trying to search the web.",
                'speak': True
            }
    
    def handle_youtube_search(self, command_text: str, entities: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle YouTube search commands with enhanced functionality.
        
        Args:
            command_text: The original command text
            entities: Extracted entities from the command
            
        Returns:
            Response dictionary with YouTube search results
        """
        try:
            # Extract search query from command
            query = self._extract_search_query(command_text, self.youtube_patterns)
            
            if not query:
                return {
                    'success': False,
                    'message': "I couldn't understand what video you want to search for. Please try again.",
                    'speak': True
                }
            
            # Perform YouTube search with enhanced functionality
            search_result = self.web_interface.search_youtube(query, open_browser=True, get_video_info=True)
            
            if search_result['success']:
                # Create detailed response message
                total_videos = search_result.get('total_videos', 0)
                source_info = ""
                if search_result.get('source') == 'cache':
                    source_info = " (from cache)"
                
                response_message = f"I found {total_videos} video{'s' if total_videos != 1 else ''} about '{query}'{source_info}."
                
                if search_result.get('browser_opened'):
                    response_message += " I've opened YouTube with the search results."
                
                # Add video information if available
                videos = search_result.get('videos', [])
                if videos and len(videos) > 0 and videos[0].get('title') != f"YouTube search: {query}":
                    top_video = videos[0]
                    response_message += f" The top result is '{top_video.get('title', 'Unknown')}' by {top_video.get('channel', 'Unknown channel')}."
                
                return {
                    'success': True,
                    'message': response_message,
                    'speak': True,
                    'data': search_result
                }
            else:
                return {
                    'success': False,
                    'message': f"I couldn't search YouTube for '{query}'. Please try again.",
                    'speak': True
                }
                
        except Exception as e:
            self.logger.error(f"Error handling YouTube search: {e}")
            return {
                'success': False,
                'message': "I encountered an error while trying to search YouTube.",
                'speak': True
            }
    
    def handle_image_search(self, command_text: str, entities: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle image search commands with enhanced functionality.
        
        Args:
            command_text: The original command text
            entities: Extracted entities from the command
            
        Returns:
            Response dictionary with image search results
        """
        try:
            # Extract search query from command
            query = self._extract_search_query(command_text, self.image_patterns)
            
            if not query:
                return {
                    'success': False,
                    'message': "I couldn't understand what images you want to search for. Please try again.",
                    'speak': True
                }
            
            # Perform image search with enhanced functionality
            search_result = self.web_interface.search_google_images(query, open_browser=True, get_image_info=True)
            
            if search_result['success']:
                # Create detailed response message
                total_images = search_result.get('total_images', 0)
                source_info = ""
                if search_result.get('source') == 'cache':
                    source_info = " (from cache)"
                
                response_message = f"I found {total_images} image{'s' if total_images != 1 else ''} of '{query}'{source_info}."
                
                if search_result.get('browser_opened'):
                    response_message += " I've opened Google Images with the search results."
                
                # Add image information if available
                images = search_result.get('images', [])
                if images and len(images) > 0 and images[0].get('title') != f"Images of {query}":
                    top_image = images[0]
                    response_message += f" The top result is '{top_image.get('title', 'Unknown')}' from {top_image.get('source_site', 'Unknown source')}."
                
                return {
                    'success': True,
                    'message': response_message,
                    'speak': True,
                    'data': search_result
                }
            else:
                return {
                    'success': False,
                    'message': f"I couldn't search for images of '{query}'. Please try again.",
                    'speak': True
                }
                
        except Exception as e:
            self.logger.error(f"Error handling image search: {e}")
            return {
                'success': False,
                'message': "I encountered an error while trying to search for images.",
                'speak': True
            }
    
    def handle_website_open(self, command_text: str, entities: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle website opening commands.
        
        Args:
            command_text: The original command text
            entities: Extracted entities from the command
            
        Returns:
            Response dictionary with website opening results
        """
        try:
            # Extract website from command
            website = self._extract_search_query(command_text, self.website_patterns)
            
            if not website:
                # Try getting from entities if extracting failed
                website = entities.get('website') or entities.get('query')
                
            if not website:
                return {
                    'success': False,
                    'message': "I couldn't understand which website you want to open. Please try again.",
                    'speak': True
                }
            
            # Check if it's a popular website shortcut or a formatted URL
            website_url = self._resolve_website_shortcut(website)
            
            # Open the website
            success = self.web_interface.open_website(website_url)
            
            if success:
                display_name = website_url if website_url.startswith('http') else website
                response_message = f"I've opened {display_name} in your browser."
                
                return {
                    'success': True,
                    'message': response_message,
                    'speak': True,
                    'data': {'website': website, 'url': website_url}
                }
            else:
                return {
                    'success': False,
                    'message': f"I couldn't open {website}. Please check the website name.",
                    'speak': True
                }
                
        except Exception as e:
            self.logger.error(f"Error handling website open: {e}")
            return {
                'success': False,
                'message': "I encountered an error while trying to open the website.",
                'speak': True
            }
    
    def _extract_search_query(self, command_text: str, patterns: List[str]) -> Optional[str]:
        """
        Extract search query from command text using regex patterns.
        
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
    
    def _resolve_website_shortcut(self, website: str) -> str:
        """
        Resolve website shortcuts or names to full URLs.
        
        Args:
            website: Website name, shortcut, or partial URL
            
        Returns:
            Full URL for the website
        """
        website_lower = website.lower().strip()
        
        # Remove common "website" related suffixes that might be captured
        clean_name = re.sub(r'\s+(?:website|official\s+site|site|web\s+page|home\s+page|online)$', '', website_lower)
        clean_name = clean_name.strip()
        
        # Common website shortcuts and their URLs
        shortcuts = {
            'google': 'https://www.google.com',
            'youtube': 'https://www.youtube.com',
            'wikipedia': 'https://www.wikipedia.org',
            'github': 'https://www.github.com',
            'stackoverflow': 'https://stackoverflow.com',
            'stack overflow': 'https://stackoverflow.com',
            'reddit': 'https://www.reddit.com',
            'twitter': 'https://www.twitter.com',
            'x': 'https://www.x.com',
            'facebook': 'https://www.facebook.com',
            'linkedin': 'https://www.linkedin.com',
            'amazon': 'https://www.amazon.com',
            'netflix': 'https://www.netflix.com',
            'instagram': 'https://www.instagram.com',
            'apple': 'https://www.apple.com',
            'microsoft': 'https://www.microsoft.com',
            'google maps': 'https://maps.google.com',
            'gmail': 'https://mail.google.com',
            'yahoo': 'https://www.yahoo.com',
            'bing': 'https://www.bing.com'
        }
        
        # 1. Check for exact shortcut match
        if clean_name in shortcuts:
            return shortcuts[clean_name]
            
        # 1a. Check for shortcut within the name (e.g., "apple phone" -> "apple")
        for shortcut, url in shortcuts.items():
            if shortcut == clean_name or (len(shortcut) > 3 and shortcut in clean_name):
                # If the shortcut name is significant and part of the query, it's likely that site
                return url
        
        # 2. If it already looks like a URL, return it
        if '.' in clean_name and ' ' not in clean_name:
            if not clean_name.startswith(('http://', 'https://')):
                return 'https://' + clean_name
            return clean_name
            
        # 3. Simple one-word names get a .com treatment
        if ' ' not in clean_name and len(clean_name) > 0:
            return f"https://www.{clean_name}.com"
        
        # 4. If it's multiple words, it's likely a search query for the site
        # We return it as-is, and WebInterface.open_website will handle it 
        # or we could return a search URL.
        return clean_name
    
    def handle_search_suggestions(self, command_text: str, entities: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle search suggestion requests.
        
        Args:
            command_text: The original command text
            entities: Extracted entities from the command
            
        Returns:
            Response dictionary with search suggestions
        """
        try:
            # Extract partial query from command
            suggestion_patterns = [
                r"suggest searches? (?:for )?(.+)",
                r"what can I search (?:for )?(?:about )?(.+)",
                r"search suggestions? (?:for )?(.+)"
            ]
            
            partial_query = self._extract_search_query(command_text, suggestion_patterns)
            
            if not partial_query:
                # Provide general suggestions
                suggestions = [
                    "programming tutorial",
                    "python programming", 
                    "machine learning",
                    "artificial intelligence",
                    "web development"
                ]
            else:
                suggestions = self.web_interface.get_search_suggestions(partial_query)
            
            if suggestions:
                suggestion_list = ", ".join(suggestions[:5])
                response_message = f"Here are some search suggestions: {suggestion_list}"
                
                return {
                    'success': True,
                    'message': response_message,
                    'speak': True,
                    'data': {'suggestions': suggestions}
                }
            else:
                return {
                    'success': False,
                    'message': "I couldn't find any search suggestions for that topic.",
                    'speak': True
                }
                
        except Exception as e:
            self.logger.error(f"Error handling search suggestions: {e}")
            return {
                'success': False,
                'message': "I encountered an error while getting search suggestions.",
                'speak': True
            }
    
    def get_supported_commands(self) -> List[str]:
        """
        Get list of supported web commands.
        
        Returns:
            List of example commands
        """
        return [
            "search for cats",
            "google python tutorial",
            "look up weather forecast",
            "web search for machine learning",
            "search youtube for music",
            "play video about cooking",
            "watch video of programming",
            "show me images of dogs",
            "search images for cars",
            "pictures of nature",
            "open google",
            "go to youtube",
            "visit wikipedia",
            "browse to github",
            "suggest searches for programming"
        ]