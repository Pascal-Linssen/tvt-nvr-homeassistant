import logging
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.const import Platform
from homeassistant.components import webhook
from .const import DOMAIN, WEBHOOK_ID
from .coordinator import TVTCoordinator
from .raw_server import TVTRawServer

PLATFORMS = [Platform.BINARY_SENSOR, Platform.SWITCH, Platform.ALARM_CONTROL_PANEL]
_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry):
    coordinator = TVTCoordinator(hass, entry)
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator

    # Webhook standard avec ID unique
    hook_id = f"{WEBHOOK_ID}_{entry.entry_id}"
    
    # S'assurer que le webhook n'existe pas déjà
    try:
        webhook.async_unregister(hass, hook_id)
        _LOGGER.debug("Cleaned up existing webhook: %s", hook_id)
    except (ValueError, KeyError):
        pass  # Le webhook n'existait pas, c'est normal
    
    async def _handle(hass, webhook_id, request):
        """Handler webhook pour les notifications du NVR."""
        try:
            result = await coordinator.handle_push(request)
            return result
        except Exception as e:
            _LOGGER.error("Webhook error: %s", e)
            return "ERROR"
    
    # Enregistrer le webhook
    webhook.async_register(hass, DOMAIN, "TVT NVR Alarm", hook_id, _handle)
    _LOGGER.info("Webhook registered: %s", hook_id)

    # Serveur TCP brut pour gérer les requêtes malformées (optionnel)
    raw_server = TVTRawServer(coordinator, port=8124)
    hass.data[DOMAIN][f"{entry.entry_id}_raw_server"] = raw_server
    
    try:
        await raw_server.start()
        _LOGGER.info("TVT Raw Server started on port 8124 for malformed requests")
    except Exception as e:
        _LOGGER.warning("Could not start TVT Raw Server: %s", e)

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
    # Arrêter le serveur TCP brut
    raw_server = hass.data[DOMAIN].get(f"{entry.entry_id}_raw_server")
    if raw_server:
        await raw_server.stop()
    
    # Désinscrire le webhook (avec gestion d'erreur)
    hook_id = f"{WEBHOOK_ID}_{entry.entry_id}"
    try:
        webhook.async_unregister(hass, hook_id)
        _LOGGER.debug("Webhook unregistered successfully: %s", hook_id)
    except ValueError as e:
        _LOGGER.warning("Error unregistering webhook %s: %s", hook_id, e)
    
    # Nettoyer les données
    if DOMAIN in hass.data and entry.entry_id in hass.data[DOMAIN]:
        del hass.data[DOMAIN][entry.entry_id]
    
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
