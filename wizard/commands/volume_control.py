"""
Volume Control Module
Handles system volume control using pycaw library
"""

try:
    from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
    from ctypes import cast, POINTER
    from comtypes import CLSCTX_ALL
    PYCAW_AVAILABLE = True
except ImportError:
    PYCAW_AVAILABLE = False

def _get_volume_interface():
    """Helper to get the volume interface robustly"""
    if not PYCAW_AVAILABLE:
        return None
    try:
        devices = AudioUtilities.GetSpeakers()
        # Newer pycaw wrapper uses EndpointVolume attribute
        if hasattr(devices, 'EndpointVolume'):
            return devices.EndpointVolume
        # Traditional pycaw uses Activate method
        interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
        return cast(interface, POINTER(IAudioEndpointVolume))
    except Exception:
        return None

def get_current_volume():
    """Get current system volume (0-100)"""
    volume = _get_volume_interface()
    if not volume:
        return 50
    try:
        current_volume = int(volume.GetMasterVolumeLevelScalar() * 100)
        return current_volume
    except Exception:
        return 50

def set_volume(level):
    """Set volume to specific level (0-100)"""
    volume = _get_volume_interface()
    if not volume:
        return "Volume control not available. Please install pycaw."
    try:
        if not 0 <= level <= 100:
            return "Volume must be between 0 and 100"
        volume.SetMasterVolumeLevelScalar(level / 100.0, None)
        return f"Volume set to {level} percent"
    except Exception as e:
        return f"Error setting volume: {str(e)}"

def increase_volume(increment=10):
    """Increase volume by percentage"""
    current = get_current_volume()
    new_volume = min(100, current + increment)
    return set_volume(new_volume)

def decrease_volume(decrement=10):
    """Decrease volume by percentage"""
    current = get_current_volume()
    new_volume = max(0, current - decrement)
    return set_volume(new_volume)

def mute_volume():
    """Mute audio"""
    volume = _get_volume_interface()
    if not volume:
        return "Volume control not available."
    try:
        volume.SetMute(1, None)
        return "Audio muted"
    except Exception as e:
        return f"Error muting audio: {str(e)}"

def unmute_volume():
    """Unmute audio"""
    volume = _get_volume_interface()
    if not volume:
        return "Volume control not available."
    try:
        volume.SetMute(0, None)
        return "Audio unmuted"
    except Exception as e:
        return f"Error unmuting audio: {str(e)}"

