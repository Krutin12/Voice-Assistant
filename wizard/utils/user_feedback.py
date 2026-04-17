"""
User Feedback System for Content Filtering

This module provides user feedback and messaging functionality for the content filtering system.
It handles appropriate user messaging for blocked content and supports false positive reporting.
"""

from dataclasses import dataclass
from enum import Enum
from typing import List, Optional, Dict, Any
import datetime
from .content_filter import FilterResult, ContentCategory, AgeProfile, FilterConfig, FilterLogger


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
            age_profile: User's age profile for appropriate messaging
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
            age_profile: User's age profile
            
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
            age_profile: User's age profile for appropriate messaging
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
            age_profile: User's age profile
            
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
            user_feedback: User's explanation of why this is a false positive
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
            age_profile: User's age profile for appropriate messaging
            
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