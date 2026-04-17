"""
Domain Database Management for Content Filtering System

This module provides comprehensive domain database management including
curated blacklists of inappropriate domains organized by category,
database CRUD operations, and initialization of default filtering rules.
"""

import sqlite3
import os
from typing import List, Dict, Optional, Tuple
from enum import Enum


class DomainCategory(Enum):
    """Categories for domain classification"""
    ADULT = "adult"
    VIOLENCE = "violence"
    GAMBLING = "gambling"
    DRUGS = "drugs"
    HATE_SPEECH = "hate_speech"
    MALWARE = "malware"
    PHISHING = "phishing"
    SOCIAL_MEDIA = "social_media"
    GAMING = "gaming"
    DEFAULT = "default"


class DomainDatabaseManager:
    """
    Manages the domain filtering database with comprehensive CRUD operations
    and curated blacklists organized by content category.
    """
    
    def __init__(self, db_path: Optional[str] = None):
        """
        Initialize the domain database manager.
        
        Args:
            db_path: Path to SQLite database file, defaults to wizard/data/content_filter.db
        """
        if db_path is None:
            # Default to wizard/data/content_filter.db
            current_dir = os.path.dirname(os.path.abspath(__file__))
            data_dir = os.path.join(current_dir, '..', 'data')
            db_path = os.path.join(data_dir, 'content_filter.db')
        
        self.db_path = os.path.abspath(db_path)
        self._ensure_data_directory()
        self._init_database()
        self._populate_default_blacklists()
    
    def _ensure_data_directory(self):
        """Ensure the data directory exists"""
        data_dir = os.path.dirname(self.db_path)
        os.makedirs(data_dir, exist_ok=True)
    
    def _init_database(self):
        """Initialize the database with required tables and indexes"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
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
                
        except sqlite3.Error as e:
            print(f"Database initialization error: {e}")
            raise
    
    def _init_categories(self, cursor):
        """Initialize domain categories metadata"""
        categories_data = [
            (DomainCategory.ADULT.value, "Adult and pornographic content", 3),
            (DomainCategory.VIOLENCE.value, "Violence, gore, and disturbing content", 3),
            (DomainCategory.GAMBLING.value, "Gambling and betting sites", 2),
            (DomainCategory.DRUGS.value, "Illegal drugs and substance abuse", 3),
            (DomainCategory.HATE_SPEECH.value, "Hate speech and extremist content", 3),
            (DomainCategory.MALWARE.value, "Malware and malicious software", 3),
            (DomainCategory.PHISHING.value, "Phishing and scam sites", 3),
            (DomainCategory.SOCIAL_MEDIA.value, "Social media platforms", 1),
            (DomainCategory.GAMING.value, "Gaming and entertainment sites", 1),
            (DomainCategory.DEFAULT.value, "General inappropriate content", 2)
        ]
        
        for category, description, severity in categories_data:
            cursor.execute('''
                INSERT OR IGNORE INTO domain_categories (category, description, default_severity)
                VALUES (?, ?, ?)
            ''', (category, description, severity))
    
    def _populate_default_blacklists(self):
        """Populate the database with comprehensive default blacklists"""
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
            DomainCategory.ADULT.value: [
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
            DomainCategory.VIOLENCE.value: [
                ("*violence*", "Violence content patterns", 3),
                ("*gore*", "Gore content patterns", 3),
                ("*death*", "Death-related content", 3),
                ("*murder*", "Murder-related content", 3),
                ("*torture*", "Torture content", 3),
                ("*brutal*", "Brutal content", 3),
                ("violence-test.com", "Test violence site", 3),
                ("gore-content.net", "Test gore site", 3)
            ],
            DomainCategory.GAMBLING.value: [
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
            DomainCategory.DRUGS.value: [
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
            DomainCategory.HATE_SPEECH.value: [
                ("*hate*", "Hate speech content", 3),
                ("*nazi*", "Nazi content", 3),
                ("*supremacist*", "Supremacist content", 3),
                ("*extremist*", "Extremist content", 3),
                ("*terrorist*", "Terrorist content", 3),
                ("*racism*", "Racist content", 3),
                ("hate-group.org", "Test hate group site", 3),
                ("extremist-forum.net", "Test extremist site", 3)
            ],
            DomainCategory.MALWARE.value: [
                ("*malware*", "Malware distribution", 3),
                ("*virus*", "Virus distribution", 3),
                ("*trojan*", "Trojan distribution", 3),
                ("*ransomware*", "Ransomware sites", 3),
                ("*exploit*", "Exploit sites", 3),
                ("malicious-site.com", "Test malware site", 3),
                ("virus-download.net", "Test virus site", 3),
                ("fake-antivirus.org", "Test fake antivirus", 3)
            ],
            DomainCategory.PHISHING.value: [
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
    
    # CRUD Operations
    
    def add_blocked_domain(self, domain: str, category: str = DomainCategory.DEFAULT.value, 
                          severity: int = 2, description: str = "") -> bool:
        """Add a domain to the blacklist"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                is_pattern = 1 if '*' in domain else 0
                cursor.execute('''
                    INSERT OR REPLACE INTO blocked_domains 
                    (domain, category, severity, description, is_pattern)
                    VALUES (?, ?, ?, ?, ?)
                ''', (domain.lower().strip(), category, severity, description, is_pattern))
                conn.commit()
                return cursor.rowcount > 0
        except sqlite3.Error as e:
            print(f"Error adding blocked domain: {e}")
            return False
    
    def add_allowed_domain(self, domain: str, description: str = "") -> bool:
        """Add a domain to the whitelist"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                is_pattern = 1 if '*' in domain else 0
                cursor.execute('''
                    INSERT OR REPLACE INTO allowed_domains (domain, description, is_pattern)
                    VALUES (?, ?, ?)
                ''', (domain.lower().strip(), description, is_pattern))
                conn.commit()
                return cursor.rowcount > 0
        except sqlite3.Error as e:
            print(f"Error adding allowed domain: {e}")
            return False
    
    def remove_blocked_domain(self, domain: str) -> bool:
        """Remove a domain from the blacklist"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('DELETE FROM blocked_domains WHERE domain = ?', (domain.lower().strip(),))
                conn.commit()
                return cursor.rowcount > 0
        except sqlite3.Error as e:
            print(f"Error removing blocked domain: {e}")
            return False
    
    def remove_allowed_domain(self, domain: str) -> bool:
        """Remove a domain from the whitelist"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('DELETE FROM allowed_domains WHERE domain = ?', (domain.lower().strip(),))
                conn.commit()
                return cursor.rowcount > 0
        except sqlite3.Error as e:
            print(f"Error removing allowed domain: {e}")
            return False
    
    def get_blocked_domains(self, category: Optional[str] = None) -> List[Tuple[str, str, int, str]]:
        """Get blocked domains, optionally filtered by category"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                if category:
                    cursor.execute('''
                        SELECT domain, category, severity, description 
                        FROM blocked_domains 
                        WHERE category = ?
                        ORDER BY severity DESC, domain
                    ''', (category,))
                else:
                    cursor.execute('''
                        SELECT domain, category, severity, description 
                        FROM blocked_domains 
                        ORDER BY severity DESC, domain
                    ''')
                return cursor.fetchall()
        except sqlite3.Error as e:
            print(f"Error getting blocked domains: {e}")
            return []
    
    def get_allowed_domains(self) -> List[Tuple[str, str]]:
        """Get all allowed domains"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT domain, description FROM allowed_domains ORDER BY domain')
                return cursor.fetchall()
        except sqlite3.Error as e:
            print(f"Error getting allowed domains: {e}")
            return []
    
    def get_categories(self) -> List[Tuple[str, str, int]]:
        """Get all domain categories"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT category, description, default_severity FROM domain_categories ORDER BY category')
                return cursor.fetchall()
        except sqlite3.Error as e:
            print(f"Error getting categories: {e}")
            return []
    
    def get_filter_stats(self) -> Dict[str, int]:
        """Get filtering statistics"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                stats = {}
                
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
                
                return stats
                
        except sqlite3.Error as e:
            print(f"Error getting filter stats: {e}")
            return {}


def initialize_domain_database(db_path: Optional[str] = None) -> DomainDatabaseManager:
    """Initialize and return a domain database manager with default data"""
    return DomainDatabaseManager(db_path)


def main():
    """Main function for testing and initialization"""
    print("Initializing domain database...")
    db_manager = initialize_domain_database()
    
    print("Database initialized successfully!")
    
    # Print statistics
    stats = db_manager.get_filter_stats()
    print(f"Total blocked domains: {stats.get('total_blocked', 0)}")
    print(f"Total allowed domains: {stats.get('total_allowed', 0)}")
    
    print("\nBlocked domains by category:")
    for category, count in stats.get('blocked_by_category', {}).items():
        print(f"  {category}: {count}")
    
    print("\nCategories:")
    categories = db_manager.get_categories()
    for category, description, severity in categories:
        print(f"  {category}: {description} (severity: {severity})")


if __name__ == "__main__":
    main()