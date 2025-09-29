import logging
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.const import Platform
from homeassistant.components import webhook
from .const import DOMAIN, WEBHOOK_ID
from .coordinator import TVTCoordinator

PLATFORMS = [Platform.BINARY_SENSOR]
_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry):
    coordinator = TVTCoordinator(hass, entry)
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator

    # Webhook
    hook_id = f"{WEBHOOK_ID}_{entry.entry_id}"

    async def _handle(hass, webhook_id, request):
        await coordinator.handle_push(request)
        from homeassistant.components.webhook import WebhookResponse
        return WebhookResponse(text="OK")

    webhook.async_register(hass, DOMAIN, "TVT NVR Alarm", hook_id, _handle)

    # Service pulse_output
    async def pulse_output(call):
        out_id = int(call.data["output"])
        hold = int(call.data.get("hold", 1))
        await coordinator.pulse_output(out_id, hold)

    hass.services.async_register(DOMAIN, "pulse_output", pulse_output)

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True
