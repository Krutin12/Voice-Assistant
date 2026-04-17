"""
App Discovery Module

Dynamically discovers ALL installed Windows applications by scanning:
1. Start Menu shortcuts (.lnk files)
2. Windows Registry uninstall entries
3. Microsoft Store (UWP) apps via PowerShell
4. Common installation directories

Provides a unified name → path mapping and fuzzy matching so the
voice assistant can open any installed app by name.
"""

import os
import re
import json
import glob
import subprocess
import logging
import time
import winreg
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from difflib import SequenceMatcher

logger = logging.getLogger(__name__)

# Cache file location
CACHE_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data")
CACHE_FILE = os.path.join(CACHE_DIR, "app_cache.json")
CACHE_MAX_AGE_HOURS = 24  # Refresh cache after 24 hours


class AppDiscovery:
    """
    Discovers all installed Windows applications and provides
    fuzzy name matching for voice commands.
    """

    def __init__(self, extra_apps: Dict[str, str] = None):
        """
        Initialize the app discovery engine.

        Args:
            extra_apps: Additional name→path mappings to merge in
                        (e.g. from user config)
        """
        self.extra_apps = extra_apps or {}
        self._apps: Dict[str, str] = {}
        self._aliases: Dict[str, str] = {}  # alias → canonical name
        self._load_apps()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def get_all_apps(self) -> Dict[str, str]:
        """Return the full name → path dictionary."""
        return dict(self._apps)

    def find_app(self, query: str) -> Optional[Tuple[str, str]]:
        """
        Find the best matching application for a voice query.

        Args:
            query: The application name spoken by the user.

        Returns:
            (display_name, executable_path) or None
        """
        query_lower = query.lower().strip()

        # 1. Exact match
        if query_lower in self._apps:
            return (query_lower, self._apps[query_lower])

        # 2. Alias match
        if query_lower in self._aliases:
            canonical = self._aliases[query_lower]
            return (canonical, self._apps[canonical])

        # 3. Substring / contains match
        for name, path in self._apps.items():
            if query_lower in name or name in query_lower:
                return (name, path)

        # 4. Fuzzy match
        best_name = None
        best_score = 0.0
        for name in self._apps:
            score = SequenceMatcher(None, query_lower, name).ratio()
            if score > best_score:
                best_score = score
                best_name = name

        if best_score >= 0.55 and best_name:
            return (best_name, self._apps[best_name])

        # 5. Try word-level matching (e.g. "vs code" → "visual studio code")
        query_words = set(query_lower.split())
        for name in self._apps:
            name_words = set(name.split())
            if query_words and query_words.issubset(name_words):
                return (name, self._apps[name])
            # Or if most words match
            overlap = len(query_words & name_words)
            if overlap >= max(1, len(query_words) - 1) and overlap > 0:
                return (name, self._apps[name])

        return None

    def refresh(self):
        """Force a full re-scan of installed applications."""
        self._apps = {}
        self._aliases = {}
        self._discover_all()
        self._save_cache()

    # ------------------------------------------------------------------
    # Internal: loading & caching
    # ------------------------------------------------------------------

    def _load_apps(self):
        """Load from cache if fresh, otherwise discover."""
        if self._load_cache():
            logger.info(f"Loaded {len(self._apps)} apps from cache")
        else:
            logger.info("Cache miss – scanning for installed applications...")
            self._discover_all()
            self._save_cache()
            logger.info(f"Discovered {len(self._apps)} applications")

        # Always merge in extra / user-defined apps (they take priority)
        for name, path in self.extra_apps.items():
            self._apps[name.lower().strip()] = path

        # Build aliases
        self._build_aliases()

    def _load_cache(self) -> bool:
        """Try to load the app cache. Returns True on success."""
        try:
            if not os.path.exists(CACHE_FILE):
                return False
            age_hours = (time.time() - os.path.getmtime(CACHE_FILE)) / 3600
            if age_hours > CACHE_MAX_AGE_HOURS:
                return False
            with open(CACHE_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
            self._apps = data.get("apps", {})
            return bool(self._apps)
        except Exception as e:
            logger.warning(f"Could not load app cache: {e}")
            return False

    def _save_cache(self):
        """Persist current app list to disk."""
        try:
            os.makedirs(CACHE_DIR, exist_ok=True)
            with open(CACHE_FILE, "w", encoding="utf-8") as f:
                json.dump({"apps": self._apps, "timestamp": time.time()}, f, indent=2)
        except Exception as e:
            logger.warning(f"Could not save app cache: {e}")

    # ------------------------------------------------------------------
    # Internal: discovery strategies
    # ------------------------------------------------------------------

    def _discover_all(self):
        """Run every discovery strategy and merge results."""
        self._discover_start_menu()
        self._discover_registry()
        self._discover_uwp_apps()
        self._discover_common_paths()
        self._add_builtin_windows_apps()

    # ---- 1. Start Menu shortcuts (.lnk) --------------------------------

    def _discover_start_menu(self):
        """Scan Start Menu folders for .lnk shortcuts."""
        start_menu_dirs = [
            os.path.join(os.environ.get("PROGRAMDATA", r"C:\ProgramData"),
                         r"Microsoft\Windows\Start Menu\Programs"),
            os.path.join(os.environ.get("APPDATA", ""),
                         r"Microsoft\Windows\Start Menu\Programs"),
        ]
        for base_dir in start_menu_dirs:
            if not os.path.isdir(base_dir):
                continue
            for root, _dirs, files in os.walk(base_dir):
                for fname in files:
                    if fname.lower().endswith(".lnk"):
                        lnk_path = os.path.join(root, fname)
                        target = self._resolve_lnk(lnk_path)
                        if target and target.lower().endswith(".exe"):
                            display_name = self._clean_app_name(fname[:-4])  # strip .lnk
                            if display_name:
                                self._apps[display_name] = target

    def _resolve_lnk(self, lnk_path: str) -> Optional[str]:
        """Resolve a .lnk shortcut to its target path using PowerShell."""
        try:
            # Use COM via PowerShell (most reliable cross-version approach)
            ps_cmd = (
                f'(New-Object -ComObject WScript.Shell)'
                f'.CreateShortcut("{lnk_path}").TargetPath'
            )
            result = subprocess.run(
                ["powershell", "-NoProfile", "-Command", ps_cmd],
                capture_output=True, text=True, timeout=5,
                creationflags=subprocess.CREATE_NO_WINDOW,
            )
            target = result.stdout.strip().strip('"')
            if target and os.path.isfile(target):
                return target
        except Exception:
            pass

        # Fallback: try reading target from the .lnk binary header
        try:
            with open(lnk_path, "rb") as f:
                data = f.read()
            # Look for a path ending in .exe inside the binary
            matches = re.findall(
                rb'[A-Za-z]:\\[^\x00]{3,260}\.exe', data, re.IGNORECASE
            )
            for m in matches:
                path = m.decode("utf-8", errors="ignore")
                if os.path.isfile(path):
                    return path
        except Exception:
            pass

        return None

    # ---- 2. Windows Registry uninstall entries --------------------------

    def _discover_registry(self):
        """Scan registry Uninstall keys for installed software."""
        reg_paths = [
            (winreg.HKEY_LOCAL_MACHINE,
             r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall"),
            (winreg.HKEY_LOCAL_MACHINE,
             r"SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall"),
            (winreg.HKEY_CURRENT_USER,
             r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall"),
        ]
        for hive, sub_key in reg_paths:
            try:
                key = winreg.OpenKey(hive, sub_key)
                for i in range(winreg.QueryInfoKey(key)[0]):
                    try:
                        subkey_name = winreg.EnumKey(key, i)
                        app_key = winreg.OpenKey(key, subkey_name)

                        display_name = self._reg_value(app_key, "DisplayName")
                        install_location = self._reg_value(app_key, "InstallLocation")
                        display_icon = self._reg_value(app_key, "DisplayIcon")

                        if not display_name:
                            continue

                        # Try to get an executable
                        exe_path = None
                        if install_location:
                            exe_path = self._find_exe_in_dir(install_location, display_name)
                        if not exe_path and display_icon:
                            icon_path = display_icon.split(",")[0].strip('"')
                            if icon_path.lower().endswith(".exe") and os.path.isfile(icon_path):
                                exe_path = icon_path

                        if exe_path:
                            clean_name = self._clean_app_name(display_name)
                            if clean_name:
                                self._apps[clean_name] = exe_path

                        winreg.CloseKey(app_key)
                    except OSError:
                        continue
                winreg.CloseKey(key)
            except OSError:
                continue

    @staticmethod
    def _reg_value(key, name: str) -> Optional[str]:
        """Safely read a registry string value."""
        try:
            val, _ = winreg.QueryValueEx(key, name)
            return str(val) if val else None
        except OSError:
            return None

    # ---- 3. UWP / Microsoft Store apps ----------------------------------

    def _discover_uwp_apps(self):
        """Discover Microsoft Store (UWP/MSIX) apps via PowerShell."""
        try:
            ps_cmd = (
                "Get-StartApps | "
                "Select-Object Name, AppID | "
                "ConvertTo-Json -Compress"
            )
            result = subprocess.run(
                ["powershell", "-NoProfile", "-Command", ps_cmd],
                capture_output=True, text=True, timeout=30,
                creationflags=subprocess.CREATE_NO_WINDOW,
            )
            if result.returncode != 0:
                return

            apps = json.loads(result.stdout)
            if isinstance(apps, dict):
                apps = [apps]  # single result comes as dict

            for app in apps:
                name = app.get("Name", "")
                app_id = app.get("AppID", "")
                if name and app_id:
                    clean = self._clean_app_name(name)
                    if clean and clean not in self._apps:
                        # Store the AppID – we'll launch via `start shell:AppsFolder\{AppID}`
                        self._apps[clean] = f"shell:AppsFolder\\{app_id}"
        except Exception as e:
            logger.debug(f"UWP discovery skipped: {e}")

    # ---- 4. Common installation directories ----------------------------

    def _discover_common_paths(self):
        """Scan common directories for executables."""
        user_home = str(Path.home())
        search_dirs = [
            r"C:\Program Files",
            r"C:\Program Files (x86)",
            os.path.join(user_home, "AppData", "Local"),
            os.path.join(user_home, "AppData", "Roaming"),
            os.path.join(user_home, "Desktop"),
        ]
        # Only top 2 levels to keep it fast
        for base in search_dirs:
            if not os.path.isdir(base):
                continue
            for entry in os.scandir(base):
                if entry.is_dir():
                    exe = self._find_exe_in_dir(entry.path, entry.name)
                    if exe:
                        clean = self._clean_app_name(entry.name)
                        if clean and clean not in self._apps:
                            self._apps[clean] = exe

    # ---- 5. Built-in Windows apps / accessories -------------------------

    def _add_builtin_windows_apps(self):
        """Add well-known built-in Windows apps and accessories."""
        builtins = {
            "notepad": "notepad.exe",
            "calculator": "calc.exe",
            "paint": "mspaint.exe",
            "wordpad": "wordpad.exe",
            "snipping tool": "snippingtool.exe",
            "task manager": "taskmgr.exe",
            "control panel": "control.exe",
            "settings": "ms-settings:",
            "file explorer": "explorer.exe",
            "command prompt": "cmd.exe",
            "powershell": "powershell.exe",
            "registry editor": "regedit.exe",
            "device manager": "devmgmt.msc",
            "disk management": "diskmgmt.msc",
            "system information": "msinfo32.exe",
            "character map": "charmap.exe",
            "remote desktop": "mstsc.exe",
            "windows media player": "wmplayer.exe",
            "sound recorder": "soundrecorder.exe",
            "magnifier": "magnify.exe",
            "on-screen keyboard": "osk.exe",
            "narrator": "narrator.exe",
            "windows terminal": "wt.exe",
            "xbox game bar": "ms-gamebar:",
            "microsoft store": "ms-windows-store:",
            "maps": "bingmaps:",
            "camera": "microsoft.windows.camera:",
            "clock": "ms-clock:",
            "calendar": "outlookcal:",
            "mail": "outlookmail:",
            "photos": "ms-photos:",
            "weather": "bingweather:",
            "feedback hub": "feedback-hub:",
            "tips": "ms-get-started:",
        }
        for name, path in builtins.items():
            if name not in self._apps:
                self._apps[name] = path

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _find_exe_in_dir(self, directory: str, hint_name: str = "") -> Optional[str]:
        """
        Locate the primary .exe in a directory.
        Prefers an exe whose name matches the directory/hint name.
        """
        try:
            if not os.path.isdir(directory):
                return None
            exes: List[str] = []
            for entry in os.scandir(directory):
                if entry.is_file() and entry.name.lower().endswith(".exe"):
                    exes.append(entry.path)
            if not exes:
                # Check one level deeper
                for sub in os.scandir(directory):
                    if sub.is_dir():
                        for entry in os.scandir(sub.path):
                            if entry.is_file() and entry.name.lower().endswith(".exe"):
                                exes.append(entry.path)

            if not exes:
                return None

            # Prefer exe matching the hint name
            hint_lower = hint_name.lower().replace(" ", "")
            for exe in exes:
                exe_stem = Path(exe).stem.lower().replace(" ", "")
                if exe_stem == hint_lower or hint_lower in exe_stem:
                    return exe

            # Exclude obvious non-app executables
            skip_patterns = {"unins", "update", "setup", "install", "crash", "helper",
                             "service", "daemon", "worker", "repair", "uninst"}
            filtered = [e for e in exes
                        if not any(s in Path(e).stem.lower() for s in skip_patterns)]
            return filtered[0] if filtered else exes[0]
        except PermissionError:
            return None

    @staticmethod
    def _clean_app_name(raw_name: str) -> str:
        """
        Clean a raw application name for use as a voice command key.
        E.g. 'Google Chrome (64-bit)' → 'google chrome'
        """
        name = raw_name.strip()
        # Remove version numbers & parenthetical info
        name = re.sub(r'\(.*?\)', '', name)
        name = re.sub(r'\[.*?\]', '', name)
        name = re.sub(r'\bv?\d+(\.\d+)*\b', '', name)
        # Remove common suffixes
        for suffix in (" - Shortcut", " Desktop", " Setup", " Installer",
                       " Portable", " Updater", " Launcher"):
            if name.lower().endswith(suffix.lower()):
                name = name[:-len(suffix)]
        name = name.strip(" -–—_.")
        name = name.lower()
        # Remove double spaces
        name = re.sub(r'\s+', ' ', name).strip()
        # Skip very short / numeric-only names
        if len(name) < 2 or name.isdigit():
            return ""
        return name

    def _build_aliases(self):
        """Create common aliases for discovered apps."""
        alias_map = {
            "chrome": "google chrome",
            "firefox": "mozilla firefox",
            "edge": "microsoft edge",
            "vs code": "visual studio code",
            "vscode": "visual studio code",
            "code": "visual studio code",
            "word": "microsoft word",
            "excel": "microsoft excel",
            "powerpoint": "microsoft powerpoint",
            "ppt": "microsoft powerpoint",
            "outlook": "microsoft outlook",
            "teams": "microsoft teams",
            "onenote": "microsoft onenote",
            "one note": "microsoft onenote",
            "spotify": "spotify",
            "discord": "discord",
            "steam": "steam",
            "vlc": "vlc media player",
            "obs": "obs studio",
            "photoshop": "adobe photoshop",
            "illustrator": "adobe illustrator",
            "premiere": "adobe premiere pro",
            "aftereffects": "adobe after effects",
            "after effects": "adobe after effects",
            "blender": "blender",
            "gimp": "gimp",
            "whatsapp": "whatsapp",
            "telegram": "telegram",
            "slack": "slack",
            "zoom": "zoom",
            "skype": "skype",
            "brave": "brave browser",
            "opera": "opera browser",
            "notepad++": "notepad++",
            "notepad plus": "notepad++",
            "7zip": "7-zip",
            "7 zip": "7-zip",
            "winrar": "winrar",
            "git": "git",
            "github desktop": "github desktop",
            "terminal": "windows terminal",
            "cmd": "command prompt",
            "powershell": "powershell",
            "explorer": "file explorer",
            "files": "file explorer",
            "calc": "calculator",
            "paint": "paint",
            "camera": "camera",
            "store": "microsoft store",
            "snip": "snipping tool",
            "snipping": "snipping tool",
        }
        for alias, canonical in alias_map.items():
            if canonical in self._apps and alias not in self._apps:
                self._aliases[alias] = canonical


def open_any_app(app_name: str, discovery: AppDiscovery = None) -> Tuple[bool, str]:
    """
    High-level helper: find and launch any Windows application by name.

    Args:
        app_name: Natural-language name of the application.
        discovery: Optional pre-built AppDiscovery instance.

    Returns:
        (success, message)
    """
    if discovery is None:
        discovery = AppDiscovery()

    result = discovery.find_app(app_name)

    if result is None:
        # Last resort: use Windows `start` command which searches PATH + Start Menu
        try:
            subprocess.Popen(
                f'start "" "{app_name}"',
                shell=True,
                creationflags=subprocess.CREATE_NO_WINDOW,
            )
            return True, f"Attempting to open {app_name} via Windows search."
        except Exception:
            return False, f"Could not find any application matching '{app_name}'."

    display_name, exe_path = result

    try:
        if exe_path.startswith("shell:"):
            # UWP / Store app
            subprocess.Popen(
                f'start "" "{exe_path}"',
                shell=True,
                creationflags=subprocess.CREATE_NO_WINDOW,
            )
        elif exe_path.startswith("ms-") or exe_path.endswith(":"):
            # Protocol URI (Settings, Store, etc.)
            subprocess.Popen(
                f'start "" "{exe_path}"',
                shell=True,
                creationflags=subprocess.CREATE_NO_WINDOW,
            )
        elif exe_path.lower().endswith(".msc"):
            # Management console snap-ins
            subprocess.Popen(
                ["mmc", exe_path],
                creationflags=subprocess.CREATE_NO_WINDOW,
            )
        elif os.path.isfile(exe_path):
            subprocess.Popen(
                [exe_path],
                creationflags=subprocess.CREATE_NO_WINDOW,
            )
        else:
            # Might be a system exe in PATH
            subprocess.Popen(
                f'start "" "{exe_path}"',
                shell=True,
                creationflags=subprocess.CREATE_NO_WINDOW,
            )

        return True, f"Successfully opened {display_name}."

    except Exception as e:
        logger.error(f"Failed to launch {display_name}: {e}")
        return False, f"Found {display_name} but failed to launch it: {e}"
