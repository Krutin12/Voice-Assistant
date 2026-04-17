"""
Speech Normalizer Utility for Wizard Voice Assistant
Handles speech disorder accessibility by normalizing repetitions and broken words.
"""

import re

class SpeechNormalizer:
    @staticmethod
    def normalize(text: str) -> str:
        """
        Normalizes speech input:
        1. Collapses repeated identical words or parts of words.
        2. Cleans up stuttering/repetitions (e.g., 'g-g-google' -> 'google').
        3. Joins broken compound words.
        """
        if not text:
            return ""

        text = text.lower().strip()

        # 1. Handle letter repetitions with dashes (e.g., "g-g-goo-google")
        # Matches patterns like "g-" repeated and then the word
        text = re.sub(r'\b([a-z])-\1-?([a-z]*)', r'\1\2', text)
        text = re.sub(r'\b([a-z])-([a-z]{2,})', r'\1\2', text) # "s-spotify" -> "spotify"

        # 2. Handle repeated identical words (e.g., "the the google google")
        words = text.split()
        if not words:
            return ""
            
        normalized_words = []
        last_word = ""
        for word in words:
            # Clean punctuation from comparison
            clean_word = re.sub(r'[^\w\s]', '', word)
            if clean_word != last_word:
                normalized_words.append(word)
                last_word = clean_word
        
        text = " ".join(normalized_words)

        # 3. Handle specific common broken phrases for this assistant
        replacements = {
            "shut down": "shutdown",
            "turn off": "shutdown",
            "volume up": "volume up",
            "volume down": "volume down",
            "set volume": "set volume"
        }
        
        for key, val in replacements.items():
            if key in text:
                text = text.replace(key, val)

        return text

    @staticmethod
    def predict_intended_command(text: str, command_list: list) -> str:
        """Simple prefix/fuzzy matching to predict command if input is very messy."""
        # This can be expanded later
        return text
