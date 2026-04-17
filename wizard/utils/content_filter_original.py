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
        
        # Apply age-based profile defaults only if this is a new instance
        # (not being loaded from saved configuration)
        if not hasattr(self, '_skip_age_profile_defaults'):
            self._apply_age_profile_defaults()
    
    def _apply_age_profile_defaults(self):
        """Apply default settings based on age profile"""
        if self.age_profile == AgeProfile.CHILD:
            # Strict settings for children
            self.filtering_level = FilterLevel.STRICT
            self.safe_search_enabled = True
            self.allow_social_media = False
            self.allow_gaming_sites = True  # Educational games allowed
            self.allow_video_streaming = False  # Restricted video content
            self.allow_news_sites = False  # News can contain disturbing content
            self.keyword_severity_threshold = 1  # Block even low-severity keywords
            self.enable_context_analysis = True
            # Only set blocked categories if not already set
            if not hasattr(self, '_categories_set_from_config'):
                self.blocked_categories = [
                    ContentCategory.ADULT,
                    ContentCategory.VIOLENCE,
                    ContentCategory.GAMBLING,
                    ContentCategory.DRUGS,
                    ContentCategory.HATE_SPEECH,
                    ContentCategory.MALWARE,
                    ContentCategory.PHISHING
                ]
            
        elif self.age_profile == AgeProfile.TEEN:
            # Moderate settings for teenagers
            self.filtering_level = FilterLevel.MODERATE
            self.safe_search_enabled = True
            self.allow_social_media = True
            self.allow_gaming_sites = True
            self.allow_video_streaming = True
            self.allow_news_sites = True
            self.keyword_severity_threshold = 2  # Block medium and high severity
            self.enable_context_analysis = True
            # Only set blocked categories if not already set
            if not hasattr(self, '_categories_set_from_config'):
                self.blocked_categories = [
                    ContentCategory.ADULT,
                    ContentCategory.VIOLENCE,
                    ContentCategory.DRUGS,
                    ContentCategory.HATE_SPEECH,
                    ContentCategory.MALWARE,
                    ContentCategory.PHISHING
                ]
            
        elif self.age_profile == AgeProfile.ADULT:
            # Permissive settings for adults
            self.filtering_level = FilterLevel.PERMISSIVE
            self.safe_search_enabled = False  # Adults can choose
            self.allow_social_media = True
            self.allow_gaming_sites = True
            self.allow_video_streaming = True
            self.allow_news_sites = True
            self.keyword_severity_threshold = 3  # Only block high severity
            self.enable_context_analysis = False  # Less restrictive
            # Only set blocked categories if not already set
            if not hasattr(self, '_categories_set_from_config'):
                self.blocked_categories = [
                    ContentCategory.MALWARE,
                    ContentCategory.PHISHING
                ]
    
    def set_age_profile(self, profile: AgeProfile):
        """
        Set age profile and apply corresponding defaults.
        
        Args:
            profile: Age profile to apply
        """
        self.age_profile = profile
        self._apply_age_profile_defaults()
    
    def set_filtering_level(self, level: FilterLevel):
        """
        Set filtering level and adjust related settings.
        
        Args:
            level: Filtering level to apply
        """
        self.filtering_level = level
        
        # Adjust keyword severity threshold based on filtering level
        if level == FilterLevel.STRICT:
            self.keyword_severity_threshold = 1
            self.enable_context_analysis = True
        elif level == FilterLevel.MODERATE:
            self.keyword_severity_threshold = 2
            self.enable_context_analysis = True
        elif level == FilterLevel.PERMISSIVE:
            self.keyword_severity_threshold = 3
            self.enable_context_analysis = False
    
    def add_custom_blacklist_domain(self, domain: str) -> bool:
        """
        Add a domain to the custom blacklist.
        
        Args:
            domain: Domain to add
            
        Returns:
            True if added successfully, False if already exists
        """
        if domain and domain not in self.custom_blacklist:
            self.custom_blacklist.append(domain)
            return True
        return False
    
    def remove_custom_blacklist_domain(self, domain: str) -> bool:
        """
        Remove a domain from the custom blacklist.
        
        Args:
            domain: Domain to remove
            
        Returns:
            True if removed successfully, False if not found
        """
        if domain in self.custom_blacklist:
            self.custom_blacklist.remove(domain)
            return True
        return False
    
    def add_custom_whitelist_domain(self, domain: str) -> bool:
        """
        Add a domain to the custom whitelist.
        
        Args:
            domain: Domain to add
            
        Returns:
            True if added successfully, False if already exists
        """
        if domain and domain not in self.custom_whitelist:
            self.custom_whitelist.append(domain)
            return True
        return False
    
    def remove_custom_whitelist_domain(self, domain: str) -> bool:
        """
        Remove a domain from the custom whitelist.
        
        Args:
            domain: Domain to remove
            
        Returns:
            True if removed successfully, False if not found
        """
        if domain in self.custom_whitelist:
            self.custom_whitelist.remove(domain)
            return True
        return False
    
    def enable_category(self, category: ContentCategory):
        """
        Enable blocking for a content category.
        
        Args:
            category: Category to enable blocking for
        """
        if category not in self.blocked_categories:
            self.blocked_categories.append(category)
    
    def disable_category(self, category: ContentCategory):
        """
        Disable blocking for a content category.
        
        Args:
            category: Category to disable blocking for
        """
        if category in self.blocked_categories:
            self.blocked_categories.remove(category)
    
    def is_category_blocked(self, category: ContentCategory) -> bool:
        """
        Check if a content category is blocked.
        
        Args:
            category: Category to check
            
        Returns:
            True if category is blocked, False otherwise
        """
        return category in self.blocked_categories
    
    def get_profile_description(self) -> str:
        """
        Get a human-readable description of the current profile.
        
        Returns:
            Description string
        """
        descriptions = {
            AgeProfile.CHILD: "Child-safe browsing with strict content filtering and educational focus",
            AgeProfile.TEEN: "Teen-appropriate browsing with moderate content filtering",
            AgeProfile.ADULT: "Adult browsing with minimal content restrictions"
        }
        return descriptions.get(self.age_profile, "Custom filtering configuration")
    
    def validate(self) -> List[str]:
        """
        Validate the configuration and return any issues found.
        
        Returns:
            List of validation error messages (empty if valid)
        """
        errors = []
        
        # Validate performance settings
        if self.performance_cache_size < 0:
            errors.append("Performance cache size must be non-negative")
        if self.performance_timeout_ms < 0:
            errors.append("Performance timeout must be non-negative")
        
        # Validate keyword severity threshold
        if not 1 <= self.keyword_severity_threshold <= 3:
            errors.append("Keyword severity threshold must be between 1 and 3")
        
        # Validate fuzzy similarity threshold
        if not 0.0 <= self.fuzzy_similarity_threshold <= 1.0:
            errors.append("Fuzzy similarity threshold must be between 0.0 and 1.0")
        
        # Validate custom lists - DO NOT modify them during validation
        for domain in self.custom_blacklist:
            if not domain or not isinstance(domain, str):
                errors.append(f"Invalid blacklist domain: {domain}")
        
        for domain in self.custom_whitelist:
            if not domain or not isinstance(domain, str):
                errors.append(f"Invalid whitelist domain: {domain}")
        
        # Check for conflicts between blacklist and whitelist
        conflicts = set(self.custom_blacklist) & set(self.custom_whitelist)
        if conflicts:
            errors.append(f"Domains appear in both blacklist and whitelist: {', '.join(conflicts)}")
        
        return errors
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert configuration to dictionary for serialization.
        
        Returns:
            Dictionary representation of the configuration
        """
        return {
            "enabled": self.enabled,
            "filtering_level": self.filtering_level.value,
            "age_profile": self.age_profile.value,
            "safe_search_enabled": self.safe_search_enabled,
            "custom_blacklist": list(self.custom_blacklist),  # Ensure it's a list copy
            "custom_whitelist": list(self.custom_whitelist),  # Ensure it's a list copy
            "blocked_categories": [cat.value for cat in self.blocked_categories],
            "performance": {
                "cache_size": self.performance_cache_size,
                "timeout_ms": self.performance_timeout_ms
            },
            "age_restrictions": {
                "allow_social_media": self.allow_social_media,
                "allow_gaming_sites": self.allow_gaming_sites,
                "allow_video_streaming": self.allow_video_streaming,
                "allow_news_sites": self.allow_news_sites
            },
            "advanced_filtering": {
                "keyword_severity_threshold": self.keyword_severity_threshold,
                "enable_fuzzy_matching": self.enable_fuzzy_matching,
                "fuzzy_similarity_threshold": self.fuzzy_similarity_threshold,
                "enable_context_analysis": self.enable_context_analysis
            },
            "logging": {
                "log_blocked_attempts": self.log_blocked_attempts,
                "log_allowed_requests": self.log_allowed_requests,
                "enable_statistics": self.enable_statistics
            }
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'FilterConfig':
        """
        Create configuration from dictionary.
        
        Args:
            data: Dictionary containing configuration data
            
        Returns:
            FilterConfig instance
        """
        # Create config without calling __post_init__ to avoid age profile defaults
        config = cls.__new__(cls)
        
        # Set flag to skip age profile defaults
        config._skip_age_profile_defaults = True
        
        # Basic settings
        config.enabled = data.get("enabled", True)
        
        # Parse filtering level
        level_str = data.get("filtering_level", "moderate")
        try:
            config.filtering_level = FilterLevel(level_str)
        except ValueError:
            config.filtering_level = FilterLevel.MODERATE
        
        # Parse age profile
        profile_str = data.get("age_profile", "adult")
        try:
            config.age_profile = AgeProfile(profile_str)
        except ValueError:
            config.age_profile = AgeProfile.ADULT
        
        config.safe_search_enabled = data.get("safe_search_enabled", True)
        config.custom_blacklist = data.get("custom_blacklist", []).copy()
        config.custom_whitelist = data.get("custom_whitelist", []).copy()
        
        # Parse blocked categories
        categories_data = data.get("blocked_categories", [])
        config.blocked_categories = []
        for cat_str in categories_data:
            try:
                category = ContentCategory(cat_str)
                config.blocked_categories.append(category)
            except ValueError:
                continue  # Skip unknown categories
        
        # Mark that categories were set from config
        config._categories_set_from_config = True
        
        # Performance settings
        performance = data.get("performance", {})
        config.performance_cache_size = performance.get("cache_size", 1000)
        config.performance_timeout_ms = performance.get("timeout_ms", 100)
        
        # Age restrictions
        age_restrictions = data.get("age_restrictions", {})
        config.allow_social_media = age_restrictions.get("allow_social_media", True)
        config.allow_gaming_sites = age_restrictions.get("allow_gaming_sites", True)
        config.allow_video_streaming = age_restrictions.get("allow_video_streaming", True)
        config.allow_news_sites = age_restrictions.get("allow_news_sites", True)
        
        # Advanced filtering
        advanced = data.get("advanced_filtering", {})
        config.keyword_severity_threshold = advanced.get("keyword_severity_threshold", 2)
        config.enable_fuzzy_matching = advanced.get("enable_fuzzy_matching", False)
        config.fuzzy_similarity_threshold = advanced.get("fuzzy_similarity_threshold", 0.8)
        config.enable_context_analysis = advanced.get("enable_context_analysis", True)
        
        # Logging settings
        logging = data.get("logging", {})
        config.log_blocked_attempts = logging.get("log_blocked_attempts", True)
        config.log_allowed_requests = logging.get("log_allowed_requests", False)
        config.enable_statistics = logging.get("enable_statistics", True)
        
        return config


class DomainChecker:
    """
    Manages domain-based filtering using blacklists and whitelists.
    
    This class handles domain validation, pattern matching, and supports
    wildcard domain patterns for flexible filtering rules.
    """
    
    def __init__(self, db_path: Optional[str] = None):
        """
        Initialize the domain checker with optional database path.
        
        Args:
            db_path: Path to SQLite database file, or None for in-memory database
        """
        self.db_path = db_path or self._get_default_db_path()
        self._blacklist_cache = set()
        self._whitelist_cache = set()
        self._cache_dirty = True
        
        # Initialize database with enhanced schema and default data
        self._init_database()
        self._load_default_lists()
    
    def _get_default_db_path(self) -> str:
        """Get the default database path"""
        current_dir = os.path.dirname(os.path.abspath(__file__))
        data_dir = os.path.join(current_dir, '..', 'data')
        return os.path.join(data_dir, 'content_filter.db')
    
    def _init_database(self):
        """Initialize the SQLite database with required tables"""
        try:
            # Ensure data directory exists
            data_dir = os.path.dirname(self.db_path)
            os.makedirs(data_dir, exist_ok=True)
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Check if we need to migrate existing schema
                cursor.execute("PRAGMA table_info(blocked_domains)")
                columns = [column[1] for column in cursor.fetchall()]
                needs_migration = 'severity' not in columns
                
                if needs_migration:
                    # Backup existing data
                    cursor.execute('SELECT domain, category FROM blocked_domains')
                    existing_blocked = cursor.fetchall()
                    
                    cursor.execute('SELECT domain FROM allowed_domains')
                    existing_allowed = [row[0] for row in cursor.fetchall()]
                    
                    # Drop existing tables
                    cursor.execute('DROP TABLE IF EXISTS blocked_domains')
                    cursor.execute('DROP TABLE IF EXISTS allowed_domains')
                
                # Create blocked domains table with enhanced schema
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS blocked_domains (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        domain TEXT UNIQUE NOT NULL,
                        category TEXT NOT NULL,
                        severity INTEGER DEFAULT 1,
                        description TEXT,
                        added_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        is_pattern BOOLEAN DEFAULT 0
                    )
                ''')
                
                # Create allowed domains table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS allowed_domains (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        domain TEXT UNIQUE NOT NULL,
                        description TEXT,
                        added_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        is_pattern BOOLEAN DEFAULT 0
                    )
                ''')
                
                # Create domain categories table for metadata
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS domain_categories (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        category TEXT UNIQUE NOT NULL,
                        description TEXT,
                        default_severity INTEGER DEFAULT 1
                    )
                ''')
                
                # Create filter logs table for monitoring
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS filter_logs (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        domain TEXT NOT NULL,
                        url TEXT,
                        action TEXT NOT NULL,
                        category TEXT,
                        reason TEXT,
                        user_id TEXT
                    )
                ''')
                
                # Create indexes for better performance
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_blocked_domain ON blocked_domains(domain)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_blocked_category ON blocked_domains(category)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_allowed_domain ON allowed_domains(domain)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_filter_logs_timestamp ON filter_logs(timestamp)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_filter_logs_domain ON filter_logs(domain)')
                
                conn.commit()
                
                # Initialize categories metadata
                self._init_categories(cursor)
                conn.commit()
                
                # Restore existing data if we migrated
                if needs_migration and (existing_blocked or existing_allowed):
                    for domain, category in existing_blocked:
                        cursor.execute('''
                            INSERT OR IGNORE INTO blocked_domains 
                            (domain, category, severity, description, is_pattern)
                            VALUES (?, ?, ?, ?, ?)
                        ''', (domain, category, 2, f"Migrated {category} domain", 1 if '*' in domain else 0))
                    
                    for domain in existing_allowed:
                        cursor.execute('''
                            INSERT OR IGNORE INTO allowed_domains (domain, description, is_pattern)
                            VALUES (?, ?, ?)
                        ''', (domain, "Migrated allowed domain", 1 if '*' in domain else 0))
                    
                    conn.commit()
                
        except sqlite3.Error as e:
            # If database initialization fails, continue with in-memory caches
            print(f"Database initialization error: {e}")
    
    def _init_categories(self, cursor):
        """Initialize domain categories metadata"""
        categories_data = [
            ("adult", "Adult and pornographic content", 3),
            ("violence", "Violence, gore, and disturbing content", 3),
            ("gambling", "Gambling and betting sites", 2),
            ("drugs", "Illegal drugs and substance abuse", 3),
            ("hate_speech", "Hate speech and extremist content", 3),
            ("malware", "Malware and malicious software", 3),
            ("phishing", "Phishing and scam sites", 3),
            ("social_media", "Social media platforms", 1),
            ("gaming", "Gaming and entertainment sites", 1),
            ("default", "General inappropriate content", 2)
        ]
        
        for category, description, severity in categories_data:
            cursor.execute('''
                INSERT OR IGNORE INTO domain_categories (category, description, default_severity)
                VALUES (?, ?, ?)
            ''', (category, description, severity))
    
    def _load_default_lists(self):
        """Load default blacklist and whitelist entries"""
        if self._has_default_data():
            return  # Already populated
        
        # Comprehensive blacklists organized by category
        default_blacklists = self._get_default_blacklists()
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                for category, domains in default_blacklists.items():
                    for domain_info in domains:
                        if isinstance(domain_info, str):
                            domain = domain_info
                            description = f"Default {category} content"
                            severity = 2
                        else:
                            domain, description, severity = domain_info
                        
                        is_pattern = 1 if '*' in domain else 0
                        
                        cursor.execute('''
                            INSERT OR IGNORE INTO blocked_domains 
                            (domain, category, severity, description, is_pattern)
                            VALUES (?, ?, ?, ?, ?)
                        ''', (domain, category, severity, description, is_pattern))
                
                # Add default whitelisted domains
                default_whitelist = self._get_default_whitelist()
                for domain_info in default_whitelist:
                    if isinstance(domain_info, str):
                        domain = domain_info
                        description = "Default safe domain"
                    else:
                        domain, description = domain_info
                    
                    is_pattern = 1 if '*' in domain else 0
                    
                    cursor.execute('''
                        INSERT OR IGNORE INTO allowed_domains (domain, description, is_pattern)
                        VALUES (?, ?, ?)
                    ''', (domain, description, is_pattern))
                
                conn.commit()
                
        except sqlite3.Error as e:
            print(f"Error populating default blacklists: {e}")
    
    def _has_default_data(self) -> bool:
        """Check if default data has already been populated"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT COUNT(*) FROM blocked_domains')
                count = cursor.fetchone()[0]
                return count > 10  # Assume populated if more than 10 entries
        except sqlite3.Error:
            return False
    
    def _get_default_blacklists(self) -> Dict[str, List]:
        """Get comprehensive default blacklists organized by category"""
        return {
            "adult": [
                ("*.adult*", "Adult content sites", 3),
                ("*.porn*", "Pornographic content", 3),
                ("*.xxx*", "Adult content domains", 3),
                ("*.sex*", "Sexual content sites", 3),
                ("*adult*", "Adult content patterns", 3),
                ("*porn*", "Pornographic patterns", 3),
                ("*nude*", "Nudity content", 3),
                ("*erotic*", "Erotic content", 3),
                ("*.xxx", "Adult content TLD", 3),
                ("adult-test-site.com", "Test adult site", 3),
                ("inappropriate-content.net", "Test inappropriate site", 3)
            ],
            "violence": [
                ("*violence*", "Violence content patterns", 3),
                ("*gore*", "Gore content patterns", 3),
                ("*death*", "Death-related content", 3),
                ("*murder*", "Murder-related content", 3),
                ("*torture*", "Torture content", 3),
                ("*brutal*", "Brutal content", 3),
                ("violence-test.com", "Test violence site", 3),
                ("gore-content.net", "Test gore site", 3)
            ],
            "gambling": [
                ("*casino*", "Casino gambling sites", 2),
                ("*poker*", "Poker gambling sites", 2),
                ("*betting*", "Betting sites", 2),
                ("*gamble*", "Gambling sites", 2),
                ("*lottery*", "Lottery sites", 2),
                ("*slots*", "Slot machine sites", 2),
                ("casino-test.com", "Test casino site", 2),
                ("betting-site.net", "Test betting site", 2),
                ("online-poker.org", "Test poker site", 2)
            ],
            "drugs": [
                ("*drugs*", "Drug-related content", 3),
                ("*cocaine*", "Cocaine-related content", 3),
                ("*heroin*", "Heroin-related content", 3),
                ("*marijuana*", "Marijuana-related content", 2),
                ("*cannabis*", "Cannabis-related content", 2),
                ("*meth*", "Methamphetamine content", 3),
                ("*dealer*", "Drug dealer sites", 3),
                ("drug-market.onion", "Test drug market", 3),
                ("illegal-substances.net", "Test drug site", 3)
            ],
            "hate_speech": [
                ("*hate*", "Hate speech content", 3),
                ("*nazi*", "Nazi content", 3),
                ("*supremacist*", "Supremacist content", 3),
                ("*extremist*", "Extremist content", 3),
                ("*terrorist*", "Terrorist content", 3),
                ("*racism*", "Racist content", 3),
                ("hate-group.org", "Test hate group site", 3),
                ("extremist-forum.net", "Test extremist site", 3)
            ],
            "malware": [
                ("*malware*", "Malware distribution", 3),
                ("*virus*", "Virus distribution", 3),
                ("*trojan*", "Trojan distribution", 3),
                ("*ransomware*", "Ransomware sites", 3),
                ("*exploit*", "Exploit sites", 3),
                ("malicious-site.com", "Test malware site", 3),
                ("virus-download.net", "Test virus site", 3),
                ("fake-antivirus.org", "Test fake antivirus", 3)
            ],
            "phishing": [
                ("*phishing*", "Phishing sites", 3),
                ("*scam*", "Scam sites", 3),
                ("*fake-bank*", "Fake banking sites", 3),
                ("*fake-paypal*", "Fake PayPal sites", 3),
                ("*fake-amazon*", "Fake Amazon sites", 3),
                ("phishing-test.com", "Test phishing site", 3),
                ("fake-login.net", "Test fake login", 3),
                ("scam-site.org", "Test scam site", 3)
            ]
        }
    
    def _get_default_whitelist(self) -> List:
        """Get default whitelist of safe domains"""
        return [
            ("*.edu", "Educational institutions"),
            ("*.gov", "Government sites"),
            ("wikipedia.org", "Wikipedia"),
            ("*.wikipedia.org", "Wikipedia domains"),
            ("khan-academy.org", "Khan Academy"),
            ("*.khan-academy.org", "Khan Academy domains"),
            ("coursera.org", "Coursera education"),
            ("*.coursera.org", "Coursera domains"),
            ("github.com", "GitHub"),
            ("*.github.com", "GitHub domains"),
            ("stackoverflow.com", "Stack Overflow"),
            ("*.stackoverflow.com", "Stack Overflow domains"),
            ("bbc.com", "BBC News"),
            ("*.bbc.com", "BBC domains"),
            ("cnn.com", "CNN News"),
            ("reuters.com", "Reuters News"),
            ("npr.org", "NPR News"),
            ("pbs.org", "PBS"),
            ("*.pbs.org", "PBS domains"),
            ("pbskids.org", "PBS Kids"),
            ("*.pbskids.org", "PBS Kids domains"),
            ("nationalgeographic.com", "National Geographic"),
            ("*.nationalgeographic.com", "National Geographic domains")
        ]
    
    def _normalize_domain(self, domain: str) -> str:
        """
        Normalize a domain name for consistent comparison.
        
        Args:
            domain: Domain name to normalize
            
        Returns:
            Normalized domain name
        """
        if not domain:
            return ""
        
        # Remove protocol if present
        if "://" in domain:
            domain = urlparse(domain).netloc
        
        # Convert to lowercase
        domain = domain.lower().strip()
        
        # Remove www. prefix for consistency
        if domain.startswith("www."):
            domain = domain[4:]
        
        return domain
    
    def _matches_pattern(self, domain: str, pattern: str) -> bool:
        """
        Check if a domain matches a wildcard pattern.
        
        Args:
            domain: Domain to check
            pattern: Pattern to match against (may contain wildcards)
            
        Returns:
            True if domain matches pattern, False otherwise
        """
        domain = self._normalize_domain(domain)
        pattern = self._normalize_domain(pattern)
        
        if not domain or not pattern:
            return False
        
        # Convert wildcard pattern to regex
        # Escape special regex characters except *
        escaped_pattern = re.escape(pattern).replace(r'\*', '.*')
        
        # Ensure pattern matches the entire domain
        regex_pattern = f"^{escaped_pattern}$"
        
        try:
            return bool(re.match(regex_pattern, domain))
        except re.error:
            # If regex compilation fails, fall back to exact match
            return domain == pattern.replace('*', '')
    
    def _refresh_cache(self):
        """Refresh the in-memory caches from database"""
        if not self._cache_dirty:
            return
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Load blacklist
                cursor.execute('SELECT domain FROM blocked_domains')
                self._blacklist_cache = {row[0] for row in cursor.fetchall()}
                
                # Load whitelist
                cursor.execute('SELECT domain FROM allowed_domains')
                self._whitelist_cache = {row[0] for row in cursor.fetchall()}
                
                self._cache_dirty = False
        except sqlite3.Error:
            # If database access fails, keep existing cache
            pass
    
    def check_domain(self, domain: str) -> DomainStatus:
        """
        Check the status of a domain against blacklists and whitelists.
        
        Args:
            domain: Domain name to check
            
        Returns:
            DomainStatus indicating if domain is allowed, blocked, or unknown
        """
        if not domain:
            return DomainStatus.BLOCKED
        
        normalized_domain = self._normalize_domain(domain)
        self._refresh_cache()
        
        # Check whitelist first (whitelist overrides blacklist)
        if self.is_whitelisted(normalized_domain):
            return DomainStatus.ALLOWED
        
        # Check blacklist
        if self.is_blacklisted(normalized_domain):
            return DomainStatus.BLOCKED
        
        # Domain not found in either list
        return DomainStatus.UNKNOWN
    
    def is_blacklisted(self, domain: str) -> bool:
        """
        Check if a domain is on the blacklist.
        
        Args:
            domain: Domain to check
            
        Returns:
            True if domain is blacklisted, False otherwise
        """
        normalized_domain = self._normalize_domain(domain)
        self._refresh_cache()
        
        # Check exact matches first
        if normalized_domain in self._blacklist_cache:
            return True
        
        # Check wildcard patterns
        for pattern in self._blacklist_cache:
            if '*' in pattern and self._matches_pattern(normalized_domain, pattern):
                return True
        
        return False
    
    def is_whitelisted(self, domain: str) -> bool:
        """
        Check if a domain is on the whitelist.
        
        Args:
            domain: Domain to check
            
        Returns:
            True if domain is whitelisted, False otherwise
        """
        normalized_domain = self._normalize_domain(domain)
        self._refresh_cache()
        
        # Check exact matches first
        if normalized_domain in self._whitelist_cache:
            return True
        
        # Check wildcard patterns
        for pattern in self._whitelist_cache:
            if '*' in pattern and self._matches_pattern(normalized_domain, pattern):
                return True
        
        return False
    
    def add_to_blacklist(self, domain: str, category: str = "custom") -> bool:
        """
        Add a domain to the blacklist.
        
        Args:
            domain: Domain to add
            category: Category of the blocked content
            
        Returns:
            True if successfully added, False otherwise
        """
        normalized_domain = self._normalize_domain(domain)
        if not normalized_domain:
            return False
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                is_pattern = 1 if '*' in normalized_domain else 0
                cursor.execute('''
                    INSERT OR REPLACE INTO blocked_domains 
                    (domain, category, severity, description, is_pattern)
                    VALUES (?, ?, ?, ?, ?)
                ''', (normalized_domain, category, 2, f"Custom {category} domain", is_pattern))
                conn.commit()
                self._cache_dirty = True
                return cursor.rowcount > 0
        except sqlite3.Error:
            return False
    
    def add_to_whitelist(self, domain: str) -> bool:
        """
        Add a domain to the whitelist.
        
        Args:
            domain: Domain to add
            
        Returns:
            True if successfully added, False otherwise
        """
        normalized_domain = self._normalize_domain(domain)
        if not normalized_domain:
            return False
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                is_pattern = 1 if '*' in normalized_domain else 0
                cursor.execute('''
                    INSERT OR REPLACE INTO allowed_domains (domain, description, is_pattern)
                    VALUES (?, ?, ?)
                ''', (normalized_domain, "Custom allowed domain", is_pattern))
                conn.commit()
                self._cache_dirty = True
                return cursor.rowcount > 0
        except sqlite3.Error:
            return False
    

    def remove_from_blacklist(self, domain: str) -> bool:
        """
        Remove a domain from the blacklist.
        
        Args:
            domain: Domain to remove
            
        Returns:
            True if successfully removed, False otherwise
        """
        normalized_domain = self._normalize_domain(domain)
        if not normalized_domain:
            return False
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('DELETE FROM blocked_domains WHERE domain = ?', (normalized_domain,))
                conn.commit()
                self._cache_dirty = True
                return cursor.rowcount > 0
        except sqlite3.Error:
            return False
    
    def remove_from_whitelist(self, domain: str) -> bool:
        """
        Remove a domain from the whitelist.
        
        Args:
            domain: Domain to remove
            
        Returns:
            True if successfully removed, False otherwise
        """
        normalized_domain = self._normalize_domain(domain)
        if not normalized_domain:
            return False
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('DELETE FROM allowed_domains WHERE domain = ?', (normalized_domain,))
                conn.commit()
                self._cache_dirty = True
                return cursor.rowcount > 0
        except sqlite3.Error:
            return False
    
    def load_blacklist(self) -> List[str]:
        """
        Load the current blacklist.
        
        Returns:
            List of blacklisted domains
        """
        self._refresh_cache()
        return list(self._blacklist_cache)
    
    def load_whitelist(self) -> List[str]:
        """
        Load the current whitelist.
        
        Returns:
            List of whitelisted domains
        """
        self._refresh_cache()
        return list(self._whitelist_cache)
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get domain checker statistics.
        
        Returns:
            Dictionary containing statistics
        """
        self._refresh_cache()
        stats = {
            "blacklist_size": len(self._blacklist_cache),
            "whitelist_size": len(self._whitelist_cache),
            "database_path": self.db_path
        }
        
        # Add detailed stats from database
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Count blocked domains by category
                cursor.execute('''
                    SELECT category, COUNT(*) 
                    FROM blocked_domains 
                    GROUP BY category
                ''')
                blocked_by_category = dict(cursor.fetchall())
                stats['blocked_by_category'] = blocked_by_category
                
                # Total counts
                cursor.execute('SELECT COUNT(*) FROM blocked_domains')
                stats['total_blocked'] = cursor.fetchone()[0]
                
                cursor.execute('SELECT COUNT(*) FROM allowed_domains')
                stats['total_allowed'] = cursor.fetchone()[0]
                
        except sqlite3.Error:
            # If database access fails, use cache sizes
            stats['total_blocked'] = len(self._blacklist_cache)
            stats['total_allowed'] = len(self._whitelist_cache)
            stats['blocked_by_category'] = {}
        
        return stats


class KeywordFilter:
    """
    Manages keyword-based content filtering for search queries and URLs.
    
    This class analyzes text content for inappropriate keywords, supports
    multiple languages and variations, and includes severity levels for
    different types of inappropriate content.
    """
    
    def __init__(self, db_path: Optional[str] = None):
        """
        Initialize the keyword filter with optional database path.
        
        Args:
            db_path: Path to SQLite database file, or None for default path
        """
        self.db_path = db_path or self._get_default_db_path()
        self._keyword_cache: Dict[str, Tuple[int, str]] = {}  # keyword -> (severity, category)
        self._cache_dirty = True
        
        # Initialize database and load default keywords
        self._init_database()
        self._load_default_keywords()
    
    def _get_default_db_path(self) -> str:
        """Get the default database path"""
        current_dir = os.path.dirname(os.path.abspath(__file__))
        data_dir = os.path.join(current_dir, '..', 'data')
        return os.path.join(data_dir, 'content_filter.db')
    
    def _init_database(self):
        """Initialize the SQLite database with keyword tables"""
        try:
            # Ensure data directory exists
            data_dir = os.path.dirname(self.db_path)
            os.makedirs(data_dir, exist_ok=True)
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Create blocked keywords table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS blocked_keywords (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        keyword TEXT UNIQUE NOT NULL,
                        category TEXT NOT NULL,
                        severity INTEGER DEFAULT 1,
                        language TEXT DEFAULT 'en',
                        description TEXT,
                        added_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        is_pattern BOOLEAN DEFAULT 0
                    )
                ''')
                
                # Create keyword variations table for fuzzy matching
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS keyword_variations (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        base_keyword_id INTEGER,
                        variation TEXT NOT NULL,
                        similarity_score REAL DEFAULT 1.0,
                        FOREIGN KEY (base_keyword_id) REFERENCES blocked_keywords (id)
                    )
                ''')
                
                # Create keyword context rules table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS keyword_context_rules (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        keyword_id INTEGER,
                        context_pattern TEXT,
                        action TEXT DEFAULT 'block',
                        description TEXT,
                        FOREIGN KEY (keyword_id) REFERENCES blocked_keywords (id)
                    )
                ''')
                
                # Create indexes for better performance
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_keyword ON blocked_keywords(keyword)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_keyword_category ON blocked_keywords(category)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_keyword_severity ON blocked_keywords(severity)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_variation ON keyword_variations(variation)')
                
                conn.commit()
                
        except sqlite3.Error as e:
            print(f"Keyword database initialization error: {e}")
    
    def _load_default_keywords(self):
        """Load default inappropriate keywords into the database"""
        if self._has_default_keywords():
            return  # Already populated
        
        # Comprehensive keyword lists organized by category
        default_keywords = self._get_default_keywords()
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                for category, keywords in default_keywords.items():
                    for keyword_info in keywords:
                        if isinstance(keyword_info, str):
                            keyword = keyword_info
                            severity = 2
                            language = 'en'
                            description = f"Default {category} keyword"
                        else:
                            keyword, severity, language, description = keyword_info
                        
                        is_pattern = 1 if '*' in keyword or '[' in keyword else 0
                        
                        cursor.execute('''
                            INSERT OR IGNORE INTO blocked_keywords 
                            (keyword, category, severity, language, description, is_pattern)
                            VALUES (?, ?, ?, ?, ?, ?)
                        ''', (keyword.lower(), category, severity, language, description, is_pattern))
                
                conn.commit()
                
        except sqlite3.Error as e:
            print(f"Error populating default keywords: {e}")
    
    def _has_default_keywords(self) -> bool:
        """Check if default keywords have already been populated"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT COUNT(*) FROM blocked_keywords')
                count = cursor.fetchone()[0]
                return count > 20  # Assume populated if more than 20 entries
        except sqlite3.Error:
            return False
    
    def _get_default_keywords(self) -> Dict[str, List]:
        """Get comprehensive default keyword lists organized by category"""
        return {
            "adult": [
                ("porn", 3, "en", "Pornographic content"),
                ("sex", 2, "en", "Sexual content - context dependent"),
                ("nude", 3, "en", "Nudity content"),
                ("naked", 3, "en", "Nudity content"),
                ("erotic", 3, "en", "Erotic content"),
                ("xxx", 3, "en", "Adult content marker"),
                ("adult", 2, "en", "Adult content - context dependent"),
                ("explicit", 2, "en", "Explicit content"),
                ("nsfw", 3, "en", "Not safe for work content"),
                ("18+", 3, "en", "Adult age restriction"),
                ("mature", 1, "en", "Mature content - low severity"),
                ("*porn*", 3, "en", "Pornographic pattern matching"),
                ("*sex*", 2, "en", "Sexual pattern matching"),
                ("*nude*", 3, "en", "Nudity pattern matching")
            ],
            "violence": [
                ("kill", 3, "en", "Violence - killing"),
                ("murder", 3, "en", "Violence - murder"),
                ("death", 2, "en", "Death content - context dependent"),
                ("blood", 2, "en", "Blood content"),
                ("gore", 3, "en", "Gore content"),
                ("torture", 3, "en", "Torture content"),
                ("brutal", 3, "en", "Brutal violence"),
                ("violent", 2, "en", "Violence - general"),
                ("violence", 2, "en", "Violence - general"),
                ("weapon", 1, "en", "Weapons - low severity"),
                ("gun", 1, "en", "Firearms - context dependent"),
                ("knife", 1, "en", "Knives - context dependent"),
                ("bomb", 3, "en", "Explosives"),
                ("*kill*", 3, "en", "Killing pattern matching"),
                ("*murder*", 3, "en", "Murder pattern matching"),
                ("*gore*", 3, "en", "Gore pattern matching"),
                ("*violence*", 2, "en", "Violence pattern matching")
            ],
            "gambling": [
                ("casino", 2, "en", "Casino gambling"),
                ("poker", 2, "en", "Poker gambling"),
                ("betting", 2, "en", "Betting activities"),
                ("gamble", 2, "en", "Gambling activities"),
                ("lottery", 2, "en", "Lottery gambling"),
                ("slots", 2, "en", "Slot machines"),
                ("blackjack", 2, "en", "Blackjack gambling"),
                ("roulette", 2, "en", "Roulette gambling"),
                ("bet", 1, "en", "Betting - context dependent"),
                ("wager", 2, "en", "Wagering"),
                ("jackpot", 2, "en", "Gambling jackpot"),
                ("*casino*", 2, "en", "Casino pattern matching"),
                ("*gambling*", 2, "en", "Gambling pattern matching"),
                ("*betting*", 2, "en", "Betting pattern matching")
            ],
            "drugs": [
                ("cocaine", 3, "en", "Illegal drug - cocaine"),
                ("heroin", 3, "en", "Illegal drug - heroin"),
                ("meth", 3, "en", "Illegal drug - methamphetamine"),
                ("crack", 3, "en", "Illegal drug - crack cocaine"),
                ("marijuana", 2, "en", "Cannabis - context dependent"),
                ("cannabis", 2, "en", "Cannabis - context dependent"),
                ("weed", 2, "en", "Cannabis slang"),
                ("drug", 1, "en", "Drugs - context dependent"),
                ("dealer", 3, "en", "Drug dealing"),
                ("narcotic", 3, "en", "Narcotic substances"),
                ("substance", 1, "en", "Substance - context dependent"),
                ("high", 1, "en", "Drug high - context dependent"),
                ("*drug*", 2, "en", "Drug pattern matching"),
                ("*cocaine*", 3, "en", "Cocaine pattern matching"),
                ("*heroin*", 3, "en", "Heroin pattern matching")
            ],
            "hate_speech": [
                ("hate", 2, "en", "Hate speech - context dependent"),
                ("nazi", 3, "en", "Nazi content"),
                ("racist", 3, "en", "Racist content"),
                ("supremacist", 3, "en", "Supremacist content"),
                ("extremist", 3, "en", "Extremist content"),
                ("terrorist", 3, "en", "Terrorist content"),
                ("bigot", 3, "en", "Bigotry"),
                ("discrimination", 2, "en", "Discrimination"),
                ("prejudice", 2, "en", "Prejudice"),
                ("intolerance", 2, "en", "Intolerance"),
                ("*hate*", 2, "en", "Hate pattern matching"),
                ("*nazi*", 3, "en", "Nazi pattern matching"),
                ("*racist*", 3, "en", "Racist pattern matching")
            ],
            "profanity": [
                ("damn", 1, "en", "Mild profanity"),
                ("hell", 1, "en", "Mild profanity - context dependent"),
                ("crap", 1, "en", "Mild profanity"),
                ("stupid", 1, "en", "Mild offensive language"),
                ("idiot", 1, "en", "Mild offensive language"),
                ("moron", 1, "en", "Mild offensive language"),
                ("*profanity*", 2, "en", "Profanity pattern matching")
            ]
        }
    
    def _refresh_cache(self):
        """Refresh the in-memory keyword cache from database"""
        if not self._cache_dirty:
            return
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Load keywords with severity and category
                cursor.execute('SELECT keyword, severity, category FROM blocked_keywords')
                self._keyword_cache = {
                    keyword: (severity, category) 
                    for keyword, severity, category in cursor.fetchall()
                }
                
                self._cache_dirty = False
        except sqlite3.Error:
            # If database access fails, keep existing cache
            pass
    
    def scan_text(self, text: str) -> List[str]:
        """
        Scan text for inappropriate keywords.
        
        Args:
            text: Text to scan for keywords
            
        Returns:
            List of detected inappropriate keywords
        """
        if not text:
            return []
        
        self._refresh_cache()
        detected_keywords = []
        
        # Normalize text for analysis
        normalized_text = text.lower().strip()
        
        # Check for exact keyword matches
        for keyword, (severity, category) in self._keyword_cache.items():
            if self._keyword_matches(normalized_text, keyword):
                detected_keywords.append(keyword)
        
        return detected_keywords
    
    def _keyword_matches(self, text: str, keyword: str) -> bool:
        """
        Check if a keyword matches in the given text.
        
        Args:
            text: Text to search in (should be normalized)
            keyword: Keyword to search for
            
        Returns:
            True if keyword matches, False otherwise
        """
        if not text or not keyword:
            return False
        
        # Handle pattern matching (wildcards)
        if '*' in keyword:
            # Convert wildcard pattern to regex
            pattern = keyword.replace('*', '.*')
            try:
                return bool(re.search(pattern, text))
            except re.error:
                # If regex fails, fall back to substring search
                return keyword.replace('*', '') in text
        
        # Handle word boundary matching for exact words
        # Use word boundaries to avoid false positives
        word_pattern = r'\b' + re.escape(keyword) + r'\b'
        try:
            return bool(re.search(word_pattern, text))
        except re.error:
            # If regex fails, fall back to substring search
            return keyword in text
    
    def is_query_safe(self, query: str) -> bool:
        """
        Check if a search query is safe (contains no inappropriate keywords).
        
        Args:
            query: Search query to check
            
        Returns:
            True if query is safe, False if it contains inappropriate keywords
        """
        detected_keywords = self.scan_text(query)
        return len(detected_keywords) == 0
    
    def get_blocked_keywords(self) -> List[str]:
        """
        Get the list of all blocked keywords.
        
        Returns:
            List of blocked keywords
        """
        self._refresh_cache()
        return list(self._keyword_cache.keys())
    
    def suggest_alternative_query(self, query: str) -> str:
        """
        Suggest an alternative query by removing inappropriate keywords.
        
        Args:
            query: Original query that contains inappropriate keywords
            
        Returns:
            Modified query with inappropriate keywords removed or replaced
        """
        if not query:
            return query
        
        detected_keywords = self.scan_text(query)
        if not detected_keywords:
            return query  # Query is already safe
        
        # Create a modified query by removing detected keywords
        modified_query = query.lower()
        
        for keyword in detected_keywords:
            # Remove the keyword and clean up extra spaces
            if '*' in keyword:
                # Handle wildcard patterns
                pattern = keyword.replace('*', '.*')
                try:
                    modified_query = re.sub(pattern, '', modified_query)
                except re.error:
                    # If regex fails, remove the base keyword
                    base_keyword = keyword.replace('*', '')
                    modified_query = modified_query.replace(base_keyword, '')
            else:
                # Remove exact keyword with word boundaries
                word_pattern = r'\b' + re.escape(keyword) + r'\b'
                try:
                    modified_query = re.sub(word_pattern, '', modified_query)
                except re.error:
                    # If regex fails, use simple replacement
                    modified_query = modified_query.replace(keyword, '')
        
        # Clean up the modified query
        modified_query = ' '.join(modified_query.split())  # Remove extra whitespace
        
        # If the query becomes empty or too short, suggest a generic safe search
        if len(modified_query.strip()) < 2:
            return "safe search"
        
        return modified_query.strip()
    
    def add_keyword(self, keyword: str, category: str = "custom", severity: int = 2, language: str = "en") -> bool:
        """
        Add a keyword to the blocked list.
        
        Args:
            keyword: Keyword to add
            category: Category of the keyword
            severity: Severity level (1=low, 2=medium, 3=high)
            language: Language code for the keyword
            
        Returns:
            True if successfully added, False otherwise
        """
        if not keyword:
            return False
        
        normalized_keyword = keyword.lower().strip()
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                is_pattern = 1 if '*' in normalized_keyword or '[' in normalized_keyword else 0
                cursor.execute('''
                    INSERT OR REPLACE INTO blocked_keywords 
                    (keyword, category, severity, language, description, is_pattern)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (normalized_keyword, category, severity, language, f"Custom {category} keyword", is_pattern))
                conn.commit()
                self._cache_dirty = True
                return cursor.rowcount > 0
        except sqlite3.Error:
            return False
    
    def remove_keyword(self, keyword: str) -> bool:
        """
        Remove a keyword from the blocked list.
        
        Args:
            keyword: Keyword to remove
            
        Returns:
            True if successfully removed, False otherwise
        """
        if not keyword:
            return False
        
        normalized_keyword = keyword.lower().strip()
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('DELETE FROM blocked_keywords WHERE keyword = ?', (normalized_keyword,))
                conn.commit()
                self._cache_dirty = True
                return cursor.rowcount > 0
        except sqlite3.Error:
            return False
    
    def get_keyword_severity(self, keyword: str) -> int:
        """
        Get the severity level of a keyword.
        
        Args:
            keyword: Keyword to check
            
        Returns:
            Severity level (1=low, 2=medium, 3=high), or 0 if not found
        """
        self._refresh_cache()
        normalized_keyword = keyword.lower().strip()
        
        if normalized_keyword in self._keyword_cache:
            return self._keyword_cache[normalized_keyword][0]
        
        return 0
    
    def get_keyword_category(self, keyword: str) -> str:
        """
        Get the category of a keyword.
        
        Args:
            keyword: Keyword to check
            
        Returns:
            Category string, or empty string if not found
        """
        self._refresh_cache()
        normalized_keyword = keyword.lower().strip()
        
        if normalized_keyword in self._keyword_cache:
            return self._keyword_cache[normalized_keyword][1]
        
        return ""
    
    def fuzzy_match_keywords(self, text: str, similarity_threshold: float = 0.8) -> List[Tuple[str, float]]:
        """
        Find keywords that are similar to words in the text using fuzzy matching.
        
        Args:
            text: Text to analyze
            similarity_threshold: Minimum similarity score (0.0 to 1.0)
            
        Returns:
            List of tuples (keyword, similarity_score) for matches above threshold
        """
        if not text:
            return []
        
        self._refresh_cache()
        matches = []
        
        # Split text into words for analysis
        words = re.findall(r'\b\w+\b', text.lower())
        
        for word in words:
            for keyword in self._keyword_cache.keys():
                # Skip pattern keywords for fuzzy matching
                if '*' in keyword or '[' in keyword:
                    continue
                
                # Calculate similarity using difflib
                similarity = difflib.SequenceMatcher(None, word, keyword).ratio()
                
                if similarity >= similarity_threshold:
                    matches.append((keyword, similarity))
        
        # Sort by similarity score (highest first) and remove duplicates
        matches = list(set(matches))
        matches.sort(key=lambda x: x[1], reverse=True)
        
        return matches
    
    def analyze_context(self, text: str, keyword: str) -> bool:
        """
        Analyze the context around a keyword to determine if it should be blocked.
        
        This is a basic implementation that can be extended with more sophisticated
        natural language processing techniques.
        
        Args:
            text: Full text containing the keyword
            keyword: Keyword to analyze
            
        Returns:
            True if keyword should be blocked in this context, False otherwise
        """
        if not text or not keyword:
            return False
        
        # Get the severity and category of the keyword
        severity = self.get_keyword_severity(keyword)
        category = self.get_keyword_category(keyword)
        
        # High severity keywords are always blocked
        if severity >= 3:
            return True
        
        # For medium severity keywords, check context
        if severity == 2:
            # Look for educational or informational context indicators
            educational_indicators = [
                'definition', 'meaning', 'what is', 'information about',
                'learn about', 'study', 'research', 'academic', 'educational',
                'health', 'medical', 'safety', 'prevention', 'awareness'
            ]
            
            text_lower = text.lower()
            for indicator in educational_indicators:
                if indicator in text_lower:
                    return False  # Allow in educational context
            
            return True  # Block by default for medium severity
        
        # Low severity keywords require more context analysis
        if severity == 1:
            # Look for clearly inappropriate context
            inappropriate_indicators = [
                'buy', 'purchase', 'order', 'get', 'find', 'download',
                'free', 'cheap', 'best', 'top', 'hot', 'new'
            ]
            
            text_lower = text.lower()
            for indicator in inappropriate_indicators:
                if indicator in text_lower:
                    return True  # Block if combined with commercial/seeking language
            
            return False  # Allow by default for low severity
        
        return False  # Default to allow if severity is unknown
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get keyword filter statistics.
        
        Returns:
            Dictionary containing statistics
        """
        self._refresh_cache()
        stats = {
            "total_keywords": len(self._keyword_cache),
            "database_path": self.db_path
        }
        
        # Add detailed stats from database
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Count keywords by category
                cursor.execute('''
                    SELECT category, COUNT(*) 
                    FROM blocked_keywords 
                    GROUP BY category
                ''')
                keywords_by_category = dict(cursor.fetchall())
                stats['keywords_by_category'] = keywords_by_category
                
                # Count keywords by severity
                cursor.execute('''
                    SELECT severity, COUNT(*) 
                    FROM blocked_keywords 
                    GROUP BY severity
                ''')
                keywords_by_severity = dict(cursor.fetchall())
                stats['keywords_by_severity'] = keywords_by_severity
                
                # Count keywords by language
                cursor.execute('''
                    SELECT language, COUNT(*) 
                    FROM blocked_keywords 
                    GROUP BY language
                ''')
                keywords_by_language = dict(cursor.fetchall())
                stats['keywords_by_language'] = keywords_by_language
                
        except sqlite3.Error:
            # If database access fails, use basic stats
            stats['keywords_by_category'] = {}
            stats['keywords_by_severity'] = {}
            stats['keywords_by_language'] = {}
        
        return stats


class ConfigurationManager:
    """
    Manages configuration persistence, validation, and migration for content filtering.
    
    This class handles loading and saving configuration to JSON files,
    validates configuration data, and supports configuration migration
    between different versions.
    """
    
    CONFIG_VERSION = "1.0"
    DEFAULT_CONFIG_FILENAME = "content_filter_config.json"
    
    def __init__(self, config_dir: Optional[str] = None):
        """
        Initialize the configuration manager.
        
        Args:
            config_dir: Directory to store configuration files, or None for default
        """
        self.config_dir = config_dir or self._get_default_config_dir()
        self.config_path = os.path.join(self.config_dir, self.DEFAULT_CONFIG_FILENAME)
        self.backup_dir = os.path.join(self.config_dir, "backups")
        
        # Ensure directories exist
        os.makedirs(self.config_dir, exist_ok=True)
        os.makedirs(self.backup_dir, exist_ok=True)
    
    def _get_default_config_dir(self) -> str:
        """Get the default configuration directory"""
        current_dir = os.path.dirname(os.path.abspath(__file__))
        return os.path.join(current_dir, '..', 'data', 'config')
    
    def save_config(self, config: FilterConfig, config_path: Optional[str] = None) -> bool:
        """
        Save configuration to JSON file.
        
        Args:
            config: FilterConfig instance to save
            config_path: Optional custom path, uses default if None
            
        Returns:
            True if successfully saved, False otherwise
        """
        target_path = config_path or self.config_path
        
        try:
            # Validate configuration before saving
            validation_errors = config.validate()
            if validation_errors:
                print(f"Configuration validation failed: {'; '.join(validation_errors)}")
                return False
            
            # Create backup of existing config if it exists
            if os.path.exists(target_path):
                self._create_backup(target_path)
            
            # Get configuration data BEFORE any modifications
            config_dict = config.to_dict()
            
            # Prepare configuration data with metadata
            config_data = {
                "version": self.CONFIG_VERSION,
                "created_at": self._get_timestamp(),
                "last_modified": self._get_timestamp(),
                "content_filter": config_dict
            }
            
            # Ensure target directory exists
            os.makedirs(os.path.dirname(target_path), exist_ok=True)
            
            # Write configuration to file
            with open(target_path, 'w', encoding='utf-8') as f:
                json.dump(config_data, f, indent=2, ensure_ascii=False)
            
            return True
            
        except (OSError, json.JSONEncodeError, ValueError) as e:
            print(f"Error saving configuration: {e}")
            return False
    
    def load_config(self, config_path: Optional[str] = None) -> Optional[FilterConfig]:
        """
        Load configuration from JSON file.
        
        Args:
            config_path: Optional custom path, uses default if None
            
        Returns:
            FilterConfig instance if successfully loaded, None otherwise
        """
        source_path = config_path or self.config_path
        
        try:
            if not os.path.exists(source_path):
                # Return default configuration if file doesn't exist
                return FilterConfig()
            
            with open(source_path, 'r', encoding='utf-8') as f:
                config_data = json.load(f)
            
            # Check if migration is needed
            config_version = config_data.get("version", "0.0")
            if config_version != self.CONFIG_VERSION:
                config_data = self._migrate_config(config_data, config_version)
                if config_data is None:
                    print(f"Configuration migration failed for version {config_version}")
                    return None
            
            # Extract content filter configuration
            filter_config_data = config_data.get("content_filter", {})
            
            # Create FilterConfig from data
            config = FilterConfig.from_dict(filter_config_data)
            
            # Validate loaded configuration
            validation_errors = config.validate()
            if validation_errors:
                print(f"Loaded configuration is invalid: {'; '.join(validation_errors)}")
                # Return default config if validation fails
                return FilterConfig()
            
            return config
            
        except (FileNotFoundError, json.JSONDecodeError, KeyError, ValueError) as e:
            print(f"Error loading configuration: {e}")
            # Return default configuration on error
            return FilterConfig()
    
    def _migrate_config(self, config_data: Dict[str, Any], from_version: str) -> Optional[Dict[str, Any]]:
        """
        Migrate configuration from older version to current version.
        
        Args:
            config_data: Configuration data to migrate
            from_version: Version to migrate from
            
        Returns:
            Migrated configuration data, or None if migration failed
        """
        try:
            # Create backup before migration
            backup_path = os.path.join(
                self.backup_dir, 
                f"config_v{from_version}_{self._get_timestamp()}.json"
            )
            with open(backup_path, 'w', encoding='utf-8') as f:
                json.dump(config_data, f, indent=2)
            
            # Migration logic based on version
            if from_version == "0.0" or "content_filter" not in config_data:
                # Migrate from old format (direct config) to new format (with metadata)
                migrated_data = {
                    "version": self.CONFIG_VERSION,
                    "created_at": self._get_timestamp(),
                    "last_modified": self._get_timestamp(),
                    "content_filter": config_data if "content_filter" not in config_data else config_data["content_filter"]
                }
            else:
                # Update version and timestamp
                migrated_data = config_data.copy()
                migrated_data["version"] = self.CONFIG_VERSION
                migrated_data["last_modified"] = self._get_timestamp()
            
            # Apply version-specific migrations
            if from_version < "1.0":
                migrated_data = self._migrate_to_v1_0(migrated_data)
            
            return migrated_data
            
        except Exception as e:
            print(f"Configuration migration error: {e}")
            return None
    
    def _migrate_to_v1_0(self, config_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Migrate configuration to version 1.0.
        
        Args:
            config_data: Configuration data to migrate
            
        Returns:
            Migrated configuration data
        """
        filter_config = config_data.get("content_filter", {})
        
        # Add new fields with defaults if they don't exist
        if "age_profile" not in filter_config:
            filter_config["age_profile"] = "adult"
        
        if "age_restrictions" not in filter_config:
            filter_config["age_restrictions"] = {
                "allow_social_media": True,
                "allow_gaming_sites": True,
                "allow_video_streaming": True,
                "allow_news_sites": True
            }
        
        if "advanced_filtering" not in filter_config:
            filter_config["advanced_filtering"] = {
                "keyword_severity_threshold": 2,
                "enable_fuzzy_matching": False,
                "fuzzy_similarity_threshold": 0.8,
                "enable_context_analysis": True
            }
        
        if "logging" not in filter_config:
            filter_config["logging"] = {
                "log_blocked_attempts": True,
                "log_allowed_requests": False,
                "enable_statistics": True
            }
        
        config_data["content_filter"] = filter_config
        return config_data
    
    def _create_backup(self, config_path: str) -> bool:
        """
        Create a backup of the existing configuration file.
        
        Args:
            config_path: Path to configuration file to backup
            
        Returns:
            True if backup created successfully, False otherwise
        """
        try:
            timestamp = self._get_timestamp()
            backup_filename = f"config_backup_{timestamp}.json"
            backup_path = os.path.join(self.backup_dir, backup_filename)
            
            # Copy existing config to backup
            with open(config_path, 'r', encoding='utf-8') as src:
                with open(backup_path, 'w', encoding='utf-8') as dst:
                    dst.write(src.read())
            
            # Keep only the last 10 backups to avoid clutter
            self._cleanup_old_backups()
            
            return True
            
        except (OSError, IOError) as e:
            print(f"Error creating backup: {e}")
            return False
    
    def _cleanup_old_backups(self, max_backups: int = 10):
        """
        Remove old backup files, keeping only the most recent ones.
        
        Args:
            max_backups: Maximum number of backup files to keep
        """
        try:
            # Get all backup files
            backup_files = []
            for filename in os.listdir(self.backup_dir):
                if filename.startswith("config_backup_") and filename.endswith(".json"):
                    filepath = os.path.join(self.backup_dir, filename)
                    backup_files.append((filepath, os.path.getmtime(filepath)))
            
            # Sort by modification time (newest first)
            backup_files.sort(key=lambda x: x[1], reverse=True)
            
            # Remove old backups
            for filepath, _ in backup_files[max_backups:]:
                os.remove(filepath)
                
        except OSError as e:
            print(f"Error cleaning up backups: {e}")
    
    def _get_timestamp(self) -> str:
        """Get current timestamp as string"""
        from datetime import datetime
        return datetime.now().strftime("%Y%m%d_%H%M%S")
    
    def validate_config_file(self, config_path: Optional[str] = None) -> Tuple[bool, List[str]]:
        """
        Validate a configuration file without loading it.
        
        Args:
            config_path: Optional custom path, uses default if None
            
        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        source_path = config_path or self.config_path
        errors = []
        
        try:
            if not os.path.exists(source_path):
                errors.append(f"Configuration file not found: {source_path}")
                return False, errors
            
            # Check if file is readable
            with open(source_path, 'r', encoding='utf-8') as f:
                config_data = json.load(f)
            
            # Validate JSON structure
            if not isinstance(config_data, dict):
                errors.append("Configuration file must contain a JSON object")
                return False, errors
            
            # Check for required fields
            if "content_filter" not in config_data:
                errors.append("Missing 'content_filter' section in configuration")
            
            # Validate version
            version = config_data.get("version", "0.0")
            if version > self.CONFIG_VERSION:
                errors.append(f"Configuration version {version} is newer than supported version {self.CONFIG_VERSION}")
            
            # Try to create FilterConfig to validate content
            if "content_filter" in config_data:
                try:
                    filter_config = FilterConfig.from_dict(config_data["content_filter"])
                    validation_errors = filter_config.validate()
                    errors.extend(validation_errors)
                except Exception as e:
                    errors.append(f"Error validating filter configuration: {e}")
            
            return len(errors) == 0, errors
            
        except json.JSONDecodeError as e:
            errors.append(f"Invalid JSON format: {e}")
            return False, errors
        except Exception as e:
            errors.append(f"Error validating configuration file: {e}")
            return False, errors
    
    def reset_to_defaults(self, config_path: Optional[str] = None) -> bool:
        """
        Reset configuration to default values.
        
        Args:
            config_path: Optional custom path, uses default if None
            
        Returns:
            True if successfully reset, False otherwise
        """
        target_path = config_path or self.config_path
        
        try:
            # Create backup of existing config if it exists
            if os.path.exists(target_path):
                self._create_backup(target_path)
            
            # Create default configuration
            default_config = FilterConfig()
            
            # Save default configuration
            return self.save_config(default_config, target_path)
            
        except Exception as e:
            print(f"Error resetting configuration: {e}")
            return False
    
    def export_config(self, config: FilterConfig, export_path: str) -> bool:
        """
        Export configuration to a specific file for sharing or backup.
        
        Args:
            config: FilterConfig instance to export
            export_path: Path where to export the configuration
            
        Returns:
            True if successfully exported, False otherwise
        """
        try:
            # Add export metadata
            export_data = {
                "version": self.CONFIG_VERSION,
                "exported_at": self._get_timestamp(),
                "export_type": "content_filter_config",
                "content_filter": config.to_dict()
            }
            
            # Ensure export directory exists
            os.makedirs(os.path.dirname(export_path), exist_ok=True)
            
            # Write export file
            with open(export_path, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, indent=2, ensure_ascii=False)
            
            return True
            
        except (OSError, json.JSONEncodeError) as e:
            print(f"Error exporting configuration: {e}")
            return False
    
    def import_config(self, import_path: str) -> Optional[FilterConfig]:
        """
        Import configuration from a file.
        
        Args:
            import_path: Path to configuration file to import
            
        Returns:
            FilterConfig instance if successfully imported, None otherwise
        """
        try:
            if not os.path.exists(import_path):
                print(f"Import file not found: {import_path}")
                return None
            
            with open(import_path, 'r', encoding='utf-8') as f:
                import_data = json.load(f)
            
            # Validate import data
            if not isinstance(import_data, dict):
                print("Import file must contain a JSON object")
                return None
            
            if "content_filter" not in import_data:
                print("Import file missing 'content_filter' section")
                return None
            
            # Check version compatibility
            import_version = import_data.get("version", "0.0")
            if import_version > self.CONFIG_VERSION:
                print(f"Import version {import_version} is newer than supported version {self.CONFIG_VERSION}")
                return None
            
            # Create FilterConfig from imported data
            filter_config = FilterConfig.from_dict(import_data["content_filter"])
            
            # Validate imported configuration
            validation_errors = filter_config.validate()
            if validation_errors:
                print(f"Imported configuration is invalid: {'; '.join(validation_errors)}")
                return None
            
            return filter_config
            
        except (json.JSONDecodeError, KeyError, ValueError) as e:
            print(f"Error importing configuration: {e}")
            return None
    
    def get_config_info(self, config_path: Optional[str] = None) -> Dict[str, Any]:
        """
        Get information about a configuration file.
        
        Args:
            config_path: Optional custom path, uses default if None
            
        Returns:
            Dictionary containing configuration file information
        """
        source_path = config_path or self.config_path
        info = {
            "path": source_path,
            "exists": False,
            "readable": False,
            "valid": False,
            "version": None,
            "created_at": None,
            "last_modified": None,
            "file_size": 0,
            "errors": []
        }
        
        try:
            if os.path.exists(source_path):
                info["exists"] = True
                info["file_size"] = os.path.getsize(source_path)
                
                try:
                    with open(source_path, 'r', encoding='utf-8') as f:
                        config_data = json.load(f)
                    
                    info["readable"] = True
                    info["version"] = config_data.get("version", "0.0")
                    info["created_at"] = config_data.get("created_at")
                    info["last_modified"] = config_data.get("last_modified")
                    
                    # Validate configuration
                    is_valid, errors = self.validate_config_file(source_path)
                    info["valid"] = is_valid
                    info["errors"] = errors
                    
                except json.JSONDecodeError as e:
                    info["errors"].append(f"Invalid JSON: {e}")
                except Exception as e:
                    info["errors"].append(f"Error reading file: {e}")
            else:
                info["errors"].append("Configuration file does not exist")
                
        except Exception as e:
            info["errors"].append(f"Error accessing file: {e}")
        
        return info
    
    def list_backups(self) -> List[Dict[str, Any]]:
        """
        List available backup files.
        
        Returns:
            List of dictionaries containing backup file information
        """
        backups = []
        
        try:
            if not os.path.exists(self.backup_dir):
                return backups
            
            for filename in os.listdir(self.backup_dir):
                if filename.endswith(".json"):
                    filepath = os.path.join(self.backup_dir, filename)
                    try:
                        stat = os.stat(filepath)
                        backups.append({
                            "filename": filename,
                            "path": filepath,
                            "size": stat.st_size,
                            "created": stat.st_mtime,
                            "created_str": self._format_timestamp(stat.st_mtime)
                        })
                    except OSError:
                        continue
            
            # Sort by creation time (newest first)
            backups.sort(key=lambda x: x["created"], reverse=True)
            
        except OSError as e:
            print(f"Error listing backups: {e}")
        
        return backups
    
    def restore_backup(self, backup_filename: str) -> bool:
        """
        Restore configuration from a backup file.
        
        Args:
            backup_filename: Name of backup file to restore
            
        Returns:
            True if successfully restored, False otherwise
        """
        backup_path = os.path.join(self.backup_dir, backup_filename)
        
        try:
            if not os.path.exists(backup_path):
                print(f"Backup file not found: {backup_filename}")
                return False
            
            # Load configuration from backup
            config = self.load_config(backup_path)
            if config is None:
                print(f"Failed to load configuration from backup: {backup_filename}")
                return False
            
            # Save as current configuration
            return self.save_config(config)
            
        except Exception as e:
            print(f"Error restoring backup: {e}")
            return False
    
    def _format_timestamp(self, timestamp: float) -> str:
        """Format timestamp for display"""
        from datetime import datetime
        return datetime.fromtimestamp(timestamp).strftime("%Y-%m-%d %H:%M:%S")


class ContentFilter:
    """
    Main content filtering engine that coordinates all filtering operations.
    
    This class provides the primary interface for filtering web requests,
    managing configuration, and coordinating with various filtering components.
    """
    
    def __init__(self, config: Optional[FilterConfig] = None, config_manager: Optional[ConfigurationManager] = None):
        """
        Initialize the content filter with configuration.
        
        Args:
            config: FilterConfig object, or None to use default configuration
            config_manager: ConfigurationManager instance, or None to create default
        """
        print("DEBUG: ContentFilter __init__ called")
        self.config = config or FilterConfig()
        print("DEBUG: config set")
        self.config_manager = config_manager or ConfigurationManager()
        print("DEBUG: config_manager set")
        self._cache: Dict[str, FilterResult] = {}
        print("DEBUG: cache initialized")
        self._initialize_components()
        print("DEBUG: _initialize_components called")
    
    def _initialize_components(self):
        """Initialize filtering components"""
        print("DEBUG: _initialize_components called")
        
        # Initialize domain checker with database
        db_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'content_filter.db')
        self.domain_checker = DomainChecker(db_path)
        print("DEBUG: domain_checker initialized")
        
        # Initialize keyword filter with same database
        self.keyword_filter = KeywordFilter(db_path)
        print("DEBUG: keyword_filter initialized")
        
        # Initialize safe search enforcer
        self.safe_search_enforcer = SafeSearchEnforcer(enabled=self.config.safe_search_enabled)
        print("DEBUG: safe_search_enforcer initialized")
        
        # Initialize filter logger
        self.logger = FilterLogger(db_path, self.config)
        print("DEBUG: logger initialized")
        
        # Initialize alternative suggester
        self.alternative_suggester = AlternativeSuggester(db_path)
        print("DEBUG: alternative_suggester initialized")
        
        # Initialize user feedback system
        try:
            import sys
            import os
            sys.path.append(os.path.dirname(os.path.abspath(__file__)))
            from wizard.utils.user_feedback import UserFeedbackSystem
            self.user_feedback = UserFeedbackSystem(self.logger, self.config)
            print("✓ User feedback system initialized successfully")
        except Exception as e:
            print(f"Warning: Could not initialize user feedback system: {e}")
            import traceback
            traceback.print_exc()
            self.user_feedback = None
        
        print("DEBUG: _initialize_components completed")
    
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
        
        # Check cache first for performance
        cache_key = f"{request.url}:{request.query}:{request.request_type.value}"
        if cache_key in self._cache:
            return self._cache[cache_key]
        
        # Apply filtering pipeline
        result = self._apply_filtering_pipeline(request)
        
        # Cache result for performance
        if len(self._cache) < self.config.performance_cache_size:
            self._cache[cache_key] = result
        
        return result
    
    def _apply_filtering_pipeline(self, request: WebRequest) -> FilterResult:
        """
        Apply the complete filtering pipeline to a request.
        
        This method applies domain checking, keyword filtering, and safe search enforcement.
        """
        # Extract domain from URL if present
        domain = ""
        if request.url:
            try:
                from urllib.parse import urlparse
                parsed = urlparse(request.url)
                domain = parsed.netloc or parsed.path
            except:
                domain = request.url
        
        # Apply domain filtering if domain checker is available
        if self.domain_checker and domain:
            domain_status = self.domain_checker.check_domain(domain)
            
            if domain_status == DomainStatus.BLOCKED:
                # Get age-appropriate alternative suggestions for blocked content
                blocked_category = self._determine_blocked_category(domain)
                suggested_alternatives = self.get_age_appropriate_suggestions(
                    blocked_category, 
                    blocked_query=request.query if request.query else None
                )
                
                result = FilterResult(
                    allowed=False,
                    reason="Domain is on blacklist",
                    category=blocked_category,
                    suggested_alternatives=suggested_alternatives
                )
                
                # Log blocked attempt
                if self.logger:
                    self.logger.log_blocked_attempt(
                        domain=domain,
                        url=request.url,
                        category=result.category,
                        reason=result.reason,
                        request_type=request.request_type
                    )
                
                return result
                
            elif domain_status == DomainStatus.ALLOWED:
                # Even whitelisted domains should have safe search applied if it's a search
                modified_url = self._apply_safe_search_if_needed(request.url)
                result = FilterResult(
                    allowed=True,
                    reason="Domain is on whitelist",
                    category=ContentCategory.ADULT,
                    suggested_alternatives=[],
                    modified_url=modified_url if modified_url != request.url else None
                )
                
                # Log allowed request
                if self.logger:
                    self.logger.log_allowed_request(
                        domain=domain,
                        url=request.url,
                        request_type=request.request_type
                    )
                
                return result
        
        # Apply keyword filtering if keyword filter is available
        if self.keyword_filter:
            # Check both URL and query for inappropriate keywords
            text_to_check = f"{request.url} {request.query}".strip()
            
            if text_to_check:
                detected_keywords = self.keyword_filter.scan_text(text_to_check)
                
                if detected_keywords:
                    # Determine the most severe category from detected keywords
                    max_severity = 0
                    primary_category = ContentCategory.ADULT
                    
                    for keyword in detected_keywords:
                        severity = self.keyword_filter.get_keyword_severity(keyword)
                        if severity > max_severity:
                            max_severity = severity
                            category_name = self.keyword_filter.get_keyword_category(keyword)
                            try:
                                primary_category = ContentCategory(category_name)
                            except ValueError:
                                primary_category = ContentCategory.ADULT
                    
                    # Check if any detected keywords should be blocked based on context
                    should_block = False
                    for keyword in detected_keywords:
                        if self.keyword_filter.analyze_context(text_to_check, keyword):
                            should_block = True
                            break
                    
                    if should_block:
                        # Get age-appropriate alternative suggestions for blocked content
                        suggested_alternatives = self.get_age_appropriate_suggestions(
                            primary_category, 
                            blocked_query=request.query if request.request_type == RequestType.SEARCH else None
                        )
                        
                        result = FilterResult(
                            allowed=False,
                            reason=f"Content contains inappropriate keywords: {', '.join(detected_keywords[:3])}",
                            category=primary_category,
                            suggested_alternatives=suggested_alternatives
                        )
                        
                        # Log blocked attempt
                        if self.logger:
                            self.logger.log_blocked_attempt(
                                domain=domain,
                                url=request.url,
                                category=result.category,
                                reason=result.reason,
                                request_type=request.request_type,
                                keywords_detected=detected_keywords,
                                severity=max_severity
                            )
                        
                        return result
        
        # Apply safe search enforcement if enabled and this is a search request
        modified_url = self._apply_safe_search_if_needed(request.url)
        
        # If domain status is unknown and no keywords detected, allow by default
        result = FilterResult(
            allowed=True,
            reason="Content filtering passed - no restrictions applied",
            category=ContentCategory.ADULT,
            suggested_alternatives=[],
            modified_url=modified_url if modified_url != request.url else None
        )
        
        # Log allowed request
        if self.logger:
            self.logger.log_allowed_request(
                domain=domain,
                url=request.url,
                request_type=request.request_type
            )
        
        return result
    
    def _apply_safe_search_if_needed(self, url: str) -> str:
        """
        Apply safe search enforcement to URL if needed.
        
        Args:
            url: Original URL
            
        Returns:
            Modified URL with safe search parameters, or original URL if not applicable
        """
        if not self.safe_search_enforcer or not self.config.safe_search_enabled or not url:
            return url
        
        return self.safe_search_enforcer.enforce_safe_search(url)
    
    def _determine_blocked_category(self, domain: str) -> ContentCategory:
        """
        Determine the content category for a blocked domain.
        
        Args:
            domain: Domain that was blocked
            
        Returns:
            ContentCategory that best matches the blocked domain
        """
        if not domain:
            return ContentCategory.ADULT
        
        domain_lower = domain.lower()
        
        # Check domain patterns to determine category
        if any(pattern in domain_lower for pattern in ['adult', 'porn', 'xxx', 'sex', 'nude', 'erotic']):
            return ContentCategory.ADULT
        elif any(pattern in domain_lower for pattern in ['violence', 'gore', 'blood', 'murder', 'death']):
            return ContentCategory.VIOLENCE
        elif any(pattern in domain_lower for pattern in ['casino', 'poker', 'betting', 'gamble', 'lottery']):
            return ContentCategory.GAMBLING
        elif any(pattern in domain_lower for pattern in ['drug', 'cocaine', 'heroin', 'meth', 'cannabis']):
            return ContentCategory.DRUGS
        elif any(pattern in domain_lower for pattern in ['hate', 'nazi', 'racist', 'supremacist', 'extremist']):
            return ContentCategory.HATE_SPEECH
        elif any(pattern in domain_lower for pattern in ['malware', 'virus', 'trojan', 'ransomware']):
            return ContentCategory.MALWARE
        elif any(pattern in domain_lower for pattern in ['phishing', 'scam', 'fake']):
            return ContentCategory.PHISHING
        
        # Try to get category from database if domain checker is available
        if self.domain_checker:
            try:
                with sqlite3.connect(self.domain_checker.db_path) as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT category FROM blocked_domains WHERE domain = ?', (domain,))
                    result = cursor.fetchone()
                    if result:
                        category_name = result[0]
                        try:
                            return ContentCategory(category_name)
                        except ValueError:
                            pass
            except sqlite3.Error:
                pass
        
        # Default to adult content category
        return ContentCategory.ADULT
    
    def get_comprehensive_suggestions(self, blocked_category: ContentCategory, 
                                    blocked_query: Optional[str] = None,
                                    max_alternatives: int = 3,
                                    max_search_terms: int = 2) -> List[str]:
        """
        Get comprehensive suggestions for blocked content including both alternative websites and search terms.
        
        Args:
            blocked_category: Category of the blocked content
            blocked_query: Original search query that was blocked (optional)
            max_alternatives: Maximum number of alternative websites to suggest
            max_search_terms: Maximum number of alternative search terms to suggest
            
        Returns:
            List of suggestion strings formatted for user display
        """
        suggestions = []
        
        if not self.alternative_suggester:
            return suggestions
        
        # Get alternative websites
        alternatives = self.alternative_suggester.get_alternatives_for_blocked_content(
            blocked_category, max_results=max_alternatives
        )
        
        for alt in alternatives:
            suggestions.append(f"Visit {alt['name']}: {alt['url']} - {alt['description']}")
        
        # Get alternative search terms if a query was provided
        if blocked_query:
            alternative_terms = self.alternative_suggester.suggest_alternative_search_terms(
                blocked_query, max_suggestions=max_search_terms
            )
            for term in alternative_terms:
                suggestions.append(f"Try searching for: {term}")
        
        return suggestions
    
    def provide_educational_alternatives(self, blocked_category: ContentCategory) -> List[str]:
        """
        Provide educational alternatives when inappropriate content is blocked.
        
        Args:
            blocked_category: Category of the blocked content
            
        Returns:
            List of educational alternative suggestions
        """
        if not self.alternative_suggester:
            return ["Try searching for educational content instead."]
        
        # Focus on educational alternatives
        educational_alternatives = self.alternative_suggester.get_alternatives_by_category(
            "educational", max_results=3, age_appropriate_only=True
        )
        
        suggestions = []
        for alt in educational_alternatives:
            suggestions.append(f"Learn something new at {alt['name']}: {alt['url']}")
        
        # Add category-specific educational suggestions
        if blocked_category == ContentCategory.VIOLENCE:
            nature_alternatives = self.alternative_suggester.get_alternatives_by_category(
                "nature", max_results=2, age_appropriate_only=True
            )
            for alt in nature_alternatives:
                suggestions.append(f"Explore nature at {alt['name']}: {alt['url']}")
        
        elif blocked_category == ContentCategory.GAMBLING:
            math_alternatives = self.alternative_suggester.get_alternatives_by_category(
                "kids_games", max_results=2, age_appropriate_only=True
            )
            for alt in math_alternatives:
                suggestions.append(f"Play educational games at {alt['name']}: {alt['url']}")
        
        return suggestions[:3]  # Limit to 3 suggestions
    
    def get_age_appropriate_suggestions(self, blocked_category: ContentCategory,
                                      blocked_query: Optional[str] = None) -> List[str]:
        """
        Get age-appropriate suggestions based on the current age profile.
        
        Args:
            blocked_category: Category of the blocked content
            blocked_query: Original search query that was blocked (optional)
            
        Returns:
            List of age-appropriate suggestion strings
        """
        if not self.alternative_suggester:
            return ["Try searching for something else."]
        
        suggestions = []
        
        # Adjust suggestions based on age profile
        if self.config.age_profile == AgeProfile.CHILD:
            # For children, focus on educational and safe entertainment
            educational_alts = self.alternative_suggester.get_alternatives_by_category(
                "educational", max_results=2, age_appropriate_only=True
            )
            kids_games = self.alternative_suggester.get_alternatives_by_category(
                "kids_games", max_results=2, age_appropriate_only=True
            )
            
            for alt in educational_alts + kids_games:
                suggestions.append(f"Try {alt['name']}: {alt['url']}")
            
            # Suggest safe search terms for children
            if blocked_query:
                safe_terms = ["fun learning games", "educational videos", "kids activities"]
                suggestions.extend([f"Search for: {term}" for term in safe_terms[:2]])
        
        elif self.config.age_profile == AgeProfile.TEEN:
            # For teens, include more variety but still age-appropriate
            categories = ["educational", "entertainment", "science", "sports"]
            for category in categories[:2]:
                alts = self.alternative_suggester.get_alternatives_by_category(
                    category, max_results=1, age_appropriate_only=True
                )
                for alt in alts:
                    suggestions.append(f"Check out {alt['name']}: {alt['url']}")
            
            # Suggest modified search terms
            if blocked_query:
                alternative_terms = self.alternative_suggester.suggest_alternative_search_terms(
                    blocked_query, max_suggestions=2
                )
                for term in alternative_terms:
                    suggestions.append(f"Try searching: {term}")
        
        else:  # Adult profile
            # For adults, provide comprehensive alternatives
            return self.get_comprehensive_suggestions(
                blocked_category, blocked_query, max_alternatives=2, max_search_terms=2
            )
        
        return suggestions[:4]  # Limit to 4 suggestions
    
    def get_voice_friendly_suggestions(self, filter_result: FilterResult) -> List[str]:
        """
        Get suggestions formatted for voice response when content is blocked.
        
        Args:
            filter_result: FilterResult containing blocking information
            
        Returns:
            List of concise suggestions suitable for voice response
        """
        if not filter_result.suggested_alternatives:
            return ["Try searching for something else."]
        
        # Convert detailed suggestions to voice-friendly format
        voice_suggestions = []
        
        for suggestion in filter_result.suggested_alternatives[:3]:  # Limit for voice
            if "Try searching for:" in suggestion:
                # Extract just the search term
                term = suggestion.replace("Try searching for:", "").strip()
                voice_suggestions.append(f"Search for {term}")
            elif ":" in suggestion and "http" in suggestion:
                # Extract website name from URL suggestions
                parts = suggestion.split(":")
                if len(parts) >= 2:
                    name = parts[0].replace("Visit", "").replace("Try", "").replace("Check out", "").strip()
                    voice_suggestions.append(f"Visit {name}")
            else:
                # Use suggestion as-is but keep it concise
                voice_suggestions.append(suggestion[:50])  # Truncate long suggestions
        
        return voice_suggestions
    
    def provide_helpful_alternatives_message(self, blocked_category: ContentCategory,
                                           blocked_query: Optional[str] = None,
                                           include_educational: bool = True) -> str:
        """
        Provide a helpful message with alternatives when content is blocked.
        
        Args:
            blocked_category: Category of the blocked content
            blocked_query: Original search query that was blocked (optional)
            include_educational: Whether to emphasize educational alternatives
            
        Returns:
            Formatted message with helpful alternatives
        """
        if include_educational and self.config.age_profile in [AgeProfile.CHILD, AgeProfile.TEEN]:
            suggestions = self.provide_educational_alternatives(blocked_category)
        else:
            suggestions = self.get_age_appropriate_suggestions(blocked_category, blocked_query)
        
        if not suggestions:
            return "This content has been blocked. Please try searching for something else."
        
        message = "This content has been blocked for your safety. Here are some helpful alternatives:\n\n"
        
        for i, suggestion in enumerate(suggestions[:3], 1):
            message += f"{i}. {suggestion}\n"
        
        if blocked_query:
            message += f"\nYou can also try modifying your search terms to find appropriate content."
        
        return message
    
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
    
    def is_domain_allowed(self, domain: str) -> bool:
        """
        Check if a domain is allowed by the filter.
        
        Args:
            domain: Domain name to check
            
        Returns:
            True if domain is allowed, False otherwise
        """
        if not self.domain_checker:
            return True
        
        status = self.domain_checker.check_domain(domain)
        return status != DomainStatus.BLOCKED
    
    def add_to_blacklist(self, domain: str) -> bool:
        """
        Add a domain to the custom blacklist.
        
        Args:
            domain: Domain to add to blacklist
            
        Returns:
            True if successfully added, False otherwise
        """
        # Add to configuration
        if domain not in self.config.custom_blacklist:
            self.config.custom_blacklist.append(domain)
        
        # Add to domain checker if available
        success = True
        if self.domain_checker:
            success = self.domain_checker.add_to_blacklist(domain, "custom")
        
        if success:
            self._clear_cache()  # Clear cache to ensure new rules apply
        
        return success
    
    def add_to_whitelist(self, domain: str) -> bool:
        """
        Add a domain to the custom whitelist.
        
        Args:
            domain: Domain to add to whitelist
            
        Returns:
            True if successfully added, False otherwise
        """
        # Add to configuration
        if domain not in self.config.custom_whitelist:
            self.config.custom_whitelist.append(domain)
        
        # Add to domain checker if available
        success = True
        if self.domain_checker:
            success = self.domain_checker.add_to_whitelist(domain)
        
        if success:
            self._clear_cache()  # Clear cache to ensure new rules apply
        
        return success
    
    def _clear_cache(self):
        """Clear the filtering cache"""
        self._cache.clear()
    
    def get_comprehensive_suggestions(self, blocked_category: ContentCategory, 
                                    blocked_query: Optional[str] = None,
                                    max_alternatives: int = 3,
                                    max_search_terms: int = 2) -> List[str]:
        """
        Get comprehensive suggestions for blocked content including both alternative websites and search terms.
        
        Args:
            blocked_category: Category of the blocked content
            blocked_query: Original search query that was blocked (optional)
            max_alternatives: Maximum number of alternative websites to suggest
            max_search_terms: Maximum number of alternative search terms to suggest
            
        Returns:
            List of suggestion strings formatted for user display
        """
        suggestions = []
        
        if not self.alternative_suggester:
            return suggestions
        
        # Get alternative websites
        alternatives = self.alternative_suggester.get_alternatives_for_blocked_content(
            blocked_category, max_results=max_alternatives
        )
        
        for alt in alternatives:
            suggestions.append(f"Visit {alt['name']}: {alt['url']} - {alt['description']}")
        
        # Get alternative search terms if a query was provided
        if blocked_query:
            alternative_terms = self.alternative_suggester.suggest_alternative_search_terms(
                blocked_query, max_suggestions=max_search_terms
            )
            for term in alternative_terms:
                suggestions.append(f"Try searching for: {term}")
        
        return suggestions
    
    def get_age_appropriate_suggestions(self, blocked_category: ContentCategory,
                                      blocked_query: Optional[str] = None) -> List[str]:
        """
        Get age-appropriate suggestions based on the current age profile.
        
        Args:
            blocked_category: Category of the blocked content
            blocked_query: Original search query that was blocked (optional)
            
        Returns:
            List of age-appropriate suggestion strings
        """
        if not self.alternative_suggester:
            return ["Try searching for something else."]
        
        suggestions = []
        
        # Adjust suggestions based on age profile
        if self.config.age_profile == AgeProfile.CHILD:
            # For children, focus on educational and safe entertainment
            educational_alts = self.alternative_suggester.get_alternatives_by_category(
                "educational", max_results=2, age_appropriate_only=True
            )
            kids_games = self.alternative_suggester.get_alternatives_by_category(
                "kids_games", max_results=2, age_appropriate_only=True
            )
            
            for alt in educational_alts + kids_games:
                suggestions.append(f"Try {alt['name']}: {alt['url']}")
            
            # Suggest safe search terms for children
            if blocked_query:
                safe_terms = ["fun learning games", "educational videos", "kids activities"]
                suggestions.extend([f"Search for: {term}" for term in safe_terms[:2]])
        
        elif self.config.age_profile == AgeProfile.TEEN:
            # For teens, include more variety but still age-appropriate
            categories = ["educational", "entertainment", "science", "sports"]
            for category in categories[:2]:
                alts = self.alternative_suggester.get_alternatives_by_category(
                    category, max_results=1, age_appropriate_only=True
                )
                for alt in alts:
                    suggestions.append(f"Check out {alt['name']}: {alt['url']}")
            
            # Suggest modified search terms
            if blocked_query:
                alternative_terms = self.alternative_suggester.suggest_alternative_search_terms(
                    blocked_query, max_suggestions=2
                )
                for term in alternative_terms:
                    suggestions.append(f"Try searching: {term}")
        
        else:  # Adult profile
            # For adults, provide comprehensive alternatives
            return self.get_comprehensive_suggestions(
                blocked_category, blocked_query, max_alternatives=2, max_search_terms=2
            )
        
        return suggestions[:4]  # Limit to 4 suggestions
    
    def get_voice_friendly_suggestions(self, filter_result: FilterResult) -> List[str]:
        """
        Get suggestions formatted for voice response when content is blocked.
        
        Args:
            filter_result: FilterResult containing blocking information
            
        Returns:
            List of concise suggestions suitable for voice response
        """
        if not filter_result.suggested_alternatives:
            return ["Try searching for something else."]
        
        # Convert detailed suggestions to voice-friendly format
        voice_suggestions = []
        
        for suggestion in filter_result.suggested_alternatives[:3]:  # Limit for voice
            if "Try searching for:" in suggestion:
                # Extract just the search term
                term = suggestion.replace("Try searching for:", "").strip()
                voice_suggestions.append(f"Search for {term}")
            elif ":" in suggestion and "http" in suggestion:
                # Extract website name from URL suggestions
                parts = suggestion.split(":")
                if len(parts) >= 2:
                    name = parts[0].replace("Visit", "").replace("Try", "").replace("Check out", "").strip()
                    voice_suggestions.append(f"Visit {name}")
            else:
                # Use suggestion as-is but keep it concise
                voice_suggestions.append(suggestion[:50])  # Truncate long suggestions
        
        return voice_suggestions
    
    def provide_helpful_alternatives_message(self, blocked_category: ContentCategory,
                                           blocked_query: Optional[str] = None,
                                           include_educational: bool = True) -> str:
        """
        Provide a helpful message with alternatives when content is blocked.
        
        Args:
            blocked_category: Category of the blocked content
            blocked_query: Original search query that was blocked (optional)
            include_educational: Whether to emphasize educational alternatives
            
        Returns:
            Formatted message with helpful alternatives
        """
        if include_educational and self.config.age_profile in [AgeProfile.CHILD, AgeProfile.TEEN]:
            suggestions = self.provide_educational_alternatives(blocked_category)
        else:
            suggestions = self.get_age_appropriate_suggestions(blocked_category, blocked_query)
        
        if not suggestions:
            return "This content has been blocked. Please try searching for something else."
        
        message = "This content has been blocked for your safety. Here are some helpful alternatives:\n\n"
        
        for i, suggestion in enumerate(suggestions[:3], 1):
            message += f"{i}. {suggestion}\n"
        
        if blocked_query:
            message += f"\nYou can also try modifying your search terms to find appropriate content."
        
        return message
    
    def provide_educational_alternatives(self, blocked_category: ContentCategory) -> List[str]:
        """
        Provide educational alternatives when inappropriate content is blocked.
        
        Args:
            blocked_category: Category of the blocked content
            
        Returns:
            List of educational alternative suggestions
        """
        if not self.alternative_suggester:
            return ["Try searching for educational content instead."]
        
        # Focus on educational alternatives
        educational_alternatives = self.alternative_suggester.get_alternatives_by_category(
            "educational", max_results=3, age_appropriate_only=True
        )
        
        suggestions = []
        for alt in educational_alternatives:
            suggestions.append(f"Learn something new at {alt['name']}: {alt['url']}")
        
        # Add category-specific educational suggestions
        if blocked_category == ContentCategory.VIOLENCE:
            nature_alternatives = self.alternative_suggester.get_alternatives_by_category(
                "nature", max_results=2, age_appropriate_only=True
            )
            for alt in nature_alternatives:
                suggestions.append(f"Explore nature at {alt['name']}: {alt['url']}")
        
        elif blocked_category == ContentCategory.GAMBLING:
            math_alternatives = self.alternative_suggester.get_alternatives_by_category(
                "kids_games", max_results=2, age_appropriate_only=True
            )
            for alt in math_alternatives:
                suggestions.append(f"Play educational games at {alt['name']}: {alt['url']}")
        
        return suggestions[:3]  # Limit to 3 suggestions
        """
        if not self.domain_checker:
            return True
        
        status = self.domain_checker.check_domain(domain)
        return status != DomainStatus.BLOCKED
    
    def add_to_blacklist(self, domain: str) -> bool:
        """
        Add a domain to the custom blacklist.
        
        Args:
            domain: Domain to add to blacklist
            
        Returns:
            True if successfully added, False otherwise
        """
        # Add to configuration
        if domain not in self.config.custom_blacklist:
            self.config.custom_blacklist.append(domain)
        
        # Add to domain checker if available
        success = True
        if self.domain_checker:
            success = self.domain_checker.add_to_blacklist(domain, "custom")
        
        if success:
            self._clear_cache()  # Clear cache to ensure new rules apply
        
        return success
    
    def add_to_whitelist(self, domain: str) -> bool:
        """
        Add a domain to the custom whitelist.
        
        Args:
            domain: Domain to add to whitelist
            
        Returns:
            True if successfully added, False otherwise
        """
        # Add to configuration
        if domain not in self.config.custom_whitelist:
            self.config.custom_whitelist.append(domain)
        
        # Add to domain checker if available
        success = True
        if self.domain_checker:
            success = self.domain_checker.add_to_whitelist(domain)
        
        if success:
            self._clear_cache()  # Clear cache to ensure new rules apply
        
        return success
    
    def enforce_safe_search(self, url: str) -> str:
        """
        Enforce safe search on a URL.
        
        Args:
            url: URL to modify with safe search parameters
            
        Returns:
            Modified URL with safe search enabled, or original URL if not applicable
        """
        if not self.safe_search_enforcer:
            return url
        
        return self.safe_search_enforcer.enforce_safe_search(url)
    
    def is_safe_search_enabled_in_url(self, url: str) -> bool:
        """
        Check if safe search is already enabled in a URL.
        
        Args:
            url: URL to check
            
        Returns:
            True if safe search parameters are present, False otherwise
        """
        if not self.safe_search_enforcer:
            return False
        
        return self.safe_search_enforcer.is_safe_search_enabled(url)
    
    def set_safe_search_enabled(self, enabled: bool):
        """
        Enable or disable safe search enforcement.
        
        Args:
            enabled: Whether to enable safe search enforcement
        """
        self.config.safe_search_enabled = enabled
        if self.safe_search_enforcer:
            self.safe_search_enforcer.set_enabled(enabled)
        self._clear_cache()  # Clear cache to ensure new settings apply
    
    def _clear_cache(self):
        """Clear the filtering cache"""
        self._cache.clear()
    
    def load_config(self, config_path: Optional[str] = None) -> bool:
        """
        Load configuration from a JSON file using ConfigurationManager.
        
        Args:
            config_path: Path to configuration file, or None to use default
            
        Returns:
            True if successfully loaded, False otherwise
        """
        try:
            loaded_config = self.config_manager.load_config(config_path)
            if loaded_config is not None:
                self.config = loaded_config
                self._clear_cache()  # Clear cache after config change
                return True
            return False
        except Exception as e:
            print(f"Error loading configuration: {e}")
            return False
    
    def save_config(self, config_path: Optional[str] = None) -> bool:
        """
        Save current configuration to a JSON file using ConfigurationManager.
        
        Args:
            config_path: Path where to save configuration, or None to use default
            
        Returns:
            True if successfully saved, False otherwise
        """
        try:
            return self.config_manager.save_config(self.config, config_path)
        except Exception as e:
            print(f"Error saving configuration: {e}")
            return False
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get filtering statistics.
        
        Returns:
            Dictionary containing filtering statistics
        """
        stats = {
            "cache_size": len(self._cache),
            "max_cache_size": self.config.performance_cache_size,
            "filtering_enabled": self.config.enabled,
            "filtering_level": self.config.filtering_level.value,
            "safe_search_enabled": self.config.safe_search_enabled,
            "blocked_categories": [cat.value for cat in self.config.blocked_categories],
            "custom_blacklist_size": len(self.config.custom_blacklist),
            "custom_whitelist_size": len(self.config.custom_whitelist)
        }
        
        # Add domain checker statistics if available
        if self.domain_checker:
            domain_stats = self.domain_checker.get_stats()
            stats.update({
                "domain_blacklist_size": domain_stats.get("blacklist_size", 0),
                "domain_whitelist_size": domain_stats.get("whitelist_size", 0),
                "domain_database_path": domain_stats.get("database_path", "")
            })
        
        # Add keyword filter statistics if available
        if self.keyword_filter:
            keyword_stats = self.keyword_filter.get_stats()
            stats.update({
                "keyword_total": keyword_stats.get("total_keywords", 0),
                "keywords_by_category": keyword_stats.get("keywords_by_category", {}),
                "keywords_by_severity": keyword_stats.get("keywords_by_severity", {}),
                "keywords_by_language": keyword_stats.get("keywords_by_language", {})
            })
        
        # Add safe search enforcer statistics if available
        if self.safe_search_enforcer:
            safe_search_stats = self.safe_search_enforcer.get_stats()
            stats.update({
                "safe_search_enforcer_enabled": safe_search_stats.get("enabled", False),
                "supported_search_engines": safe_search_stats.get("supported_engines", 0),
                "search_engines": safe_search_stats.get("engines", []),
                "total_search_domains": safe_search_stats.get("total_domains", 0)
            })
        
        return stats
    
    def get_logging_statistics(self, days: int = 30) -> Dict[str, Any]:
        """
        Get logging and monitoring statistics.
        
        Args:
            days: Number of days to include in statistics (default: 30)
            
        Returns:
            Dictionary containing logging statistics
        """
        if not self.logger:
            return {"error": "Logger not initialized"}
        
        return self.logger.get_statistics(days)
    
    def export_logs(self, output_path: str, format: str = "csv", 
                   start_date: Optional[datetime.date] = None,
                   end_date: Optional[datetime.date] = None,
                   action_filter: Optional[str] = None,
                   category_filter: Optional[str] = None) -> bool:
        """
        Export filter logs to a file.
        
        Args:
            output_path: Path to output file
            format: Export format ('csv' or 'json')
            start_date: Optional start date filter
            end_date: Optional end date filter
            action_filter: Optional action filter ('blocked' or 'allowed')
            category_filter: Optional category filter
            
        Returns:
            True if export successful, False otherwise
        """
        if not self.logger:
            return False
        
        return self.logger.export_logs(
            output_path, format, start_date, end_date, action_filter, category_filter
        )
    
    def report_false_positive(self, domain: str, url: str, category: str, 
                             reason: str, user_feedback: str) -> bool:
        """
        Report a false positive blocking.
        
        Args:
            domain: Domain that was incorrectly blocked
            url: Full URL that was incorrectly blocked
            category: Category that triggered the false positive
            reason: Original reason for blocking
            user_feedback: User explanation of why this is a false positive
            
        Returns:
            True if report submitted successfully, False otherwise
        """
        if not self.logger:
            return False
        
        return self.logger.report_false_positive(domain, url, category, reason, user_feedback)
    
    def get_false_positive_reports(self, status: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get false positive reports.
        
        Args:
            status: Optional status filter ('pending', 'resolved', 'rejected')
            
        Returns:
            List of false positive reports
        """
        if not self.logger:
            return []
        
        return self.logger.get_false_positive_reports(status)
    
    def get_log_summary(self) -> Dict[str, Any]:
        """
        Get a summary of the logging system status.
        
        Returns:
            Dictionary containing logging system information
        """
        if not self.logger:
            return {"error": "Logger not initialized"}
        
        return self.logger.get_log_summary()
    
    def clear_old_logs(self, days_to_keep: int = 90) -> int:
        """
        Clear old log entries to manage database size.
        
        Args:
            days_to_keep: Number of days of logs to keep (default: 90)
            
        Returns:
            Number of log entries deleted
        """
        if not self.logger:
            return 0
        
        return self.logger.clear_old_logs(days_to_keep)
    
    def get_user_feedback_message(self, filter_result: FilterResult,
                                 include_alternatives: bool = True,
                                 include_report_option: bool = True) -> Dict[str, Any]:
        """
        Get user-friendly feedback message for blocked content.
        
        Args:
            filter_result: FilterResult containing blocking information
            include_alternatives: Whether to include alternative suggestions
            include_report_option: Whether to include false positive reporting option
            
        Returns:
            Dictionary containing user message and options
        """
        if not hasattr(self, 'user_feedback') or not self.user_feedback:
            return {"error": "User feedback system not available"}
        
        return self.user_feedback.get_blocked_content_message(
            filter_result, 
            self.config.age_profile,
            include_alternatives,
            include_report_option
        )
    
    def get_search_blocked_feedback(self, query: str, detected_keywords: List[str],
                                   suggest_alternatives: bool = True) -> Dict[str, Any]:
        """
        Get user-friendly feedback message for blocked search queries.
        
        Args:
            query: The blocked search query
            detected_keywords: List of inappropriate keywords detected
            suggest_alternatives: Whether to suggest alternative search terms
            
        Returns:
            Dictionary containing user message and suggestions
        """
        if not hasattr(self, 'user_feedback') or not self.user_feedback:
            return {"error": "User feedback system not available"}
        
        return self.user_feedback.get_search_blocked_message(
            query, 
            detected_keywords,
            self.config.age_profile,
            suggest_alternatives
        )
    
    def get_voice_response_message(self, filter_result: FilterResult) -> str:
        """
        Get a concise message suitable for voice response when content is blocked.
        
        Args:
            filter_result: FilterResult containing blocking information
            
        Returns:
            String message suitable for text-to-speech
        """
        if not hasattr(self, 'user_feedback') or not self.user_feedback:
            return "Content has been blocked by the filter."
        
        return self.user_feedback.get_user_message_for_voice_response(
            filter_result, 
            self.config.age_profile
        )
    
    def submit_false_positive_report(self, domain: str, url: str, category: str,
                                   reason: str, user_feedback: str,
                                   user_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Submit a false positive report with user feedback.
        
        Args:
            domain: Domain that was incorrectly blocked
            url: Full URL that was incorrectly blocked
            category: Category that triggered the false positive
            reason: Original reason for blocking
            user_feedback: User explanation of why this is a false positive
            user_id: Optional user identifier
            
        Returns:
            Dictionary containing report status and information
        """
        if not hasattr(self, 'user_feedback') or not self.user_feedback:
            return {"success": False, "error": "User feedback system not available"}
        
        return self.user_feedback.report_false_positive(
            domain, url, category, reason, user_feedback, user_id
        )
    
    def get_false_positive_form(self, domain: str, url: str, 
                               category: str, reason: str) -> Dict[str, Any]:
        """
        Get form data for false positive reporting.
        
        Args:
            domain: Domain that was blocked
            url: URL that was blocked
            category: Category that triggered the block
            reason: Reason for blocking
            
        Returns:
            Dictionary containing form data and instructions
        """
        if not hasattr(self, 'user_feedback') or not self.user_feedback:
            return {"error": "User feedback system not available"}
        
        return self.user_feedback.get_false_positive_form_data(domain, url, category, reason)
        
        return self.logger.clear_old_logs(days_to_keep)
    
    def get_user_feedback_message(self, filter_result: FilterResult,
                                 include_alternatives: bool = True,
                                 include_report_option: bool = True) -> Dict[str, Any]:
        """
        Get user-friendly feedback message for blocked content.
        
        Args:
            filter_result: FilterResult containing blocking information
            include_alternatives: Whether to include alternative suggestions
            include_report_option: Whether to include false positive reporting option
            
        Returns:
            Dictionary containing user message and options
        """
        if not hasattr(self, 'user_feedback') or not self.user_feedback:
            return {"error": "User feedback system not available"}
        
        return self.user_feedback.get_blocked_content_message(
            filter_result, 
            self.config.age_profile,
            include_alternatives,
            include_report_option
        )
    
    def get_search_blocked_feedback(self, query: str, detected_keywords: List[str],
                                   suggest_alternatives: bool = True) -> Dict[str, Any]:
        """
        Get user-friendly feedback message for blocked search queries.
        
        Args:
            query: The blocked search query
            detected_keywords: List of inappropriate keywords detected
            suggest_alternatives: Whether to suggest alternative search terms
            
        Returns:
            Dictionary containing user message and suggestions
        """
        if not hasattr(self, 'user_feedback') or not self.user_feedback:
            return {"error": "User feedback system not available"}
        
        return self.user_feedback.get_search_blocked_message(
            query, 
            detected_keywords,
            self.config.age_profile,
            suggest_alternatives
        )
    
    def get_voice_response_message(self, filter_result: FilterResult) -> str:
        """
        Get a concise message suitable for voice response when content is blocked.
        
        Args:
            filter_result: FilterResult containing blocking information
            
        Returns:
            String message suitable for text-to-speech
        """
        if not hasattr(self, 'user_feedback') or not self.user_feedback:
            return "Content has been blocked by the filter."
        
        return self.user_feedback.get_user_message_for_voice_response(
            filter_result, 
            self.config.age_profile
        )
    
    def submit_false_positive_report(self, domain: str, url: str, category: str,
                                   reason: str, user_feedback: str,
                                   user_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Submit a false positive report with user feedback.
        
        Args:
            domain: Domain that was incorrectly blocked
            url: Full URL that was incorrectly blocked
            category: Category that triggered the false positive
            reason: Original reason for blocking
            user_feedback: User explanation of why this is a false positive
            user_id: Optional user identifier
            
        Returns:
            Dictionary containing report status and information
        """
        if not hasattr(self, 'user_feedback') or not self.user_feedback:
            return {"success": False, "error": "User feedback system not available"}
        
        return self.user_feedback.report_false_positive(
            domain, url, category, reason, user_feedback, user_id
        )
    
    def get_false_positive_form(self, domain: str, url: str, 
                               category: str, reason: str) -> Dict[str, Any]:
        """
        Get form data for false positive reporting.
        
        Args:
            domain: Domain that was blocked
            url: URL that was blocked
            category: Category that triggered the block
            reason: Reason for blocking
            
        Returns:
            Dictionary containing form data and instructions
        """
        if not hasattr(self, 'user_feedback') or not self.user_feedback:
            return {"error": "User feedback system not available"}
        
        return self.user_feedback.get_false_positive_form_data(domain, url, category, reason)
    
    def get_user_feedback_message(self, filter_result: FilterResult,
                                 include_alternatives: bool = True,
                                 include_report_option: bool = True) -> Dict[str, Any]:
        """
        Get user-friendly feedback message for blocked content.
        
        Args:
            filter_result: FilterResult containing blocking information
            include_alternatives: Whether to include alternative suggestions
            include_report_option: Whether to include false positive reporting option
            
        Returns:
            Dictionary containing user message and options
        """
        if not hasattr(self, 'user_feedback') or not self.user_feedback:
            return {"error": "User feedback system not available"}
        
        return self.user_feedback.get_blocked_content_message(
            filter_result, 
            self.config.age_profile,
            include_alternatives,
            include_report_option
        )
    
    def get_search_blocked_feedback(self, query: str, detected_keywords: List[str],
                                   suggest_alternatives: bool = True) -> Dict[str, Any]:
        """
        Get user-friendly feedback message for blocked search queries.
        
        Args:
            query: The blocked search query
            detected_keywords: List of inappropriate keywords detected
            suggest_alternatives: Whether to suggest alternative search terms
            
        Returns:
            Dictionary containing user message and suggestions
        """
        if not hasattr(self, 'user_feedback') or not self.user_feedback:
            return {"error": "User feedback system not available"}
        
        return self.user_feedback.get_search_blocked_message(
            query, 
            detected_keywords,
            self.config.age_profile,
            suggest_alternatives
        )
    
    def get_voice_response_message(self, filter_result: FilterResult) -> str:
        """
        Get a concise message suitable for voice response when content is blocked.
        
        Args:
            filter_result: FilterResult containing blocking information
            
        Returns:
            String message suitable for text-to-speech
        """
        if not hasattr(self, 'user_feedback') or not self.user_feedback:
            return "Content has been blocked by the filter."
        
        return self.user_feedback.get_user_message_for_voice_response(
            filter_result, 
            self.config.age_profile
        )
    
    def submit_false_positive_report(self, domain: str, url: str, category: str,
                                   reason: str, user_feedback: str,
                                   user_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Submit a false positive report with user feedback.
        
        Args:
            domain: Domain that was incorrectly blocked
            url: Full URL that was incorrectly blocked
            category: Category that triggered the false positive
            reason: Original reason for blocking
            user_feedback: User explanation of why this is a false positive
            user_id: Optional user identifier
            
        Returns:
            Dictionary containing report status and information
        """
        if not hasattr(self, 'user_feedback') or not self.user_feedback:
            return {"success": False, "error": "User feedback system not available"}
        
        return self.user_feedback.report_false_positive(
            domain, url, category, reason, user_feedback, user_id
        )
    
    def get_false_positive_form(self, domain: str, url: str, 
                               category: str, reason: str) -> Dict[str, Any]:
        """
        Get form data for false positive reporting.
        
        Args:
            domain: Domain that was blocked
            url: URL that was blocked
            category: Category that triggered the block
            reason: Reason for blocking
            
        Returns:
            Dictionary containing form data and instructions
        """
        if not hasattr(self, 'user_feedback') or not self.user_feedback:
            return {"error": "User feedback system not available"}
        
        return self.user_feedback.get_false_positive_form_data(domain, url, category, reason)
    
    def get_user_feedback_message(self, filter_result: FilterResult,
                                 include_alternatives: bool = True,
                                 include_report_option: bool = True) -> Dict[str, Any]:
        """
        Get user-friendly feedback message for blocked content.
        
        Args:
            filter_result: FilterResult containing blocking information
            include_alternatives: Whether to include alternative suggestions
            include_report_option: Whether to include false positive reporting option
            
        Returns:
            Dictionary containing user message and options
        """
        if not self.user_feedback:
            return {"error": "User feedback system not available"}
        
        return self.user_feedback.get_blocked_content_message(
            filter_result, 
            self.config.age_profile,
            include_alternatives,
            include_report_option
        )
    
    def get_search_blocked_feedback(self, query: str, detected_keywords: List[str],
                                   suggest_alternatives: bool = True) -> Dict[str, Any]:
        """
        Get user-friendly feedback message for blocked search queries.
        
        Args:
            query: The blocked search query
            detected_keywords: List of inappropriate keywords detected
            suggest_alternatives: Whether to suggest alternative search terms
            
        Returns:
            Dictionary containing user message and suggestions
        """
        if not self.user_feedback:
            return {"error": "User feedback system not available"}
        
        return self.user_feedback.get_search_blocked_message(
            query, 
            detected_keywords,
            self.config.age_profile,
            suggest_alternatives
        )
    
    def get_voice_response_message(self, filter_result: FilterResult) -> str:
        """
        Get a concise message suitable for voice response when content is blocked.
        
        Args:
            filter_result: FilterResult containing blocking information
            
        Returns:
            String message suitable for text-to-speech
        """
        if not self.user_feedback:
            return "Content has been blocked by the filter."
        
        return self.user_feedback.get_user_message_for_voice_response(
            filter_result, 
            self.config.age_profile
        )
    
    def submit_false_positive_report(self, domain: str, url: str, category: str,
                                   reason: str, user_feedback: str,
                                   user_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Submit a false positive report with user feedback.
        
        Args:
            domain: Domain that was incorrectly blocked
            url: Full URL that was incorrectly blocked
            category: Category that triggered the false positive
            reason: Original reason for blocking
            user_feedback: User explanation of why this is a false positive
            user_id: Optional user identifier
            
        Returns:
            Dictionary containing report status and information
        """
        if not self.user_feedback:
            return {"success": False, "error": "User feedback system not available"}
        
        return self.user_feedback.report_false_positive(
            domain, url, category, reason, user_feedback, user_id
        )
    
    def get_false_positive_form(self, domain: str, url: str, 
                               category: str, reason: str) -> Dict[str, Any]:
        """
        Get form data for false positive reporting.
        
        Args:
            domain: Domain that was blocked
            url: URL that was blocked
            category: Category that triggered the block
            reason: Reason for blocking
            
        Returns:
            Dictionary containing form data and instructions
        """
        if not self.user_feedback:
            return {"error": "User feedback system not available"}
        
        return self.user_feedback.get_false_positive_form_data(domain, url, category, reason)


class SafeSearchEnforcer:
    """
    Manages safe search enforcement for major search engines.
    
    This class modifies search URLs to enable safe search parameters,
    supporting Google, Bing, YouTube, and image search safe modes.
    """
    
    def __init__(self, enabled: bool = True):
        """
        Initialize the safe search enforcer.
        
        Args:
            enabled: Whether safe search enforcement is enabled
        """
        self.enabled = enabled
        self._search_engines = self._initialize_search_engines()
    
    def _initialize_search_engines(self) -> Dict[str, Dict[str, str]]:
        """
        Initialize search engine configurations with safe search parameters.
        
        Returns:
            Dictionary mapping search engines to their safe search configurations
        """
        return {
            "google": {
                "domains": ["google.com", "google.co.uk", "google.ca", "google.com.au", 
                           "google.de", "google.fr", "google.es", "google.it", "google.co.jp"],
                "safe_param": "safe=active",
                "image_param": "safe=active",
                "video_param": "safe=active"
            },
            "bing": {
                "domains": ["bing.com", "www.bing.com"],
                "safe_param": "adlt=strict",
                "image_param": "adlt=strict",
                "video_param": "adlt=strict"
            },
            "youtube": {
                "domains": ["youtube.com", "www.youtube.com", "m.youtube.com"],
                "safe_param": "safe_search=1",
                "search_param": "safe_search=1"
            },
            "duckduckgo": {
                "domains": ["duckduckgo.com", "www.duckduckgo.com"],
                "safe_param": "safe_search=1",
                "moderate_param": "safe_search=0"
            },
            "yahoo": {
                "domains": ["yahoo.com", "search.yahoo.com"],
                "safe_param": "vm=r&fl=1",
                "image_param": "vm=r&fl=1"
            }
        }
    
    def _detect_search_engine(self, url: str) -> Optional[str]:
        """
        Detect which search engine a URL belongs to.
        
        Args:
            url: URL to analyze
            
        Returns:
            Search engine name if detected, None otherwise
        """
        if not url:
            return None
        
        try:
            from urllib.parse import urlparse
            parsed = urlparse(url.lower())
            domain = parsed.netloc
            
            # Remove www. prefix for consistency
            if domain.startswith("www."):
                domain = domain[4:]
            
            # Check each search engine's domains
            for engine, config in self._search_engines.items():
                for engine_domain in config["domains"]:
                    if engine_domain.startswith("www."):
                        engine_domain = engine_domain[4:]
                    
                    if domain == engine_domain or domain.endswith("." + engine_domain):
                        return engine
            
            return None
            
        except Exception:
            return None
    
    def _is_image_search(self, url: str) -> bool:
        """
        Check if URL is for image search.
        
        Args:
            url: URL to check
            
        Returns:
            True if this is an image search URL
        """
        image_indicators = [
            "tbm=isch",  # Google Images
            "images/search",  # Bing Images
            "/images?",  # Generic images
            "image_search",
            "imagesearch"
        ]
        
        url_lower = url.lower()
        return any(indicator in url_lower for indicator in image_indicators)
    
    def _is_video_search(self, url: str) -> bool:
        """
        Check if URL is for video search.
        
        Args:
            url: URL to check
            
        Returns:
            True if this is a video search URL
        """
        video_indicators = [
            "tbm=vid",  # Google Videos
            "videos/search",  # Bing Videos
            "/videos?",  # Generic videos
            "video_search",
            "videosearch",
            "youtube.com/results"  # YouTube search
        ]
        
        url_lower = url.lower()
        return any(indicator in url_lower for indicator in video_indicators)
    
    def _add_safe_search_param(self, url: str, param: str) -> str:
        """
        Add safe search parameter to URL.
        
        Args:
            url: Original URL
            param: Safe search parameter to add
            
        Returns:
            Modified URL with safe search parameter
        """
        if not url or not param:
            return url
        
        try:
            from urllib.parse import urlparse, parse_qs, urlencode, urlunparse
            
            parsed = urlparse(url)
            query_params = parse_qs(parsed.query)
            
            # Parse the new parameter
            if "=" in param:
                key, value = param.split("=", 1)
                
                # Handle special cases for different parameter formats
                if key == "vm" and "fl" in param:
                    # Yahoo format: vm=r&fl=1
                    parts = param.split("&")
                    for part in parts:
                        if "=" in part:
                            k, v = part.split("=", 1)
                            query_params[k] = [v]
                else:
                    query_params[key] = [value]
            
            # Rebuild query string
            new_query = urlencode(query_params, doseq=True)
            
            # Rebuild URL
            new_parsed = parsed._replace(query=new_query)
            return urlunparse(new_parsed)
            
        except Exception:
            # If URL parsing fails, try simple append
            separator = "&" if "?" in url else "?"
            return f"{url}{separator}{param}"
    
    def enforce_google_safe_search(self, url: str) -> str:
        """
        Enforce safe search for Google URLs.
        
        Args:
            url: Google search URL
            
        Returns:
            Modified URL with Google safe search enabled
        """
        if not self.enabled or not url:
            return url
        
        # Check if this is actually a Google URL
        if self._detect_search_engine(url) != "google":
            return url
        
        # Determine the appropriate safe search parameter
        if self._is_image_search(url):
            param = self._search_engines["google"]["image_param"]
        elif self._is_video_search(url):
            param = self._search_engines["google"]["video_param"]
        else:
            param = self._search_engines["google"]["safe_param"]
        
        return self._add_safe_search_param(url, param)
    
    def enforce_youtube_safe_search(self, url: str) -> str:
        """
        Enforce safe search for YouTube URLs.
        
        Args:
            url: YouTube search URL
            
        Returns:
            Modified URL with YouTube safe search enabled
        """
        if not self.enabled or not url:
            return url
        
        # Check if this is actually a YouTube URL
        if self._detect_search_engine(url) != "youtube":
            return url
        
        param = self._search_engines["youtube"]["safe_param"]
        return self._add_safe_search_param(url, param)
    
    def enforce_image_safe_search(self, url: str) -> str:
        """
        Enforce safe search for image search URLs.
        
        Args:
            url: Image search URL
            
        Returns:
            Modified URL with image safe search enabled
        """
        if not self.enabled or not url:
            return url
        
        # Detect search engine
        engine = self._detect_search_engine(url)
        if not engine:
            return url
        
        # Get appropriate image safe search parameter
        engine_config = self._search_engines.get(engine, {})
        param = engine_config.get("image_param") or engine_config.get("safe_param")
        
        if param:
            return self._add_safe_search_param(url, param)
        
        return url
    
    def enforce_safe_search(self, url: str) -> str:
        """
        Enforce safe search for any supported search engine URL.
        
        This is the main method that automatically detects the search engine
        and applies the appropriate safe search parameters.
        
        Args:
            url: Search URL to modify
            
        Returns:
            Modified URL with safe search enabled, or original URL if not supported
        """
        if not self.enabled or not url:
            return url
        
        # Detect search engine
        engine = self._detect_search_engine(url)
        if not engine:
            return url
        
        # Apply engine-specific safe search
        if engine == "google":
            return self.enforce_google_safe_search(url)
        elif engine == "youtube":
            return self.enforce_youtube_safe_search(url)
        elif engine == "bing":
            param = self._search_engines["bing"]["safe_param"]
            return self._add_safe_search_param(url, param)
        elif engine == "duckduckgo":
            param = self._search_engines["duckduckgo"]["safe_param"]
            return self._add_safe_search_param(url, param)
        elif engine == "yahoo":
            param = self._search_engines["yahoo"]["safe_param"]
            return self._add_safe_search_param(url, param)
        
        return url
    
    def is_safe_search_enabled(self, url: str) -> bool:
        """
        Check if safe search is already enabled in a URL.
        
        Args:
            url: URL to check
            
        Returns:
            True if safe search parameters are present, False otherwise
        """
        if not url:
            return False
        
        # Detect search engine
        engine = self._detect_search_engine(url)
        if not engine:
            return False
        
        # Check for safe search parameters
        engine_config = self._search_engines.get(engine, {})
        safe_params = [
            engine_config.get("safe_param", ""),
            engine_config.get("image_param", ""),
            engine_config.get("video_param", ""),
            engine_config.get("search_param", "")
        ]
        
        url_lower = url.lower()
        for param in safe_params:
            if param and param.lower() in url_lower:
                return True
        
        return False
    
    def get_supported_engines(self) -> List[str]:
        """
        Get list of supported search engines.
        
        Returns:
            List of supported search engine names
        """
        return list(self._search_engines.keys())
    
    def add_search_engine(self, name: str, domains: List[str], safe_param: str, 
                         image_param: Optional[str] = None, video_param: Optional[str] = None) -> bool:
        """
        Add support for a custom search engine.
        
        Args:
            name: Name of the search engine
            domains: List of domains for this search engine
            safe_param: Safe search parameter for general searches
            image_param: Safe search parameter for image searches (optional)
            video_param: Safe search parameter for video searches (optional)
            
        Returns:
            True if successfully added, False otherwise
        """
        if not name or not domains or not safe_param:
            return False
        
        self._search_engines[name.lower()] = {
            "domains": domains,
            "safe_param": safe_param,
            "image_param": image_param or safe_param,
            "video_param": video_param or safe_param
        }
        
        return True
    
    def remove_search_engine(self, name: str) -> bool:
        """
        Remove support for a search engine.
        
        Args:
            name: Name of the search engine to remove
            
        Returns:
            True if successfully removed, False otherwise
        """
        if name.lower() in self._search_engines:
            del self._search_engines[name.lower()]
            return True
        return False
    
    def set_enabled(self, enabled: bool):
        """
        Enable or disable safe search enforcement.
        
        Args:
            enabled: Whether to enable safe search enforcement
        """
        self.enabled = enabled
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get safe search enforcer statistics.
        
        Returns:
            Dictionary containing statistics
        """
        return {
            "enabled": self.enabled,
            "supported_engines": len(self._search_engines),
            "engines": list(self._search_engines.keys()),
            "total_domains": sum(len(config["domains"]) for config in self._search_engines.values())
        }


@dataclass
class LogEntry:
    """Represents a single log entry for content filtering"""
    timestamp: datetime.datetime
    domain: str
    url: str
    action: str  # 'blocked' or 'allowed'
    category: str
    reason: str
    user_id: Optional[str] = None
    request_type: Optional[str] = None
    keywords_detected: Optional[List[str]] = None
    severity: Optional[int] = None


class FilterLogger:
    """
    Manages logging and monitoring for content filtering operations.
    
    This class handles logging of blocked attempts, statistics tracking by category,
    and provides functionality for log export and analysis.
    """
    
    def __init__(self, db_path: Optional[str] = None, config: Optional[FilterConfig] = None):
        """
        Initialize the filter logger.
        
        Args:
            db_path: Path to SQLite database file, or None for default path
            config: FilterConfig object for logging settings
        """
        self.db_path = db_path or self._get_default_db_path()
        self.config = config or FilterConfig()
        self._stats_cache: Dict[str, Any] = {}
        self._cache_dirty = True
        
        # Initialize database
        self._init_database()
    
    def _get_default_db_path(self) -> str:
        """Get the default database path"""
        current_dir = os.path.dirname(os.path.abspath(__file__))
        data_dir = os.path.join(current_dir, '..', 'data')
        return os.path.join(data_dir, 'content_filter.db')
    
    def _init_database(self):
        """Initialize the SQLite database with logging tables"""
        try:
            # Ensure data directory exists
            data_dir = os.path.dirname(self.db_path)
            os.makedirs(data_dir, exist_ok=True)
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Create enhanced filter logs table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS filter_logs (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        domain TEXT NOT NULL,
                        url TEXT,
                        action TEXT NOT NULL,
                        category TEXT,
                        reason TEXT,
                        user_id TEXT,
                        request_type TEXT,
                        keywords_detected TEXT,
                        severity INTEGER,
                        session_id TEXT,
                        ip_address TEXT,
                        user_agent TEXT
                    )
                ''')
                
                # Create statistics summary table for faster queries
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS filter_statistics (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        date DATE NOT NULL,
                        category TEXT NOT NULL,
                        action TEXT NOT NULL,
                        count INTEGER DEFAULT 0,
                        UNIQUE(date, category, action)
                    )
                ''')
                
                # Create false positive reports table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS false_positive_reports (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        domain TEXT NOT NULL,
                        url TEXT,
                        category TEXT,
                        reason TEXT,
                        user_feedback TEXT,
                        status TEXT DEFAULT 'pending',
                        resolved_by TEXT,
                        resolved_at TIMESTAMP
                    )
                ''')
                
                # Create indexes for better performance
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_filter_logs_timestamp ON filter_logs(timestamp)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_filter_logs_domain ON filter_logs(domain)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_filter_logs_action ON filter_logs(action)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_filter_logs_category ON filter_logs(category)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_filter_statistics_date ON filter_statistics(date)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_false_positive_status ON false_positive_reports(status)')
                
                conn.commit()
                
        except sqlite3.Error as e:
            print(f"Filter logger database initialization error: {e}")
    
    def log_blocked_attempt(self, domain: str, url: str, category: ContentCategory, 
                           reason: str, user_id: Optional[str] = None, 
                           request_type: Optional[RequestType] = None,
                           keywords_detected: Optional[List[str]] = None,
                           severity: Optional[int] = None,
                           session_id: Optional[str] = None,
                           ip_address: Optional[str] = None,
                           user_agent: Optional[str] = None) -> bool:
        """
        Log a blocked content attempt.
        
        Args:
            domain: Domain that was blocked
            url: Full URL that was blocked
            category: Content category that triggered the block
            reason: Reason for blocking
            user_id: Optional user identifier
            request_type: Type of request (search, website, etc.)
            keywords_detected: List of inappropriate keywords detected
            severity: Severity level of the blocked content
            session_id: Optional session identifier
            ip_address: Optional IP address
            user_agent: Optional user agent string
            
        Returns:
            True if logged successfully, False otherwise
        """
        if not self.config.log_blocked_attempts:
            return True  # Logging disabled, but return success
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Convert enums to strings
                category_str = category.value if category else "unknown"
                request_type_str = request_type.value if request_type else None
                keywords_str = json.dumps(keywords_detected) if keywords_detected else None
                
                cursor.execute('''
                    INSERT INTO filter_logs 
                    (timestamp, domain, url, action, category, reason, user_id, 
                     request_type, keywords_detected, severity, session_id, ip_address, user_agent)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    datetime.datetime.now(),
                    domain,
                    url,
                    'blocked',
                    category_str,
                    reason,
                    user_id,
                    request_type_str,
                    keywords_str,
                    severity,
                    session_id,
                    ip_address,
                    user_agent
                ))
                
                # Update statistics
                self._update_statistics(cursor, category_str, 'blocked')
                
                conn.commit()
                self._cache_dirty = True
                return True
                
        except sqlite3.Error as e:
            print(f"Error logging blocked attempt: {e}")
            return False
    
    def log_allowed_request(self, domain: str, url: str, 
                           user_id: Optional[str] = None,
                           request_type: Optional[RequestType] = None,
                           session_id: Optional[str] = None,
                           ip_address: Optional[str] = None,
                           user_agent: Optional[str] = None) -> bool:
        """
        Log an allowed content request.
        
        Args:
            domain: Domain that was allowed
            url: Full URL that was allowed
            user_id: Optional user identifier
            request_type: Type of request (search, website, etc.)
            session_id: Optional session identifier
            ip_address: Optional IP address
            user_agent: Optional user agent string
            
        Returns:
            True if logged successfully, False otherwise
        """
        if not self.config.log_allowed_requests:
            return True  # Logging disabled, but return success
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                request_type_str = request_type.value if request_type else None
                
                cursor.execute('''
                    INSERT INTO filter_logs 
                    (timestamp, domain, url, action, category, reason, user_id, 
                     request_type, session_id, ip_address, user_agent)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    datetime.datetime.now(),
                    domain,
                    url,
                    'allowed',
                    'allowed',
                    'Content filtering passed',
                    user_id,
                    request_type_str,
                    session_id,
                    ip_address,
                    user_agent
                ))
                
                # Update statistics
                self._update_statistics(cursor, 'allowed', 'allowed')
                
                conn.commit()
                self._cache_dirty = True
                return True
                
        except sqlite3.Error as e:
            print(f"Error logging allowed request: {e}")
            return False
    
    def _update_statistics(self, cursor, category: str, action: str):
        """Update daily statistics for the given category and action"""
        today = datetime.date.today()
        
        cursor.execute('''
            INSERT OR REPLACE INTO filter_statistics (date, category, action, count)
            VALUES (?, ?, ?, COALESCE((
                SELECT count FROM filter_statistics 
                WHERE date = ? AND category = ? AND action = ?
            ), 0) + 1)
        ''', (today, category, action, today, category, action))
    
    def get_statistics(self, days: int = 30) -> Dict[str, Any]:
        """
        Get filtering statistics for the specified number of days.
        
        Args:
            days: Number of days to include in statistics (default: 30)
            
        Returns:
            Dictionary containing comprehensive statistics
        """
        if not self.config.enable_statistics:
            return {"statistics_disabled": True}
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Calculate date range
                end_date = datetime.date.today()
                start_date = end_date - datetime.timedelta(days=days)
                
                stats = {
                    "period": {
                        "start_date": start_date.isoformat(),
                        "end_date": end_date.isoformat(),
                        "days": days
                    },
                    "totals": {},
                    "by_category": {},
                    "by_date": {},
                    "top_blocked_domains": [],
                    "recent_activity": []
                }
                
                # Get total counts
                cursor.execute('''
                    SELECT action, SUM(count) 
                    FROM filter_statistics 
                    WHERE date >= ? AND date <= ?
                    GROUP BY action
                ''', (start_date, end_date))
                
                for action, count in cursor.fetchall():
                    stats["totals"][action] = count
                
                # Get counts by category
                cursor.execute('''
                    SELECT category, action, SUM(count) 
                    FROM filter_statistics 
                    WHERE date >= ? AND date <= ?
                    GROUP BY category, action
                ''', (start_date, end_date))
                
                for category, action, count in cursor.fetchall():
                    if category not in stats["by_category"]:
                        stats["by_category"][category] = {}
                    stats["by_category"][category][action] = count
                
                # Get daily breakdown
                cursor.execute('''
                    SELECT date, action, SUM(count) 
                    FROM filter_statistics 
                    WHERE date >= ? AND date <= ?
                    GROUP BY date, action
                    ORDER BY date DESC
                ''', (start_date, end_date))
                
                for date_str, action, count in cursor.fetchall():
                    if date_str not in stats["by_date"]:
                        stats["by_date"][date_str] = {}
                    stats["by_date"][date_str][action] = count
                
                # Get top blocked domains
                cursor.execute('''
                    SELECT domain, COUNT(*) as block_count
                    FROM filter_logs 
                    WHERE action = 'blocked' 
                    AND timestamp >= ? 
                    AND timestamp <= ?
                    GROUP BY domain
                    ORDER BY block_count DESC
                    LIMIT 10
                ''', (start_date, end_date))
                
                stats["top_blocked_domains"] = [
                    {"domain": domain, "count": count} 
                    for domain, count in cursor.fetchall()
                ]
                
                # Get recent activity (last 24 hours)
                yesterday = datetime.datetime.now() - datetime.timedelta(hours=24)
                cursor.execute('''
                    SELECT timestamp, domain, action, category, reason
                    FROM filter_logs 
                    WHERE timestamp >= ?
                    ORDER BY timestamp DESC
                    LIMIT 20
                ''', (yesterday,))
                
                stats["recent_activity"] = [
                    {
                        "timestamp": timestamp,
                        "domain": domain,
                        "action": action,
                        "category": category,
                        "reason": reason
                    }
                    for timestamp, domain, action, category, reason in cursor.fetchall()
                ]
                
                return stats
                
        except sqlite3.Error as e:
            print(f"Error getting statistics: {e}")
            return {"error": str(e)}
    
    def export_logs(self, output_path: str, format: str = "csv", 
                   start_date: Optional[datetime.date] = None,
                   end_date: Optional[datetime.date] = None,
                   action_filter: Optional[str] = None,
                   category_filter: Optional[str] = None) -> bool:
        """
        Export filter logs to a file.
        
        Args:
            output_path: Path to output file
            format: Export format ('csv' or 'json')
            start_date: Optional start date filter
            end_date: Optional end date filter
            action_filter: Optional action filter ('blocked' or 'allowed')
            category_filter: Optional category filter
            
        Returns:
            True if export successful, False otherwise
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Build query with filters
                query = '''
                    SELECT timestamp, domain, url, action, category, reason, 
                           user_id, request_type, keywords_detected, severity
                    FROM filter_logs 
                    WHERE 1=1
                '''
                params = []
                
                if start_date:
                    query += ' AND DATE(timestamp) >= ?'
                    params.append(start_date)
                
                if end_date:
                    query += ' AND DATE(timestamp) <= ?'
                    params.append(end_date)
                
                if action_filter:
                    query += ' AND action = ?'
                    params.append(action_filter)
                
                if category_filter:
                    query += ' AND category = ?'
                    params.append(category_filter)
                
                query += ' ORDER BY timestamp DESC'
                
                cursor.execute(query, params)
                rows = cursor.fetchall()
                
                # Export based on format
                if format.lower() == 'csv':
                    return self._export_csv(output_path, rows)
                elif format.lower() == 'json':
                    return self._export_json(output_path, rows)
                else:
                    print(f"Unsupported export format: {format}")
                    return False
                    
        except sqlite3.Error as e:
            print(f"Error exporting logs: {e}")
            return False
    
    def _export_csv(self, output_path: str, rows: List[Tuple]) -> bool:
        """Export logs to CSV format"""
        try:
            with open(output_path, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.writer(csvfile)
                
                # Write header
                writer.writerow([
                    'Timestamp', 'Domain', 'URL', 'Action', 'Category', 'Reason',
                    'User ID', 'Request Type', 'Keywords Detected', 'Severity'
                ])
                
                # Write data rows
                for row in rows:
                    writer.writerow(row)
                
            return True
            
        except Exception as e:
            print(f"Error writing CSV file: {e}")
            return False
    
    def _export_json(self, output_path: str, rows: List[Tuple]) -> bool:
        """Export logs to JSON format"""
        try:
            logs = []
            for row in rows:
                log_entry = {
                    'timestamp': row[0],
                    'domain': row[1],
                    'url': row[2],
                    'action': row[3],
                    'category': row[4],
                    'reason': row[5],
                    'user_id': row[6],
                    'request_type': row[7],
                    'keywords_detected': json.loads(row[8]) if row[8] else None,
                    'severity': row[9]
                }
                logs.append(log_entry)
            
            with open(output_path, 'w', encoding='utf-8') as jsonfile:
                json.dump({
                    'export_timestamp': datetime.datetime.now().isoformat(),
                    'total_entries': len(logs),
                    'logs': logs
                }, jsonfile, indent=2, default=str)
            
            return True
            
        except Exception as e:
            print(f"Error writing JSON file: {e}")
            return False
    
    def report_false_positive(self, domain: str, url: str, category: str, 
                             reason: str, user_feedback: str) -> bool:
        """
        Report a false positive blocking.
        
        Args:
            domain: Domain that was incorrectly blocked
            url: Full URL that was incorrectly blocked
            category: Category that triggered the false positive
            reason: Original reason for blocking
            user_feedback: User explanation of why this is a false positive
            
        Returns:
            True if report submitted successfully, False otherwise
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    INSERT INTO false_positive_reports 
                    (timestamp, domain, url, category, reason, user_feedback, status)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (
                    datetime.datetime.now(),
                    domain,
                    url,
                    category,
                    reason,
                    user_feedback,
                    'pending'
                ))
                
                conn.commit()
                return True
                
        except sqlite3.Error as e:
            print(f"Error reporting false positive: {e}")
            return False
    
    def get_false_positive_reports(self, status: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get false positive reports.
        
        Args:
            status: Optional status filter ('pending', 'resolved', 'rejected')
            
        Returns:
            List of false positive reports
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                if status:
                    cursor.execute('''
                        SELECT id, timestamp, domain, url, category, reason, 
                               user_feedback, status, resolved_by, resolved_at
                        FROM false_positive_reports 
                        WHERE status = ?
                        ORDER BY timestamp DESC
                    ''', (status,))
                else:
                    cursor.execute('''
                        SELECT id, timestamp, domain, url, category, reason, 
                               user_feedback, status, resolved_by, resolved_at
                        FROM false_positive_reports 
                        ORDER BY timestamp DESC
                    ''')
                
                reports = []
                for row in cursor.fetchall():
                    reports.append({
                        'id': row[0],
                        'timestamp': row[1],
                        'domain': row[2],
                        'url': row[3],
                        'category': row[4],
                        'reason': row[5],
                        'user_feedback': row[6],
                        'status': row[7],
                        'resolved_by': row[8],
                        'resolved_at': row[9]
                    })
                
                return reports
                
        except sqlite3.Error as e:
            print(f"Error getting false positive reports: {e}")
            return []
    
    def resolve_false_positive(self, report_id: int, status: str, 
                              resolved_by: str, resolution_notes: Optional[str] = None) -> bool:
        """
        Resolve a false positive report.
        
        Args:
            report_id: ID of the report to resolve
            status: New status ('resolved' or 'rejected')
            resolved_by: Identifier of who resolved the report
            resolution_notes: Optional notes about the resolution
            
        Returns:
            True if resolved successfully, False otherwise
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    UPDATE false_positive_reports 
                    SET status = ?, resolved_by = ?, resolved_at = ?
                    WHERE id = ?
                ''', (status, resolved_by, datetime.datetime.now(), report_id))
                
                conn.commit()
                return cursor.rowcount > 0
                
        except sqlite3.Error as e:
            print(f"Error resolving false positive: {e}")
            return False
    
    def clear_old_logs(self, days_to_keep: int = 90) -> int:
        """
        Clear old log entries to manage database size.
        
        Args:
            days_to_keep: Number of days of logs to keep (default: 90)
            
        Returns:
            Number of log entries deleted
        """
        try:
            cutoff_date = datetime.datetime.now() - datetime.timedelta(days=days_to_keep)
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Delete old filter logs
                cursor.execute('''
                    DELETE FROM filter_logs 
                    WHERE timestamp < ?
                ''', (cutoff_date,))
                
                deleted_count = cursor.rowcount
                
                # Delete old statistics (keep longer for historical analysis)
                stats_cutoff = datetime.date.today() - datetime.timedelta(days=days_to_keep * 2)
                cursor.execute('''
                    DELETE FROM filter_statistics 
                    WHERE date < ?
                ''', (stats_cutoff,))
                
                conn.commit()
                self._cache_dirty = True
                
                return deleted_count
                
        except sqlite3.Error as e:
            print(f"Error clearing old logs: {e}")
            return 0
    
    def get_log_summary(self) -> Dict[str, Any]:
        """
        Get a summary of the logging system status.
        
        Returns:
            Dictionary containing logging system information
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Get total log counts
                cursor.execute('SELECT COUNT(*) FROM filter_logs')
                total_logs = cursor.fetchone()[0]
                
                cursor.execute('SELECT COUNT(*) FROM filter_logs WHERE action = "blocked"')
                blocked_count = cursor.fetchone()[0]
                
                cursor.execute('SELECT COUNT(*) FROM filter_logs WHERE action = "allowed"')
                allowed_count = cursor.fetchone()[0]
                
                # Get date range
                cursor.execute('SELECT MIN(timestamp), MAX(timestamp) FROM filter_logs')
                date_range = cursor.fetchone()
                
                # Get pending false positive reports
                cursor.execute('SELECT COUNT(*) FROM false_positive_reports WHERE status = "pending"')
                pending_reports = cursor.fetchone()[0]
                
                return {
                    "database_path": self.db_path,
                    "total_logs": total_logs,
                    "blocked_count": blocked_count,
                    "allowed_count": allowed_count,
                    "earliest_log": date_range[0],
                    "latest_log": date_range[1],
                    "pending_false_positive_reports": pending_reports,
                    "logging_config": {
                        "log_blocked_attempts": self.config.log_blocked_attempts,
                        "log_allowed_requests": self.config.log_allowed_requests,
                        "enable_statistics": self.config.enable_statistics
                    }
                }
                
        except sqlite3.Error as e:
            return {
                "error": str(e),
                "database_path": self.db_path
            }


class UserFeedbackSystem:
    """
    Manages user feedback and messaging for content filtering operations.
    
    This class provides appropriate user messaging for blocked content and
    supports false positive reporting as required by the content filtering system.
    """
    
    def __init__(self, logger: Optional[FilterLogger] = None, config: Optional[FilterConfig] = None):
        """
        Initialize the user feedback system.
        
        Args:
            logger: FilterLogger instance for logging feedback
            config: FilterConfig for feedback settings
        """
        self.logger = logger or FilterLogger()
        self.config = config or FilterConfig()
        
        # Message templates for different content categories
        self._message_templates = self._get_message_templates()
        
        # Alternative suggestions database
        self._alternatives_db = self._get_alternatives_database()
    
    def _get_message_templates(self) -> Dict[str, Dict[str, str]]:
        """Get message templates for different content categories and age profiles"""
        return {
            ContentCategory.ADULT.value:{
                AgeProfile.CHILD.value: "This website isn't appropriate for children. Let's find something fun and educational instead!",
 
    """
    Create a ContentFilter instance with optional configuration file.
    
    Args:
        config_path: Optional path to configuration file
        config_manager: Optional ConfigurationManager instance
        
    Returns:
        Configured ContentFilter instance
    """
    # Create configuration manager if not provided
    if config_manager is None:
        config_manager = ConfigurationManager()
    
    # Load configuration
    config = None
    if config_path:
        config = config_manager.load_config(config_path)
    else:
        config = config_manager.load_config()  # Use default path
    
    # Create filter with loaded configuration
    return ContentFilter(config=config, config_manager=config_manager)


class UserFeedbackSystem:
    """
    Manages user feedback and messaging for content filtering operations.
    
    This class provides appropriate user messaging for blocked content and
    supports false positive reporting functionality.
    """
    
    def __init__(self, logger: Optional[FilterLogger] = None, config: Optional[FilterConfig] = None):
        """
        Initialize the user feedback system.
        
        Args:
            logger: FilterLogger instance for logging feedback
            config: FilterConfig for messaging settings
        """
        self.logger = logger
        self.config = config or FilterConfig()
        self._message_templates = self._initialize_message_templates()
        self._alternative_suggestions = self._initialize_alternative_suggestions()
    
    def _initialize_message_templates(self) -> Dict[str, Dict[str, str]]:
        """
        Initialize message templates for different content categories and age profiles.
        
        Returns:
            Dictionary of message templates organized by category and age profile
        """
        return {
            ContentCategory.ADULT.value: {
                AgeProfile.CHILD.value: "This website isn't suitable for children. Let's find something fun and educational instead!",
                AgeProfile.TEEN.value: "This content is restricted. Try searching for something else.",
                AgeProfile.ADULT.value: "This content has been blocked by your current filter settings."
            },
            ContentCategory.VIOLENCE.value: {
                AgeProfile.CHILD.value: "This content might be scary. Let's look for something more appropriate.",
                AgeProfile.TEEN.value: "This content contains violence and has been blocked.",
                AgeProfile.ADULT.value: "This content contains violent material and has been blocked by your filter settings."
            },
            ContentCategory.GAMBLING.value: {
                AgeProfile.CHILD.value: "This isn't a good website for kids. Let's find something better!",
                AgeProfile.TEEN.value: "Gambling sites are not appropriate for your age group.",
                AgeProfile.ADULT.value: "This gambling site has been blocked by your current filter settings."
            },
            ContentCategory.DRUGS.value: {
                AgeProfile.CHILD.value: "This website isn't safe for children. Let's find something educational instead.",
                AgeProfile.TEEN.value: "This content about illegal substances has been blocked.",
                AgeProfile.ADULT.value: "This drug-related content has been blocked by your filter settings."
            },
            ContentCategory.HATE_SPEECH.value: {
                AgeProfile.CHILD.value: "This content isn't kind or appropriate. Let's find something positive!",
                AgeProfile.TEEN.value: "This content promotes hate speech and has been blocked.",
                AgeProfile.ADULT.value: "This hate speech content has been blocked by your filter settings."
            },
            ContentCategory.MALWARE.value: {
                AgeProfile.CHILD.value: "This website isn't safe! Let's go somewhere else.",
                AgeProfile.TEEN.value: "This website may be dangerous and has been blocked for your safety.",
                AgeProfile.ADULT.value: "This website has been identified as potentially malicious and blocked for your security."
            },
            ContentCategory.PHISHING.value: {
                AgeProfile.CHILD.value: "This website isn't real! Let's find a safe one instead.",
                AgeProfile.TEEN.value: "This appears to be a fake website trying to steal information. It has been blocked.",
                AgeProfile.ADULT.value: "This website appears to be a phishing attempt and has been blocked for your security."
            },
            "default": {
                AgeProfile.CHILD.value: "This website isn't appropriate right now. Let's try something else!",
                AgeProfile.TEEN.value: "This content has been blocked by the content filter.",
                AgeProfile.ADULT.value: "This content has been blocked by your current filter settings."
            }
        }
    
    def _initialize_alternative_suggestions(self) -> Dict[str, List[str]]:
        """
        Initialize alternative suggestions for different content categories.
        
        Returns:
            Dictionary of alternative suggestions organized by category
        """
        return {
            ContentCategory.ADULT.value: [
                "Try searching for educational content instead",
                "Visit a news website like BBC or CNN",
                "Check out Wikipedia for interesting articles",
                "Look for hobby or interest-related websites"
            ],
            ContentCategory.VIOLENCE.value: [
                "Try searching for peaceful or educational content",
                "Visit National Geographic for nature content",
                "Check out PBS for educational videos",
                "Look for sports or fitness websites"
            ],
            ContentCategory.GAMBLING.value: [
                "Try searching for entertainment or games that don't involve money",
                "Visit educational gaming sites",
                "Check out puzzle or brain training websites",
                "Look for hobby-related content"
            ],
            ContentCategory.DRUGS.value: [
                "Try searching for health and wellness information",
                "Visit medical information sites like WebMD",
                "Check out fitness and nutrition websites",
                "Look for educational content about healthy living"
            ],
            ContentCategory.HATE_SPEECH.value: [
                "Try searching for positive and inclusive content",
                "Visit educational websites about different cultures",
                "Check out community service or volunteer websites",
                "Look for inspirational or motivational content"
            ],
            ContentCategory.MALWARE.value: [
                "Use trusted websites like official company sites",
                "Visit well-known educational institutions",
                "Check out government websites (.gov domains)",
                "Use reputable news sources"
            ],
            ContentCategory.PHISHING.value: [
                "Always visit official websites directly",
                "Use bookmarks for important sites",
                "Check the website address carefully",
                "Visit trusted sources for the information you need"
            ],
            "search_alternatives": [
                "Try using different, more specific search terms",
                "Search for educational content on your topic",
                "Use safe search engines like KidzSearch for children",
                "Try searching for the same topic with 'educational' or 'learning' added"
            ],
            "general": [
                "Visit educational websites like Khan Academy",
                "Check out library websites for research",
                "Try government or university websites",
                "Look for content from trusted news sources"
            ]
        }
    
    def get_blocked_content_message(self, filter_result: FilterResult, 
                                   age_profile: Optional[AgeProfile] = None,
                                   include_alternatives: bool = True,
                                   include_report_option: bool = True) -> Dict[str, Any]:
        """
        Generate an appropriate user message for blocked content.
        
        Args:
            filter_result: FilterResult containing blocking information
            age_profile: User age profile for appropriate messaging
            include_alternatives: Whether to include alternative suggestions
            include_report_option: Whether to include false positive reporting option
            
        Returns:
            Dictionary containing user message and options
        """
        if not filter_result or filter_result.allowed:
            return {"error": "Content was not blocked"}
        
        # Determine age profile
        profile = age_profile or self.config.age_profile
        
        # Get appropriate message template
        category_key = filter_result.category.value if filter_result.category else "default"
        profile_key = profile.value
        
        # Get base message
        category_templates = self._message_templates.get(category_key, self._message_templates["default"])
        message = category_templates.get(profile_key, category_templates[AgeProfile.ADULT.value])
        
        # Build response
        response = {
            "message": message,
            "category": category_key,
            "reason": filter_result.reason,
            "timestamp": datetime.datetime.now().isoformat(),
            "age_appropriate": True
        }
        
        # Add alternative suggestions if requested
        if include_alternatives:
            alternatives = self._get_alternative_suggestions(filter_result, profile)
            if alternatives:
                response["alternatives"] = alternatives
        
        # Add false positive reporting option if requested
        if include_report_option and profile != AgeProfile.CHILD:
            response["report_option"] = {
                "available": True,
                "message": "Think this was blocked by mistake? You can report it as a false positive.",
                "action": "report_false_positive"
            }
        
        # Add educational content for children
        if profile == AgeProfile.CHILD:
            response["educational_note"] = "Remember, the internet has lots of great things to learn and explore safely!"
        
        return response
    
    def _get_alternative_suggestions(self, filter_result: FilterResult, 
                                   age_profile: AgeProfile) -> List[str]:
        """
        Get alternative suggestions based on the blocked content and user profile.
        
        Args:
            filter_result: FilterResult containing blocking information
            age_profile: User age profile
            
        Returns:
            List of alternative suggestions
        """
        suggestions = []
        
        # Get category-specific suggestions
        category_key = filter_result.category.value if filter_result.category else "general"
        category_suggestions = self._alternative_suggestions.get(category_key, [])
        
        # Add general suggestions
        general_suggestions = self._alternative_suggestions.get("general", [])
        
        # Combine and limit suggestions
        all_suggestions = category_suggestions + general_suggestions
        
        # Filter suggestions based on age profile
        if age_profile == AgeProfile.CHILD:
            # More specific, child-friendly suggestions
            suggestions = [s for s in all_suggestions if "educational" in s.lower() or "safe" in s.lower()][:3]
        elif age_profile == AgeProfile.TEEN:
            # Moderate suggestions
            suggestions = all_suggestions[:4]
        else:
            # All suggestions for adults
            suggestions = all_suggestions[:5]
        
        # Add any pre-existing suggestions from filter result
        if filter_result.suggested_alternatives:
            suggestions.extend(filter_result.suggested_alternatives[:2])
        
        return suggestions[:5]  # Limit to 5 suggestions maximum
    
    def get_search_blocked_message(self, query: str, detected_keywords: List[str],
                                  age_profile: Optional[AgeProfile] = None,
                                  suggest_alternatives: bool = True) -> Dict[str, Any]:
        """
        Generate an appropriate message for blocked search queries.
        
        Args:
            query: The blocked search query
            detected_keywords: List of inappropriate keywords detected
            age_profile: User age profile for appropriate messaging
            suggest_alternatives: Whether to suggest alternative search terms
            
        Returns:
            Dictionary containing user message and suggestions
        """
        profile = age_profile or self.config.age_profile
        
        # Age-appropriate messaging for search blocks
        if profile == AgeProfile.CHILD:
            message = "Let's try searching for something else! That search isn't appropriate for kids."
        elif profile == AgeProfile.TEEN:
            message = "That search contains inappropriate terms. Try searching for something different."
        else:
            message = "Your search contains terms that are blocked by the current filter settings."
        
        response = {
            "message": message,
            "blocked_query": query,
            "timestamp": datetime.datetime.now().isoformat(),
            "type": "search_blocked"
        }
        
        # Add alternative search suggestions if requested
        if suggest_alternatives:
            alternative_queries = self._generate_alternative_search_queries(query, detected_keywords, profile)
            if alternative_queries:
                response["alternative_queries"] = alternative_queries
        
        # Add search tips based on age profile
        if profile == AgeProfile.CHILD:
            response["search_tips"] = [
                "Try searching for your favorite animals or hobbies",
                "Search for educational topics you're learning about",
                "Ask a grown-up to help you find what you're looking for"
            ]
        elif profile == AgeProfile.TEEN:
            response["search_tips"] = [
                "Use more specific terms related to your topic",
                "Try adding 'educational' or 'information' to your search",
                "Consider searching for academic or news sources"
            ]
        else:
            response["search_tips"] = [
                "Try using different keywords for your topic",
                "Consider adjusting your content filter settings if needed",
                "Use more specific or professional terminology"
            ]
        
        return response
    
    def _generate_alternative_search_queries(self, original_query: str, 
                                           detected_keywords: List[str],
                                           age_profile: AgeProfile) -> List[str]:
        """
        Generate alternative search queries by removing inappropriate keywords.
        
        Args:
            original_query: The original blocked search query
            detected_keywords: List of inappropriate keywords detected
            age_profile: User age profile
            
        Returns:
            List of alternative search queries
        """
        alternatives = []
        
        # Remove detected keywords and suggest alternatives
        clean_query = original_query.lower()
        for keyword in detected_keywords:
            clean_query = clean_query.replace(keyword.lower(), "").strip()
        
        # Clean up extra spaces
        clean_query = " ".join(clean_query.split())
        
        if clean_query and len(clean_query) > 2:
            # Add educational modifiers based on age profile
            if age_profile == AgeProfile.CHILD:
                alternatives.extend([
                    f"{clean_query} for kids",
                    f"educational {clean_query}",
                    f"learning about {clean_query}"
                ])
            elif age_profile == AgeProfile.TEEN:
                alternatives.extend([
                    f"{clean_query} information",
                    f"{clean_query} facts",
                    f"educational {clean_query}"
                ])
            else:
                alternatives.extend([
                    f"{clean_query} information",
                    f"{clean_query} research",
                    f"academic {clean_query}"
                ])
        
        # Add general safe search suggestions
        safe_suggestions = self._alternative_suggestions.get("search_alternatives", [])
        alternatives.extend(safe_suggestions[:2])
        
        return alternatives[:4]  # Limit to 4 alternatives
    
    def report_false_positive(self, domain: str, url: str, category: str,
                             reason: str, user_feedback: str,
                             user_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Report a false positive blocking with user feedback.
        
        Args:
            domain: Domain that was incorrectly blocked
            url: Full URL that was incorrectly blocked
            category: Category that triggered the false positive
            reason: Original reason for blocking
            user_feedback: User explanation of why this is a false positive
            user_id: Optional user identifier
            
        Returns:
            Dictionary containing report status and information
        """
        if not self.logger:
            return {
                "success": False,
                "error": "Logging system not available",
                "message": "Unable to submit false positive report at this time."
            }
        
        # Submit the false positive report
        success = self.logger.report_false_positive(domain, url, category, reason, user_feedback)
        
        if success:
            return {
                "success": True,
                "message": "Thank you for your feedback! Your false positive report has been submitted and will be reviewed.",
                "next_steps": [
                    "Your report will be reviewed by our content filtering team",
                    "If confirmed as a false positive, the site will be added to the whitelist",
                    "You may see changes in filtering within 24-48 hours"
                ],
                "timestamp": datetime.datetime.now().isoformat()
            }
        else:
            return {
                "success": False,
                "error": "Failed to submit report",
                "message": "There was an error submitting your false positive report. Please try again later."
            }
    
    def get_false_positive_form_data(self, domain: str, url: str, 
                                   category: str, reason: str) -> Dict[str, Any]:
        """
        Get form data for false positive reporting.
        
        Args:
            domain: Domain that was blocked
            url: URL that was blocked
            category: Category that triggered the block
            reason: Reason for blocking
            
        Returns:
            Dictionary containing form data and instructions
        """
        return {
            "form_data": {
                "domain": domain,
                "url": url,
                "category": category,
                "reason": reason,
                "timestamp": datetime.datetime.now().isoformat()
            },
            "instructions": {
                "title": "Report False Positive",
                "description": "Help us improve our content filtering by reporting incorrectly blocked content.",
                "feedback_prompt": "Please explain why you believe this content was incorrectly blocked:",
                "examples": [
                    "This is an educational website about [topic]",
                    "This is a legitimate business website",
                    "This content is appropriate for my age group",
                    "This is a false positive due to keyword matching"
                ]
            },
            "privacy_note": "Your feedback will be used to improve our content filtering system. No personal information will be shared."
        }
    
    def get_user_message_for_voice_response(self, filter_result: FilterResult,
                                          age_profile: Optional[AgeProfile] = None) -> str:
        """
        Get a concise message suitable for voice response when content is blocked.
        
        Args:
            filter_result: FilterResult containing blocking information
            age_profile: User age profile for appropriate messaging
            
        Returns:
            String message suitable for text-to-speech
        """
        if not filter_result or filter_result.allowed:
            return "Content is allowed."
        
        profile = age_profile or self.config.age_profile
        category = filter_result.category.value if filter_result.category else "default"
        
        # Voice-optimized messages (shorter and more natural)
        voice_messages = {
            ContentCategory.ADULT.value: {
                AgeProfile.CHILD.value: "That website isn't for kids. Let's find something fun instead!",
                AgeProfile.TEEN.value: "That content is restricted. Try something else.",
                AgeProfile.ADULT.value: "That content is blocked by your filter settings."
            },
            ContentCategory.VIOLENCE.value: {
                AgeProfile.CHILD.value: "That might be scary. Let's look for something nicer.",
                AgeProfile.TEEN.value: "That content is too violent and has been blocked.",
                AgeProfile.ADULT.value: "That violent content is blocked by your filters."
            },
            ContentCategory.GAMBLING.value: {
                AgeProfile.CHILD.value: "That's not a good website for kids. Let's find something better!",
                AgeProfile.TEEN.value: "Gambling sites aren't appropriate for you.",
                AgeProfile.ADULT.value: "That gambling site is blocked by your settings."
            },
            "default": {
                AgeProfile.CHILD.value: "That website isn't appropriate right now. Let's try something else!",
                AgeProfile.TEEN.value: "That content has been blocked.",
                AgeProfile.ADULT.value: "That content is blocked by your current settings."
            }
        }
        
        category_messages = voice_messages.get(category, voice_messages["default"])
        return category_messages.get(profile.value, category_messages[AgeProfile.ADULT.value])
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Get user feedback system statistics.
        
        Returns:
            Dictionary containing feedback system statistics
        """
        stats = {
            "message_templates": len(self._message_templates),
            "alternative_suggestions": sum(len(suggestions) for suggestions in self._alternative_suggestions.values()),
            "supported_categories": list(self._message_templates.keys()),
            "supported_age_profiles": [profile.value for profile in AgeProfile]
        }
        
        # Add false positive report statistics if logger is available
        if self.logger:
            try:
                reports = self.logger.get_false_positive_reports()
                stats.update({
                    "total_false_positive_reports": len(reports),
                    "pending_reports": len([r for r in reports if r["status"] == "pending"]),
                    "resolved_reports": len([r for r in reports if r["status"] == "resolved"]),
                    "rejected_reports": len([r for r in reports if r["status"] == "rejected"])
                })
            except Exception as e:
                stats["false_positive_stats_error"] = str(e)
        
        return stats


# Configuration Manager for Content Filter Settings
class ConfigurationManager:
    """
    Manages loading and saving of content filter configurations.
    
    This class handles configuration persistence, validation, and provides
    methods for managing filter settings across application restarts.
    """
    
    def __init__(self, config_dir: Optional[str] = None):
        """
        Initialize the configuration manager.
        
        Args:
            config_dir: Directory to store configuration files, or None for default
        """
        self.config_dir = config_dir or self._get_default_config_dir()
        self.config_file = os.path.join(self.config_dir, "content_filter_config.json")
        
        # Ensure config directory exists
        os.makedirs(self.config_dir, exist_ok=True)
    
    def _get_default_config_dir(self) -> str:
        """Get the default configuration directory"""
        current_dir = os.path.dirname(os.path.abspath(__file__))
        return os.path.join(current_dir, '..', 'data', 'config')
    
    def save_config(self, config: FilterConfig, config_path: Optional[str] = None) -> bool:
        """
        Save configuration to a JSON file.
        
        Args:
            config: FilterConfig object to save
            config_path: Optional path to save to, or None to use default
            
        Returns:
            True if saved successfully, False otherwise
        """
        try:
            # Validate configuration before saving
            validation_errors = config.validate()
            if validation_errors:
                print(f"Configuration validation errors: {validation_errors}")
                return False
            
            file_path = config_path or self.config_file
            
            # Create backup of existing config if it exists
            if os.path.exists(file_path):
                backup_path = f"{file_path}.backup"
                try:
                    import shutil
                    shutil.copy2(file_path, backup_path)
                except Exception as e:
                    print(f"Warning: Could not create config backup: {e}")
            
            # Save configuration
            config_data = {
                "version": "1.0",
                "saved_at": datetime.datetime.now().isoformat(),
                "config": config.to_dict()
            }
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(config_data, f, indent=2, default=str)
            
            return True
            
        except Exception as e:
            print(f"Error saving configuration: {e}")
            return False
    
    def load_config(self, config_path: Optional[str] = None) -> Optional[FilterConfig]:
        """
        Load configuration from a JSON file.
        
        Args:
            config_path: Optional path to load from, or None to use default
            
        Returns:
            FilterConfig object if loaded successfully, None otherwise
        """
        try:
            file_path = config_path or self.config_file
            
            if not os.path.exists(file_path):
                print(f"Configuration file not found: {file_path}")
                return None
            
            with open(file_path, 'r', encoding='utf-8') as f:
                config_data = json.load(f)
            
            # Extract config section
            if "config" in config_data:
                config_dict = config_data["config"]
            else:
                # Assume the entire file is the config (backward compatibility)
                config_dict = config_data
            
            # Create FilterConfig from dictionary
            config = FilterConfig.from_dict(config_dict)
            
            # Validate loaded configuration
            validation_errors = config.validate()
            if validation_errors:
                print(f"Loaded configuration has validation errors: {validation_errors}")
                # Return the config anyway, but warn the user
            
            return config
            
        except Exception as e:
            print(f"Error loading configuration: {e}")
            return None
    
    def get_default_config(self) -> FilterConfig:
        """
        Get a default configuration.
        
        Returns:
            FilterConfig with default settings
        """
        return FilterConfig()
    
    def reset_to_defaults(self, config_path: Optional[str] = None) -> bool:
        """
        Reset configuration to defaults.
        
        Args:
            config_path: Optional path to reset, or None to use default
            
        Returns:
            True if reset successfully, False otherwise
        """
        default_config = self.get_default_config()
        return self.save_config(default_config, config_path)
    
    def backup_config(self, backup_path: Optional[str] = None) -> bool:
        """
        Create a backup of the current configuration.
        
        Args:
            backup_path: Optional path for backup, or None for default naming
            
        Returns:
            True if backup created successfully, False otherwise
        """
        try:
            if not os.path.exists(self.config_file):
                print("No configuration file to backup")
                return False
            
            if backup_path is None:
                timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                backup_path = f"{self.config_file}.backup_{timestamp}"
            
            import shutil
            shutil.copy2(self.config_file, backup_path)
            print(f"Configuration backed up to: {backup_path}")
            return True
            
        except Exception as e:
            print(f"Error creating configuration backup: {e}")
            return False
    
    def list_backups(self) -> List[str]:
        """
        List available configuration backups.
        
        Returns:
            List of backup file paths
        """
        try:
            config_dir = os.path.dirname(self.config_file)
            config_name = os.path.basename(self.config_file)
            
            backups = []
            for filename in os.listdir(config_dir):
                if filename.startswith(f"{config_name}.backup"):
                    backups.append(os.path.join(config_dir, filename))
            
            return sorted(backups, reverse=True)  # Most recent first
            
        except Exception as e:
            print(f"Error listing backups: {e}")
            return []
    
    def restore_from_backup(self, backup_path: str) -> bool:
        """
        Restore configuration from a backup.
        
        Args:
            backup_path: Path to backup file to restore from
            
        Returns:
            True if restored successfully, False otherwise
        """
        try:
            if not os.path.exists(backup_path):
                print(f"Backup file not found: {backup_path}")
                return False
            
            # Load and validate the backup
            config = self.load_config(backup_path)
            if config is None:
                print("Failed to load configuration from backup")
                return False
            
            # Save as current configuration
            return self.save_config(config)
            
        except Exception as e:
            print(f"Error restoring from backup: {e}")
            return False


class UserFeedbackSystem:
    """
    Manages user feedback and messaging for content filtering operations.
    
    This class provides appropriate user messaging for blocked content and
    supports false positive reporting functionality.
    """
    
    def __init__(self, logger: Optional[FilterLogger] = None, config: Optional[FilterConfig] = None):
        """
        Initialize the user feedback system.
        
        Args:
            logger: FilterLogger instance for logging feedback
            config: FilterConfig for messaging settings
        """
        self.logger = logger
        self.config = config or FilterConfig()
        self._message_templates = self._initialize_message_templates()
        self._alternative_suggestions = self._initialize_alternative_suggestions()
    
    def _initialize_message_templates(self) -> Dict[str, Dict[str, str]]:
        """
        Initialize message templates for different content categories and age profiles.
        
        Returns:
            Dictionary of message templates organized by category and age profile
        """
        return {
            ContentCategory.ADULT.value: {
                AgeProfile.CHILD.value: "This website isn't suitable for children. Let's find something fun and educational instead!",
                AgeProfile.TEEN.value: "This content is restricted. Try searching for something else.",
                AgeProfile.ADULT.value: "This content has been blocked by your current filter settings."
            },
            ContentCategory.VIOLENCE.value: {
                AgeProfile.CHILD.value: "This content might be scary. Let's look for something more appropriate.",
                AgeProfile.TEEN.value: "This content contains violence and has been blocked.",
                AgeProfile.ADULT.value: "This content contains violent material and has been blocked by your filter settings."
            },
            ContentCategory.GAMBLING.value: {
                AgeProfile.CHILD.value: "This isn't a good website for kids. Let's find something better!",
                AgeProfile.TEEN.value: "Gambling sites are not appropriate for your age group.",
                AgeProfile.ADULT.value: "This gambling site has been blocked by your current filter settings."
            },
            ContentCategory.DRUGS.value: {
                AgeProfile.CHILD.value: "This website isn't safe for children. Let's find something educational instead.",
                AgeProfile.TEEN.value: "This content about illegal substances has been blocked.",
                AgeProfile.ADULT.value: "This drug-related content has been blocked by your filter settings."
            },
            ContentCategory.HATE_SPEECH.value: {
                AgeProfile.CHILD.value: "This content isn't kind or appropriate. Let's find something positive!",
                AgeProfile.TEEN.value: "This content promotes hate speech and has been blocked.",
                AgeProfile.ADULT.value: "This hate speech content has been blocked by your filter settings."
            },
            ContentCategory.MALWARE.value: {
                AgeProfile.CHILD.value: "This website isn't safe! Let's go somewhere else.",
                AgeProfile.TEEN.value: "This website may be dangerous and has been blocked for your safety.",
                AgeProfile.ADULT.value: "This website has been identified as potentially malicious and blocked for your security."
            },
            ContentCategory.PHISHING.value: {
                AgeProfile.CHILD.value: "This website isn't real! Let's find a safe one instead.",
                AgeProfile.TEEN.value: "This appears to be a fake website trying to steal information. It has been blocked.",
                AgeProfile.ADULT.value: "This website appears to be a phishing attempt and has been blocked for your security."
            },
            "default": {
                AgeProfile.CHILD.value: "This website isn't appropriate right now. Let's try something else!",
                AgeProfile.TEEN.value: "This content has been blocked by the content filter.",
                AgeProfile.ADULT.value: "This content has been blocked by your current filter settings."
            }
        }
    
    def _initialize_alternative_suggestions(self) -> Dict[str, List[str]]:
        """
        Initialize alternative suggestions for different content categories.
        
        Returns:
            Dictionary of alternative suggestions organized by category
        """
        return {
            ContentCategory.ADULT.value: [
                "Try searching for educational content instead",
                "Visit a news website like BBC or CNN",
                "Check out Wikipedia for interesting articles",
                "Look for hobby or interest-related websites"
            ],
            ContentCategory.VIOLENCE.value: [
                "Try searching for peaceful or educational content",
                "Visit National Geographic for nature content",
                "Check out PBS for educational videos",
                "Look for sports or fitness websites"
            ],
            ContentCategory.GAMBLING.value: [
                "Try searching for entertainment or games that don't involve money",
                "Visit educational gaming sites",
                "Check out puzzle or brain training websites",
                "Look for hobby-related content"
            ],
            ContentCategory.DRUGS.value: [
                "Try searching for health and wellness information",
                "Visit medical information sites like WebMD",
                "Check out fitness and nutrition websites",
                "Look for educational content about healthy living"
            ],
            ContentCategory.HATE_SPEECH.value: [
                "Try searching for positive and inclusive content",
                "Visit educational websites about different cultures",
                "Check out community service or volunteer websites",
                "Look for inspirational or motivational content"
            ],
            ContentCategory.MALWARE.value: [
                "Use trusted websites like official company sites",
                "Visit well-known educational institutions",
                "Check out government websites (.gov domains)",
                "Use reputable news sources"
            ],
            ContentCategory.PHISHING.value: [
                "Always visit official websites directly",
                "Use bookmarks for important sites",
                "Check the website address carefully",
                "Visit trusted sources for the information you need"
            ],
            "search_alternatives": [
                "Try using different, more specific search terms",
                "Search for educational content on your topic",
                "Use safe search engines like KidzSearch for children",
                "Try searching for the same topic with 'educational' or 'learning' added"
            ],
            "general": [
                "Visit educational websites like Khan Academy",
                "Check out library websites for research",
                "Try government or university websites",
                "Look for content from trusted news sources"
            ]
        }
    
    def get_blocked_content_message(self, filter_result: FilterResult, 
                                   age_profile: Optional[AgeProfile] = None,
                                   include_alternatives: bool = True,
                                   include_report_option: bool = True) -> Dict[str, Any]:
        """
        Generate an appropriate user message for blocked content.
        
        Args:
            filter_result: FilterResult containing blocking information
            age_profile: User age profile for appropriate messaging
            include_alternatives: Whether to include alternative suggestions
            include_report_option: Whether to include false positive reporting option
            
        Returns:
            Dictionary containing user message and options
        """
        if not filter_result or filter_result.allowed:
            return {"error": "Content was not blocked"}
        
        # Determine age profile
        profile = age_profile or self.config.age_profile
        
        # Get appropriate message template
        category_key = filter_result.category.value if filter_result.category else "default"
        profile_key = profile.value
        
        # Get base message
        category_templates = self._message_templates.get(category_key, self._message_templates["default"])
        message = category_templates.get(profile_key, category_templates[AgeProfile.ADULT.value])
        
        # Build response
        response = {
            "message": message,
            "category": category_key,
            "reason": filter_result.reason,
            "timestamp": datetime.datetime.now().isoformat(),
            "age_appropriate": True
        }
        
        # Add alternative suggestions if requested
        if include_alternatives:
            alternatives = self._get_alternative_suggestions(filter_result, profile)
            if alternatives:
                response["alternatives"] = alternatives
        
        # Add false positive reporting option if requested
        if include_report_option and profile != AgeProfile.CHILD:
            response["report_option"] = {
                "available": True,
                "message": "Think this was blocked by mistake? You can report it as a false positive.",
                "action": "report_false_positive"
            }
        
        # Add educational content for children
        if profile == AgeProfile.CHILD:
            response["educational_note"] = "Remember, the internet has lots of great things to learn and explore safely!"
        
        return response
    
    def _get_alternative_suggestions(self, filter_result: FilterResult, 
                                   age_profile: AgeProfile) -> List[str]:
        """
        Get alternative suggestions based on the blocked content and user profile.
        
        Args:
            filter_result: FilterResult containing blocking information
            age_profile: User age profile
            
        Returns:
            List of alternative suggestions
        """
        suggestions = []
        
        # Get category-specific suggestions
        category_key = filter_result.category.value if filter_result.category else "general"
        category_suggestions = self._alternative_suggestions.get(category_key, [])
        
        # Add general suggestions
        general_suggestions = self._alternative_suggestions.get("general", [])
        
        # Combine and limit suggestions
        all_suggestions = category_suggestions + general_suggestions
        
        # Filter suggestions based on age profile
        if age_profile == AgeProfile.CHILD:
            # More specific, child-friendly suggestions
            suggestions = [s for s in all_suggestions if "educational" in s.lower() or "safe" in s.lower()][:3]
        elif age_profile == AgeProfile.TEEN:
            # Moderate suggestions
            suggestions = all_suggestions[:4]
        else:
            # All suggestions for adults
            suggestions = all_suggestions[:5]
        
        # Add any pre-existing suggestions from filter result
        if filter_result.suggested_alternatives:
            suggestions.extend(filter_result.suggested_alternatives[:2])
        
        return suggestions[:5]  # Limit to 5 suggestions maximum
    
    def get_search_blocked_message(self, query: str, detected_keywords: List[str],
                                  age_profile: Optional[AgeProfile] = None,
                                  suggest_alternatives: bool = True) -> Dict[str, Any]:
        """
        Generate an appropriate message for blocked search queries.
        
        Args:
            query: The blocked search query
            detected_keywords: List of inappropriate keywords detected
            age_profile: User age profile for appropriate messaging
            suggest_alternatives: Whether to suggest alternative search terms
            
        Returns:
            Dictionary containing user message and suggestions
        """
        profile = age_profile or self.config.age_profile
        
        # Age-appropriate messaging for search blocks
        if profile == AgeProfile.CHILD:
            message = "Let's try searching for something else! That search isn't appropriate for kids."
        elif profile == AgeProfile.TEEN:
            message = "That search contains inappropriate terms. Try searching for something different."
        else:
            message = "Your search contains terms that are blocked by the current filter settings."
        
        response = {
            "message": message,
            "blocked_query": query,
            "timestamp": datetime.datetime.now().isoformat(),
            "type": "search_blocked"
        }
        
        # Add alternative search suggestions if requested
        if suggest_alternatives:
            alternative_queries = self._generate_alternative_search_queries(query, detected_keywords, profile)
            if alternative_queries:
                response["alternative_queries"] = alternative_queries
        
        # Add search tips based on age profile
        if profile == AgeProfile.CHILD:
            response["search_tips"] = [
                "Try searching for your favorite animals or hobbies",
                "Search for educational topics you're learning about",
                "Ask a grown-up to help you find what you're looking for"
            ]
        elif profile == AgeProfile.TEEN:
            response["search_tips"] = [
                "Use more specific terms related to your topic",
                "Try adding 'educational' or 'information' to your search",
                "Consider searching for academic or news sources"
            ]
        else:
            response["search_tips"] = [
                "Try using different keywords for your topic",
                "Consider adjusting your content filter settings if needed",
                "Use more specific or professional terminology"
            ]
        
        return response
    
    def _generate_alternative_search_queries(self, original_query: str, 
                                           detected_keywords: List[str],
                                           age_profile: AgeProfile) -> List[str]:
        """
        Generate alternative search queries by removing inappropriate keywords.
        
        Args:
            original_query: The original blocked search query
            detected_keywords: List of inappropriate keywords detected
            age_profile: User age profile
            
        Returns:
            List of alternative search queries
        """
        alternatives = []
        
        # Remove detected keywords and suggest alternatives
        clean_query = original_query.lower()
        for keyword in detected_keywords:
            clean_query = clean_query.replace(keyword.lower(), "").strip()
        
        # Clean up extra spaces
        clean_query = " ".join(clean_query.split())
        
        if clean_query and len(clean_query) > 2:
            # Add educational modifiers based on age profile
            if age_profile == AgeProfile.CHILD:
                alternatives.extend([
                    f"{clean_query} for kids",
                    f"educational {clean_query}",
                    f"learning about {clean_query}"
                ])
            elif age_profile == AgeProfile.TEEN:
                alternatives.extend([
                    f"{clean_query} information",
                    f"{clean_query} facts",
                    f"educational {clean_query}"
                ])
            else:
                alternatives.extend([
                    f"{clean_query} information",
                    f"{clean_query} research",
                    f"academic {clean_query}"
                ])
        
        # Add general safe search suggestions
        safe_suggestions = self._alternative_suggestions.get("search_alternatives", [])
        alternatives.extend(safe_suggestions[:2])
        
        return alternatives[:4]  # Limit to 4 alternatives
    
    def report_false_positive(self, domain: str, url: str, category: str,
                             reason: str, user_feedback: str,
                             user_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Report a false positive blocking with user feedback.
        
        Args:
            domain: Domain that was incorrectly blocked
            url: Full URL that was incorrectly blocked
            category: Category that triggered the false positive
            reason: Original reason for blocking
            user_feedback: User explanation of why this is a false positive
            user_id: Optional user identifier
            
        Returns:
            Dictionary containing report status and information
        """
        if not self.logger:
            return {
                "success": False,
                "error": "Logging system not available",
                "message": "Unable to submit false positive report at this time."
            }
        
        # Submit the false positive report
        success = self.logger.report_false_positive(domain, url, category, reason, user_feedback)
        
        if success:
            return {
                "success": True,
                "message": "Thank you for your feedback! Your false positive report has been submitted and will be reviewed.",
                "next_steps": [
                    "Your report will be reviewed by our content filtering team",
                    "If confirmed as a false positive, the site will be added to the whitelist",
                    "You may see changes in filtering within 24-48 hours"
                ],
                "timestamp": datetime.datetime.now().isoformat()
            }
        else:
            return {
                "success": False,
                "error": "Failed to submit report",
                "message": "There was an error submitting your false positive report. Please try again later."
            }
    
    def get_false_positive_form_data(self, domain: str, url: str, 
                                   category: str, reason: str) -> Dict[str, Any]:
        """
        Get form data for false positive reporting.
        
        Args:
            domain: Domain that was blocked
            url: URL that was blocked
            category: Category that triggered the block
            reason: Reason for blocking
            
        Returns:
            Dictionary containing form data and instructions
        """
        return {
            "form_data": {
                "domain": domain,
                "url": url,
                "category": category,
                "reason": reason,
                "timestamp": datetime.datetime.now().isoformat()
            },
            "instructions": {
                "title": "Report False Positive",
                "description": "Help us improve our content filtering by reporting incorrectly blocked content.",
                "feedback_prompt": "Please explain why you believe this content was incorrectly blocked:",
                "examples": [
                    "This is an educational website about [topic]",
                    "This is a legitimate business website",
                    "This content is appropriate for my age group",
                    "This is a false positive due to keyword matching"
                ]
            },
            "privacy_note": "Your feedback will be used to improve our content filtering system. No personal information will be shared."
        }
    
    def get_user_message_for_voice_response(self, filter_result: FilterResult,
                                          age_profile: Optional[AgeProfile] = None) -> str:
        """
        Get a concise message suitable for voice response when content is blocked.
        
        Args:
            filter_result: FilterResult containing blocking information
            age_profile: User age profile for appropriate messaging
            
        Returns:
            String message suitable for text-to-speech
        """
        if not filter_result or filter_result.allowed:
            return "Content is allowed."
        
        profile = age_profile or self.config.age_profile
        category = filter_result.category.value if filter_result.category else "default"
        
        # Voice-optimized messages (shorter and more natural)
        voice_messages = {
            ContentCategory.ADULT.value: {
                AgeProfile.CHILD.value: "That website isn't for kids. Let's find something fun instead!",
                AgeProfile.TEEN.value: "That content is restricted. Try something else.",
                AgeProfile.ADULT.value: "That content is blocked by your filter settings."
            },
            ContentCategory.VIOLENCE.value: {
                AgeProfile.CHILD.value: "That might be scary. Let's look for something nicer.",
                AgeProfile.TEEN.value: "That content is too violent and has been blocked.",
                AgeProfile.ADULT.value: "That violent content is blocked by your filters."
            },
            ContentCategory.GAMBLING.value: {
                AgeProfile.CHILD.value: "That's not a good website for kids. Let's find something better!",
                AgeProfile.TEEN.value: "Gambling sites aren't appropriate for you.",
                AgeProfile.ADULT.value: "That gambling site is blocked by your settings."
            },
            "default": {
                AgeProfile.CHILD.value: "That website isn't appropriate right now. Let's try something else!",
                AgeProfile.TEEN.value: "That content has been blocked.",
                AgeProfile.ADULT.value: "That content is blocked by your current settings."
            }
        }
        
        category_messages = voice_messages.get(category, voice_messages["default"])
        return category_messages.get(profile.value, category_messages[AgeProfile.ADULT.value])
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Get user feedback system statistics.
        
        Returns:
            Dictionary containing feedback system statistics
        """
        stats = {
            "message_templates": len(self._message_templates),
            "alternative_suggestions": sum(len(suggestions) for suggestions in self._alternative_suggestions.values()),
            "supported_categories": list(self._message_templates.keys()),
            "supported_age_profiles": [profile.value for profile in AgeProfile]
        }
        
        # Add false positive report statistics if logger is available
        if self.logger:
            try:
                reports = self.logger.get_false_positive_reports()
                stats.update({
                    "total_false_positive_reports": len(reports),
                    "pending_reports": len([r for r in reports if r["status"] == "pending"]),
                    "resolved_reports": len([r for r in reports if r["status"] == "resolved"]),
                    "rejected_reports": len([r for r in reports if r["status"] == "rejected"])
                })
            except Exception as e:
                stats["false_positive_stats_error"] = str(e)
        
        return stats


# Configuration Manager for Content Filter Settings
class ConfigurationManager:
    """
    Manages loading and saving of content filter configurations.
    
    This class handles configuration persistence, validation, and provides
    methods for managing filter settings across application restarts.
    """
    
    def __init__(self, config_dir: Optional[str] = None):
        """
        Initialize the configuration manager.
        
        Args:
            config_dir: Directory to store configuration files, or None for default
        """
        self.config_dir = config_dir or self._get_default_config_dir()
        self.config_file = os.path.join(self.config_dir, "content_filter_config.json")
        
        # Ensure config directory exists
        os.makedirs(self.config_dir, exist_ok=True)
    
    def _get_default_config_dir(self) -> str:
        """Get the default configuration directory"""
        current_dir = os.path.dirname(os.path.abspath(__file__))
        return os.path.join(current_dir, '..', 'data', 'config')
    
    def save_config(self, config: FilterConfig, config_path: Optional[str] = None) -> bool:
        """
        Save configuration to a JSON file.
        
        Args:
            config: FilterConfig object to save
            config_path: Optional path to save to, or None to use default
            
        Returns:
            True if saved successfully, False otherwise
        """
        try:
            # Validate configuration before saving
            validation_errors = config.validate()
            if validation_errors:
                print(f"Configuration validation errors: {validation_errors}")
                return False
            
            file_path = config_path or self.config_file
            
            # Create backup of existing config if it exists
            if os.path.exists(file_path):
                backup_path = f"{file_path}.backup"
                try:
                    import shutil
                    shutil.copy2(file_path, backup_path)
                except Exception as e:
                    print(f"Warning: Could not create config backup: {e}")
            
            # Save configuration
            config_data = {
                "version": "1.0",
                "saved_at": datetime.datetime.now().isoformat(),
                "config": config.to_dict()
            }
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(config_data, f, indent=2, default=str)
            
            return True
            
        except Exception as e:
            print(f"Error saving configuration: {e}")
            return False
    
    def load_config(self, config_path: Optional[str] = None) -> Optional[FilterConfig]:
        """
        Load configuration from a JSON file.
        
        Args:
            config_path: Optional path to load from, or None to use default
            
        Returns:
            FilterConfig object if loaded successfully, None otherwise
        """
        try:
            file_path = config_path or self.config_file
            
            if not os.path.exists(file_path):
                print(f"Configuration file not found: {file_path}")
                return None
            
            with open(file_path, 'r', encoding='utf-8') as f:
                config_data = json.load(f)
            
            # Extract config section
            if "config" in config_data:
                config_dict = config_data["config"]
            else:
                # Assume the entire file is the config (backward compatibility)
                config_dict = config_data
            
            # Create FilterConfig from dictionary
            config = FilterConfig.from_dict(config_dict)
            
            # Validate loaded configuration
            validation_errors = config.validate()
            if validation_errors:
                print(f"Loaded configuration has validation errors: {validation_errors}")
                # Return the config anyway, but warn the user
            
            return config
            
        except Exception as e:
            print(f"Error loading configuration: {e}")
            return None
    
    def get_default_config(self) -> FilterConfig:
        """
        Get a default configuration.
        
        Returns:
            FilterConfig with default settings
        """
        return FilterConfig()
    
    def reset_to_defaults(self, config_path: Optional[str] = None) -> bool:
        """
        Reset configuration to defaults.
        
        Args:
            config_path: Optional path to reset, or None to use default
            
        Returns:
            True if reset successfully, False otherwise
        """
        default_config = self.get_default_config()
        return self.save_config(default_config, config_path)
    
    def backup_config(self, backup_path: Optional[str] = None) -> bool:
        """
        Create a backup of the current configuration.
        
        Args:
            backup_path: Optional path for backup, or None for default naming
            
        Returns:
            True if backup created successfully, False otherwise
        """
        try:
            if not os.path.exists(self.config_file):
                print("No configuration file to backup")
                return False
            
            if backup_path is None:
                timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                backup_path = f"{self.config_file}.backup_{timestamp}"
            
            import shutil
            shutil.copy2(self.config_file, backup_path)
            print(f"Configuration backed up to: {backup_path}")
            return True
            
        except Exception as e:
            print(f"Error creating configuration backup: {e}")
            return False
    
    def list_backups(self) -> List[str]:
        """
        List available configuration backups.
        
        Returns:
            List of backup file paths
        """
        try:
            config_dir = os.path.dirname(self.config_file)
            config_name = os.path.basename(self.config_file)
            
            backups = []
            for filename in os.listdir(config_dir):
                if filename.startswith(f"{config_name}.backup"):
                    backups.append(os.path.join(config_dir, filename))
            
            return sorted(backups, reverse=True)  # Most recent first
            
        except Exception as e:
            print(f"Error listing backups: {e}")
            return []
    
    def restore_from_backup(self, backup_path: str) -> bool:
        """
        Restore configuration from a backup.
        
        Args:
            backup_path: Path to backup file to restore from
            
        Returns:
            True if restored successfully, False otherwise
        """
        try:
            if not os.path.exists(backup_path):
                print(f"Backup file not found: {backup_path}")
                return False
            
            # Load and validate the backup
            config = self.load_config(backup_path)
            if config is None:
                print("Failed to load configuration from backup")
                return False
            
            # Save as current configuration
            return self.save_config(config)
            
        except Exception as e:
            print(f"Error restoring from backup: {e}")
            return False


class AlternativeSuggester:
    """
    Provides safe alternative suggestions when content is blocked.
    
    This class maintains a database of safe alternative websites organized by
    category and provides helpful suggestions when inappropriate content is blocked.
    """
    
    def __init__(self, db_path: Optional[str] = None):
        """
        Initialize the alternative suggester with optional database path.
        
        Args:
            db_path: Path to SQLite database file, or None for default path
        """
        self.db_path = db_path or self._get_default_db_path()
        self._alternatives_cache: Dict[str, List[Dict[str, str]]] = {}
        self._cache_dirty = True
        
        # Initialize database and load default alternatives
        self._init_database()
        self._load_default_alternatives()
    
    def _get_default_db_path(self) -> str:
        """Get the default database path"""
        current_dir = os.path.dirname(os.path.abspath(__file__))
        data_dir = os.path.join(current_dir, '..', 'data')
        return os.path.join(data_dir, 'content_filter.db')
    
    def _init_database(self):
        """Initialize the SQLite database with alternative suggestions tables"""
        try:
            # Ensure data directory exists
            data_dir = os.path.dirname(self.db_path)
            os.makedirs(data_dir, exist_ok=True)
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Create alternative websites table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS alternative_websites (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        category TEXT NOT NULL,
                        name TEXT NOT NULL,
                        url TEXT NOT NULL,
                        description TEXT,
                        age_appropriate BOOLEAN DEFAULT 1,
                        educational_value INTEGER DEFAULT 1,
                        safety_rating INTEGER DEFAULT 5,
                        added_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                # Create alternative search terms table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS alternative_search_terms (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        blocked_term TEXT NOT NULL,
                        suggested_term TEXT NOT NULL,
                        category TEXT,
                        description TEXT,
                        added_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                # Create content categories for alternatives
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS alternative_categories (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        category TEXT UNIQUE NOT NULL,
                        description TEXT,
                        parent_category TEXT,
                        display_order INTEGER DEFAULT 0
                    )
                ''')
                
                # Create indexes for better performance
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_alt_category ON alternative_websites(category)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_alt_age ON alternative_websites(age_appropriate)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_alt_rating ON alternative_websites(safety_rating)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_search_blocked ON alternative_search_terms(blocked_term)')
                
                conn.commit()
                
                # Initialize categories
                self._init_alternative_categories(cursor)
                conn.commit()
                
        except sqlite3.Error as e:
            print(f"Alternative suggester database initialization error: {e}")
    
    def _init_alternative_categories(self, cursor):
        """Initialize alternative content categories"""
        categories_data = [
            ("educational", "Educational and learning resources", None, 1),
            ("entertainment", "Family-friendly entertainment", None, 2),
            ("news", "News and current events", None, 3),
            ("science", "Science and technology", "educational", 4),
            ("history", "History and culture", "educational", 5),
            ("math", "Mathematics and calculations", "educational", 6),
            ("language", "Language learning and literature", "educational", 7),
            ("kids_games", "Educational games for children", "entertainment", 8),
            ("documentaries", "Educational documentaries", "entertainment", 9),
            ("music", "Family-friendly music", "entertainment", 10),
            ("art", "Art and creativity", "entertainment", 11),
            ("sports", "Sports and fitness", "entertainment", 12),
            ("cooking", "Cooking and recipes", "entertainment", 13),
            ("nature", "Nature and wildlife", "educational", 14),
            ("health", "Health and wellness", "educational", 15)
        ]
        
        for category, description, parent, order in categories_data:
            cursor.execute('''
                INSERT OR IGNORE INTO alternative_categories 
                (category, description, parent_category, display_order)
                VALUES (?, ?, ?, ?)
            ''', (category, description, parent, order))
    
    def _load_default_alternatives(self):
        """Load default alternative websites and search terms"""
        if self._has_default_alternatives():
            return  # Already populated
        
        # Default alternative websites organized by category
        default_alternatives = self._get_default_alternatives()
        
        # Default alternative search terms
        default_search_terms = self._get_default_search_terms()
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Load alternative websites
                for category, sites in default_alternatives.items():
                    for site_info in sites:
                        name, url, description, age_appropriate, educational_value, safety_rating = site_info
                        
                        cursor.execute('''
                            INSERT OR IGNORE INTO alternative_websites 
                            (category, name, url, description, age_appropriate, educational_value, safety_rating)
                            VALUES (?, ?, ?, ?, ?, ?, ?)
                        ''', (category, name, url, description, age_appropriate, educational_value, safety_rating))
                
                # Load alternative search terms
                for blocked_term, suggested_term, category, description in default_search_terms:
                    cursor.execute('''
                        INSERT OR IGNORE INTO alternative_search_terms 
                        (blocked_term, suggested_term, category, description)
                        VALUES (?, ?, ?, ?)
                    ''', (blocked_term, suggested_term, category, description))
                
                conn.commit()
                
        except sqlite3.Error as e:
            print(f"Error populating default alternatives: {e}")
    
    def _has_default_alternatives(self) -> bool:
        """Check if default alternatives have already been populated"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT COUNT(*) FROM alternative_websites')
                count = cursor.fetchone()[0]
                return count > 10  # Assume populated if more than 10 entries
        except sqlite3.Error:
            return False
    
    def _get_default_alternatives(self) -> Dict[str, List[Tuple]]:
        """Get comprehensive default alternative websites organized by category"""
        return {
            "educational": [
                ("Khan Academy", "https://www.khanacademy.org", "Free online courses and lessons", True, 5, 5),
                ("Wikipedia", "https://www.wikipedia.org", "Free encyclopedia", True, 5, 5),
                ("Coursera", "https://www.coursera.org", "Online university courses", True, 5, 5),
                ("edX", "https://www.edx.org", "University-level online courses", True, 5, 5),
                ("MIT OpenCourseWare", "https://ocw.mit.edu", "Free MIT course materials", True, 5, 5),
                ("Codecademy", "https://www.codecademy.com", "Learn to code interactively", True, 4, 5),
                ("Duolingo", "https://www.duolingo.com", "Language learning platform", True, 4, 5),
                ("TED-Ed", "https://ed.ted.com", "Educational videos and lessons", True, 5, 5),
                ("National Geographic Kids", "https://kids.nationalgeographic.com", "Educational content for children", True, 5, 5),
                ("Smithsonian Learning", "https://www.si.edu/learn", "Museum educational resources", True, 5, 5)
            ],
            "science": [
                ("NASA", "https://www.nasa.gov", "Space exploration and science", True, 5, 5),
                ("Science Museum", "https://www.sciencemuseum.org.uk", "Science exhibits and learning", True, 5, 5),
                ("How Stuff Works", "https://www.howstuffworks.com", "Science and technology explanations", True, 4, 5),
                ("Scientific American", "https://www.scientificamerican.com", "Science news and articles", True, 4, 5),
                ("Bill Nye", "https://www.billnye.com", "Science education and fun", True, 5, 5),
                ("Crash Course", "https://thecrashcourse.com", "Educational video series", True, 5, 5),
                ("SciShow", "https://www.youtube.com/user/scishow", "Science education videos", True, 4, 5),
                ("Brain Scoop", "https://www.youtube.com/user/thebrainscoop", "Natural history education", True, 4, 5)
            ],
            "kids_games": [
                ("PBS Kids", "https://pbskids.org", "Educational games for children", True, 5, 5),
                ("Funbrain", "https://www.funbrain.com", "Educational games and books", True, 5, 5),
                ("ABCya", "https://www.abcya.com", "Educational computer games", True, 5, 5),
                ("Coolmath Games", "https://www.coolmathgames.com", "Math and logic games", True, 4, 5),
                ("National Geographic Kids Games", "https://kids.nationalgeographic.com/games", "Educational nature games", True, 5, 5),
                ("Scratch", "https://scratch.mit.edu", "Learn programming through games", True, 5, 5),
                ("Code.org", "https://code.org", "Learn computer science", True, 5, 5),
                ("Typing Club", "https://www.typingclub.com", "Learn typing skills", True, 4, 5)
            ],
            "entertainment": [
                ("Disney", "https://www.disney.com", "Family-friendly entertainment", True, 3, 5),
                ("Nickelodeon", "https://www.nick.com", "Children's entertainment", True, 4, 5),
                ("Cartoon Network", "https://www.cartoonnetwork.com", "Animated entertainment", True, 3, 4),
                ("BBC iPlayer Kids", "https://www.bbc.co.uk/iplayer/cbbc", "Educational children's content", True, 5, 5),
                ("Sesame Street", "https://www.sesamestreet.org", "Educational children's content", True, 5, 5),
                ("Mr. Rogers Neighborhood", "https://www.misterrogers.org", "Classic children's education", True, 5, 5),
                ("Highlights Kids", "https://www.highlightskids.com", "Children's magazine and activities", True, 5, 5)
            ],
            "news": [
                ("BBC News", "https://www.bbc.com/news", "International news coverage", True, 3, 5),
                ("NPR", "https://www.npr.org", "Public radio news", True, 4, 5),
                ("Reuters", "https://www.reuters.com", "International news agency", True, 3, 5),
                ("Associated Press", "https://apnews.com", "News wire service", True, 3, 5),
                ("PBS NewsHour", "https://www.pbs.org/newshour", "Public television news", True, 4, 5),
                ("Time for Kids", "https://www.timeforkids.com", "News for children", True, 5, 5),
                ("Scholastic News", "https://www.scholastic.com/teachers/magazines/scholastic-news", "Educational news for students", True, 5, 5)
            ],
            "art": [
                ("Metropolitan Museum", "https://www.metmuseum.org", "Art museum and collections", True, 4, 5),
                ("Louvre Virtual Tours", "https://www.louvre.fr/en/visites-en-ligne", "Virtual museum tours", True, 5, 5),
                ("Google Arts & Culture", "https://artsandculture.google.com", "Art collections and virtual tours", True, 5, 5),
                ("Tate Kids", "https://www.tate.org.uk/kids", "Art activities for children", True, 5, 5),
                ("Art for Kids Hub", "https://www.artforkidshub.com", "Drawing tutorials for children", True, 5, 5),
                ("Crayola", "https://www.crayola.com", "Art supplies and activities", True, 4, 5)
            ],
            "music": [
                ("Classics for Kids", "https://www.classicsforkids.com", "Classical music education", True, 5, 5),
                ("Spotify Kids", "https://www.spotify.com/us/kids", "Family-friendly music streaming", True, 4, 5),
                ("YouTube Music Kids", "https://music.youtube.com", "Curated music for children", True, 4, 4),
                ("Smithsonian Folkways", "https://folkways.si.edu", "Traditional and folk music", True, 4, 5),
                ("Carnegie Hall", "https://www.carnegiehall.org", "Classical music venue and education", True, 4, 5)
            ],
            "sports": [
                ("ESPN", "https://www.espn.com", "Sports news and coverage", True, 3, 4),
                ("Olympic Games", "https://www.olympic.org", "Olympic sports and athletes", True, 4, 5),
                ("FIFA", "https://www.fifa.com", "International football/soccer", True, 3, 4),
                ("NBA", "https://www.nba.com", "Professional basketball", True, 3, 4),
                ("Special Olympics", "https://www.specialolympics.org", "Inclusive sports organization", True, 5, 5)
            ],
            "nature": [
                ("National Geographic", "https://www.nationalgeographic.com", "Nature and wildlife content", True, 4, 5),
                ("World Wildlife Fund", "https://www.worldwildlife.org", "Wildlife conservation", True, 4, 5),
                ("Audubon Society", "https://www.audubon.org", "Bird watching and conservation", True, 4, 5),
                ("Nature Conservancy", "https://www.nature.org", "Environmental conservation", True, 4, 5),
                ("Ranger Rick", "https://rangerrick.org", "Nature magazine for kids", True, 5, 5),
                ("San Diego Zoo", "https://zoo.sandiegozoo.org", "Zoo and wildlife conservation", True, 5, 5)
            ]
        }
    
    def _get_default_search_terms(self) -> List[Tuple[str, str, str, str]]:
        """Get default alternative search terms for blocked queries"""
        return [
            # Adult content alternatives
            ("adult content", "educational resources", "educational", "Redirect to learning materials"),
            ("inappropriate videos", "educational videos", "educational", "Suggest educational video content"),
            ("mature content", "age-appropriate content", "entertainment", "Suggest family-friendly alternatives"),
            
            # Violence alternatives
            ("violent games", "educational games", "kids_games", "Suggest non-violent educational games"),
            ("fighting videos", "sports videos", "sports", "Redirect to sports content"),
            ("war movies", "history documentaries", "educational", "Suggest educational history content"),
            
            # Gambling alternatives
            ("casino games", "math games", "kids_games", "Suggest educational math games"),
            ("poker online", "card games for kids", "kids_games", "Suggest family-friendly card games"),
            ("betting sites", "sports news", "sports", "Redirect to sports information"),
            
            # Drug-related alternatives
            ("drug information", "health education", "health", "Suggest health and wellness resources"),
            ("substance abuse", "health resources", "health", "Redirect to health education"),
            
            # General inappropriate alternatives
            ("inappropriate content", "educational content", "educational", "Suggest learning resources"),
            ("blocked content", "safe browsing", "educational", "Suggest safe browsing practices"),
            ("restricted material", "family-friendly content", "entertainment", "Suggest appropriate entertainment"),
            
            # Search refinement suggestions
            ("bad words", "vocabulary building", "language", "Suggest language learning resources"),
            ("scary content", "nature documentaries", "nature", "Suggest calming nature content"),
            ("disturbing images", "art galleries", "art", "Suggest beautiful art content")
        ]
    
    def _refresh_cache(self):
        """Refresh the in-memory alternatives cache from database"""
        if not self._cache_dirty:
            return
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Load alternatives by category
                cursor.execute('''
                    SELECT category, name, url, description, age_appropriate, 
                           educational_value, safety_rating
                    FROM alternative_websites
                    ORDER BY category, safety_rating DESC, educational_value DESC
                ''')
                
                self._alternatives_cache = {}
                for row in cursor.fetchall():
                    category, name, url, description, age_appropriate, educational_value, safety_rating = row
                    
                    if category not in self._alternatives_cache:
                        self._alternatives_cache[category] = []
                    
                    self._alternatives_cache[category].append({
                        'name': name,
                        'url': url,
                        'description': description,
                        'age_appropriate': bool(age_appropriate),
                        'educational_value': educational_value,
                        'safety_rating': safety_rating
                    })
                
                self._cache_dirty = False
        except sqlite3.Error:
            # If database access fails, keep existing cache
            pass
    
    def get_alternatives_by_category(self, category: str, max_results: int = 5, 
                                   age_appropriate_only: bool = True) -> List[Dict[str, Any]]:
        """
        Get alternative websites for a specific category.
        
        Args:
            category: Content category to get alternatives for
            max_results: Maximum number of alternatives to return
            age_appropriate_only: Whether to only return age-appropriate content
            
        Returns:
            List of alternative website dictionaries
        """
        self._refresh_cache()
        
        if category not in self._alternatives_cache:
            return []
        
        alternatives = self._alternatives_cache[category]
        
        # Filter by age appropriateness if requested
        if age_appropriate_only:
            alternatives = [alt for alt in alternatives if alt['age_appropriate']]
        
        # Return top results (already sorted by safety rating and educational value)
        return alternatives[:max_results]
    
    def get_alternatives_for_blocked_content(self, blocked_category: ContentCategory, 
                                           max_results: int = 3) -> List[Dict[str, Any]]:
        """
        Get appropriate alternatives when content is blocked.
        
        Args:
            blocked_category: Category of the blocked content
            max_results: Maximum number of alternatives to return
            
        Returns:
            List of alternative suggestions
        """
        # Map blocked categories to appropriate alternative categories
        category_mapping = {
            ContentCategory.ADULT: ["educational", "entertainment"],
            ContentCategory.VIOLENCE: ["sports", "nature", "art"],
            ContentCategory.GAMBLING: ["kids_games", "math", "educational"],
            ContentCategory.DRUGS: ["health", "science", "educational"],
            ContentCategory.HATE_SPEECH: ["educational", "news", "art"],
            ContentCategory.MALWARE: ["educational", "science"],
            ContentCategory.PHISHING: ["educational", "news"]
        }
        
        alternative_categories = category_mapping.get(blocked_category, ["educational", "entertainment"])
        
        all_alternatives = []
        for category in alternative_categories:
            alternatives = self.get_alternatives_by_category(category, max_results=2)
            all_alternatives.extend(alternatives)
        
        # Remove duplicates and limit results
        seen_urls = set()
        unique_alternatives = []
        for alt in all_alternatives:
            if alt['url'] not in seen_urls:
                seen_urls.add(alt['url'])
                unique_alternatives.append(alt)
                if len(unique_alternatives) >= max_results:
                    break
        
        return unique_alternatives
    
    def suggest_alternative_search_terms(self, blocked_query: str, max_suggestions: int = 3) -> List[str]:
        """
        Suggest alternative search terms for blocked queries.
        
        Args:
            blocked_query: The search query that was blocked
            max_suggestions: Maximum number of suggestions to return
            
        Returns:
            List of suggested alternative search terms
        """
        suggestions = []
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Look for exact matches first
                cursor.execute('''
                    SELECT suggested_term FROM alternative_search_terms
                    WHERE LOWER(blocked_term) = LOWER(?)
                    LIMIT ?
                ''', (blocked_query.strip(), max_suggestions))
                
                suggestions.extend([row[0] for row in cursor.fetchall()])
                
                # If we don't have enough suggestions, look for partial matches
                if len(suggestions) < max_suggestions:
                    remaining = max_suggestions - len(suggestions)
                    cursor.execute('''
                        SELECT suggested_term FROM alternative_search_terms
                        WHERE LOWER(blocked_term) LIKE LOWER(?) 
                        AND LOWER(blocked_term) != LOWER(?)
                        LIMIT ?
                    ''', (f'%{blocked_query.strip()}%', blocked_query.strip(), remaining))
                    
                    suggestions.extend([row[0] for row in cursor.fetchall()])
                
        except sqlite3.Error:
            pass
        
        # If still no suggestions, provide generic safe alternatives
        if not suggestions:
            generic_suggestions = [
                "educational resources",
                "family-friendly content",
                "learning materials",
                "safe browsing topics"
            ]
            suggestions = generic_suggestions[:max_suggestions]
        
        return suggestions[:max_suggestions]
    
    def add_alternative_website(self, category: str, name: str, url: str, 
                              description: str = "", age_appropriate: bool = True,
                              educational_value: int = 3, safety_rating: int = 5) -> bool:
        """
        Add a new alternative website to the database.
        
        Args:
            category: Content category
            name: Website name
            url: Website URL
            description: Website description
            age_appropriate: Whether content is age-appropriate
            educational_value: Educational value (1-5 scale)
            safety_rating: Safety rating (1-5 scale)
            
        Returns:
            True if added successfully, False otherwise
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT OR REPLACE INTO alternative_websites 
                    (category, name, url, description, age_appropriate, educational_value, safety_rating)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (category, name, url, description, age_appropriate, educational_value, safety_rating))
                conn.commit()
                self._cache_dirty = True
                return cursor.rowcount > 0
        except sqlite3.Error:
            return False
    
    def add_alternative_search_term(self, blocked_term: str, suggested_term: str, 
                                  category: str = "general", description: str = "") -> bool:
        """
        Add a new alternative search term mapping.
        
        Args:
            blocked_term: The term that gets blocked
            suggested_term: The alternative term to suggest
            category: Content category
            description: Description of the mapping
            
        Returns:
            True if added successfully, False otherwise
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT OR REPLACE INTO alternative_search_terms 
                    (blocked_term, suggested_term, category, description)
                    VALUES (?, ?, ?, ?)
                ''', (blocked_term, suggested_term, category, description))
                conn.commit()
                return cursor.rowcount > 0
        except sqlite3.Error:
            return False
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get alternative suggester statistics.
        
        Returns:
            Dictionary containing statistics
        """
        stats = {
            "database_path": self.db_path,
            "categories": [],
            "total_alternatives": 0,
            "total_search_terms": 0
        }
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Count alternatives by category
                cursor.execute('''
                    SELECT category, COUNT(*) 
                    FROM alternative_websites 
                    GROUP BY category
                    ORDER BY COUNT(*) DESC
                ''')
                category_counts = cursor.fetchall()
                stats['categories'] = [{'category': cat, 'count': count} for cat, count in category_counts]
                
                # Total counts
                cursor.execute('SELECT COUNT(*) FROM alternative_websites')
                stats['total_alternatives'] = cursor.fetchone()[0]
                
                cursor.execute('SELECT COUNT(*) FROM alternative_search_terms')
                stats['total_search_terms'] = cursor.fetchone()[0]
                
                # Age-appropriate content percentage
                cursor.execute('SELECT COUNT(*) FROM alternative_websites WHERE age_appropriate = 1')
                age_appropriate_count = cursor.fetchone()[0]
                if stats['total_alternatives'] > 0:
                    stats['age_appropriate_percentage'] = (age_appropriate_count / stats['total_alternatives']) * 100
                else:
                    stats['age_appropriate_percentage'] = 0
                
        except sqlite3.Error:
            pass
        
        return stats"""