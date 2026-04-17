#!/usr/bin/env python3
"""
Text-to-Speech Engine for Wizard Voice Assistant
"""

import pyttsx3
import pythoncom
import threading

class TTSEngine:
    def __init__(self):
        """Initialize the TTS engine properties state without locking SAPI5 to main thread"""
        self.rate = 150
        self.volume = 0.9
        self.gender = 'female'
        
        # We don't initialize the engine here because COM objects (like SAPI5) 
        # get corrupted if initialized on the main thread but run on background threads.
        
    def _create_engine(self):
        """Creates a fresh engine instance securely bound to the current thread"""
        pythoncom.CoInitialize()
        engine = pyttsx3.init()
        engine.setProperty('rate', self.rate)
        engine.setProperty('volume', self.volume)
        
        # Apply voice
        voices = engine.getProperty('voices')
        if self.gender == 'female':
            for voice in voices:
                if "Zira" in voice.name or "female" in voice.name.lower():
                    engine.setProperty('voice', voice.id)
                    break
            else:
                if len(voices) > 1:
                    engine.setProperty('voice', voices[1].id)
        else:
            engine.setProperty('voice', voices[0].id)
            
        return engine
    
    def speak(self, text, **kwargs):
        """Speak the given text safely on the calling thread"""
        print(f'Speaking: {text}')
        try:
            # Create a localized engine to avoid inter-thread COM locking
            engine = self._create_engine()
            engine.say(text)
            engine.runAndWait()
        except Exception as e:
            print(f"TTS Engine Error: {e}")
    
    def set_voice(self, gender='female'):
        """Set voice gender globally"""
        self.gender = gender

# Global instance
tts = TTSEngine()

