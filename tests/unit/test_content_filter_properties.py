"""
Property-based tests for Content Filtering System

This module contains property-based tests that validate universal properties
of the content filtering system using the Hypothesis library.
"""

import pytest
from hypothesis import given, strategies as st, assume, settings
import sys
import os

# Add project root to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from wizard.utils.content_filter import (
    ContentFilter, FilterConfig, WebRequest, FilterResult,
    ContentCategory, FilterLevel, RequestType, DomainChecker, DomainStatus,
    KeywordFilter, SafeSearchEnforcer
)


class TestSafeSearchEnforcementProperties:
    """Property-based tests for safe search enforcement functionality"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.safe_search_enforcer = SafeSearchEnforcer(enabled=True)
    
    @given(
        search_engine=st.sampled_from(['google', 'bing', 'youtube', 'duckduckgo', 'yahoo']),
        search_query=st.text(min_size=1, max_size=100).filter(lambda x: x.strip() and not any(c in x for c in ['&', '?', '=', '#'])),
        domain_variant=st.sampled_from(['', 'www.'])
    )
    @settings(max_examples=100, deadline=None)
    def test_safe_search_consistency_property(self, search_engine, search_query, domain_variant):
        """
        Property 5: Safe search consistency
        For any search request when safe search is enabled, the resulting URL 
        should contain appropriate safe search parameters.
        **Validates: Requirements 4.1, 4.2, 4.3**
        """
        # Assume valid inputs
        assume(len(search_query.strip()) > 0)
        assume(not any(char in search_query for char in ['&', '?', '=', '#', '%']))
        
        # Create a search URL for the given search engine
        search_urls = {
            'google': f"https://{domain_variant}google.com/search?q={search_query.replace(' ', '+')}",
            'bing': f"https://{domain_variant}bing.com/search?q={search_query.replace(' ', '+')}",
            'youtube': f"https://{domain_variant}youtube.com/results?search_query={search_query.replace(' ', '+')}",
            'duckduckgo': f"https://{domain_variant}duckduckgo.com/?q={search_query.replace(' ', '+')}",
            'yahoo': f"https://search.yahoo.com/search?p={search_query.replace(' ', '+')}"
        }
        
        original_url = search_urls[search_engine]
        
        # Apply safe search enforcement
        modified_url = self.safe_search_enforcer.enforce_safe_search(original_url)
        
        # The URL should be modified (unless it already had safe search)
        if not self.safe_search_enforcer.is_safe_search_enabled(original_url):
            assert modified_url != original_url, \
                f"Safe search enforcement should modify URL for {search_engine}, but URL remained unchanged: {original_url}"
        
        # The modified URL should contain appropriate safe search parameters
        expected_params = {
            'google': ['safe=active'],
            'bing': ['adlt=strict'],
            'youtube': ['safe_search=1'],
            'duckduckgo': ['safe_search=1'],
            'yahoo': ['vm=r', 'fl=1']
        }
        
        expected_for_engine = expected_params[search_engine]
        
        # Check that at least one expected parameter is present
        param_found = False
        for param in expected_for_engine:
            if param in modified_url:
                param_found = True
                break
        
        assert param_found, \
            f"Modified URL should contain safe search parameters {expected_for_engine} for {search_engine}, but got: {modified_url}"
        
        # Verify that safe search is now detected as enabled
        assert self.safe_search_enforcer.is_safe_search_enabled(modified_url), \
            f"Safe search should be detected as enabled in modified URL: {modified_url}"
    
    @given(
        search_engine=st.sampled_from(['google', 'bing']),
        search_query=st.text(min_size=1, max_size=100).filter(lambda x: x.strip() and not any(c in x for c in ['&', '?', '=', '#'])),
        search_type=st.sampled_from(['web', 'images', 'videos'])
    )
    @settings(max_examples=100, deadline=None)
    def test_safe_search_type_specific_property(self, search_engine, search_query, search_type):
        """
        Property 5b: Safe search type-specific consistency
        For any image or video search request, the appropriate safe search 
        parameters should be applied based on the search type.
        **Validates: Requirements 4.1, 4.2, 4.3**
        """
        # Assume valid inputs
        assume(len(search_query.strip()) > 0)
        assume(not any(char in search_query for char in ['&', '?', '=', '#', '%']))
        
        # Create type-specific search URLs
        if search_type == 'images':
            if search_engine == 'google':
                original_url = f"https://www.google.com/search?q={search_query.replace(' ', '+')}&tbm=isch"
            else:  # bing
                original_url = f"https://www.bing.com/images/search?q={search_query.replace(' ', '+')}"
        elif search_type == 'videos':
            if search_engine == 'google':
                original_url = f"https://www.google.com/search?q={search_query.replace(' ', '+')}&tbm=vid"
            else:  # bing
                original_url = f"https://www.bing.com/videos/search?q={search_query.replace(' ', '+')}"
        else:  # web
            if search_engine == 'google':
                original_url = f"https://www.google.com/search?q={search_query.replace(' ', '+')}"
            else:  # bing
                original_url = f"https://www.bing.com/search?q={search_query.replace(' ', '+')}"
        
        # Apply safe search enforcement
        modified_url = self.safe_search_enforcer.enforce_safe_search(original_url)
        
        # The URL should be modified (unless it already had safe search)
        if not self.safe_search_enforcer.is_safe_search_enabled(original_url):
            assert modified_url != original_url, \
                f"Safe search enforcement should modify {search_type} search URL for {search_engine}, but URL remained unchanged: {original_url}"
        
        # Check for appropriate safe search parameters
        if search_engine == 'google':
            assert 'safe=active' in modified_url, \
                f"Google {search_type} search should contain 'safe=active' parameter: {modified_url}"
        elif search_engine == 'bing':
            assert 'adlt=strict' in modified_url, \
                f"Bing {search_type} search should contain 'adlt=strict' parameter: {modified_url}"
        
        # Verify that safe search is detected as enabled
        assert self.safe_search_enforcer.is_safe_search_enabled(modified_url), \
            f"Safe search should be detected as enabled in modified {search_type} URL: {modified_url}"


class TestKeywordFilteringProperties:
    """Property-based tests for keyword filtering functionality"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.keyword_filter = KeywordFilter()
        self.content_filter = ContentFilter()
    
    @given(
        text=st.text(min_size=1, max_size=200).filter(lambda x: x.strip()),
        keyword=st.sampled_from(['adult', 'casino', 'violent', 'kill', 'porn', 'murder'])
    )
    @settings(max_examples=100, deadline=None)
    def test_keyword_detection_accuracy_property(self, text, keyword):
        """
        Property 4: Keyword detection accuracy
        For any text containing blocked keywords, the keyword filter should detect 
        at least one inappropriate term.
        **Validates: Requirements 2.3**
        """
        # Assume valid inputs
        assume(len(text.strip()) > 0)
        
        # Create text that definitely contains the keyword
        test_text = f"{text} {keyword} more text"
        
        # Scan for keywords
        detected_keywords = self.keyword_filter.scan_text(test_text)
        
        # The keyword should be detected
        assert len(detected_keywords) > 0, \
            f"Text containing '{keyword}' should detect at least one keyword, but detected: {detected_keywords}"
        
        # The specific keyword or a pattern matching it should be in the detected list
        keyword_found = False
        for detected in detected_keywords:
            if keyword in detected or detected in keyword or detected.replace('*', '') in keyword:
                keyword_found = True
                break
        
        assert keyword_found, \
            f"Expected to find '{keyword}' or related pattern in detected keywords: {detected_keywords}"
        
        # Test that is_query_safe returns False for text with inappropriate keywords
        is_safe = self.keyword_filter.is_query_safe(test_text)
        assert not is_safe, \
            f"Text containing '{keyword}' should not be considered safe, but is_query_safe returned: {is_safe}"


# Standalone test functions for pytest discovery

@given(
    search_engine=st.sampled_from(['google', 'bing', 'youtube', 'duckduckgo', 'yahoo']),
    search_query=st.text(min_size=1, max_size=100).filter(lambda x: x.strip() and not any(c in x for c in ['&', '?', '=', '#'])),
    domain_variant=st.sampled_from(['', 'www.'])
)
@settings(max_examples=100, deadline=None)
def test_safe_search_consistency_property_standalone(search_engine, search_query, domain_variant):
    """
    Property 5: Safe search consistency
    For any search request when safe search is enabled, the resulting URL 
    should contain appropriate safe search parameters.
    **Validates: Requirements 4.1, 4.2, 4.3**
    """
    # Assume valid inputs
    assume(len(search_query.strip()) > 0)
    assume(not any(char in search_query for char in ['&', '?', '=', '#', '%']))
    
    safe_search_enforcer = SafeSearchEnforcer(enabled=True)
    
    # Create a search URL for the given search engine
    search_urls = {
        'google': f"https://{domain_variant}google.com/search?q={search_query.replace(' ', '+')}",
        'bing': f"https://{domain_variant}bing.com/search?q={search_query.replace(' ', '+')}",
        'youtube': f"https://{domain_variant}youtube.com/results?search_query={search_query.replace(' ', '+')}",
        'duckduckgo': f"https://{domain_variant}duckduckgo.com/?q={search_query.replace(' ', '+')}",
        'yahoo': f"https://search.yahoo.com/search?p={search_query.replace(' ', '+')}"
    }
    
    original_url = search_urls[search_engine]
    
    # Apply safe search enforcement
    modified_url = safe_search_enforcer.enforce_safe_search(original_url)
    
    # The URL should be modified (unless it already had safe search)
    if not safe_search_enforcer.is_safe_search_enabled(original_url):
        assert modified_url != original_url, \
            f"Safe search enforcement should modify URL for {search_engine}, but URL remained unchanged: {original_url}"
    
    # The modified URL should contain appropriate safe search parameters
    expected_params = {
        'google': ['safe=active'],
        'bing': ['adlt=strict'],
        'youtube': ['safe_search=1'],
        'duckduckgo': ['safe_search=1'],
        'yahoo': ['vm=r', 'fl=1']
    }
    
    expected_for_engine = expected_params[search_engine]
    
    # Check that at least one expected parameter is present
    param_found = False
    for param in expected_for_engine:
        if param in modified_url:
            param_found = True
            break
    
    assert param_found, \
        f"Modified URL should contain safe search parameters {expected_for_engine} for {search_engine}, but got: {modified_url}"
    
    # Verify that safe search is now detected as enabled
    assert safe_search_enforcer.is_safe_search_enabled(modified_url), \
        f"Safe search should be detected as enabled in modified URL: {modified_url}"


@given(
    search_engine=st.sampled_from(['google', 'bing']),
    search_query=st.text(min_size=1, max_size=100).filter(lambda x: x.strip() and not any(c in x for c in ['&', '?', '=', '#'])),
    search_type=st.sampled_from(['web', 'images', 'videos'])
)
@settings(max_examples=100, deadline=None)
def test_safe_search_type_specific_property_standalone(search_engine, search_query, search_type):
    """
    Property 5b: Safe search type-specific consistency
    For any image or video search request, the appropriate safe search 
    parameters should be applied based on the search type.
    **Validates: Requirements 4.1, 4.2, 4.3**
    """
    # Assume valid inputs
    assume(len(search_query.strip()) > 0)
    assume(not any(char in search_query for char in ['&', '?', '=', '#', '%']))
    
    safe_search_enforcer = SafeSearchEnforcer(enabled=True)
    
    # Create type-specific search URLs
    if search_type == 'images':
        if search_engine == 'google':
            original_url = f"https://www.google.com/search?q={search_query.replace(' ', '+')}&tbm=isch"
        else:  # bing
            original_url = f"https://www.bing.com/images/search?q={search_query.replace(' ', '+')}"
    elif search_type == 'videos':
        if search_engine == 'google':
            original_url = f"https://www.google.com/search?q={search_query.replace(' ', '+')}&tbm=vid"
        else:  # bing
            original_url = f"https://www.bing.com/videos/search?q={search_query.replace(' ', '+')}"
    else:  # web
        if search_engine == 'google':
            original_url = f"https://www.google.com/search?q={search_query.replace(' ', '+')}"
        else:  # bing
            original_url = f"https://www.bing.com/search?q={search_query.replace(' ', '+')}"
    
    # Apply safe search enforcement
    modified_url = safe_search_enforcer.enforce_safe_search(original_url)
    
    # The URL should be modified (unless it already had safe search)
    if not safe_search_enforcer.is_safe_search_enabled(original_url):
        assert modified_url != original_url, \
            f"Safe search enforcement should modify {search_type} search URL for {search_engine}, but URL remained unchanged: {original_url}"
    
    # Check for appropriate safe search parameters
    if search_engine == 'google':
        assert 'safe=active' in modified_url, \
            f"Google {search_type} search should contain 'safe=active' parameter: {modified_url}"
    elif search_engine == 'bing':
        assert 'adlt=strict' in modified_url, \
            f"Bing {search_type} search should contain 'adlt=strict' parameter: {modified_url}"
    
    # Verify that safe search is detected as enabled
    assert safe_search_enforcer.is_safe_search_enabled(modified_url), \
        f"Safe search should be detected as enabled in modified {search_type} URL: {modified_url}"


# Standalone test function for pytest discovery
@given(
    text=st.text(min_size=1, max_size=200).filter(lambda x: x.strip()),
    keyword=st.sampled_from(['adult', 'casino', 'violent', 'kill', 'porn', 'murder'])
)
@settings(max_examples=100, deadline=None)
def test_keyword_detection_accuracy_property_standalone(text, keyword):
    """
    Property 4: Keyword detection accuracy
    For any text containing blocked keywords, the keyword filter should detect 
    at least one inappropriate term.
    **Validates: Requirements 2.3**
    """
    # Assume valid inputs
    assume(len(text.strip()) > 0)
    
    keyword_filter = KeywordFilter()
    
    # Create text that definitely contains the keyword
    test_text = f"{text} {keyword} more text"
    
    # Scan for keywords
    detected_keywords = keyword_filter.scan_text(test_text)
    
    # The keyword should be detected
    assert len(detected_keywords) > 0, \
        f"Text containing '{keyword}' should detect at least one keyword, but detected: {detected_keywords}"
    
    # The specific keyword or a pattern matching it should be in the detected list
    keyword_found = False
    for detected in detected_keywords:
        if keyword in detected or detected in keyword or detected.replace('*', '') in keyword:
            keyword_found = True
            break
    
    assert keyword_found, \
        f"Expected to find '{keyword}' or related pattern in detected keywords: {detected_keywords}"
    
    # Test that is_query_safe returns False for text with inappropriate keywords
    is_safe = keyword_filter.is_query_safe(test_text)
    assert not is_safe, \
        f"Text containing '{keyword}' should not be considered safe, but is_query_safe returned: {is_safe}"


def test_safe_search_enforcer_import():
    """Test that SafeSearchEnforcer can be imported and instantiated"""
    safe_search_enforcer = SafeSearchEnforcer()
    assert safe_search_enforcer is not None
    assert isinstance(safe_search_enforcer, SafeSearchEnforcer)


def test_keyword_filter_import():
    """Test that KeywordFilter can be imported and instantiated"""
    keyword_filter = KeywordFilter()
    assert keyword_filter is not None
    assert isinstance(keyword_filter, KeywordFilter)


class TestConfigurationPersistenceProperties:
    """Property-based tests for configuration persistence functionality"""
    
    def setup_method(self):
        """Set up test fixtures"""
        import tempfile
        import shutil
        
        # Create a temporary directory for test configurations
        self.test_config_dir = tempfile.mkdtemp()
        
        # Import ConfigurationManager here to avoid import issues
        from wizard.utils.content_filter import ConfigurationManager
        self.config_manager = ConfigurationManager(config_dir=self.test_config_dir)
    
    def teardown_method(self):
        """Clean up test fixtures"""
        import shutil
        if hasattr(self, 'test_config_dir') and os.path.exists(self.test_config_dir):
            shutil.rmtree(self.test_config_dir)
    
    @given(
        enabled=st.booleans(),
        filtering_level=st.sampled_from(['strict', 'moderate', 'permissive']),
        age_profile=st.sampled_from(['child', 'teen', 'adult']),
        safe_search_enabled=st.booleans(),
        custom_blacklist=st.lists(st.text(min_size=1, max_size=50).filter(lambda x: '.' in x and len(x.split('.')) >= 2), min_size=0, max_size=10),
        custom_whitelist=st.lists(st.text(min_size=1, max_size=50).filter(lambda x: '.' in x and len(x.split('.')) >= 2), min_size=0, max_size=10),
        blocked_categories=st.lists(st.sampled_from(['adult', 'violence', 'gambling', 'drugs', 'hate_speech', 'malware', 'phishing']), min_size=1, max_size=7, unique=True),
        cache_size=st.integers(min_value=10, max_value=10000),
        timeout_ms=st.integers(min_value=10, max_value=5000),
        keyword_severity_threshold=st.integers(min_value=1, max_value=3),
        fuzzy_similarity_threshold=st.floats(min_value=0.1, max_value=1.0),
        log_blocked_attempts=st.booleans(),
        enable_statistics=st.booleans()
    )
    @settings(max_examples=100, deadline=None)
    def test_configuration_persistence_property(self, enabled, filtering_level, age_profile, safe_search_enabled,
                                              custom_blacklist, custom_whitelist, blocked_categories, cache_size,
                                              timeout_ms, keyword_severity_threshold, fuzzy_similarity_threshold,
                                              log_blocked_attempts, enable_statistics):
        """
        Property 6: Configuration persistence
        For any configuration change, the settings should be saved and restored correctly 
        after application restart.
        **Validates: Requirements 7.5**
        """
        from wizard.utils.content_filter import FilterConfig, FilterLevel, AgeProfile, ContentCategory
        
        # Assume valid inputs
        assume(len(set(custom_blacklist) & set(custom_whitelist)) == 0)  # No conflicts between lists
        assume(all(domain.strip() and '.' in domain for domain in custom_blacklist + custom_whitelist))
        
        # Create a configuration with the generated values
        original_config = FilterConfig()
        original_config.enabled = enabled
        original_config.filtering_level = FilterLevel(filtering_level)
        original_config.age_profile = AgeProfile(age_profile)
        original_config.safe_search_enabled = safe_search_enabled
        original_config.custom_blacklist = list(custom_blacklist)  # Ensure it's a list
        original_config.custom_whitelist = list(custom_whitelist)  # Ensure it's a list
        original_config.blocked_categories = [ContentCategory(cat) for cat in blocked_categories]
        original_config.performance_cache_size = cache_size
        original_config.performance_timeout_ms = timeout_ms
        original_config.keyword_severity_threshold = keyword_severity_threshold
        original_config.fuzzy_similarity_threshold = fuzzy_similarity_threshold
        original_config.log_blocked_attempts = log_blocked_attempts
        original_config.enable_statistics = enable_statistics
        
        # Validate the configuration is valid before testing
        validation_errors = original_config.validate()
        assume(len(validation_errors) == 0)
        
        # Save the configuration
        save_success = self.config_manager.save_config(original_config)
        assert save_success, "Configuration should be saved successfully"
        
        # Load the configuration back
        loaded_config = self.config_manager.load_config()
        assert loaded_config is not None, "Configuration should be loaded successfully"
        
        # Verify all settings are preserved correctly
        assert loaded_config.enabled == original_config.enabled, \
            f"Enabled setting should be preserved: expected {original_config.enabled}, got {loaded_config.enabled}"
        
        assert loaded_config.filtering_level == original_config.filtering_level, \
            f"Filtering level should be preserved: expected {original_config.filtering_level}, got {loaded_config.filtering_level}"
        
        assert loaded_config.age_profile == original_config.age_profile, \
            f"Age profile should be preserved: expected {original_config.age_profile}, got {loaded_config.age_profile}"
        
        assert loaded_config.safe_search_enabled == original_config.safe_search_enabled, \
            f"Safe search setting should be preserved: expected {original_config.safe_search_enabled}, got {loaded_config.safe_search_enabled}"
        
        assert set(loaded_config.custom_blacklist) == set(original_config.custom_blacklist), \
            f"Custom blacklist should be preserved: expected {set(original_config.custom_blacklist)}, got {set(loaded_config.custom_blacklist)}"
        
        assert set(loaded_config.custom_whitelist) == set(original_config.custom_whitelist), \
            f"Custom whitelist should be preserved: expected {set(original_config.custom_whitelist)}, got {set(loaded_config.custom_whitelist)}"
        
        assert set(loaded_config.blocked_categories) == set(original_config.blocked_categories), \
            f"Blocked categories should be preserved: expected {set(original_config.blocked_categories)}, got {set(loaded_config.blocked_categories)}"
        
        assert loaded_config.performance_cache_size == original_config.performance_cache_size, \
            f"Cache size should be preserved: expected {original_config.performance_cache_size}, got {loaded_config.performance_cache_size}"
        
        assert loaded_config.performance_timeout_ms == original_config.performance_timeout_ms, \
            f"Timeout should be preserved: expected {original_config.performance_timeout_ms}, got {loaded_config.performance_timeout_ms}"
        
        assert loaded_config.keyword_severity_threshold == original_config.keyword_severity_threshold, \
            f"Keyword severity threshold should be preserved: expected {original_config.keyword_severity_threshold}, got {loaded_config.keyword_severity_threshold}"
        
        assert abs(loaded_config.fuzzy_similarity_threshold - original_config.fuzzy_similarity_threshold) < 0.001, \
            f"Fuzzy similarity threshold should be preserved: expected {original_config.fuzzy_similarity_threshold}, got {loaded_config.fuzzy_similarity_threshold}"
        
        assert loaded_config.log_blocked_attempts == original_config.log_blocked_attempts, \
            f"Log blocked attempts setting should be preserved: expected {original_config.log_blocked_attempts}, got {loaded_config.log_blocked_attempts}"
        
        assert loaded_config.enable_statistics == original_config.enable_statistics, \
            f"Enable statistics setting should be preserved: expected {original_config.enable_statistics}, got {loaded_config.enable_statistics}"
        
        # Test that the loaded configuration is still valid
        loaded_validation_errors = loaded_config.validate()
        assert len(loaded_validation_errors) == 0, \
            f"Loaded configuration should be valid, but got errors: {loaded_validation_errors}"


# Standalone test function for pytest discovery
@given(
    enabled=st.booleans(),
    filtering_level=st.sampled_from(['strict', 'moderate', 'permissive']),
    age_profile=st.sampled_from(['child', 'teen', 'adult']),
    safe_search_enabled=st.booleans(),
    custom_blacklist=st.lists(st.text(min_size=1, max_size=50).filter(lambda x: '.' in x and len(x.split('.')) >= 2), min_size=0, max_size=10),
    custom_whitelist=st.lists(st.text(min_size=1, max_size=50).filter(lambda x: '.' in x and len(x.split('.')) >= 2), min_size=0, max_size=10),
    blocked_categories=st.lists(st.sampled_from(['adult', 'violence', 'gambling', 'drugs', 'hate_speech', 'malware', 'phishing']), min_size=1, max_size=7, unique=True),
    cache_size=st.integers(min_value=10, max_value=10000),
    timeout_ms=st.integers(min_value=10, max_value=5000),
    keyword_severity_threshold=st.integers(min_value=1, max_value=3),
    fuzzy_similarity_threshold=st.floats(min_value=0.1, max_value=1.0),
    log_blocked_attempts=st.booleans(),
    enable_statistics=st.booleans()
)
@settings(max_examples=100, deadline=None)
def test_configuration_persistence_property_standalone(enabled, filtering_level, age_profile, safe_search_enabled,
                                                     custom_blacklist, custom_whitelist, blocked_categories, cache_size,
                                                     timeout_ms, keyword_severity_threshold, fuzzy_similarity_threshold,
                                                     log_blocked_attempts, enable_statistics):
    """
    Property 6: Configuration persistence
    For any configuration change, the settings should be saved and restored correctly 
    after application restart.
    **Validates: Requirements 7.5**
    """
    import tempfile
    import shutil
    from wizard.utils.content_filter import FilterConfig, FilterLevel, AgeProfile, ContentCategory, ConfigurationManager
    
    # Assume valid inputs
    assume(len(set(custom_blacklist) & set(custom_whitelist)) == 0)  # No conflicts between lists
    assume(all(domain.strip() and '.' in domain for domain in custom_blacklist + custom_whitelist))
    
    # Create a temporary directory for test configurations
    test_config_dir = tempfile.mkdtemp()
    
    try:
        config_manager = ConfigurationManager(config_dir=test_config_dir)
        
        # Create a configuration with the generated values
        original_config = FilterConfig()
        original_config.enabled = enabled
        original_config.filtering_level = FilterLevel(filtering_level)
        original_config.age_profile = AgeProfile(age_profile)
        original_config.safe_search_enabled = safe_search_enabled
        original_config.custom_blacklist = list(custom_blacklist)  # Ensure it's a list
        original_config.custom_whitelist = list(custom_whitelist)  # Ensure it's a list
        original_config.blocked_categories = [ContentCategory(cat) for cat in blocked_categories]
        original_config.performance_cache_size = cache_size
        original_config.performance_timeout_ms = timeout_ms
        original_config.keyword_severity_threshold = keyword_severity_threshold
        original_config.fuzzy_similarity_threshold = fuzzy_similarity_threshold
        original_config.log_blocked_attempts = log_blocked_attempts
        original_config.enable_statistics = enable_statistics
        
        # Validate the configuration is valid before testing
        validation_errors = original_config.validate()
        assume(len(validation_errors) == 0)
        
        # Save the configuration
        save_success = config_manager.save_config(original_config)
        assert save_success, "Configuration should be saved successfully"
        
        # Load the configuration back
        loaded_config = config_manager.load_config()
        assert loaded_config is not None, "Configuration should be loaded successfully"
        
        # Verify all settings are preserved correctly
        assert loaded_config.enabled == original_config.enabled, \
            f"Enabled setting should be preserved: expected {original_config.enabled}, got {loaded_config.enabled}"
        
        assert loaded_config.filtering_level == original_config.filtering_level, \
            f"Filtering level should be preserved: expected {original_config.filtering_level}, got {loaded_config.filtering_level}"
        
        assert loaded_config.age_profile == original_config.age_profile, \
            f"Age profile should be preserved: expected {original_config.age_profile}, got {loaded_config.age_profile}"
        
        assert loaded_config.safe_search_enabled == original_config.safe_search_enabled, \
            f"Safe search setting should be preserved: expected {original_config.safe_search_enabled}, got {loaded_config.safe_search_enabled}"
        
        assert set(loaded_config.custom_blacklist) == set(original_config.custom_blacklist), \
            f"Custom blacklist should be preserved: expected {set(original_config.custom_blacklist)}, got {set(loaded_config.custom_blacklist)}"
        
        assert set(loaded_config.custom_whitelist) == set(original_config.custom_whitelist), \
            f"Custom whitelist should be preserved: expected {set(original_config.custom_whitelist)}, got {set(loaded_config.custom_whitelist)}"
        
        assert set(loaded_config.blocked_categories) == set(original_config.blocked_categories), \
            f"Blocked categories should be preserved: expected {set(original_config.blocked_categories)}, got {set(loaded_config.blocked_categories)}"
        
        assert loaded_config.performance_cache_size == original_config.performance_cache_size, \
            f"Cache size should be preserved: expected {original_config.performance_cache_size}, got {loaded_config.performance_cache_size}"
        
        assert loaded_config.performance_timeout_ms == original_config.performance_timeout_ms, \
            f"Timeout should be preserved: expected {original_config.performance_timeout_ms}, got {loaded_config.performance_timeout_ms}"
        
        assert loaded_config.keyword_severity_threshold == original_config.keyword_severity_threshold, \
            f"Keyword severity threshold should be preserved: expected {original_config.keyword_severity_threshold}, got {loaded_config.keyword_severity_threshold}"
        
        assert abs(loaded_config.fuzzy_similarity_threshold - original_config.fuzzy_similarity_threshold) < 0.001, \
            f"Fuzzy similarity threshold should be preserved: expected {original_config.fuzzy_similarity_threshold}, got {loaded_config.fuzzy_similarity_threshold}"
        
        assert loaded_config.log_blocked_attempts == original_config.log_blocked_attempts, \
            f"Log blocked attempts setting should be preserved: expected {original_config.log_blocked_attempts}, got {loaded_config.log_blocked_attempts}"
        
        assert loaded_config.enable_statistics == original_config.enable_statistics, \
            f"Enable statistics setting should be preserved: expected {original_config.enable_statistics}, got {loaded_config.enable_statistics}"
        
        # Test that the loaded configuration is still valid
        loaded_validation_errors = loaded_config.validate()
        assert len(loaded_validation_errors) == 0, \
            f"Loaded configuration should be valid, but got errors: {loaded_validation_errors}"
    
    finally:
        # Clean up temporary directory
        if os.path.exists(test_config_dir):
            shutil.rmtree(test_config_dir)