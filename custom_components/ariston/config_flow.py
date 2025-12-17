"""Config flow for Ariston integration."""
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import CONF_NAME, CONF_PASSWORD, CONF_USERNAME
from homeassistant.core import callback
import homeassistant.helpers.config_validation as cv

from .const import (
    DOMAIN,
    CONF_GW,
    CONF_LOG,
    CONF_PERIOD_SET,
    CONF_PERIOD_GET,
    CONF_MAX_SET_RETRIES,
    CONF_CH_ZONES,
)

DEFAULT_NAME = "Ariston"
DEFAULT_MAX_RETRIES = 5
DEFAULT_PERIOD_GET = 30
DEFAULT_PERIOD_SET = 30
DEFAULT_LOG = "WARNING"
DEFAULT_CH_ZONES = 1


class AristonConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Ariston."""

    VERSION = 1

    async def async_step_user(self, user_input=None):
        """Handle the initial step."""
        errors = {}

        if user_input is not None:
            await self.async_set_unique_id(user_input[CONF_USERNAME])

            # If an entry with this unique_id already exists, remove it and replace
            existing = next(
                (e for e in self._async_current_entries() if e.unique_id == user_input[CONF_USERNAME]),
                None,
            )
            if existing:
                await self.hass.config_entries.async_remove(existing.entry_id)

            # Create a fresh entry with the provided data
            return self.async_create_entry(
                title=user_input.get(CONF_NAME, DEFAULT_NAME),
                data=user_input,
            )

        # Show the form
        data_schema = vol.Schema(
            {
                vol.Required(CONF_USERNAME): cv.string,
                vol.Required(CONF_PASSWORD): cv.string,
                vol.Optional(CONF_NAME, default=DEFAULT_NAME): cv.string,
                vol.Optional(CONF_GW, default=""): cv.string,
                vol.Optional(
                    CONF_LOG,
                    default=DEFAULT_LOG,
                ): vol.In(["CRITICAL", "ERROR", "WARNING", "INFO", "DEBUG", "NOTSET"]),
            }
        )

        return self.async_show_form(
            step_id="user",
            data_schema=data_schema,
            errors=errors,
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        """Get the options flow for this handler."""
        return AristonOptionsFlowHandler(config_entry)


class AristonOptionsFlowHandler(config_entries.OptionsFlow):
    """Handle options flow for Ariston."""

    def __init__(self, config_entry):
        """Initialize options flow."""
        self.config_entry = config_entry

    async def async_step_init(self, user_input=None):
        """Manage the options."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        options = self.config_entry.options
        
        data_schema = vol.Schema(
            {
                vol.Optional(
                    CONF_PERIOD_GET,
                    default=options.get(CONF_PERIOD_GET, DEFAULT_PERIOD_GET),
                ): vol.All(int, vol.Range(min=30, max=3600)),
                vol.Optional(
                    CONF_PERIOD_SET,
                    default=options.get(CONF_PERIOD_SET, DEFAULT_PERIOD_SET),
                ): vol.All(int, vol.Range(min=30, max=3600)),
                vol.Optional(
                    CONF_MAX_SET_RETRIES,
                    default=options.get(CONF_MAX_SET_RETRIES, DEFAULT_MAX_RETRIES),
                ): vol.All(int, vol.Range(min=1, max=10)),
                vol.Optional(
                    CONF_LOG,
                    default=options.get(CONF_LOG, self.config_entry.data.get(CONF_LOG, DEFAULT_LOG)),
                ): vol.In(["CRITICAL", "ERROR", "WARNING", "INFO", "DEBUG", "NOTSET"]),
                vol.Optional(
                    CONF_CH_ZONES,
                    default=options.get(CONF_CH_ZONES, DEFAULT_CH_ZONES),
                ): vol.All(int, vol.Range(min=1, max=6)),
            }
        )

        return self.async_show_form(
            step_id="init",
            data_schema=data_schema,
        )
