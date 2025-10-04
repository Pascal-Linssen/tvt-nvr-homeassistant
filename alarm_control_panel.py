from homeassistant.components.alarm_control_panel import AlarmControlPanelEntity
from .const import DOMAIN

# Import des features avec fallback pour différentes versions de HA
try:
    from homeassistant.components.alarm_control_panel import AlarmControlPanelEntityFeature
    FEATURES_AVAILABLE = True
except ImportError:
    try:
        from homeassistant.components.alarm_control_panel.const import AlarmControlPanelEntityFeature
        FEATURES_AVAILABLE = True
    except ImportError:
        FEATURES_AVAILABLE = False

async def async_setup_entry(hass, entry, async_add_entities):
    coordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([TVTAlarmPanel(coordinator)], True)

class TVTAlarmPanel(AlarmControlPanelEntity):
    _attr_should_poll = True
    
    def __init__(self, coordinator):
        self.coordinator = coordinator
        self._state = "armed_home" if coordinator.armed else "disarmed"
        self._attr_name = "TVT NVR Alarm"
        self._attr_unique_id = "tvt_alarm_panel"
        
        # Support des fonctionnalités avec gestion des versions
        if FEATURES_AVAILABLE:
            try:
                # Essayons d'abord les nouvelles constantes
                features = 0
                if hasattr(AlarmControlPanelEntityFeature, 'ARM_HOME'):
                    features |= AlarmControlPanelEntityFeature.ARM_HOME
                if hasattr(AlarmControlPanelEntityFeature, 'ARM_AWAY'):
                    features |= AlarmControlPanelEntityFeature.ARM_AWAY
                if hasattr(AlarmControlPanelEntityFeature, 'DISARM'):
                    features |= AlarmControlPanelEntityFeature.DISARM
                    
                self._attr_supported_features = features
            except Exception:
                # Fallback sans features
                self._attr_supported_features = 0
        else:
            self._attr_supported_features = 0

    @property
    def state(self):
        return self._state

    async def async_alarm_arm_home(self, code=None):
        await self.coordinator.set_armed(True)
        self._state = "armed_home"
        self.async_write_ha_state()

    async def async_alarm_disarm(self, code=None):
        await self.coordinator.set_armed(False)
        self._state = "disarmed"
        self.async_write_ha_state()

    async def async_update(self):
        self._state = "armed_home" if self.coordinator.armed else "disarmed"
