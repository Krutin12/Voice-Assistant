"""
Web Browser Module
Handles web browsing operations like opening Google, searching, and opening websites
"""

import webbrowser
import re
from typing import Optional

# Import content filter for safe search enforcement
try:
    from wizard.utils.content_filter import create_content_filter
    _content_filter = None
    
    def _get_content_filter():
        """Get or create content filter instance"""
        global _content_filter
        if _content_filter is None:
            _content_filter = create_content_filter()
        return _content_filter
        
except ImportError:
    # Fallback if content filter is not available
    def _get_content_filter():
        return None

# Common website mappings
WEBSITE_MAP = {
    'google': 'https://www.google.com',
    'youtube': 'https://www.youtube.com',
    'facebook': 'https://www.facebook.com',
    'twitter': 'https://www.twitter.com',
    'gmail': 'https://www.gmail.com',
    'github': 'https://www.github.com',
    'reddit': 'https://www.reddit.com',
    'instagram': 'https://www.instagram.com',
    'linkedin': 'https://www.linkedin.com',
    'amazon': 'https://www.amazon.com',
    'netflix': 'https://www.netflix.com',
    'wikipedia': 'https://www.wikipedia.org',
    'stackoverflow': 'https://stackoverflow.com',
    'stack overflow': 'https://stackoverflow.com'
}

def _format_blocked_message_with_alternatives(reason: str, suggested_alternatives: list[str], 
                                           blocked_query: Optional[str] = None) -> str:
    """
    Format a user-friendly blocked message with helpful alternatives.
    
    Args:
        reason: Reason why content was blocked
        suggested_alternatives: List of alternative suggestions
        blocked_query: Original search query that was blocked (optional)
        
    Returns:
        Formatted message with alternatives
    """
    message = f"I can't access that content: {reason}"
    
    if suggested_alternatives:
        message += "\n\nHere are some helpful alternatives:"
        
        # Limit to 3 suggestions for voice-friendly response
        for i, suggestion in enumerate(suggested_alternatives[:3], 1):
            if "Try searching for:" in suggestion:
                # Extract just the search term for cleaner voice response
                term = suggestion.replace("Try searching for:", "").strip()
                message += f"\n{i}. Search for '{term}'"
            elif "Visit" in suggestion and ":" in suggestion:
                # Extract website name and URL
                parts = suggestion.split(":", 1)
                if len(parts) >= 2:
                    name_part = parts[0].replace("Visit", "").strip()
                    url_part = parts[1].split(" - ")[0].strip()  # Remove description for voice
                    message += f"\n{i}. Try {name_part} at {url_part}"
            else:
                # Use suggestion as-is but keep it concise
                message += f"\n{i}. {suggestion}"
    
    if blocked_query:
        message += f"\n\nYou can also try modifying your search terms to find appropriate content."
    
    return message
def open_google():
    """Open Google in the default browser"""
    try:
        webbrowser.open('https://www.google.com')
        return "Opening Google"
    except Exception as e:
        return f"Error opening Google: {str(e)}"

def _apply_content_filtering(url: str, query: str = "") -> tuple[bool, str, Optional[str], list[str]]:
    """
    Apply content filtering to a URL and query.
    
    Args:
        url: URL to filter
        query: Search query (if applicable)
        
    Returns:
        Tuple of (allowed, reason, modified_url, suggested_alternatives)
    """
    content_filter = _get_content_filter()
    if not content_filter:
        return True, "Content filtering not available", None, []
    
    try:
        from wizard.utils.content_filter import WebRequest, RequestType
        
        # Determine request type
        request_type = RequestType.SEARCH if query else RequestType.WEBSITE
        
        # Create web request
        request = WebRequest(
            url=url,
            query=query,
            request_type=request_type
        )
        
        # Apply filtering
        result = content_filter.filter_request(request)
        
        return result.allowed, result.reason, result.modified_url, result.suggested_alternatives
        
    except Exception as e:
        # If filtering fails, allow by default but log the error
        return True, f"Content filtering error: {str(e)}", None, []


def search_google(query):
    """Search Google with the given query"""
    try:
        if not query:
            return "What would you like me to search for?"
        
        # URL encode the query
        query_encoded = query.replace(' ', '+')
        url = f"https://www.google.com/search?q={query_encoded}"
        
        # Apply content filtering
        allowed, reason, modified_url, suggested_alternatives = _apply_content_filtering(url, query)
        
        if not allowed:
            return f"Search blocked: {reason}"
        
        # Use modified URL if safe search was applied
        final_url = modified_url or url
        
        webbrowser.open(final_url)
        
        # Inform user if safe search was applied
        if modified_url and modified_url != url:
            return f"Searching Google for {query} (with safe search enabled)"
        else:
            return f"Searching Google for {query}"
            
    except Exception as e:
        return f"Error searching Google: {str(e)}"

def open_website(url_or_name):
    """Open a website by name or URL"""
    try:
        url_or_name = url_or_name.lower().strip()
        final_url = ""
        
        # Check if it's already a URL
        if url_or_name.startswith('http://') or url_or_name.startswith('https://'):
            final_url = url_or_name
        # Check website map
        elif url_or_name in WEBSITE_MAP:
            final_url = WEBSITE_MAP[url_or_name]
        # Try adding .com
        elif '.' not in url_or_name:
            final_url = f"https://www.{url_or_name}.com"
        else:
            # Assume it's a domain
            final_url = f"https://{url_or_name}"
        
        # Apply content filtering
        allowed, reason, modified_url, suggested_alternatives = _apply_content_filtering(final_url)
        
        if not allowed:
            return f"Website blocked: {reason}"
        
        # Use modified URL if safe search was applied
        url_to_open = modified_url or final_url
        
        webbrowser.open(url_to_open)
        
        # Inform user if safe search was applied
        if modified_url and modified_url != final_url:
            return f"Opening {url_or_name} (with safe search enabled)"
        else:
            return f"Opening {url_or_name}"
            
    except Exception as e:
        return f"Error opening website: {str(e)}"

def search_youtube(query, auto_play=True):
    """Search YouTube and optionally play the first result with reliable click simulation"""
    try:
        if not query:
            return "What would you like me to search for on YouTube?"
        
        query_encoded = query.replace(' ', '+')
        url = f"https://www.youtube.com/results?search_query={query_encoded}"
        
        # Apply content filtering
        allowed, reason, modified_url, suggested_alternatives = _apply_content_filtering(url, query)
        
        if not allowed:
            return f"YouTube search blocked: {reason}"
        
        # Use modified URL if safe search was applied
        final_url = modified_url or url
        
        webbrowser.open(final_url)
        
        if auto_play:
            # Wait for page to load (YouTube can be slow)
            import time
            import pyautogui
            time.sleep(10)  # Wait for page to fully load
            
            # Navigate to the first video result using Tab
            # YouTube search page structure: 
            #   Tab 1 → Skip navigation / logo area
            #   Tab 2 → Search bar
            #   Tab 3 → First video result thumbnail
            # We need to tab past the top navigation to reach the first video
            
            # Click somewhere neutral first to ensure page has focus
            pyautogui.click(x=640, y=400)
            time.sleep(0.5)
            
            # Use Tab to navigate to first video result
            # On YouTube search results, the first few tabs go through:
            # logo, search bar, voice search, filter - then first video
            for i in range(6):
                pyautogui.press('tab')
                time.sleep(0.3)
            
            # Press Enter to open the first video
            pyautogui.press('enter')
            
            # Wait for video page to load
            time.sleep(6)
            
            # Use YouTube's 'K' keyboard shortcut to play/pause (ensures video plays)
            pyautogui.press('k')
            time.sleep(1)
            
            # Scroll down slightly for a better view (hides search bar)
            pyautogui.scroll(-3)
            
            return f"Opening YouTube and playing {query}"
        
        return f"Searching YouTube for {query}"
            
    except Exception as e:
        return f"Error searching YouTube: {str(e)}"



def search_images(query):
    """Search Google Images with the given query"""
    try:
        if not query:
            return "What images would you like me to search for?"
        
        query_encoded = query.replace(' ', '+')
        url = f"https://www.google.com/search?tbm=isch&q={query_encoded}"
        
        # Apply content filtering
        allowed, reason, modified_url, suggested_alternatives = _apply_content_filtering(url, query)
        
        if not allowed:
            return f"Image search blocked: {reason}"
        
        # Use modified URL if safe search was applied
        final_url = modified_url or url
        
        webbrowser.open(final_url)
        
        # Inform user if safe search was applied
        if modified_url and modified_url != url:
            return f"Searching Google Images for {query} (with safe search enabled)"
        else:
            return f"Searching Google Images for {query}"
            
    except Exception as e:
        return f"Error searching images: {str(e)}"

def open_specific_site(site_name):
    """Open a specific site from the mapping"""
    try:
        site_name = site_name.lower().strip()
        if site_name in WEBSITE_MAP:
            url = WEBSITE_MAP[site_name]
            webbrowser.open(url)
            return f"Opening {site_name}"
        else:
            return open_website(site_name)
    except Exception as e:
        return f"Error opening site: {str(e)}"

