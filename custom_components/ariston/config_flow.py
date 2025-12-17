"""Config flow for Ariston integration."""
import logging
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import CONF_NAME, CONF_PASSWORD, CONF_USERNAME
from homeassistant.core import callback
import homeassistant.helpers.config_validation as cv

from .ariston import AristonHandler
from .const import (
    DOMAIN,
    CONF_GW,
    CONF_LOG,
    CONF_PERIOD_SET,
    CONF_PERIOD_GET,
    CONF_MAX_SET_RETRIES,
    CONF_CH_ZONES,
)

_LOGGER = logging.getLogger(__name__)

DEFAULT_NAME = "Ariston"
DEFAULT_MAX_RETRIES = 5
DEFAULT_PERIOD_GET = 30
DEFAULT_PERIOD_SET = 30
DEFAULT_LOG = "DEBUG"
DEFAULT_CH_ZONES = 1


class AristonConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Ariston."""

    VERSION = 1

    async def async_step_user(self, user_input=None):
        """Handle the initial step."""
        errors = {}

        if user_input is not None:
            # Validate the username and password by attempting to connect
            await self.async_set_unique_id(user_input[CONF_USERNAME])
            self._abort_if_unique_id_configured()

            # Test connection
            try:
                # Create a temporary API handler to test credentials
                test_api = AristonHandler(
                    username=user_input[CONF_USERNAME],
                    password=user_input[CONF_PASSWORD],
                    sensors=[],
                    logging_level=DEFAULT_LOG,
                    gw=user_input.get(CONF_GW, ""),
                    set_max_retries=DEFAULT_MAX_RETRIES,
                    period_get_request=DEFAULT_PERIOD_GET,
                    period_set_request=DEFAULT_PERIOD_SET,
                )
                
                # Start the API to verify credentials
                test_api.start()
                
                # Wait a moment for the API to connect
                import asyncio
                await asyncio.sleep(5)
                
                # Check if online
                if not test_api.get_value("online"):
                    test_api.stop()
                    errors["base"] = "cannot_connect"
                else:
                    test_api.stop()
                    # Create the entry
                    return self.async_create_entry(
                        title=user_input.get(CONF_NAME, DEFAULT_NAME),
                        data=user_input,
                    )
            except Exception as err:
                _LOGGER.error("Error connecting to Ariston: %s", err)
                errors["base"] = "cannot_connect"

        # Show the form
        data_schema = vol.Schema(
            {
                vol.Required(CONF_USERNAME): cv.string,
                vol.Required(CONF_PASSWORD): cv.string,
                vol.Optional(CONF_NAME, default=DEFAULT_NAME): cv.string,
                vol.Optional(CONF_GW, default=""): cv.string,
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
                    default=options.get(CONF_LOG, DEFAULT_LOG),
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
