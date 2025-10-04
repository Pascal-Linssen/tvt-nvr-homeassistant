import logging
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.const import Platform
from homeassistant.components import webhook
from homeassistant.components.webhook import WebhookResponse
from aiohttp import web
from aiohttp.web_exceptions import HTTPBadRequest
from .const import DOMAIN, WEBHOOK_ID
from .coordinator import TVTCoordinator

PLATFORMS = [Platform.BINARY_SENSOR, Platform.SWITCH, Platform.ALARM_CONTROL_PANEL]
_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry):
    coordinator = TVTCoordinator(hass, entry)
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator

    # Webhook avec gestion améliorée pour les données XML du NVR
    hook_id = f"{WEBHOOK_ID}_{entry.entry_id}"
    
    async def _handle(hass, webhook_id, request):
        """Handler webhook personnalisé pour gérer les requêtes malformées du NVR."""
        try:
            result = await coordinator.handle_push(request)
            return WebhookResponse(text=result)
        except Exception as e:
            _LOGGER.error("Webhook error: %s", e)
            return WebhookResponse(text="ERROR", status=500)
    
    webhook.async_register(hass, DOMAIN, "TVT NVR Alarm", hook_id, _handle)

    # Services
    async def pulse_output(call):
        out_id = int(call.data["output"])
        hold = int(call.data.get("hold", 1))
        await coordinator.pulse_output(out_id, hold)
    hass.services.async_register(DOMAIN, "pulse_output", pulse_output)

    async def arm(call):
        await coordinator.set_armed(True)
    hass.services.async_register(DOMAIN, "arm", arm)

    async def disarm(call):
        await coordinator.set_armed(False)
    hass.services.async_register(DOMAIN, "disarm", disarm)

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry):
    from homeassistant.components.webhook import async_unregister
    hook_id = f"{WEBHOOK_ID}_{entry.entry_id}"
    async_unregister(hass, hook_id)
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
