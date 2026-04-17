"""
System Control Module
Handles system operations like opening apps, shutdown, restart, lock, screenshots
"""

import subprocess
import os
import pyautogui
import psutil
from pathlib import Path

# Import the dynamic app discovery engine
try:
    from wizard.commands.app_discovery import AppDiscovery, open_any_app
    _app_discovery = None
    
    def _get_app_discovery():
        """Lazy-load the app discovery engine (one-time scan)."""
        global _app_discovery
        if _app_discovery is None:
            _app_discovery = AppDiscovery(extra_apps=get_app_paths())
        return _app_discovery
except ImportError:
    def _get_app_discovery():
        return None

# Application mappings (kept as fallback)
def get_app_paths():
    """Get application paths with user-specific paths resolved"""
    user_home = str(Path.home())
    return {
        'chrome': r'C:\Program Files\Google\Chrome\Application\chrome.exe',
        'firefox': r'C:\Program Files\Mozilla Firefox\firefox.exe',
        'edge': r'C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe',
        'calculator': 'calc.exe',
        'notepad': 'notepad.exe',
        'paint': 'mspaint.exe',
        'cmd': 'cmd.exe',
        'powershell': 'powershell.exe',
        'word': 'winword.exe',
        'excel': 'excel.exe',
        'powerpoint': 'powerpnt.exe',
        'spotify': os.path.join(user_home, r'AppData\Roaming\Spotify\Spotify.exe'),
    }

APP_PATHS = get_app_paths()

def open_application(app_name):
    """Open any Windows application by name using dynamic discovery + fuzzy matching."""
    try:
        app_name = app_name.lower().strip()
        
        # Strategy 1: Use AppDiscovery to find and launch ANY installed app
        discovery = _get_app_discovery()
        if discovery is not None:
            success, message = open_any_app(app_name, discovery)
            if success:
                return message
        
        # Strategy 2: Check hardcoded mapping
        path = APP_PATHS.get(app_name)
        
        # Check if already running and bring to front
        for proc in psutil.process_iter(['pid', 'name']):
            try:
                if app_name in proc.info['name'].lower():
                    try:
                        import pygetwindow as gw
                        win = gw.getWindowsWithTitle(app_name.capitalize())
                        if win:
                            win[0].activate()
                            return f"{app_name} is already open and now in focus."
                    except:
                        pass
            except:
                pass

        if path:
            if os.path.exists(path) or path.endswith('.exe'):
                subprocess.Popen([path])
                return f"Opening {app_name}"
            else:
                return f"Could not find {app_name} at {path}."
        else:
            # Strategy 3: Try system PATH / Windows start command
            try:
                subprocess.Popen(f'start "" "{app_name}"', shell=True)
                return f"Opening {app_name}"
            except:
                return f"Could not open {app_name}. Please specify the full application name."
                
    except Exception as e:
        return f"Error opening application: {str(e)}"

def close_application(app_name):
    """Close an application by name"""
    try:
        app_name = app_name.lower().strip()
        
        # Find and terminate the process
        closed = False
        for proc in psutil.process_iter(['pid', 'name']):
            try:
                proc_name = proc.info['name'].lower()
                if app_name in proc_name or proc_name.startswith(app_name):
                    proc.terminate()
                    closed = True
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
        
        if closed:
            return f"Closed {app_name}"
        else:
            return f"Could not find {app_name} to close"
            
    except Exception as e:
        return f"Error closing application: {str(e)}"

def shutdown_computer():
    """Shutdown the computer"""
    try:
        os.system('shutdown /s /t 10')
        return "Computer will shutdown in 10 seconds"
    except Exception as e:
        return f"Error shutting down: {str(e)}"

def restart_computer():
    """Restart the computer"""
    try:
        os.system('shutdown /r /t 10')
        return "Computer will restart in 10 seconds"
    except Exception as e:
        return f"Error restarting: {str(e)}"

def lock_computer():
    """Lock the computer"""
    try:
        os.system('rundll32.exe user32.dll,LockWorkStation')
        return "Computer locked"
    except Exception as e:
        return f"Error locking computer: {str(e)}"

def take_screenshot():
    """Take a screenshot and save it"""
    try:
        # Get Pictures folder
        pictures_path = Path.home() / 'Pictures'
        if not pictures_path.exists():
            pictures_path = Path.home() / 'Documents'
        
        # Create filename with timestamp
        from datetime import datetime
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = pictures_path / f'screenshot_{timestamp}.png'
        
        # Take screenshot
        screenshot = pyautogui.screenshot()
        screenshot.save(str(filename))
        
        return f"Screenshot saved to {filename.name}"
    except Exception as e:
        return f"Error taking screenshot: {str(e)}"

def minimize_all_windows():
    """Minimize all open windows (Show Desktop)"""
    try:
        pyautogui.hotkey('win', 'd')
        return "Minimizing all windows"
    except Exception as e:
        return f"Error minimizing windows: {str(e)}"

def refresh_page():
    """Press F5 to refresh current page/window"""
    try:
        pyautogui.press('f5')
        return "Refreshing"
    except Exception as e:
        return f"Error refreshing: {str(e)}"

def press_enter():
    """Simulate pressing the Enter key"""
    try:
        pyautogui.press('enter')
        return "Pressed Enter"
    except Exception as e:
        return f"Error pressing enter: {str(e)}"

def switch_window():
    """Switch to the next window (Alt+Tab)"""
    try:
        pyautogui.hotkey('alt', 'tab')
        return "Switching window"
    except Exception as e:
        return f"Error switching window: {str(e)}"

def select_all():
    """Select all text/items (Ctrl+A)"""
    try:
        pyautogui.hotkey('ctrl', 'a')
        return "Selecting all"
    except Exception as e:
        return f"Error selecting all: {str(e)}"

def copy_text():
    """Copy selected text/items (Ctrl+C)"""
    try:
        pyautogui.hotkey('ctrl', 'c')
        return "Copied"
    except Exception as e:
        return f"Error copying: {str(e)}"

def paste_text():
    """Paste from clipboard (Ctrl+V)"""
    try:
        pyautogui.hotkey('ctrl', 'v')
        return "Pasted"
    except Exception as e:
        return f"Error pasting: {str(e)}"

def play_spotify_music(query):
    """Search and play a song on Spotify with reliable autoplay using simulated clicks"""
    try:
        import time
        import webbrowser
        
        # Normalize query
        query_clean = query.strip()
        query_encoded = query_clean.replace(' ', '%20')
        
        # Step 1: Open Spotify desktop app with a search URI
        spotify_uri = f"spotify:search:{query_encoded}"
        
        try:
            os.startfile(spotify_uri)
            # Give Spotify time to open/focus and load search results
            time.sleep(6)
            
            # Step 2: Navigate to the first song result and play it
            # Press Tab multiple times to reach the first song in search results
            # Spotify's search page: focus lands on search bar first, then filters, then results
            for _ in range(3):
                pyautogui.press('tab')
                time.sleep(0.2)
            
            # Press Enter to select/play the top result
            pyautogui.press('enter')
            time.sleep(1.5)
            
            # Double-click Enter to ensure it starts playing (some Spotify versions need this)
            pyautogui.press('enter')
            time.sleep(0.5)
            
            # Fallback: use Spotify's play shortcut (Space) to force play
            pyautogui.press('space')
            
            return f"Playing '{query_clean}' on Spotify"
        except Exception:
            # Fallback: open Spotify web player with the search query
            webbrowser.open(f"https://open.spotify.com/search/{query_encoded}")
            time.sleep(5)
            
            # Try to click on the first result on Spotify Web
            # Tab through to the first playable result and click
            for _ in range(5):
                pyautogui.press('tab')
                time.sleep(0.3)
            pyautogui.press('enter')
            
            return f"Opening Spotify to search and play '{query_clean}'"
            
    except Exception as e:
        return f"Error playing Spotify music: {str(e)}"

def play_pause_media():
    """Toggle play/pause for current media (global) - works for Spotify, YouTube, and any media player"""
    try:
        # First try: use the global media play/pause key (works for Spotify desktop, VLC, etc.)
        pyautogui.press('playpause')
        return "Toggling media playback"
    except Exception as e:
        return f"Error toggling playback: {str(e)}"

def next_media():
    """Skip to next media track (global) - works for Spotify, YouTube, and any media player"""
    try:
        pyautogui.press('nexttrack')
        return "Skipping to next track"
    except Exception as e:
        return f"Error skipping track: {str(e)}"

def previous_media():
    """Go to previous media track (global) - works for Spotify, YouTube, and any media player"""
    try:
        pyautogui.press('prevtrack')
        return "Going to previous track"
    except Exception as e:
        return f"Error going to previous track: {str(e)}"


# ==========================================
# YouTube-Specific Controls (Browser-based)
# ==========================================

def youtube_play_pause():
    """Toggle play/pause on YouTube video using keyboard shortcut 'K'"""
    try:
        # YouTube's 'K' key is the play/pause toggle (works when player has focus)
        # First click on the page body to ensure focus is on the player
        import time
        pyautogui.press('k')
        return "Toggling YouTube video playback"
    except Exception as e:
        return f"Error toggling YouTube playback: {str(e)}"

def youtube_next_video():
    """Skip to next YouTube video using Shift+N shortcut"""
    try:
        import time
        # YouTube's Shift+N plays the next video in playlist/autoplay
        pyautogui.hotkey('shift', 'n')
        time.sleep(1)
        return "Playing next YouTube video"
    except Exception as e:
        return f"Error skipping to next YouTube video: {str(e)}"

def youtube_previous_video():
    """Go to previous YouTube video using Shift+P shortcut"""
    try:
        import time
        # YouTube's Shift+P plays the previous video in playlist
        pyautogui.hotkey('shift', 'p')
        time.sleep(1)
        return "Playing previous YouTube video"
    except Exception as e:
        return f"Error going to previous YouTube video: {str(e)}"

def youtube_fullscreen():
    """Toggle fullscreen on YouTube video using 'F' shortcut"""
    try:
        pyautogui.press('f')
        return "Toggling YouTube fullscreen"
    except Exception as e:
        return f"Error toggling YouTube fullscreen: {str(e)}"

def youtube_skip_ad():
    """Try to skip YouTube ad by clicking the Skip Ad button"""
    try:
        import time
        # Method 1: Tab to the Skip Ad button and press Enter
        # The Skip button is typically a few tabs from the video player
        for _ in range(5):
            pyautogui.press('tab')
            time.sleep(0.3)
        pyautogui.press('enter')
        time.sleep(0.5)
        
        # Method 2: Try pressing Escape to close overlay ads
        pyautogui.press('escape')
        
        return "Attempting to skip YouTube ad"
    except Exception as e:
        return f"Error skipping YouTube ad: {str(e)}"

def youtube_mute_unmute():
    """Toggle mute on YouTube video using 'M' shortcut"""
    try:
        pyautogui.press('m')
        return "Toggling YouTube mute"
    except Exception as e:
        return f"Error toggling YouTube mute: {str(e)}"

def youtube_seek_forward():
    """Seek forward 10 seconds in YouTube video using 'L' shortcut"""
    try:
        pyautogui.press('l')
        return "Seeking forward 10 seconds on YouTube"
    except Exception as e:
        return f"Error seeking forward: {str(e)}"

def youtube_seek_backward():
    """Seek backward 10 seconds in YouTube video using 'J' shortcut"""
    try:
        pyautogui.press('j')
        return "Seeking backward 10 seconds on YouTube"
    except Exception as e:
        return f"Error seeking backward: {str(e)}"


# ==========================================
# Spotify-Specific Controls (Desktop App)
# ==========================================

def spotify_next_track():
    """Skip to next track on Spotify using Ctrl+Right shortcut"""
    try:
        import time
        # Spotify desktop shortcut for next track
        pyautogui.hotkey('ctrl', 'right')
        time.sleep(0.5)
        return "Skipping to next Spotify track"
    except Exception as e:
        # Fallback: global media key
        try:
            pyautogui.press('nexttrack')
            return "Skipping to next track"
        except:
            return f"Error skipping Spotify track: {str(e)}"

def spotify_previous_track():
    """Go to previous track on Spotify using Ctrl+Left shortcut"""
    try:
        import time
        # Spotify desktop shortcut for previous track
        pyautogui.hotkey('ctrl', 'left')
        time.sleep(0.5)
        return "Going to previous Spotify track"
    except Exception as e:
        # Fallback: global media key
        try:
            pyautogui.press('prevtrack')
            return "Going to previous track"
        except:
            return f"Error going to previous Spotify track: {str(e)}"

def spotify_play_pause():
    """Toggle play/pause on Spotify using Space shortcut"""
    try:
        # Spotify uses Space to toggle play/pause when focused
        pyautogui.press('space')
        return "Toggling Spotify playback"
    except Exception as e:
        # Fallback: global media key
        try:
            pyautogui.press('playpause')
            return "Toggling media playback"
        except:
            return f"Error toggling Spotify playback: {str(e)}"

def spotify_shuffle_toggle():
    """Toggle shuffle on Spotify using Ctrl+S shortcut"""
    try:
        pyautogui.hotkey('ctrl', 's')
        return "Toggling Spotify shuffle"
    except Exception as e:
        return f"Error toggling Spotify shuffle: {str(e)}"

def spotify_repeat_toggle():
    """Toggle repeat on Spotify using Ctrl+R shortcut"""
    try:
        pyautogui.hotkey('ctrl', 'r')
        return "Toggling Spotify repeat"
    except Exception as e:
        return f"Error toggling Spotify repeat: {str(e)}"


# ==========================================
# Smart Media Detection
# ==========================================

def _detect_active_media_app():
    """Detect which media application is currently in the foreground"""
    try:
        import pygetwindow as gw
        active_window = gw.getActiveWindow()
        if active_window:
            title = active_window.title.lower()
            if 'youtube' in title or 'youtube.com' in title:
                return 'youtube'
            elif 'spotify' in title:
                return 'spotify'
            elif 'vlc' in title:
                return 'vlc'
            elif 'music' in title:
                return 'music'
    except:
        pass
    return 'unknown'

def smart_next():
    """Intelligently skip to next track/video based on active media app"""
    app = _detect_active_media_app()
    if app == 'youtube':
        return youtube_next_video()
    elif app == 'spotify':
        return spotify_next_track()
    else:
        return next_media()

def smart_previous():
    """Intelligently go to previous track/video based on active media app"""
    app = _detect_active_media_app()
    if app == 'youtube':
        return youtube_previous_video()
    elif app == 'spotify':
        return spotify_previous_track()
    else:
        return previous_media()

def smart_play_pause():
    """Intelligently toggle play/pause based on active media app"""
    app = _detect_active_media_app()
    if app == 'youtube':
        return youtube_play_pause()
    elif app == 'spotify':
        return spotify_play_pause()
    else:
        return play_pause_media()
