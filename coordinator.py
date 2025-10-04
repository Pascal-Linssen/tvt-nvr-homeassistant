import logging
import base64
from datetime import timedelta
import xml.etree.ElementTree as ET

from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import DOMAIN, CONF_CHANNELS, CONF_ALARM_IN, CONF_ALARM_OUT, ATTR_ARMED

_LOGGER = logging.getLogger(__name__)

def _to_bool(txt: str) -> bool:
    return str(txt).strip().lower() in ("1","true","on","start","alarm","active")

class TVTCoordinator(DataUpdateCoordinator):
    """Coordonne push + polling (statuts entrées/sorties) et armement local."""

    def __init__(self, hass, entry):
        super().__init__(hass, _LOGGER, name=DOMAIN, update_interval=timedelta(seconds=5))
        self.hass, self.entry = hass, entry
        self.ip = entry.data["ip"]
        self.port = entry.data["port"]
        self.user = entry.data["username"]
        self.pwd = entry.data["password"]

        token = base64.b64encode(f"{self.user}:{self.pwd}".encode()).decode()
        self.headers = {
            "Authorization": f"Basic {token}",
            "Content-Type": "application/xml",
        }
        self.session = async_get_clientsession(hass)

        self.channels = entry.data.get(CONF_CHANNELS, 16)
        self.alarm_in_count = entry.data.get(CONF_ALARM_IN, 4)
        self.alarm_out_count = entry.data.get(CONF_ALARM_OUT, 2)

        self.state_inputs = {}   # {1: True/False}
        self.state_outputs = {}  # {1: True/False}
        self.armed = True        # état local d'armement

    async def _async_update_data(self):
        """Polling périodique: GetAlarmStatusInfo -> met à jour entrées/sorties."""
        try:
            url = f"http://{self.ip}:{self.port}/GetAlarmStatusInfo"
            async with self.session.get(url, headers=self.headers) as r:
                text = await r.text()
        except Exception as e:
            _LOGGER.debug("Polling error: %s", e)
            return None

        try:
            root = ET.fromstring(text)
        except Exception:
            _LOGGER.debug("XML parse error in GetAlarmStatusInfo")
            return None

        new_inputs = {}
        for node in root.findall(".//sensorAlarmIn"):
            _id = int(node.findtext("id", "0"))
            _st = _to_bool(node.findtext("status", "0"))
            new_inputs[_id] = _st

        new_outputs = {}
        for node in root.findall(".//alarmOutStatus"):
            _id = int(node.findtext("id", "0"))
            _st = _to_bool(node.findtext("status", "0"))
            new_outputs[_id] = _st

        self.state_inputs.update(new_inputs)
        self.state_outputs.update(new_outputs)

        return {"inputs": self.state_inputs, "outputs": self.state_outputs, ATTR_ARMED: self.armed}

    # ==== PUSH (webhook) ======================================================
    async def handle_push(self, request):
        try:
            if request.method == "POST":
                payload = await request.json(content_type=None)
            else:
                payload = dict(request.query)
        except Exception:
            payload = {"raw": await request.text()}

        e = str(payload.get("event") or payload.get("eventType") or payload.get("type") or "unknown").lower()
        ch = int(payload.get("channel") or payload.get("ch") or payload.get("cam") or 0)
        st = str(payload.get("state") or payload.get("status") or payload.get("action") or "start").lower()
        on = st in ("start", "on", "true", "1", "alarm", "active", "begin")

        self.hass.bus.async_fire("tvt_nvr_event", {"event": e, "channel": ch, "on": on, "armed": self.armed, "raw": payload})
        return "OK"

    # ==== SORTIES =============================================================
    async def set_alarm_hold_time(self, out_id: int, seconds: int):
        xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<config version="2.0.0" xmlns="http://www.ipc.com/ver10">
  <alarmOut>
    <alarmHoldTime>{seconds}</alarmHoldTime>
  </alarmOut>
</config>"""
        url = f"http://{self.ip}:{self.port}/SetAlarmOutConfig/{out_id}"
        async with self.session.post(url, headers=self.headers, data=xml) as r:
            await r.text()

    async def pulse_output(self, out_id: int, hold: int = 1):
        await self.set_alarm_hold_time(out_id, hold)
        xml = """<?xml version="1.0" encoding="UTF-8"?>
<config version="2.0.0" xmlns="http://www.ipc.com/ver10">
  <action><status>true</status></action>
</config>"""
        url = f"http://{self.ip}:{self.port}/ManualAlarmOut/{out_id}"
        async with self.session.post(url, headers=self.headers, data=xml) as r:
            await r.text()

    async def set_output_state(self, out_id: int, state: bool):
        status = "true" if state else "false"
        xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<config version="2.0.0" xmlns="http://www.ipc.com/ver10">
  <action><status>{status}</status></action>
</config>"""
        url = f"http://{self.ip}:{self.port}/ManualAlarmOut/{out_id}"
        async with self.session.post(url, headers=self.headers, data=xml) as r:
            await r.text()

    # ==== ARM/DISARM ==========================================================
    async def set_armed(self, armed: bool):
        self.armed = bool(armed)
        self.async_set_updated_data({"inputs": self.state_inputs, "outputs": self.state_outputs, ATTR_ARMED: self.armed})
