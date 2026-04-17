"""
System Controller Module

This module handles system-level operations including application management,
window control, and system operations like shutdown, restart, and lock.
"""

import os
import sys
import subprocess
import psutil
import time
import logging
from typing import Dict, List, Optional, Tuple, Any
from pathlib import Path
import platform
import ctypes
from ctypes import wintypes
import win32gui
import win32con
import win32process
import win32api
import win32clipboard
import shutil
from PIL import ImageGrab
import cv2
import numpy as np
import threading

# Import the dynamic app discovery engine
try:
    from wizard.commands.app_discovery import AppDiscovery, open_any_app
    _HAS_APP_DISCOVERY = True
except ImportError:
    _HAS_APP_DISCOVERY = False

logger = logging.getLogger(__name__)


class SystemController:
    """
    Manages operating system interactions including application management,
    window control, and system operations.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the system controller
        
        Args:
            config: Configuration dictionary containing application paths and settings
        """
        self.config = config
        self.applications = self._load_application_paths()
        self.running_processes = {}
        self.is_windows = platform.system() == "Windows"
        
        # Initialize dynamic app discovery (discovers ALL installed apps)
        self.app_discovery = None
        if _HAS_APP_DISCOVERY and self.is_windows:
            try:
                extra_apps = dict(self.applications)  # pass hardcoded apps as fallback
                self.app_discovery = AppDiscovery(extra_apps=extra_apps)
                # Merge discovered apps back into self.applications for backward compat
                self.applications.update(self.app_discovery.get_all_apps())
                logger.info(f"App discovery loaded {len(self.applications)} applications")
            except Exception as e:
                logger.warning(f"App discovery failed, using default app list: {e}")
        
        # Windows-specific setup
        if self.is_windows:
            self._setup_windows_apis()
    
    def _setup_windows_apis(self):
        """Setup Windows-specific API functions"""
        try:
            # Setup Windows API functions for system operations
            self.user32 = ctypes.windll.user32
            self.kernel32 = ctypes.windll.kernel32
            self.shell32 = ctypes.windll.shell32
            
            # Define Windows constants
            self.SW_MINIMIZE = 6
            self.SW_MAXIMIZE = 3
            self.SW_RESTORE = 9
            self.SW_HIDE = 0
            self.SW_SHOW = 5
            
        except Exception as e:
            logger.error(f"Failed to setup Windows APIs: {e}")
    
    def _load_application_paths(self) -> Dict[str, str]:
        """
        Load application names and their executable paths
        
        Returns:
            Dictionary mapping application names to their paths
        """
        # Default Windows applications
        default_apps = {
            "notepad": "notepad.exe",
            "calculator": "calc.exe",
            "paint": "mspaint.exe",
            "wordpad": "wordpad.exe",
            "task manager": "taskmgr.exe",
            "control panel": "control.exe",
            "registry editor": "regedit.exe",
            "command prompt": "cmd.exe",
            "powershell": "powershell.exe",
            "file explorer": "explorer.exe",
            "windows media player": "wmplayer.exe",
            
            # Common third-party applications (if installed)
            "chrome": r"C:\Program Files\Google\Chrome\Application\chrome.exe",
            "firefox": r"C:\Program Files\Mozilla Firefox\firefox.exe",
            "edge": r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
            "spotify": r"C:\Users\%USERNAME%\AppData\Roaming\Spotify\Spotify.exe",
            "discord": r"C:\Users\%USERNAME%\AppData\Local\Discord\app-*\Discord.exe",
            "steam": r"C:\Program Files (x86)\Steam\steam.exe",
            "vlc": r"C:\Program Files\VideoLAN\VLC\vlc.exe",
            "vscode": r"C:\Users\%USERNAME%\AppData\Local\Programs\Microsoft VS Code\Code.exe",
            "visual studio code": r"C:\Users\%USERNAME%\AppData\Local\Programs\Microsoft VS Code\Code.exe",
            
            # Microsoft Office
            "word": r"C:\Program Files\Microsoft Office\root\Office16\WINWORD.EXE",
            "excel": r"C:\Program Files\Microsoft Office\root\Office16\EXCEL.EXE",
            "powerpoint": r"C:\Program Files\Microsoft Office\root\Office16\POWERPNT.EXE",
            "outlook": r"C:\Program Files\Microsoft Office\root\Office16\OUTLOOK.EXE",
            "teams": r"C:\Users\%USERNAME%\AppData\Local\Microsoft\Teams\current\Teams.exe",
        }
        
        # Merge with config applications
        config_apps = self.config.get("applications", {})
        default_apps.update(config_apps)
        
        # Expand environment variables in paths
        expanded_apps = {}
        for name, path in default_apps.items():
            expanded_path = os.path.expandvars(path)
            expanded_apps[name] = expanded_path
        
        return expanded_apps
    
    def open_application(self, app_name: str) -> Tuple[bool, str]:
        """
        Launch a specified application.
        Uses AppDiscovery for intelligent fuzzy matching across ALL installed
        Windows apps, falling back to hardcoded paths and Windows search.
        
        Args:
            app_name: Name of the application to open
            
        Returns:
            Tuple of (success, message)
        """
        try:
            app_name_lower = app_name.lower().strip()
            logger.info(f"Attempting to open application: {app_name_lower}")
            
            # --- Strategy 1: Use AppDiscovery (fuzzy match across all installed apps) ---
            if self.app_discovery is not None:
                success, message = open_any_app(app_name_lower, self.app_discovery)
                if success:
                    logger.info(f"AppDiscovery opened: {message}")
                    return True, message
                logger.debug(f"AppDiscovery could not find '{app_name_lower}', trying fallbacks")
            
            # --- Strategy 2: Check hardcoded application paths ---
            if app_name_lower in self.applications:
                app_path = self.applications[app_name_lower]
                
                # Handle wildcard paths (like Discord with version numbers)
                if '*' in app_path:
                    app_path = self._resolve_wildcard_path(app_path)
                
                if app_path and os.path.exists(app_path):
                    process = subprocess.Popen([app_path], shell=True)
                    self.running_processes[app_name_lower] = process.pid
                    logger.info(f"Successfully opened {app_name} (PID: {process.pid})")
                    return True, f"Successfully opened {app_name}"
                else:
                    # Try to find the application in common locations
                    found_path = self._find_application(app_name_lower)
                    if found_path:
                        process = subprocess.Popen([found_path], shell=True)
                        self.running_processes[app_name_lower] = process.pid
                        logger.info(f"Found and opened {app_name} at {found_path}")
                        return True, f"Successfully opened {app_name}"
            
            # --- Strategy 3: Try opening as a system command / Windows search ---
            try:
                if self.is_windows:
                    # Use Windows start command which searches PATH + Start Menu
                    subprocess.Popen(f'start "" "{app_name}"', shell=True)
                    logger.info(f"Opened {app_name} using Windows start command")
                    return True, f"Successfully opened {app_name}"
                else:
                    # Linux/Mac fallback
                    subprocess.Popen([app_name], shell=True)
                    return True, f"Successfully opened {app_name}"
            except Exception as e:
                logger.error(f"Failed to open {app_name} as system command: {e}")
            
            return False, f"Could not find or open application: {app_name}"
            
        except Exception as e:
            logger.error(f"Error opening application {app_name}: {e}")
            return False, f"Error opening {app_name}: {str(e)}"
    
    def _resolve_wildcard_path(self, path: str) -> Optional[str]:
        """
        Resolve paths with wildcards to actual file paths
        
        Args:
            path: Path with wildcards
            
        Returns:
            Resolved path or None if not found
        """
        try:
            import glob
            matches = glob.glob(path)
            if matches:
                # Return the first match (or most recent if multiple)
                return sorted(matches)[-1]
        except Exception as e:
            logger.error(f"Error resolving wildcard path {path}: {e}")
        return None
    
    def _find_application(self, app_name: str) -> Optional[str]:
        """
        Search for application in common installation directories
        
        Args:
            app_name: Name of the application to find
            
        Returns:
            Path to application executable or None if not found
        """
        common_paths = [
            r"C:\Program Files",
            r"C:\Program Files (x86)",
            r"C:\Users\{}\AppData\Local".format(os.getenv('USERNAME', '')),
            r"C:\Users\{}\AppData\Roaming".format(os.getenv('USERNAME', '')),
            r"C:\Windows\System32",
            r"C:\Windows"
        ]
        
        possible_names = [
            f"{app_name}.exe",
            f"{app_name}",
            app_name.replace(" ", "").lower() + ".exe",
            app_name.replace(" ", "_").lower() + ".exe"
        ]
        
        for base_path in common_paths:
            if os.path.exists(base_path):
                for root, dirs, files in os.walk(base_path):
                    for filename in files:
                        if filename.lower() in [name.lower() for name in possible_names]:
                            full_path = os.path.join(root, filename)
                            logger.info(f"Found {app_name} at {full_path}")
                            return full_path
        
        return None
    
    def close_application(self, app_name: str, force: bool = False) -> Tuple[bool, str]:
        """
        Close a specified application
        
        Args:
            app_name: Name of the application to close
            force: Whether to force close the application
            
        Returns:
            Tuple of (success, message)
        """
        try:
            app_name_lower = app_name.lower().strip()
            logger.info(f"Attempting to close application: {app_name_lower}")
            
            closed_processes = []
            
            # Find and terminate processes by name
            for proc in psutil.process_iter(['pid', 'name', 'exe']):
                try:
                    proc_info = proc.info
                    proc_name = proc_info['name'].lower() if proc_info['name'] else ""
                    proc_exe = proc_info['exe'].lower() if proc_info['exe'] else ""
                    
                    # Check if this process matches the application
                    if (app_name_lower in proc_name or 
                        any(app_name_lower in part for part in proc_exe.split('\\')) or
                        proc_name.startswith(app_name_lower)):
                        
                        if force:
                            proc.kill()  # Force kill
                        else:
                            proc.terminate()  # Graceful termination
                        
                        closed_processes.append(proc_info['name'])
                        logger.info(f"Closed process: {proc_info['name']} (PID: {proc_info['pid']})")
                        
                except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                    continue
            
            if closed_processes:
                return True, f"Successfully closed {app_name}. Processes: {', '.join(closed_processes)}"
            else:
                return False, f"No running processes found for {app_name}"
                
        except Exception as e:
            logger.error(f"Error closing application {app_name}: {e}")
            return False, f"Error closing {app_name}: {str(e)}"
    
    def control_window(self, action: str, window_title: str = None) -> Tuple[bool, str]:
        """
        Control window operations (minimize, maximize, restore, etc.)
        
        Args:
            action: Action to perform (minimize, maximize, restore, close)
            window_title: Title of the window to control (optional)
            
        Returns:
            Tuple of (success, message)
        """
        if not self.is_windows:
            return False, "Window control is only supported on Windows"
        
        try:
            action = action.lower().strip()
            logger.info(f"Window control action: {action}, target: {window_title}")
            
            if window_title:
                # Find specific window by title
                hwnd = win32gui.FindWindow(None, window_title)
                if hwnd == 0:
                    # Try partial match
                    hwnd = self._find_window_by_partial_title(window_title)
                
                if hwnd == 0:
                    return False, f"Window with title '{window_title}' not found"
                
                return self._perform_window_action(hwnd, action, window_title)
            else:
                # Control the foreground window
                hwnd = win32gui.GetForegroundWindow()
                if hwnd == 0:
                    return False, "No active window found"
                
                window_title = win32gui.GetWindowText(hwnd)
                return self._perform_window_action(hwnd, action, window_title)
                
        except Exception as e:
            logger.error(f"Error controlling window: {e}")
            return False, f"Error controlling window: {str(e)}"
    
    def _find_window_by_partial_title(self, partial_title: str) -> int:
        """
        Find window by partial title match
        
        Args:
            partial_title: Partial window title to search for
            
        Returns:
            Window handle or 0 if not found
        """
        def enum_windows_callback(hwnd, windows):
            if win32gui.IsWindowVisible(hwnd):
                window_title = win32gui.GetWindowText(hwnd)
                if partial_title.lower() in window_title.lower():
                    windows.append(hwnd)
            return True
        
        windows = []
        win32gui.EnumWindows(enum_windows_callback, windows)
        return windows[0] if windows else 0
    
    def _perform_window_action(self, hwnd: int, action: str, window_title: str) -> Tuple[bool, str]:
        """
        Perform the specified action on a window
        
        Args:
            hwnd: Window handle
            action: Action to perform
            window_title: Window title for logging
            
        Returns:
            Tuple of (success, message)
        """
        try:
            if action == "minimize":
                win32gui.ShowWindow(hwnd, self.SW_MINIMIZE)
                return True, f"Minimized window: {window_title}"
            
            elif action == "maximize":
                win32gui.ShowWindow(hwnd, self.SW_MAXIMIZE)
                return True, f"Maximized window: {window_title}"
            
            elif action == "restore":
                win32gui.ShowWindow(hwnd, self.SW_RESTORE)
                return True, f"Restored window: {window_title}"
            
            elif action == "close":
                win32gui.PostMessage(hwnd, win32con.WM_CLOSE, 0, 0)
                return True, f"Closed window: {window_title}"
            
            elif action == "hide":
                win32gui.ShowWindow(hwnd, self.SW_HIDE)
                return True, f"Hidden window: {window_title}"
            
            elif action == "show":
                win32gui.ShowWindow(hwnd, self.SW_SHOW)
                win32gui.SetForegroundWindow(hwnd)
                return True, f"Showed window: {window_title}"
            
            else:
                return False, f"Unknown window action: {action}"
                
        except Exception as e:
            logger.error(f"Error performing window action {action}: {e}")
            return False, f"Error performing window action: {str(e)}"
    
    def system_shutdown(self, confirm: bool = False) -> Tuple[bool, str]:
        """
        Shutdown the computer
        
        Args:
            confirm: Whether the user has confirmed the shutdown
            
        Returns:
            Tuple of (success, message)
        """
        if not confirm:
            return False, "Shutdown requires confirmation. Please confirm to proceed."
        
        try:
            logger.info("Initiating system shutdown")
            
            if self.is_windows:
                # Windows shutdown command
                subprocess.run(["shutdown", "/s", "/t", "10"], check=True)
                return True, "System will shutdown in 10 seconds"
            else:
                # Linux/Mac shutdown
                subprocess.run(["sudo", "shutdown", "-h", "now"], check=True)
                return True, "System shutdown initiated"
                
        except subprocess.CalledProcessError as e:
            logger.error(f"Shutdown command failed: {e}")
            return False, f"Failed to shutdown system: {str(e)}"
        except Exception as e:
            logger.error(f"Error during shutdown: {e}")
            return False, f"Error during shutdown: {str(e)}"
    
    def system_restart(self, confirm: bool = False) -> Tuple[bool, str]:
        """
        Restart the computer
        
        Args:
            confirm: Whether the user has confirmed the restart
            
        Returns:
            Tuple of (success, message)
        """
        if not confirm:
            return False, "Restart requires confirmation. Please confirm to proceed."
        
        try:
            logger.info("Initiating system restart")
            
            if self.is_windows:
                # Windows restart command
                subprocess.run(["shutdown", "/r", "/t", "10"], check=True)
                return True, "System will restart in 10 seconds"
            else:
                # Linux/Mac restart
                subprocess.run(["sudo", "reboot"], check=True)
                return True, "System restart initiated"
                
        except subprocess.CalledProcessError as e:
            logger.error(f"Restart command failed: {e}")
            return False, f"Failed to restart system: {str(e)}"
        except Exception as e:
            logger.error(f"Error during restart: {e}")
            return False, f"Error during restart: {str(e)}"
    
    def system_lock(self) -> Tuple[bool, str]:
        """
        Lock the computer screen
        
        Returns:
            Tuple of (success, message)
        """
        try:
            logger.info("Locking system")
            
            if self.is_windows:
                # Windows lock screen
                ctypes.windll.user32.LockWorkStation()
                return True, "System locked"
            else:
                # Linux lock screen (requires appropriate desktop environment)
                try:
                    subprocess.run(["gnome-screensaver-command", "-l"], check=True)
                    return True, "System locked"
                except subprocess.CalledProcessError:
                    try:
                        subprocess.run(["xdg-screensaver", "lock"], check=True)
                        return True, "System locked"
                    except subprocess.CalledProcessError:
                        return False, "Could not lock screen - no compatible screen locker found"
                        
        except Exception as e:
            logger.error(f"Error locking system: {e}")
            return False, f"Error locking system: {str(e)}"
    
    def system_logout(self) -> Tuple[bool, str]:
        """
        Log out the current user
        
        Returns:
            Tuple of (success, message)
        """
        try:
            logger.info("Logging out user")
            
            if self.is_windows:
                # Windows logout
                subprocess.run(["shutdown", "/l"], check=True)
                return True, "User logged out"
            else:
                # Linux logout (depends on desktop environment)
                try:
                    subprocess.run(["gnome-session-quit", "--logout", "--no-prompt"], check=True)
                    return True, "User logged out"
                except subprocess.CalledProcessError:
                    return False, "Could not logout - no compatible session manager found"
                    
        except subprocess.CalledProcessError as e:
            logger.error(f"Logout command failed: {e}")
            return False, f"Failed to logout: {str(e)}"
        except Exception as e:
            logger.error(f"Error during logout: {e}")
            return False, f"Error during logout: {str(e)}"
    
    def take_screenshot(self, filename: str = None) -> Tuple[bool, str]:
        """
        Take a screenshot of the desktop
        
        Args:
            filename: Optional filename for the screenshot
            
        Returns:
            Tuple of (success, message with file path)
        """
        try:
            if not filename:
                timestamp = time.strftime("%Y%m%d_%H%M%S")
                filename = f"screenshot_{timestamp}.png"
            
            # Ensure filename has .png extension
            if not filename.lower().endswith('.png'):
                filename += '.png'
            
            # Take screenshot using PIL
            screenshot = ImageGrab.grab()
            
            # Save to user's Pictures folder or current directory
            if self.is_windows:
                pictures_path = os.path.join(os.path.expanduser("~"), "Pictures")
                if os.path.exists(pictures_path):
                    filepath = os.path.join(pictures_path, filename)
                else:
                    filepath = filename
            else:
                filepath = filename
            
            screenshot.save(filepath)
            logger.info(f"Screenshot saved to: {filepath}")
            
            return True, f"Screenshot saved to: {filepath}"
            
        except Exception as e:
            logger.error(f"Error taking screenshot: {e}")
            return False, f"Error taking screenshot: {str(e)}"
    
    def start_screen_recording(self, filename: str = None, duration: int = 30) -> Tuple[bool, str]:
        """
        Start screen recording
        
        Args:
            filename: Optional filename for the recording
            duration: Recording duration in seconds
            
        Returns:
            Tuple of (success, message)
        """
        try:
            if not filename:
                timestamp = time.strftime("%Y%m%d_%H%M%S")
                filename = f"recording_{timestamp}.avi"
            
            # Ensure filename has video extension
            if not any(filename.lower().endswith(ext) for ext in ['.avi', '.mp4', '.mov']):
                filename += '.avi'
            
            # Get screen dimensions
            screen = ImageGrab.grab()
            screen_width, screen_height = screen.size
            
            # Setup video writer
            fourcc = cv2.VideoWriter_fourcc(*'XVID')
            
            # Save to user's Videos folder or current directory
            if self.is_windows:
                videos_path = os.path.join(os.path.expanduser("~"), "Videos")
                if os.path.exists(videos_path):
                    filepath = os.path.join(videos_path, filename)
                else:
                    filepath = filename
            else:
                filepath = filename
            
            out = cv2.VideoWriter(filepath, fourcc, 20.0, (screen_width, screen_height))
            
            # Start recording in a separate thread
            def record_screen():
                start_time = time.time()
                while time.time() - start_time < duration:
                    # Capture screen
                    img = ImageGrab.grab()
                    frame = np.array(img)
                    frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
                    out.write(frame)
                    time.sleep(0.05)  # 20 FPS
                
                out.release()
                logger.info(f"Screen recording completed: {filepath}")
            
            recording_thread = threading.Thread(target=record_screen)
            recording_thread.daemon = True
            recording_thread.start()
            
            return True, f"Screen recording started. Will record for {duration} seconds to: {filepath}"
            
        except Exception as e:
            logger.error(f"Error starting screen recording: {e}")
            return False, f"Error starting screen recording: {str(e)}"
    
    def empty_recycle_bin(self) -> Tuple[bool, str]:
        """
        Empty the recycle bin
        
        Returns:
            Tuple of (success, message)
        """
        try:
            if self.is_windows:
                # Windows recycle bin
                self.shell32.SHEmptyRecycleBinW(None, None, 0)
                logger.info("Recycle bin emptied")
                return True, "Recycle bin has been emptied"
            else:
                # Linux trash (if available)
                trash_path = os.path.expanduser("~/.local/share/Trash/files")
                if os.path.exists(trash_path):
                    shutil.rmtree(trash_path)
                    os.makedirs(trash_path)
                    return True, "Trash has been emptied"
                else:
                    return False, "Trash directory not found"
                    
        except Exception as e:
            logger.error(f"Error emptying recycle bin: {e}")
            return False, f"Error emptying recycle bin: {str(e)}"
    
    def get_running_applications(self) -> List[Dict[str, Any]]:
        """
        Get list of currently running applications
        
        Returns:
            List of dictionaries containing application information
        """
        applications = []
        
        try:
            for proc in psutil.process_iter(['pid', 'name', 'exe', 'memory_info']):
                try:
                    proc_info = proc.info
                    if proc_info['exe'] and proc_info['name']:
                        applications.append({
                            'pid': proc_info['pid'],
                            'name': proc_info['name'],
                            'exe': proc_info['exe'],
                            'memory_mb': proc_info['memory_info'].rss / 1024 / 1024 if proc_info['memory_info'] else 0
                        })
                except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                    continue
                    
        except Exception as e:
            logger.error(f"Error getting running applications: {e}")
        
        return applications
    
    def get_system_info(self) -> Dict[str, Any]:
        """
        Get system information
        
        Returns:
            Dictionary containing system information
        """
        try:
            return {
                'platform': platform.system(),
                'platform_version': platform.version(),
                'architecture': platform.architecture()[0],
                'processor': platform.processor(),
                'hostname': platform.node(),
                'cpu_count': psutil.cpu_count(),
                'memory_total_gb': psutil.virtual_memory().total / 1024 / 1024 / 1024,
                'memory_available_gb': psutil.virtual_memory().available / 1024 / 1024 / 1024,
                'disk_usage': {
                    'total_gb': psutil.disk_usage('/').total / 1024 / 1024 / 1024 if not self.is_windows else psutil.disk_usage('C:').total / 1024 / 1024 / 1024,
                    'free_gb': psutil.disk_usage('/').free / 1024 / 1024 / 1024 if not self.is_windows else psutil.disk_usage('C:').free / 1024 / 1024 / 1024
                }
            }
        except Exception as e:
            logger.error(f"Error getting system info: {e}")
            return {}