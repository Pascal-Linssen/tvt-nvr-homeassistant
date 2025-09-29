from homeassistant.components.binary_sensor import BinarySensorEntity
from .const import DOMAIN

EVENTS = ("motion", "intrusion")

async def async_setup_entry(hass, entry, async_add_entities):
    entities = []
    for ch in range(1, entry.data["channels"] + 1):
        for ev in EVENTS:
            entities.append(TVTBinarySensor(hass, ch, ev))
    async_add_entities(entities, True)

class TVTBinarySensor(BinarySensorEntity):
    _attr_should_poll = False

    def __init__(self, hass, channel, event):
        self._ch, self._event = channel, event
        self._state = False
        self._attr_name = f"TVT Cam {channel} {event.capitalize()}"
        self._attr_unique_id = f"tvt_cam{channel}_{event}"
        hass.bus.async_listen("tvt_nvr_event", self._handle_event)

    @property
    def is_on(self): return self._state

    def _handle_event(self, ev):
        data = ev.data
        if str(data.get("channel")) == str(self._ch) and data.get("event") == self._event:
            self._state = bool(data.get("on", True))
            self.async_write_ha_state()
