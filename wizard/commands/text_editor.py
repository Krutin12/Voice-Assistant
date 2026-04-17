"""
Text Editor Module
Handles notepad and Word operations including opening and writing text
"""

import subprocess
import time
import pyautogui
import os
from pathlib import Path
import pyperclip

def open_notepad():
    """Open Notepad application"""
    try:
        subprocess.Popen(['notepad.exe'])
        time.sleep(0.5)  # Give it time to open
        return "Opening Notepad"
    except Exception as e:
        return f"Error opening Notepad: {str(e)}"

def write_in_notepad(text):
    """Open Notepad and write text"""
    try:
        if not text:
            return "What would you like me to write?"
        
        # Open notepad
        subprocess.Popen(['notepad.exe'])
        time.sleep(1)  # Wait for notepad to open
        
        # Type the text using clipboard for better reliability and Unicode support
        pyperclip.copy(text)
        pyautogui.hotkey('ctrl', 'v')
        return f"Written to Notepad: {text[:50]}..."
    except Exception as e:
        return f"Error writing to Notepad: {str(e)}"

def create_note_file(text, filename='note.txt'):
    """Create a new text file with content"""
    try:
        if not text:
            return "What would you like me to write in the note?"
        
        # Get Documents folder
        documents_path = Path.home() / 'Documents'
        file_path = documents_path / filename
        
        # Write to file
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(text)
        
        # Open in notepad
        subprocess.Popen(['notepad.exe', str(file_path)])
        return f"Created note file {filename} with your text"
    except Exception as e:
        return f"Error creating note file: {str(e)}"

def open_word():
    """Open Microsoft Word"""
    try:
        # Try common Word installation paths
        word_paths = [
            r"C:\Program Files\Microsoft Office\root\Office16\WINWORD.EXE",
            r"C:\Program Files (x86)\Microsoft Office\root\Office16\WINWORD.EXE",
            r"C:\Program Files\Microsoft Office\Office16\WINWORD.EXE",
            r"C:\Program Files (x86)\Microsoft Office\Office16\WINWORD.EXE",
        ]
        
        for path in word_paths:
            if os.path.exists(path):
                subprocess.Popen([path])
                time.sleep(1)
                return "Opening Microsoft Word"
        
        # Try to find it in PATH
        try:
            subprocess.Popen(['winword.exe'])
            time.sleep(1)
            return "Opening Microsoft Word"
        except:
            return "Microsoft Word not found. Please make sure it's installed."
            
    except Exception as e:
        return f"Error opening Word: {str(e)}"

def write_in_word(text):
    """Open Word and write text"""
    try:
        if not text:
            return "What would you like me to write in Word?"
        
        # Open Word
        word_paths = [
            r"C:\Program Files\Microsoft Office\root\Office16\WINWORD.EXE",
            r"C:\Program Files (x86)\Microsoft Office\root\Office16\WINWORD.EXE",
            r"C:\Program Files\Microsoft Office\Office16\WINWORD.EXE",
            r"C:\Program Files (x86)\Microsoft Office\Office16\WINWORD.EXE",
        ]
        
        opened = False
        for path in word_paths:
            if os.path.exists(path):
                subprocess.Popen([path])
                opened = True
                break
        
        if not opened:
            try:
                subprocess.Popen(['winword.exe'])
                opened = True
            except:
                return "Microsoft Word not found. Please make sure it's installed."
        
        # Wait for Word to open
        time.sleep(2)
        
        # Type the text using clipboard for better reliability and Unicode support
        pyperclip.copy(text)
        pyautogui.hotkey('ctrl', 'v')
        return f"Written to Word: {text[:50]}..."
    except Exception as e:
        return f"Error writing to Word: {str(e)}"

