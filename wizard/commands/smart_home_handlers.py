"""
Smart Home Command Handlers - Voice command processing for smart home devices.

This module provides voice command handlers for controlling smart home devices,
managing device groups, and activating scenes through natural language processing.
"""

import re
import logging
from typing import Dict, List, Optional, Tuple, Any

logger = logging.getLogger(__name__)


class SmartHomeHandlers:
    """Handlers for smart home voice commands."""
    
    def __init__(self, controller):
        """Initialize smart home handlers."""
        self.controller = controller
        self.device_aliases = {
            # Light aliases
            "lights": "light",
            "light": "light",
            "lamp": "light",
            "lamps": "light",
            "bulb": "light",
            "bulbs": "light",
            
            # Thermostat aliases
            "thermostat": "thermostat",
            "temperature": "thermostat",
            "heating": "thermostat",
            "cooling": "thermostat",
            "ac": "thermostat",
            "air conditioning": "thermostat",
            
            # Lock aliases
            "lock": "lock",
            "locks": "lock",
            "door": "lock",
            "doors": "lock",
            
            # Smart plug aliases
            "plug": "smart_plug",
            "plugs": "smart_plug",
            "outlet": "smart_plug",
            "outlets": "smart_plug",
            "socket": "smart_plug",
            "sockets": "smart_plug"
        }
        
        self.room_aliases = {
            "living room": ["living", "lounge", "family room"],
            "bedroom": ["bed", "master bedroom", "guest room"],
            "kitchen": ["cook", "dining"],
            "bathroom": ["bath", "restroom", "washroom"],
            "office": ["study", "work room", "den"],
            "garage": ["car", "storage"]
        }
    
    def handle_device_control(self, command: str) -> str:
        """Handle device control commands."""
        try:
            # Parse the command
            action, device_info, parameters = self._parse_control_command(command)
            
            if not action:
                return "I didn't understand the action you want to perform. Try saying 'turn on the lights' or 'set thermostat to 72 degrees'."
            
            # Find the device(s)
            devices = self._find_devices(device_info)
            
            if not devices:
                return f"I couldn't find any devices matching '{device_info.get('name', 'unknown')}'. You can say 'list devices' to see available devices."
            
            # Control the device(s)
            results = []
            for device in devices:
                success, message = self.controller.control_device(device.device_id, action, parameters)
                results.append((device.name, success, message))
            
            # Format response
            if len(results) == 1:
                _, success, message = results[0]
                return message if success else f"Failed to control device: {message}"
            else:
                successful = [name for name, success, _ in results if success]
                failed = [name for name, success, _ in results if not success]
                
                response_parts = []
                if successful:
                    response_parts.append(f"Successfully controlled: {', '.join(successful)}")
                if failed:
                    response_parts.append(f"Failed to control: {', '.join(failed)}")
                
                return ". ".join(response_parts)
        
        except Exception as e:
            logger.error(f"Error handling device control command: {e}")
            return "Sorry, I encountered an error while trying to control the device."
    
    def handle_device_status(self, command: str) -> str:
        """Handle device status inquiry commands."""
        try:
            # Parse device from command
            device_info = self._parse_device_reference(command)
            devices = self._find_devices(device_info)
            
            if not devices:
                return "I couldn't find any devices to check. You can say 'list all devices' to see what's available."
            
            status_reports = []
            for device in devices:
                success, status_info = self.controller.get_device_status(device.device_id)
                if success:
                    status_text = self._format_device_status(status_info)
                    status_reports.append(status_text)
            
            if status_reports:
                return " ".join(status_reports)
            else:
                return "I couldn't get status information for the requested devices."
        
        except Exception as e:
            logger.error(f"Error handling device status command: {e}")
            return "Sorry, I encountered an error while checking device status."
    
    def handle_list_devices(self, command: str) -> str:
        """Handle list devices commands."""
        try:
            # Get all devices
            devices = self.controller.get_devices()
            
            if not devices:
                return "No smart home devices found."
            
            # Format device list
            device_list = []
            for device in devices:
                status_indicator = "✓" if device.status.value == "online" else "✗"
                device_list.append(f"{status_indicator} {device.name} ({device.device_type.value})")
            
            count_text = f"Found {len(devices)} device{'s' if len(devices) != 1 else ''}"
            return f"{count_text}: " + ", ".join(device_list)
        
        except Exception as e:
            logger.error(f"Error handling list devices command: {e}")
            return "Sorry, I encountered an error while listing devices."
    
    def handle_group_control(self, command: str) -> str:
        """Handle device group control commands."""
        try:
            # Parse group name and action
            group_match = re.search(r'(?:group|scene)\s+["\']?([^"\']+)["\']?', command.lower())
            if not group_match:
                return "Please specify a group name, like 'turn on living room group'."
            
            group_name = group_match.group(1).strip()
            group = self.controller.get_group_by_name(group_name)
            
            if not group:
                return f"I couldn't find a group named '{group_name}'. You can create groups by saying 'create group'."
            
            # Parse action
            action, _, parameters = self._parse_control_command(command)
            
            if not action:
                return "I didn't understand what you want to do with the group."
            
            # Control the group
            success, message = self.controller.control_group(group.group_id, action, parameters)
            return message
        
        except Exception as e:
            logger.error(f"Error handling group control command: {e}")
            return "Sorry, I encountered an error while controlling the group."
    
    def handle_scene_activation(self, command: str) -> str:
        """Handle scene activation commands."""
        try:
            # For now, return a placeholder response since scene functionality
            # would require more complex implementation
            return "Scene activation is not yet implemented. You can control individual devices or groups instead."
        
        except Exception as e:
            logger.error(f"Error handling scene activation command: {e}")
            return "Sorry, I encountered an error while activating the scene."
    
    def handle_discovery(self, command: str) -> str:
        """Handle device discovery commands."""
        try:
            # Perform device scan
            devices = self.controller._scan_for_devices()
            if devices:
                device_names = [d.name for d in devices]
                return f"Found {len(devices)} devices: {', '.join(device_names)}"
            else:
                return "No new devices found during scan."
        
        except Exception as e:
            logger.error(f"Error handling discovery command: {e}")
            return "Sorry, I encountered an error during device discovery."
    
    def _parse_control_command(self, command: str) -> Tuple[Optional[str], Dict[str, Any], Dict[str, Any]]:
        """Parse a device control command."""
        command_lower = command.lower()
        action = None
        parameters = {}
        
        # Parse actions
        if re.search(r'\b(turn on|switch on|on)\b', command_lower):
            action = "turn_on"
        elif re.search(r'\b(turn off|switch off|off)\b', command_lower):
            action = "turn_off"
        elif re.search(r'\b(toggle|switch)\b', command_lower):
            action = "toggle"
        elif re.search(r'\b(lock|secure)\b', command_lower):
            action = "lock"
        elif re.search(r'\b(unlock|open)\b', command_lower):
            action = "unlock"
        elif re.search(r'\bset\s+(?:brightness|dim)\b', command_lower):
            action = "set_brightness"
            # Extract brightness value
            brightness_match = re.search(r'(?:to\s+)?(\d+)(?:\s*%)?', command_lower)
            if brightness_match:
                parameters["brightness"] = int(brightness_match.group(1))
        elif re.search(r'\bset\s+(?:temperature|temp)\b', command_lower):
            action = "set_temperature"
            # Extract temperature value
            temp_match = re.search(r'(?:to\s+)?(\d+)(?:\s*(?:degrees?|°))?', command_lower)
            if temp_match:
                parameters["temperature"] = int(temp_match.group(1))
        
        # Parse device information
        device_info = self._parse_device_reference(command)
        
        return action, device_info, parameters
    
    def _parse_device_reference(self, command: str) -> Dict[str, Any]:
        """Parse device reference from command."""
        command_lower = command.lower()
        device_info = {}
        
        # Look for specific device names
        for device in self.controller.get_devices():
            if device.name.lower() in command_lower:
                device_info["name"] = device.name
                device_info["type"] = device.device_type
                return device_info
        
        # Look for device type references
        for alias, device_type in self.device_aliases.items():
            if alias in command_lower:
                device_info["type"] = device_type
                break
        
        # Look for room references
        for room_name, aliases in self.room_aliases.items():
            if room_name in command_lower or any(alias in command_lower for alias in aliases):
                device_info["room"] = room_name
                break
        
        return device_info
    
    def _find_devices(self, device_info: Dict[str, Any]) -> List:
        """Find devices based on parsed device information."""
        if "name" in device_info:
            # Specific device by name
            device = self.controller.get_device_by_name(device_info["name"])
            return [device] if device else []
        
        # Filter by type and/or room
        device_type = device_info.get("type")
        room = device_info.get("room")
        
        devices = self.controller.get_devices()
        
        if device_type:
            devices = [d for d in devices if d.device_type.value == device_type]
        
        if room:
            devices = [d for d in devices if d.room == room]
        
        return devices
    
    def _format_device_status(self, status_info: Dict[str, Any]) -> str:
        """Format device status information for voice response."""
        name = status_info["name"]
        device_type = status_info["type"]
        status = status_info["status"]
        state = status_info["current_state"]
        
        if status != "online":
            return f"{name} is {status}."
        
        # Format based on device type
        if device_type == "light":
            if state.get("on", False):
                brightness = state.get("brightness", 50)
                return f"{name} is on at {brightness}% brightness."
            else:
                return f"{name} is off."
        
        elif device_type == "thermostat":
            temp = state.get("temperature", "unknown")
            mode = state.get("mode", "unknown")
            return f"{name} is set to {temp} degrees in {mode} mode."
        
        elif device_type == "lock":
            locked = state.get("locked", True)
            lock_state = "locked" if locked else "unlocked"
            return f"{name} is {lock_state}."
        
        elif device_type == "smart_plug":
            if state.get("on", False):
                return f"{name} is on."
            else:
                return f"{name} is off."
        
        else:
            return f"{name} is {status}."


# Integration functions for command router
def register_smart_home_handlers(command_router, controller):
    """Register smart home handlers with the command router."""
    handlers = SmartHomeHandlers(controller)
    
    # Device control patterns
    control_patterns = [
        r'\b(turn|switch)\s+(on|off)\b.*\b(light|lamp|bulb)\b',
        r'\b(lock|unlock)\b.*\b(door|lock)\b',
        r'\bset\s+(temperature|thermostat)\b',
        r'\bset\s+(brightness|dim)\b',
        r'\b(turn|switch)\s+(on|off)\b.*\b(plug|outlet)\b'
    ]
    
    for pattern in control_patterns:
        command_router.register_handler(pattern, handlers.handle_device_control)
    
    # Status inquiry patterns
    status_patterns = [
        r'\b(status|state)\b.*\b(device|light|lock|thermostat|plug)\b',
        r'\bhow\s+is\b.*\b(device|light|lock|thermostat|plug)\b',
        r'\bis\s+.*\b(on|off|locked|unlocked)\b'
    ]
    
    for pattern in status_patterns:
        command_router.register_handler(pattern, handlers.handle_device_status)
    
    # List devices patterns
    command_router.register_handler(r'\blist\s+(all\s+)?devices\b', handlers.handle_list_devices)
    command_router.register_handler(r'\bshow\s+(all\s+)?devices\b', handlers.handle_list_devices)
    
    # Group control patterns
    command_router.register_handler(r'\b(control|turn)\b.*\bgroup\b', handlers.handle_group_control)
    
    # Scene activation patterns
    command_router.register_handler(r'\b(activate|set|run)\b.*\bscene\b', handlers.handle_scene_activation)
    
    # Discovery patterns
    command_router.register_handler(r'\b(discover|scan|find)\b.*\bdevices?\b', handlers.handle_discovery)


def create_smart_home_integration(config_path: str = "config/smart_home_config.json"):
    """Create smart home controller and handlers for integration."""
    # Import here to avoid circular imports
    # Add project root to Python path for imports
    import sys
    from pathlib import Path
    project_root = Path(__file__).parent.parent.parent
    sys.path.insert(0, str(project_root))

    import wizard.commands.smart_home_controller as shc

    controller = shc.SmartHomeController()  # Don't pass config_path for now
    handlers = SmartHomeHandlers(controller)

    return controller, handlers