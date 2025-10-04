from homeassistant.components.alarm_control_panel import AlarmControlPanelEntity, AlarmControlPanelEntityFeature
from .const import DOMAIN

async def async_setup_entry(hass, entry, async_add_entities):
    coordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([TVTAlarmPanel(coordinator)], True)

class TVTAlarmPanel(AlarmControlPanelEntity):
    _attr_should_poll = True
    _attr_supported_features = (
        AlarmControlPanelEntityFeature.ARM_HOME |
        AlarmControlPanelEntityFeature.DISARM
    )

    def __init__(self, coordinator):
        self.coordinator = coordinator
        self._state = "armed_home" if coordinator.armed else "disarmed"
        self._attr_name = "TVT NVR"
        self._attr_unique_id = "tvt_alarm_panel"

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
