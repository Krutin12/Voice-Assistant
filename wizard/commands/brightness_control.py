"""
Brightness Control Module
Handles system screen brightness control
"""

try:
    import screen_brightness_control as sbc
    BRIGHTNESS_AVAILABLE = True
except ImportError:
    BRIGHTNESS_AVAILABLE = False

def get_brightness():
    """Get current screen brightness"""
    if not BRIGHTNESS_AVAILABLE:
        return "Brightness control not available. Please install screen-brightness-control."
    
    try:
        brightness = sbc.get_brightness()
        # Returns a list, usually with one value for the primary monitor
        if isinstance(brightness, list) and len(brightness) > 0:
            return brightness[0]
        return brightness
    except Exception as e:
        return f"Error getting brightness: {str(e)}"

def set_brightness(level):
    """Set brightness to specific level (0-100)"""
    if not BRIGHTNESS_AVAILABLE:
        return "Brightness control not available."
    
    try:
        if not 0 <= level <= 100:
            return "Brightness must be between 0 and 100"
        
        sbc.set_brightness(level)
        return f"Brightness set to {level} percent"
    except Exception as e:
        return f"Error setting brightness: {str(e)}"

def increase_brightness(increment=10):
    """Increase brightness by percentage"""
    try:
        current = get_brightness()
        if isinstance(current, str): return current
        new_level = min(100, current + increment)
        return set_brightness(new_level)
    except Exception as e:
        return f"Error increasing brightness: {str(e)}"

def decrease_brightness(decrement=10):
    """Decrease brightness by percentage"""
    try:
        current = get_brightness()
        if isinstance(current, str): return current
        new_level = max(0, current - decrement)
        return set_brightness(new_level)
    except Exception as e:
        return f"Error decreasing brightness: {str(e)}"
