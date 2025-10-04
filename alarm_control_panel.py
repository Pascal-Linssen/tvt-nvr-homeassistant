"""Panneau de contrôle d'alarme pour TVT NVR."""
import logging
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

# Import avec gestion des différentes versions de Home Assistant
try:
    from homeassistant.components.alarm_control_panel import AlarmControlPanelEntity
    ALARM_ENTITY_AVAILABLE = True
except ImportError:
    _LOGGER.warning("AlarmControlPanelEntity not available, alarm panel disabled")
    ALARM_ENTITY_AVAILABLE = False
    # Classe placeholder pour éviter les erreurs
    class AlarmControlPanelEntity:
        pass

async def async_setup_entry(hass, entry, async_add_entities):
    """Configuration de l'entité panneau d'alarme."""
    if not ALARM_ENTITY_AVAILABLE:
        _LOGGER.warning("Alarm control panel not available in this HA version")
        return
        
    coordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([TVTAlarmPanel(coordinator)], True)

class TVTAlarmPanel(AlarmControlPanelEntity):
    """Panneau de contrôle d'alarme TVT NVR."""
    
    def __init__(self, coordinator):
        """Initialise le panneau d'alarme."""
        self.coordinator = coordinator
        self._attr_name = "TVT NVR Alarm"
        self._attr_unique_id = "tvt_alarm_panel"
        self._attr_should_poll = True
        
        # Ne pas définir de features pour éviter les erreurs d'import
        # Les méthodes arm/disarm seront disponibles par défaut
        
    @property
    def state(self):
        """Retourne l'état actuel de l'alarme."""
        if hasattr(self.coordinator, 'armed'):
            return "armed_home" if self.coordinator.armed else "disarmed"
        return "disarmed"
    
    @property
    def available(self):
        """Retourne si l'entité est disponible."""
        return True
        
    async def async_alarm_disarm(self, code=None):
        """Désarme l'alarme."""
        await self.coordinator.set_armed(False)
        self.async_write_ha_state()
        
    async def async_alarm_arm_home(self, code=None):
        """Arme l'alarme en mode maison.""" 
        await self.coordinator.set_armed(True)
        self.async_write_ha_state()
        
    async def async_alarm_arm_away(self, code=None):
        """Arme l'alarme en mode absent."""
        await self.coordinator.set_armed(True)
        self.async_write_ha_state()
        
    async def async_update(self):
        """Met à jour l'état de l'entité."""
        # L'état est géré par les propriétés
        pass

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
