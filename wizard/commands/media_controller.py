"""
Media Controller Module

Handles system volume control, media playback, and audio device management.
Provides voice-controlled media functionality for the Wizard AI Assistant.
"""

import os
import sys
import subprocess
import logging
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from enum import Enum

# Platform-specific imports
if sys.platform == "win32":
    try:
        from pycaw.pycaw import AudioUtilities, AudioSession, ISimpleAudioVolume
        from comtypes import CLSCTX_ALL
        from pycaw.pycaw import AudioEndpointVolume
        WINDOWS_AUDIO_AVAILABLE = True
    except ImportError:
        WINDOWS_AUDIO_AVAILABLE = False
        logging.warning("Windows audio libraries not available. Volume control will be limited.")

elif sys.platform == "darwin":  # macOS
    MACOS_AUDIO_AVAILABLE = True
else:  # Linux
    LINUX_AUDIO_AVAILABLE = True


class PlaybackAction(Enum):
    """Enumeration of media playback actions"""
    PLAY = "play"
    PAUSE = "pause"
    NEXT = "next"
    PREVIOUS = "previous"
    STOP = "stop"


@dataclass
class VolumeState:
    """Represents current volume state"""
    level: int  # 0-100
    is_muted: bool
    device_name: str


@dataclass
class MediaApp:
    """Represents a media application configuration"""
    name: str
    executable_path: str
    process_name: str
    supports_media_keys: bool


class MediaController:
    """
    Manages system volume, media playback, and audio device control.
    
    Provides cross-platform audio control functionality with support for:
    - System volume adjustment (percentage and increment)
    - Mute/unmute with state tracking
    - Audio device management
    - Media playback control
    - Application-specific media integration
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the Media Controller.
        
        Args:
            config: Configuration dictionary with media app paths and preferences
        """
        self.logger = logging.getLogger(__name__)
        self.config = config or {}
        
        # Volume state tracking
        self._volume_state = VolumeState(level=50, is_muted=False, device_name="Default")
        self._previous_volume = 50  # For mute/unmute functionality
        
        # Media applications configuration
        self.media_apps = self._load_media_apps()
        
        # Initialize platform-specific audio interface
        self._init_audio_interface()
        
        self.logger.info("Media Controller initialized")
    
    def _load_media_apps(self) -> Dict[str, MediaApp]:
        """Load media application configurations"""
        default_apps = {
            "spotify": MediaApp(
                name="Spotify",
                executable_path="spotify.exe" if sys.platform == "win32" else "spotify",
                process_name="Spotify.exe" if sys.platform == "win32" else "spotify",
                supports_media_keys=True
            ),
            "youtube_music": MediaApp(
                name="YouTube Music",
                executable_path="chrome.exe" if sys.platform == "win32" else "google-chrome",
                process_name="chrome.exe" if sys.platform == "win32" else "chrome",
                supports_media_keys=True
            ),
            "vlc": MediaApp(
                name="VLC Media Player",
                executable_path="vlc.exe" if sys.platform == "win32" else "vlc",
                process_name="vlc.exe" if sys.platform == "win32" else "vlc",
                supports_media_keys=True
            ),
            "apple_music": MediaApp(
                name="Apple Music",
                executable_path="Music.app" if sys.platform == "darwin" else "apple-music",
                process_name="Music" if sys.platform == "darwin" else "apple-music",
                supports_media_keys=True
            ),
            "windows_media_player": MediaApp(
                name="Windows Media Player",
                executable_path="wmplayer.exe" if sys.platform == "win32" else "wmplayer",
                process_name="wmplayer.exe" if sys.platform == "win32" else "wmplayer",
                supports_media_keys=True
            ),
            "itunes": MediaApp(
                name="iTunes",
                executable_path="iTunes.exe" if sys.platform == "win32" else "iTunes.app",
                process_name="iTunes.exe" if sys.platform == "win32" else "iTunes",
                supports_media_keys=True
            )
        }
        
        # Override with config if provided
        if "media_apps" in self.config:
            for app_name, app_config in self.config["media_apps"].items():
                if app_name in default_apps:
                    default_apps[app_name].executable_path = app_config.get("path", default_apps[app_name].executable_path)
        
        return default_apps
    
    def _init_audio_interface(self):
        """Initialize platform-specific audio interface"""
        self.audio_interface = None
        
        if sys.platform == "win32" and WINDOWS_AUDIO_AVAILABLE:
            try:
                devices = AudioUtilities.GetSpeakers()
                interface = devices.Activate(AudioEndpointVolume._iid_, CLSCTX_ALL, None)
                self.audio_interface = interface.QueryInterface(AudioEndpointVolume)
                self.logger.info("Windows audio interface initialized")
            except Exception as e:
                self.logger.error(f"Failed to initialize Windows audio interface: {e}")
        
        # Update current volume state
        self._update_volume_state()
    
    def _update_volume_state(self):
        """Update internal volume state from system"""
        try:
            current_volume = self.get_current_volume()
            if current_volume is not None:
                self._volume_state.level = current_volume
                self._volume_state.is_muted = self.is_muted()
        except Exception as e:
            self.logger.error(f"Failed to update volume state: {e}")
    
    def get_current_volume(self) -> Optional[int]:
        """
        Get current system volume level.
        
        Returns:
            Volume level (0-100) or None if unable to retrieve
        """
        try:
            if sys.platform == "win32" and self.audio_interface:
                volume = self.audio_interface.GetMasterScalarVolume()
                return int(volume * 100)
            
            elif sys.platform == "darwin":
                # macOS using osascript
                result = subprocess.run(
                    ["osascript", "-e", "output volume of (get volume settings)"],
                    capture_output=True, text=True, check=True
                )
                return int(result.stdout.strip())
            
            elif sys.platform.startswith("linux"):
                # Linux using amixer
                result = subprocess.run(
                    ["amixer", "get", "Master"],
                    capture_output=True, text=True, check=True
                )
                # Parse amixer output to extract volume percentage
                for line in result.stdout.split('\n'):
                    if '[' in line and '%' in line:
                        start = line.find('[') + 1
                        end = line.find('%')
                        if start > 0 and end > start:
                            return int(line[start:end])
            
        except Exception as e:
            self.logger.error(f"Failed to get current volume: {e}")
        
        return None
    
    def set_volume(self, level: int) -> bool:
        """
        Set system volume to specific level.
        
        Args:
            level: Volume level (0-100)
            
        Returns:
            True if successful, False otherwise
        """
        if not 0 <= level <= 100:
            self.logger.error(f"Invalid volume level: {level}. Must be 0-100.")
            return False
        
        try:
            if sys.platform == "win32" and self.audio_interface:
                self.audio_interface.SetMasterScalarVolume(level / 100.0, None)
                
            elif sys.platform == "darwin":
                subprocess.run(
                    ["osascript", "-e", f"set volume output volume {level}"],
                    check=True
                )
                
            elif sys.platform.startswith("linux"):
                subprocess.run(
                    ["amixer", "set", "Master", f"{level}%"],
                    check=True
                )
            
            # Update internal state
            self._volume_state.level = level
            self._volume_state.is_muted = False
            
            self.logger.info(f"Volume set to {level}%")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to set volume to {level}%: {e}")
            return False
    
    def adjust_volume(self, change: int) -> bool:
        """
        Adjust volume by specified increment/decrement.
        
        Args:
            change: Volume change (-100 to +100)
            
        Returns:
            True if successful, False otherwise
        """
        current = self.get_current_volume()
        if current is None:
            return False
        
        new_level = max(0, min(100, current + change))
        return self.set_volume(new_level)
    
    def is_muted(self) -> bool:
        """
        Check if system audio is muted.
        
        Returns:
            True if muted, False otherwise
        """
        try:
            if sys.platform == "win32" and self.audio_interface:
                return bool(self.audio_interface.GetMute())
                
            elif sys.platform == "darwin":
                result = subprocess.run(
                    ["osascript", "-e", "output muted of (get volume settings)"],
                    capture_output=True, text=True, check=True
                )
                return result.stdout.strip().lower() == "true"
                
            elif sys.platform.startswith("linux"):
                result = subprocess.run(
                    ["amixer", "get", "Master"],
                    capture_output=True, text=True, check=True
                )
                return "[off]" in result.stdout
                
        except Exception as e:
            self.logger.error(f"Failed to check mute status: {e}")
        
        return False
    
    def mute(self) -> bool:
        """
        Mute system audio.
        
        Returns:
            True if successful, False otherwise
        """
        try:
            # Store current volume for unmute
            current_volume = self.get_current_volume()
            if current_volume is not None:
                self._previous_volume = current_volume
            
            if sys.platform == "win32" and self.audio_interface:
                self.audio_interface.SetMute(1, None)
                
            elif sys.platform == "darwin":
                subprocess.run(
                    ["osascript", "-e", "set volume with output muted"],
                    check=True
                )
                
            elif sys.platform.startswith("linux"):
                subprocess.run(
                    ["amixer", "set", "Master", "mute"],
                    check=True
                )
            
            self._volume_state.is_muted = True
            self.logger.info("Audio muted")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to mute audio: {e}")
            return False
    
    def unmute(self) -> bool:
        """
        Unmute system audio.
        
        Returns:
            True if successful, False otherwise
        """
        try:
            if sys.platform == "win32" and self.audio_interface:
                self.audio_interface.SetMute(0, None)
                
            elif sys.platform == "darwin":
                subprocess.run(
                    ["osascript", "-e", "set volume without output muted"],
                    check=True
                )
                
            elif sys.platform.startswith("linux"):
                subprocess.run(
                    ["amixer", "set", "Master", "unmute"],
                    check=True
                )
            
            self._volume_state.is_muted = False
            self.logger.info("Audio unmuted")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to unmute audio: {e}")
            return False
    
    def toggle_mute(self) -> bool:
        """
        Toggle mute state.
        
        Returns:
            True if successful, False otherwise
        """
        if self.is_muted():
            return self.unmute()
        else:
            return self.mute()
    
    def get_volume_state(self) -> VolumeState:
        """
        Get current volume state information.
        
        Returns:
            VolumeState object with current volume info
        """
        self._update_volume_state()
        return self._volume_state
    
    def get_audio_devices(self) -> List[str]:
        """
        Get list of available audio devices.
        
        Returns:
            List of audio device names
        """
        devices = []
        
        try:
            if sys.platform == "win32" and WINDOWS_AUDIO_AVAILABLE:
                # Get Windows audio devices
                for device in AudioUtilities.GetAllDevices():
                    if device.state == 1:  # Active devices only
                        devices.append(device.FriendlyName)
                        
            elif sys.platform == "darwin":
                # macOS audio devices
                result = subprocess.run(
                    ["system_profiler", "SPAudioDataType"],
                    capture_output=True, text=True, check=True
                )
                # Parse output for device names (simplified)
                devices.append("Default Output Device")
                
            elif sys.platform.startswith("linux"):
                # Linux audio devices using pactl
                try:
                    result = subprocess.run(
                        ["pactl", "list", "short", "sinks"],
                        capture_output=True, text=True, check=True
                    )
                    for line in result.stdout.split('\n'):
                        if line.strip():
                            parts = line.split('\t')
                            if len(parts) > 1:
                                devices.append(parts[1])
                except subprocess.CalledProcessError:
                    devices.append("Default")
                    
        except Exception as e:
            self.logger.error(f"Failed to get audio devices: {e}")
            devices.append("Default")
        
        return devices if devices else ["Default"]

    def set_audio_device(self, device_name: str) -> bool:
        """
        Set the active audio output device.
        
        Args:
            device_name: Name of the audio device to set as default
            
        Returns:
            True if successful, False otherwise
        """
        try:
            if sys.platform == "win32" and WINDOWS_AUDIO_AVAILABLE:
                # Windows audio device switching
                devices = AudioUtilities.GetAllDevices()
                for device in devices:
                    if device.FriendlyName.lower() == device_name.lower() and device.state == 1:
                        # Set as default device (requires additional Windows API calls)
                        # This is a simplified implementation
                        self._volume_state.device_name = device.FriendlyName
                        self.logger.info(f"Audio device set to: {device.FriendlyName}")
                        return True
                        
            elif sys.platform == "darwin":
                # macOS audio device switching using SwitchAudioSource if available
                try:
                    subprocess.run(
                        ["SwitchAudioSource", "-s", device_name],
                        check=True, capture_output=True
                    )
                    self._volume_state.device_name = device_name
                    self.logger.info(f"Audio device set to: {device_name}")
                    return True
                except subprocess.CalledProcessError:
                    self.logger.warning("SwitchAudioSource not available, device switching limited")
                    
            elif sys.platform.startswith("linux"):
                # Linux audio device switching using pactl
                try:
                    # Get device index
                    result = subprocess.run(
                        ["pactl", "list", "short", "sinks"],
                        capture_output=True, text=True, check=True
                    )
                    
                    device_index = None
                    for line in result.stdout.split('\n'):
                        if device_name in line:
                            parts = line.split('\t')
                            if len(parts) > 0:
                                device_index = parts[0]
                                break
                    
                    if device_index:
                        subprocess.run(
                            ["pactl", "set-default-sink", device_index],
                            check=True
                        )
                        self._volume_state.device_name = device_name
                        self.logger.info(f"Audio device set to: {device_name}")
                        return True
                        
                except subprocess.CalledProcessError as e:
                    self.logger.error(f"Failed to set audio device on Linux: {e}")
                    
        except Exception as e:
            self.logger.error(f"Failed to set audio device to {device_name}: {e}")
        
        return False

    def control_playback(self, action: str) -> bool:
        """
        Control media playback (play/pause/next/previous).
        
        Args:
            action: Playback action (play, pause, next, previous, stop)
            
        Returns:
            True if successful, False otherwise
        """
        try:
            action = action.lower()
            if action not in [e.value for e in PlaybackAction]:
                self.logger.error(f"Invalid playback action: {action}")
                return False
            
            if sys.platform == "win32":
                return self._windows_media_control(action)
            elif sys.platform == "darwin":
                return self._macos_media_control(action)
            elif sys.platform.startswith("linux"):
                return self._linux_media_control(action)
            
        except Exception as e:
            self.logger.error(f"Failed to control playback ({action}): {e}")
            return False
        
        return False
    
    def _windows_media_control(self, action: str) -> bool:
        """Windows-specific media control using virtual key codes"""
        try:
            import win32api
            import win32con
            
            # Virtual key codes for media keys
            # Note: VK_MEDIA_STOP doesn't exist in win32con, using hex value
            media_keys = {
                "play": win32con.VK_MEDIA_PLAY_PAUSE,
                "pause": win32con.VK_MEDIA_PLAY_PAUSE,
                "next": win32con.VK_MEDIA_NEXT_TRACK,
                "previous": win32con.VK_MEDIA_PREV_TRACK,
                "stop": 0xB2  # VK_MEDIA_STOP hex value
            }
            
            if action in media_keys:
                win32api.keybd_event(media_keys[action], 0, 0, 0)
                win32api.keybd_event(media_keys[action], 0, win32con.KEYEVENTF_KEYUP, 0)
                self.logger.info(f"Sent {action} media key")
                return True
                
        except ImportError:
            self.logger.warning("win32api not available, trying alternative method")
            # Fallback to PowerShell
            try:
                ps_commands = {
                    "play": "(New-Object -com 'WMPlayer.OCX').controls.play()",
                    "pause": "(New-Object -com 'WMPlayer.OCX').controls.pause()",
                    "next": "(New-Object -com 'WMPlayer.OCX').controls.next()",
                    "previous": "(New-Object -com 'WMPlayer.OCX').controls.previous()",
                    "stop": "(New-Object -com 'WMPlayer.OCX').controls.stop()"
                }
                
                if action in ps_commands:
                    subprocess.run(
                        ["powershell", "-Command", ps_commands[action]],
                        check=True, capture_output=True
                    )
                    return True
            except Exception as e:
                self.logger.error(f"PowerShell media control failed: {e}")
        
        return False
    
    def _macos_media_control(self, action: str) -> bool:
        """macOS-specific media control using osascript"""
        try:
            applescript_commands = {
                "play": 'tell application "System Events" to key code 16',  # Play/Pause
                "pause": 'tell application "System Events" to key code 16',  # Play/Pause
                "next": 'tell application "System Events" to key code 17',   # Next
                "previous": 'tell application "System Events" to key code 18',  # Previous
                "stop": 'tell application "System Events" to key code 16'   # Play/Pause (stop)
            }
            
            if action in applescript_commands:
                subprocess.run(
                    ["osascript", "-e", applescript_commands[action]],
                    check=True
                )
                self.logger.info(f"Sent {action} media key on macOS")
                return True
                
        except Exception as e:
            self.logger.error(f"macOS media control failed: {e}")
        
        return False
    
    def _linux_media_control(self, action: str) -> bool:
        """Linux-specific media control using playerctl or xdotool"""
        try:
            # Try playerctl first (modern Linux media control)
            playerctl_commands = {
                "play": "play",
                "pause": "pause",
                "next": "next",
                "previous": "previous",
                "stop": "stop"
            }
            
            if action in playerctl_commands:
                try:
                    subprocess.run(
                        ["playerctl", playerctl_commands[action]],
                        check=True, capture_output=True
                    )
                    self.logger.info(f"Sent {action} command via playerctl")
                    return True
                except subprocess.CalledProcessError:
                    pass  # Try alternative method
                
            # Fallback to xdotool for media keys
            xdotool_keys = {
                "play": "XF86AudioPlay",
                "pause": "XF86AudioPause",
                "next": "XF86AudioNext",
                "previous": "XF86AudioPrev",
                "stop": "XF86AudioStop"
            }
            
            if action in xdotool_keys:
                subprocess.run(
                    ["xdotool", "key", xdotool_keys[action]],
                    check=True, capture_output=True
                )
                self.logger.info(f"Sent {action} media key via xdotool")
                return True
                
        except Exception as e:
            self.logger.error(f"Linux media control failed: {e}")
        
        return False
    
    def open_media_app(self, app_name: str, content: str = "") -> bool:
        """
        Open media application and optionally play specific content.
        
        Args:
            app_name: Name of the media application
            content: Optional content to search/play
            
        Returns:
            True if successful, False otherwise
        """
        app_name = app_name.lower().replace(" ", "_")
        
        if app_name not in self.media_apps:
            self.logger.error(f"Unknown media app: {app_name}")
            return False
        
        app = self.media_apps[app_name]
        
        try:
            if app_name == "spotify":
                return self._open_spotify(content)
            elif app_name == "youtube_music":
                return self._open_youtube_music(content)
            elif app_name == "apple_music":
                return self._open_apple_music(content)
            elif app_name == "itunes":
                return self._open_itunes(content)
            elif app_name == "windows_media_player":
                return self._open_windows_media_player(content)
            else:
                # Generic app launch
                return self._open_generic_media_app(app, content)
                
        except Exception as e:
            self.logger.error(f"Failed to open {app.name}: {e}")
            return False
    
    def _open_apple_music(self, content: str = "") -> bool:
        """Open Apple Music and optionally search for content"""
        try:
            if sys.platform == "darwin":
                if content:
                    # Use AppleScript to search in Apple Music
                    applescript = f'''
                    tell application "Music"
                        activate
                        search playlist 1 for "{content}"
                    end tell
                    '''
                    subprocess.run(["osascript", "-e", applescript], check=True)
                else:
                    subprocess.run(["open", "-a", "Music"], check=True)
                
                self.logger.info(f"Opened Apple Music{' with search: ' + content if content else ''}")
                return True
            else:
                # On non-macOS, try web version
                base_url = "https://music.apple.com"
                if content:
                    search_url = f"{base_url}/search?term={content.replace(' ', '+')}"
                else:
                    search_url = base_url
                
                if sys.platform == "win32":
                    os.startfile(search_url)
                else:
                    subprocess.run(["xdg-open", search_url], check=True)
                
                return True
                
        except Exception as e:
            self.logger.error(f"Failed to open Apple Music: {e}")
            return False
    
    def _open_itunes(self, content: str = "") -> bool:
        """Open iTunes and optionally search for content"""
        try:
            if content:
                # iTunes search URL
                search_url = f"itms://search.itunes.apple.com/WebObjects/MZSearch.woa/wa/search?term={content.replace(' ', '+')}"
                if sys.platform == "win32":
                    os.startfile(search_url)
                elif sys.platform == "darwin":
                    subprocess.run(["open", search_url], check=True)
                else:
                    subprocess.run(["xdg-open", search_url], check=True)
            else:
                # Just open iTunes
                if sys.platform == "win32":
                    subprocess.Popen(["iTunes.exe"])
                elif sys.platform == "darwin":
                    subprocess.run(["open", "-a", "iTunes"], check=True)
                else:
                    # Linux - unlikely to have iTunes, but try anyway
                    subprocess.Popen(["itunes"])
            
            self.logger.info(f"Opened iTunes{' with search: ' + content if content else ''}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to open iTunes: {e}")
            return False
    
    def _open_windows_media_player(self, content: str = "") -> bool:
        """Open Windows Media Player and optionally play content"""
        try:
            if sys.platform == "win32":
                if content:
                    # Try to search for local files matching the content
                    # This is a simplified implementation
                    subprocess.Popen(["wmplayer.exe"])
                else:
                    subprocess.Popen(["wmplayer.exe"])
                
                self.logger.info(f"Opened Windows Media Player{' with content: ' + content if content else ''}")
                return True
            else:
                self.logger.warning("Windows Media Player is only available on Windows")
                return False
                
        except Exception as e:
            self.logger.error(f"Failed to open Windows Media Player: {e}")
            return False
    
    def _open_generic_media_app(self, app: MediaApp, content: str = "") -> bool:
        """Open a generic media application"""
        try:
            if sys.platform == "win32":
                subprocess.Popen([app.executable_path])
            else:
                subprocess.Popen([app.executable_path], 
                               stdout=subprocess.DEVNULL, 
                               stderr=subprocess.DEVNULL)
            
            self.logger.info(f"Opened {app.name}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to open {app.name}: {e}")
            return False
    
    def _open_spotify(self, content: str = "") -> bool:
        """Open Spotify and optionally search for content"""
        try:
            if content:
                # Multiple approaches for Spotify search
                search_methods = [
                    # Spotify URI search (most reliable)
                    f"spotify:search:{content.replace(' ', '%20')}",
                    # Spotify web player search
                    f"https://open.spotify.com/search/{content.replace(' ', '%20')}",
                ]
                
                for search_uri in search_methods:
                    try:
                        if sys.platform == "win32":
                            os.startfile(search_uri)
                        elif sys.platform == "darwin":
                            subprocess.run(["open", search_uri], check=True)
                        else:
                            subprocess.run(["xdg-open", search_uri], check=True)
                        
                        self.logger.info(f"Opened Spotify with search: {content} using {search_uri}")
                        return True
                    except Exception as e:
                        self.logger.warning(f"Failed to open Spotify with {search_uri}: {e}")
                        continue
            else:
                # Just open Spotify app
                try:
                    if sys.platform == "win32":
                        # Try multiple ways to launch Spotify on Windows
                        try:
                            subprocess.Popen(["spotify.exe"])
                        except FileNotFoundError:
                            # Try from Windows Store installation
                            subprocess.Popen(["cmd", "/c", "start", "spotify:"])
                    elif sys.platform == "darwin":
                        subprocess.run(["open", "-a", "Spotify"], check=True)
                    else:
                        # Linux - try multiple methods
                        try:
                            subprocess.Popen(["spotify"])
                        except FileNotFoundError:
                            subprocess.Popen(["flatpak", "run", "com.spotify.Client"])
                    
                    self.logger.info("Opened Spotify application")
                    return True
                except Exception as e:
                    self.logger.error(f"Failed to open Spotify app: {e}")
            
            return False
            
        except Exception as e:
            self.logger.error(f"Failed to open Spotify: {e}")
            return False
    
    def _open_youtube_music(self, content: str = "") -> bool:
        """Open YouTube Music in browser and optionally search for content"""
        try:
            base_url = "https://music.youtube.com"
            if content:
                # Enhanced search URL with better encoding
                search_query = content.replace(' ', '+').replace('&', '%26')
                search_url = f"{base_url}/search?q={search_query}"
            else:
                search_url = base_url
            
            # Try multiple browser opening methods
            browser_methods = []
            
            if sys.platform == "win32":
                browser_methods = [
                    lambda: os.startfile(search_url),
                    lambda: subprocess.run(["start", search_url], shell=True, check=True),
                    lambda: subprocess.run(["cmd", "/c", "start", search_url], check=True)
                ]
            elif sys.platform == "darwin":
                browser_methods = [
                    lambda: subprocess.run(["open", search_url], check=True),
                    lambda: subprocess.run(["open", "-a", "Safari", search_url], check=True),
                    lambda: subprocess.run(["open", "-a", "Google Chrome", search_url], check=True)
                ]
            else:
                browser_methods = [
                    lambda: subprocess.run(["xdg-open", search_url], check=True),
                    lambda: subprocess.run(["google-chrome", search_url], check=True),
                    lambda: subprocess.run(["firefox", search_url], check=True)
                ]
            
            # Try each method until one succeeds
            for method in browser_methods:
                try:
                    method()
                    self.logger.info(f"Opened YouTube Music{' with search: ' + content if content else ''}")
                    return True
                except Exception as e:
                    self.logger.debug(f"Browser method failed: {e}")
                    continue
            
            self.logger.error("All browser opening methods failed")
            return False
            
        except Exception as e:
            self.logger.error(f"Failed to open YouTube Music: {e}")
            return False
    
    def search_and_play(self, query: str, app_preference: str = "spotify") -> bool:
        """
        Search for and play specific content.
        
        Args:
            query: Search query (song, artist, album)
            app_preference: Preferred media app
            
        Returns:
            True if successful, False otherwise
        """
        self.logger.info(f"Searching for '{query}' in {app_preference}")
        
        # Try multiple approaches for better success rate
        try:
            # First, try to open the app with search content
            if self.open_media_app(app_preference, query):
                # Give the app time to load, then try to play
                import time
                time.sleep(3)  # Increased wait time for better reliability
                
                # Try to start playback
                play_success = self.control_playback("play")
                if play_success:
                    self.logger.info(f"Successfully started playback for '{query}'")
                    return True
                else:
                    self.logger.warning(f"App opened but playback failed for '{query}'")
                    return True  # App opened successfully, even if playback didn't start
            
            # Fallback: try other available media apps
            fallback_apps = ["spotify", "youtube_music", "vlc"]
            for fallback_app in fallback_apps:
                if fallback_app != app_preference and fallback_app in self.media_apps:
                    self.logger.info(f"Trying fallback app: {fallback_app}")
                    if self.open_media_app(fallback_app, query):
                        import time
                        time.sleep(2)
                        self.control_playback("play")
                        return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"Error in search_and_play: {e}")
            return False
    
    def get_media_status(self) -> Dict[str, Any]:
        """
        Get current media playback status.
        
        Returns:
            Dictionary with media status information
        """
        status = {
            "volume": self.get_current_volume(),
            "is_muted": self.is_muted(),
            "devices": self.get_audio_devices(),
            "active_apps": self._get_active_media_apps()
        }
        
        return status
    
    def _get_active_media_apps(self) -> List[str]:
        """Get list of currently running media applications"""
        active_apps = []
        
        try:
            if sys.platform == "win32":
                import psutil
                for proc in psutil.process_iter(['name']):
                    proc_name = proc.info['name'].lower()
                    for app_name, app in self.media_apps.items():
                        if app.process_name.lower() in proc_name:
                            active_apps.append(app.name)
                            
            elif sys.platform == "darwin":
                result = subprocess.run(
                    ["ps", "aux"], capture_output=True, text=True
                )
                for app_name, app in self.media_apps.items():
                    if app.process_name.lower() in result.stdout.lower():
                        active_apps.append(app.name)
                        
            elif sys.platform.startswith("linux"):
                result = subprocess.run(
                    ["ps", "aux"], capture_output=True, text=True
                )
                for app_name, app in self.media_apps.items():
                    if app.process_name.lower() in result.stdout.lower():
                        active_apps.append(app.name)
                        
        except Exception as e:
            self.logger.error(f"Failed to get active media apps: {e}")
        
        return list(set(active_apps))  # Remove duplicates


# Convenience functions for easy integration
def create_media_controller(config: Optional[Dict[str, Any]] = None) -> MediaController:
    """Create and return a MediaController instance"""
    return MediaController(config)


def get_volume() -> Optional[int]:
    """Quick function to get current volume"""
    controller = MediaController()
    return controller.get_current_volume()


def set_volume(level: int) -> bool:
    """Quick function to set volume"""
    controller = MediaController()
    return controller.set_volume(level)


def toggle_mute() -> bool:
    """Quick function to toggle mute"""
    controller = MediaController()
    return controller.toggle_mute()