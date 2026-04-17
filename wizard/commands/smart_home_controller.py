"""Smart Home Controller - Foundation for IoT device management and control."""

import json
import time
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class DeviceType(Enum):
    """Enumeration of supported smart home device types."""
    LIGHT = "light"
    THERMOSTAT = "thermostat"
    LOCK = "lock"
    SMART_PLUG = "smart_plug"


class DeviceStatus(Enum):
    """Enumeration of device connection statuses."""
    ONLINE = "online"
    OFFLINE = "offline"
    ERROR = "error"


@dataclass
class SmartDevice:
    """Represents a smart home device."""
    device_id: str
    name: str
    device_type: DeviceType
    manufacturer: str
    model: str
    status: DeviceStatus = DeviceStatus.OFFLINE
    current_state: Dict[str, Any] = None
    room: Optional[str] = None
    
    def __post_init__(self):
        if self.current_state is None:
            self.current_state = {}


@dataclass
class DeviceGroup:
    """Represents a group of smart home devices."""
    group_id: str
    name: str
    device_ids: List[str]


class SmartHomeController:
    """Main controller for smart home device management."""
    
    def __init__(self, config_path: str = "config/smart_home_config.json"):
        """Initialize the Smart Home Controller."""
        self.config_path = config_path
        self.devices: Dict[str, SmartDevice] = {}
        self.groups: Dict[str, DeviceGroup] = {}
        self._initialize_sample_devices()
    
    def _initialize_sample_devices(self):
        """Initialize with sample devices for demo purposes."""
        sample_devices = [
            SmartDevice("light1", "Living Room Light", DeviceType.LIGHT, "Philips", "Hue"),
            SmartDevice("thermostat1", "Main Thermostat", DeviceType.THERMOSTAT, "Nest", "Learning"),
            SmartDevice("lock1", "Front Door Lock", DeviceType.LOCK, "August", "Smart Lock")
        ]
        
        for device in sample_devices:
            device.status = DeviceStatus.ONLINE
            device.current_state = self._get_default_state(device.device_type)
            self.devices[device.device_id] = device
    
    def _get_default_state(self, device_type: DeviceType) -> Dict[str, Any]:
        """Get default state for a device type."""
        defaults = {
            DeviceType.LIGHT: {"on": False, "brightness": 50},
            DeviceType.THERMOSTAT: {"temperature": 72, "mode": "auto"},
            DeviceType.LOCK: {"locked": True},
            DeviceType.SMART_PLUG: {"on": False}
        }
        return defaults.get(device_type, {})
    
    def get_devices(self, device_type: Optional[DeviceType] = None) -> List[SmartDevice]:
        """Get list of devices with optional filtering."""
        devices = list(self.devices.values())
        if device_type:
            devices = [d for d in devices if d.device_type == device_type]
        return devices
    
    def get_device(self, device_id: str) -> Optional[SmartDevice]:
        """Get a specific device by ID."""
        return self.devices.get(device_id)
    
    def get_device_by_name(self, name: str) -> Optional[SmartDevice]:
        """Get a device by name."""
        for device in self.devices.values():
            if device.name.lower() == name.lower():
                return device
        return None
    
    def control_device(self, device_id: str, action: str, parameters: Dict[str, Any] = None) -> Tuple[bool, str]:
        """Control a smart home device."""
        device = self.get_device(device_id)
        if not device:
            return False, f"Device {device_id} not found"
        
        if device.status != DeviceStatus.ONLINE:
            return False, f"Device {device.name} is offline"
        
        if parameters is None:
            parameters = {}
        
        # Simple device control logic
        if device.device_type == DeviceType.LIGHT:
            if action == "turn_on":
                device.current_state["on"] = True
                return True, f"{device.name} turned on"
            elif action == "turn_off":
                device.current_state["on"] = False
                return True, f"{device.name} turned off"
        
        elif device.device_type == DeviceType.THERMOSTAT:
            if action == "set_temperature":
                temp = parameters.get("temperature", 72)
                device.current_state["temperature"] = temp
                return True, f"{device.name} temperature set to {temp}°F"
        
        elif device.device_type == DeviceType.LOCK:
            if action == "lock":
                device.current_state["locked"] = True
                return True, f"{device.name} locked"
            elif action == "unlock":
                device.current_state["locked"] = False
                return True, f"{device.name} unlocked"
        
        return False, f"Action '{action}' not supported"
    
    def get_device_status(self, device_id: str) -> Tuple[bool, Dict[str, Any]]:
        """Get current status of a device."""
        device = self.get_device(device_id)
        if not device:
            return False, {"error": f"Device {device_id} not found"}
        
        return True, {
            "device_id": device.device_id,
            "name": device.name,
            "type": device.device_type.value,
            "status": device.status.value,
            "current_state": device.current_state
        }
    
    def _scan_for_devices(self) -> List[SmartDevice]:
        """Scan for new devices."""
        return list(self.devices.values())
    
    def shutdown(self) -> None:
        """Shutdown the controller."""
        pass 
   
    def create_device_group(self, group_name: str, device_ids: List[str]) -> Tuple[bool, str]:
        """Create a group of devices."""
        group_id = f"group_{len(self.groups) + 1}"
        group = DeviceGroup(group_id, group_name, device_ids)
        self.groups[group_id] = group
        return True, f"Group '{group_name}' created"
    
    def control_group(self, group_id: str, action: str, parameters: Dict[str, Any] = None) -> Tuple[bool, str]:
        """Control all devices in a group."""
        group = self.groups.get(group_id)
        if not group:
            return False, f"Group {group_id} not found"
        
        results = []
        for device_id in group.device_ids:
            success, message = self.control_device(device_id, action, parameters)
            results.append(success)
        
        successful = sum(results)
        total = len(results)
        return True, f"{successful}/{total} devices controlled successfully"
    
    def get_groups(self) -> List[DeviceGroup]:
        """Get list of all device groups."""
        return list(self.groups.values())
    
    def get_group_by_name(self, name: str) -> Optional[DeviceGroup]:
        """Get a group by name."""
        for group in self.groups.values():
            if group.name.lower() == name.lower():
                return group
        return None