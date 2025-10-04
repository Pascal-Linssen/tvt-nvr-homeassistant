from homeassistant.components.switch import SwitchEntity
from .const import DOMAIN

async def async_setup_entry(hass, entry, async_add_entities):
    coordinator = hass.data[DOMAIN][entry.entry_id]
    entities = []
    for out_id in range(1, coordinator.alarm_out_count + 1):
        entities.append(TVTAlarmOutputSwitch(coordinator, out_id))
    async_add_entities(entities, True)

class TVTAlarmOutputSwitch(SwitchEntity):
    _attr_should_poll = True

    def __init__(self, coordinator, out_id: int):
        self.coordinator = coordinator
        self._id = out_id
        self._is_on = False
        self._attr_name = f"TVT Output {out_id}"
        self._attr_unique_id = f"tvt_output_{out_id}"
        self._hold = 1

    @property
    def is_on(self): return self._is_on

    @property
    def extra_state_attributes(self):
        return {"hold": self._hold}

    async def async_turn_on(self, **kwargs):
        hold = kwargs.get("hold") or self._hold
        await self.coordinator.pulse_output(self._id, hold=hold)
        self._is_on = False
        self.async_write_ha_state()

    async def async_turn_off(self, **kwargs):
        self._is_on = False
        self.async_write_ha_state()

    async def async_update(self):
        val = self.coordinator.state_outputs.get(self._id)
        if val is not None:
            self._is_on = bool(val)
