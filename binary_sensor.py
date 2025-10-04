from homeassistant.components.binary_sensor import BinarySensorEntity
from .const import DOMAIN, ATTR_ARMED

EVENTS = ("motion", "intrusion")

async def async_setup_entry(hass, entry, async_add_entities):
    coordinator = hass.data[DOMAIN][entry.entry_id]

    entities = []
    for ch in range(1, entry.data["channels"] + 1):
        for ev in EVENTS:
            entities.append(TVTEventBinarySensor(hass, ch, ev))

    for i in range(1, coordinator.alarm_in_count + 1):
        entities.append(TVTAlarmInputBinarySensor(hass, coordinator, i))

    entities.append(TVTArmedBinarySensor(coordinator))

    async_add_entities(entities, True)

class TVTEventBinarySensor(BinarySensorEntity):
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

class TVTAlarmInputBinarySensor(BinarySensorEntity):
    _attr_should_poll = True
    device_class = "problem"

    def __init__(self, hass, coordinator, input_id: int):
        self.coordinator = coordinator
        self._id = input_id
        self._state = False
        self._attr_name = f"TVT Alarm In {input_id}"
        self._attr_unique_id = f"tvt_alarm_in_{input_id}"

    async def async_update(self):
        self._state = bool(self.coordinator.state_inputs.get(self._id, False))

    @property
    def is_on(self): return self._state

class TVTArmedBinarySensor(BinarySensorEntity):
    _attr_should_poll = True
    device_class = "safety"

    def __init__(self, coordinator):
        self.coordinator = coordinator
        self._state = coordinator.armed
        self._attr_name = "TVT NVR Armé"
        self._attr_unique_id = "tvt_armed"

    async def async_update(self):
        self._state = bool(self.coordinator.armed)

    @property
    def is_on(self): return self._state
