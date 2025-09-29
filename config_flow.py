import voluptuous as vol
from homeassistant import config_entries
from .const import DOMAIN, CONF_IP, CONF_USERNAME, CONF_PASSWORD, CONF_PORT, CONF_CHANNELS, CONF_USE_PUSH

class TVTConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(self, user_input=None):
        if user_input is not None:
            return self.async_create_entry(title=f"TVT NVR @ {user_input[CONF_IP]}", data=user_input)

        schema = vol.Schema({
            vol.Required(CONF_IP): str,
            vol.Required(CONF_USERNAME, default="admin"): str,
            vol.Required(CONF_PASSWORD): str,
            vol.Optional(CONF_PORT, default=80): int,
            vol.Optional(CONF_CHANNELS, default=16): int,
            vol.Optional(CONF_USE_PUSH, default=True): bool,
        })
        return self.async_show_form(step_id="user", data_schema=schema)
