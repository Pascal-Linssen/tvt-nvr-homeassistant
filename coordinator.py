import aiohttp, base64
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
from datetime import timedelta
from .const import DOMAIN

class TVTCoordinator(DataUpdateCoordinator):
    def __init__(self, hass, entry):
        super().__init__(hass, hass.logger, name=DOMAIN, update_interval=timedelta(seconds=10))
        self.hass, self.entry = hass, entry
        self.ip = entry.data["ip"]
        self.port = entry.data["port"]
        self.user = entry.data["username"]
        self.pwd = entry.data["password"]
        token = base64.b64encode(f"{self.user}:{self.pwd}".encode()).decode()
        self.headers = {"Authorization": f"Basic {token}", "Content-Type": "application/xml"}
        self.session = aiohttp.ClientSession()

    async def handle_push(self, request):
        try:
            if request.method == "POST":
                payload = await request.json(content_type=None)
            else:
                payload = dict(request.query)
        except:
            payload = {"raw": await request.text()}
        # Normalisation minimale (facultatif)
        e = str(payload.get("event") or payload.get("eventType") or payload.get("type") or "unknown").lower()
        ch = int(payload.get("channel") or payload.get("ch") or payload.get("cam") or 0)
        st = str(payload.get("state") or payload.get("status") or payload.get("action") or "start").lower()
        on = st in ("start","on","true","1","alarm","active","begin")
        self.hass.bus.async_fire("tvt_nvr_event", {"event": e, "channel": ch, "on": on, "raw": payload})
        return "OK"

    async def pulse_output(self, out_id, hold=1):
        xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<config version="2.0.0" xmlns="http://www.ipc.com/ver10">
  <alarmOut>
    <alarmHoldTime>{hold}</alarmHoldTime>
  </alarmOut>
</config>"""
        await self.session.post(f"http://{self.ip}:{self.port}/SetAlarmOutConfig/{out_id}", headers=self.headers, data=xml)
        xml2 = """<?xml version="1.0" encoding="UTF-8"?>
<config version="2.0.0" xmlns="http://www.ipc.com/ver10">
  <action><status>true</status></action>
</config>"""
        await self.session.post(f"http://{self.ip}:{self.port}/ManualAlarmOut/{out_id}", headers=self.headers, data=xml2)
