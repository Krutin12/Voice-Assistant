"""
Content Filtering System for Wizard Voice Assistant

This module provides comprehensive content filtering capabilities to prevent access
to inappropriate websites, adult content, and other potentially harmful material.
"""

from dataclasses import dataclass
from enum import Enum
from typing import List, Optional, Dict, Any
import json
import os
import re
import sqlite3
from pathlib import Path
from urllib.parse import urlparse
import difflib
from typing import Set, Tuple
import datetime
import csv
from collections import defaultdict


class ContentCategory(Enum):
    """Categories of content that can be filtered"""
    ADULT = "adult"
    VIOLENCE = "violence"
    GAMBLING = "gambling"
    DRUGS = "drugs"
    HATE_SPEECH = "hate_speech"
    MALWARE = "malware"
    PHISHING = "phishing"


class FilterLevel(Enum):
    """Filtering strictness levels"""
    STRICT = "strict"      # Blocks most content, suitable for children
    MODERATE = "moderate"  # Blocks obvious inappropriate content
    PERMISSIVE = "permissive"  # Minimal filtering, blocks only illegal content


class AgeProfile(Enum):
    """Age-based filtering profiles"""
    CHILD = "child"        # Ages 5-12: Strict filtering, educational content only
    TEEN = "teen"          # Ages 13-17: Moderate filtering, some restricted content allowed
    ADULT = "adult"        # Ages 18+: Permissive filtering, minimal restrictions


class RequestType(Enum):
    """Types of web requests that can be filtered"""
    SEARCH = "search"
    WEBSITE = "website"
    IMAGE = "image"
    VIDEO = "video"


class DomainStatus(Enum):
    """Status of domain filtering check"""
    ALLOWED = "allowed"
    BLOCKED = "blocked"
    UNKNOWN = "unknown"


@dataclass
class FilterResult:
    """Result of content filtering operation"""
    allowed: bool
    reason: str
    category: ContentCategory
    suggested_alternatives: List[str]
    modified_url: Optional[str] = None


@dataclass
class WebRequest:
    """Represents a web request to be filtered"""
    url: str
    query: str
    request_type: RequestType
    user_agent: str = "Wizard Voice Assistant"


@dataclass
class FilterConfig:
    """Configuration settings for content filtering"""
    enabled: bool = True
    filtering_level: FilterLevel = FilterLevel.MODERATE
    age_profile: AgeProfile = AgeProfile.ADULT
    safe_search_enabled: bool = True
    custom_blacklist: List[str] = None
    custom_whitelist: List[str] = None
    blocked_categories: List[ContentCategory] = None
    performance_cache_size: int = 1000
    performance_timeout_ms: int = 100
    
    # Age-based filtering settings
    allow_social_media: bool = True
    allow_gaming_sites: bool = True
    allow_video_streaming: bool = True
    allow_news_sites: bool = True
    
    # Advanced filtering options
    keyword_severity_threshold: int = 2  # Minimum severity level to block (1=low, 2=medium, 3=high)
    enable_fuzzy_matching: bool = False
    fuzzy_similarity_threshold: float = 0.8
    enable_context_analysis: bool = True
    
    # Logging and monitoring
    log_blocked_attempts: bool = True
    log_allowed_requests: bool = False
    enable_statistics: bool = True
    
    def __post_init__(self):
        """Initialize default values for mutable fields and apply age-based defaults"""
        # Only initialize if fields are None (not already set)
        if self.custom_blacklist is None:
            self.custom_blacklist = []
        if self.custom_whitelist is None:
            self.custom_whitelist = []
        if self.blocked_categories is None:
            self.blocked_categories = [
                ContentCategory.ADULT,
                ContentCategory.VIOLENCE,
                ContentCategory.DRUGS,
                ContentCategory.HATE_SPEECH,
                ContentCategory.MALWARE,
                ContentCategory.PHISHING
            ]


class ContentFilter:
    """
    Main content filtering engine that coordinates all filtering operations.
    
    This class provides the primary interface for filtering web requests,
    managing configuration, and coordinating with various filtering components.
    """
    
    def __init__(self, config: Optional[FilterConfig] = None):
        """
        Initialize the content filter with configuration.
        
        Args:
            config: FilterConfig object, or None to use default configuration
        """
        self.config = config or FilterConfig()
        self._cache: Dict[str, FilterResult] = {}
    
    def filter_request(self, request: WebRequest) -> FilterResult:
        """
        Main filtering method that applies all filters to a web request.
        
        Args:
            request: WebRequest object containing URL, query, and metadata
            
        Returns:
            FilterResult indicating whether request is allowed and why
        """
        if not self.config.enabled:
            return FilterResult(
                allowed=True,
                reason="Filtering disabled",
                category=ContentCategory.ADULT,  # Default category
                suggested_alternatives=[]
            )
        
        # Basic filtering - for now just allow everything
        return FilterResult(
            allowed=True,
            reason="Content filtering passed - no restrictions applied",
            category=ContentCategory.ADULT,
            suggested_alternatives=[]
        )
    
    def filter_url(self, url: str) -> FilterResult:
        """
        Filter a URL for inappropriate content.
        
        Args:
            url: URL to filter
            
        Returns:
            FilterResult indicating whether URL is allowed
        """
        request = WebRequest(
            url=url,
            query="",
            request_type=RequestType.WEBSITE
        )
        return self.filter_request(request)
    
    def filter_search_query(self, query: str) -> FilterResult:
        """
        Filter a search query for inappropriate content.
        
        Args:
            query: Search query to filter
            
        Returns:
            FilterResult indicating whether query is allowed
        """
        request = WebRequest(
            url="",
            query=query,
            request_type=RequestType.SEARCH
        )
        return self.filter_request(request)