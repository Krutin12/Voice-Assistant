"""
Language Manager for Wizard Voice Assistant
Handles language detection and normalization for multilingual support.
"""

from langdetect import detect, detect_langs
from langdetect.lang_detect_exception import LangDetectException
import logging
from typing import Optional

logger = logging.getLogger(__name__)

class LanguageManager:
    """ Manages language detection and language-specific processing """
    
    SUPPORTED_LANGUAGES = {
        'en': 'English',
        'gu': 'Gujarati'
    }

    @staticmethod
    def detect_language(text: str) -> str:
        """ Detect the language of the given text with script hints and mixed support """
        if not text or len(text.strip()) < 2:
            return 'en'
            
        text_lower = text.lower()
        
        # Script analysis
        has_gujarati_script = any('\u0A80' <= char <= '\u0AFF' for char in text)
        has_latin_script = any('a' <= char <= 'z' for char in text_lower)
        
        # Transliteration hints (common words)
        gu_trans = [
            'kem cho', 'aabhar', 'su che', 'tame', 'naste', 'maru naam', 
            'shu', 'kyare', 'ketla', 'kaye', 'halat', 'kaise', 
            'khabar che', 'lya', 'bhai', 'halne', 'mori rama', 
            'lo', 'ne', 'su lya', 'su karas', 'pela', 
            'vagad', 'vagaad', 'vagado', 'bagad', 'bagador', 'baja', 'bajado', 'shodho', 'vise', 'vishe', 'per', 'par',
            'lo', 'ne', 'pan', 'nu', 'no', 'na', 'ni', 'thi', 'karvu', 'karo', 'karas'
        ]
        
        has_gu_trans = any(word in text_lower for word in gu_trans)
        
        # Detection logic
        if has_gujarati_script and has_latin_script:
            # Check ratio or just return mixed
            return 'gu' # For now, keep as 'gu' but we could support 'mixed'
            
        if has_gujarati_script:
            return 'gu'
            
        if has_gu_trans:
            return 'gu'
            
        try:
            # Langdetect is quite good for full sentences
            results = detect_langs(text)
            # results is a list of Language objects (lang, prob)
            if results:
                primary = results[0]
                if primary.lang == 'gu' or primary.lang == 'hi':
                    return 'gu'
                
                # Check for significant Gujarati/Hindi probability in case of mix
                for res in results[1:]:
                    if (res.lang == 'gu' or res.lang == 'hi') and res.prob > 0.3:
                        return 'gu' # Prioritize Gujarati if significant
                        
                if primary.lang in LanguageManager.SUPPORTED_LANGUAGES:
                    return primary.lang
                    
            return 'en'
        except Exception:
            return 'en'

    @staticmethod
    def is_mixed(text: str) -> bool:
        """Check if the text contains a mix of English and Gujarati"""
        has_gujarati = any('\u0A80' <= char <= '\u0AFF' for char in text)
        # Check for English words in Gujarati script or Latin characters alongside Gujarati
        has_latin = any('a' <= char <= 'z' for char in text.lower())
        return has_gujarati and has_latin

    @staticmethod
    def detect_dialect(text: str) -> Optional[str]:
        """Detect specific Gujarati dialects"""
        text_lower = text.lower()
        kathiyavadi_words = ['lya', 'bhai', 'halne', 'gando', 'mori rama', 'khabar che', 'toke', 'hodo', 'danda', 'reva do']
        surati_words = ['lo', 'ne', 'su lya', 'su karas', 'pela', 'kaj', 'poti', 'su kare']
        
        if any(word in text_lower for word in kathiyavadi_words):
            return 'kathiyavadi'
        if any(word in text_lower for word in surati_words):
            return 'surati'
        return None

    @staticmethod
    def get_language_name(lang_code: str) -> str:
        """ Get the human-readable name of a language code """
        return LanguageManager.SUPPORTED_LANGUAGES.get(lang_code, 'English')
