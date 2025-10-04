"""Config flow for TVT NVR integration."""
import voluptuous as vol
from homeassistant import config_entries  # type: ignore
from .const import DOMAIN, CONF_IP, CONF_USERNAME, CONF_PASSWORD, CONF_PORT, CONF_CHANNELS, CONF_USE_PUSH, CONF_ALARM_IN, CONF_ALARM_OUT

class TVTConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):  # type: ignore
    VERSION = 1

    async def async_step_user(self, user_input=None):
        if user_input is not None:
            return self.async_create_entry(title=f"TVT NVR @ {user_input[CONF_IP]}", data=user_input)

        data_schema = vol.Schema({
            vol.Required(CONF_IP): str,
            vol.Required(CONF_USERNAME, default="admin"): str,  # type: ignore
            vol.Required(CONF_PASSWORD): str,
            vol.Optional(CONF_PORT, default=80): int,  # type: ignore
            vol.Optional(CONF_CHANNELS, default=16): int,  # type: ignore
            vol.Optional(CONF_ALARM_IN, default=4): int,  # type: ignore
            vol.Optional(CONF_ALARM_OUT, default=2): int,  # type: ignore
            vol.Optional(CONF_USE_PUSH, default=True): bool,  # type: ignore
        })

        return self.async_show_form(step_id="user", data_schema=data_schema)
