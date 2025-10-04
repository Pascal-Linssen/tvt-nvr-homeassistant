"""TVT NVR Data Update Coordinator."""
import logging
import base64
from datetime import timedelta
import xml.etree.ElementTree as ET

from homeassistant.helpers.update_coordinator import DataUpdateCoordinator  # type: ignore
from homeassistant.helpers.aiohttp_client import async_get_clientsession  # type: ignore

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
        """Gère les notifications push du NVR TVT qui envoie du XML brut."""
        try:
            # Le NVR TVT envoie du XML brut, pas du JSON
            content_type = request.headers.get('content-type', '').lower()
            
            if request.method == "POST":
                # Essayons d'abord de lire le contenu comme XML
                raw_data = await request.read()
                
                # Nettoyage des données (suppression des caractères null à la fin)
                if raw_data.endswith(b'\x00'):
                    raw_data = raw_data.rstrip(b'\x00')
                
                try:
                    text_data = raw_data.decode('utf-8')
                    _LOGGER.debug("Received push data: %s", text_data[:500])
                    
                    # Tentative de parsing XML
                    if text_data.strip().startswith('<?xml'):
                        return await self._handle_xml_push(text_data)
                    else:
                        # Essayons JSON en fallback
                        import json
                        payload = json.loads(text_data)
                        return await self._handle_json_push(payload)
                        
                except Exception as e:
                    _LOGGER.warning("Failed to parse push data as XML or JSON: %s", e)
                    # Essayons les query params
                    payload = dict(request.query)
                    return await self._handle_generic_push(payload)
            else:
                # GET request avec query params
                payload = dict(request.query)
                return await self._handle_generic_push(payload)
                
        except Exception as e:
            _LOGGER.error("Error handling push notification: %s", e)
            return "ERROR"

    async def _handle_xml_push(self, xml_data: str):
        """Traite les notifications XML du NVR."""
        try:
            root = ET.fromstring(xml_data)
            
            # Extraction des informations du XML
            event_type = "status_update"
            channel = 0
            is_alarm = False
            
            # Chercher des informations d'alarme
            alarm_offline = root.findtext(".//alarmServerOffLine")
            if alarm_offline:
                is_offline = _to_bool(alarm_offline)
                event_type = "alarm_server_offline" if is_offline else "alarm_server_online"
                
            # Chercher des informations de device
            device_name = root.findtext(".//DeviceName", "Unknown")
            device_ip = root.findtext(".//ipAddress", "")
            
            # Fire l'événement
            event_data = {
                "event": event_type,
                "channel": channel,
                "on": is_alarm,
                "armed": self.armed,
                "device_name": device_name,
                "device_ip": device_ip,
                "xml_data": xml_data[:200]  # Premier bout du XML pour debug
            }
            
            self.hass.bus.async_fire("tvt_nvr_event", event_data)
            _LOGGER.debug("Processed XML push: %s", event_data)
            
            return "OK"
            
        except Exception as e:
            _LOGGER.error("Error parsing XML push data: %s", e)
            return "ERROR"

    async def _handle_json_push(self, payload: dict):
        """Traite les notifications JSON standards."""
        e = str(payload.get("event") or payload.get("eventType") or payload.get("type") or "unknown").lower()
        ch = int(payload.get("channel") or payload.get("ch") or payload.get("cam") or 0)
        st = str(payload.get("state") or payload.get("status") or payload.get("action") or "start").lower()
        on = st in ("start", "on", "true", "1", "alarm", "active", "begin")

        self.hass.bus.async_fire("tvt_nvr_event", {"event": e, "channel": ch, "on": on, "armed": self.armed, "raw": payload})
        return "OK"

    async def _handle_generic_push(self, payload: dict):
        """Traite les notifications génériques."""
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
