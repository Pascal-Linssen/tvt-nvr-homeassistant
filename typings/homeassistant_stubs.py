# Type stubs for Home Assistant imports
# This file helps VS Code understand Home Assistant imports without requiring the full package

# homeassistant.core
class HomeAssistant:
    pass

class ConfigEntry:
    pass

# homeassistant.const
class Platform:
    BINARY_SENSOR = "binary_sensor"
    SWITCH = "switch"
    ALARM_CONTROL_PANEL = "alarm_control_panel"

# homeassistant.helpers
class DataUpdateCoordinator:
    pass

def async_get_clientsession(hass):
    pass

# homeassistant.components
class webhook:
    @staticmethod
    def async_register(hass, domain, name, hook_id, handler):
        pass
    
    @staticmethod
    def async_unregister(hass, hook_id):
        pass

# homeassistant.components.alarm_control_panel
class AlarmControlPanelEntity:
    def __init__(self):
        self._attr_should_poll = False
        self._attr_name = ""
        self._attr_unique_id = ""
    
    async def async_alarm_disarm(self, code=None):
        pass
    
    async def async_alarm_arm_home(self, code=None):
        pass
    
    async def async_alarm_arm_away(self, code=None):
        pass
    
    def async_write_ha_state(self):
        pass

# homeassistant.components.binary_sensor
class BinarySensorEntity:
    def __init__(self):
        self._attr_should_poll = False
        self._attr_name = ""
        self._attr_unique_id = ""

# homeassistant.components.switch
class SwitchEntity:
    def __init__(self):
        self._attr_should_poll = False
        self._attr_name = ""
        self._attr_unique_id = ""
    
    async def async_turn_on(self, **kwargs):
        pass
    
    async def async_turn_off(self, **kwargs):
        pass