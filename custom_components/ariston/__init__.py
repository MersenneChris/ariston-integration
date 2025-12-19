"""Support for Ariston."""
import logging
import re

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.const import (
    ATTR_ENTITY_ID,
    CONF_NAME,
    CONF_PASSWORD,
    CONF_USERNAME,
    Platform,
)

from .ariston import AristonHandler
from .const import param_zoned

from .binary_sensor import binary_sensors_default
from .const import (
    DOMAIN,
    DATA_ARISTON,
    DEVICES,
    SERVICE_SET_DATA,
    CLIMATES,
    WATER_HEATERS,
    CONF_LOG,
    CONF_GW,
    CONF_PERIOD_SET,
    CONF_PERIOD_GET,
    CONF_MAX_SET_RETRIES,
    CONF_CH_ZONES,
    ZONED_PARAMS,
    PARAM_CH_MODE,
    PARAM_CH_SET_TEMPERATURE,
    PARAM_DHW_COMFORT_FUNCTION,
    PARAM_DHW_SET_TEMPERATURE,
    PARAM_MODE,
    PARAM_THERMAL_CLEANSE_CYCLE,
    PARAM_CH_AUTO_FUNCTION,
    PARAM_INTERNET_TIME,
    PARAM_INTERNET_WEATHER,
    PARAM_CHANGING_DATA,
    PARAM_VERSION,
    PARAM_THERMAL_CLEANSE_FUNCTION,
)
from .sensor import sensors_default
from .switch import switches_default
from .select import selects_deafult

DEFAULT_NAME = "Ariston"
DEFAULT_MAX_RETRIES = 5
DEFAULT_PERIOD_GET = 30
DEFAULT_PERIOD_SET = 30

_LOGGER = logging.getLogger(__name__)

PLATFORMS = [
    Platform.CLIMATE,
    Platform.WATER_HEATER,
    Platform.SENSOR,
    Platform.BINARY_SENSOR,
    Platform.SWITCH,
    Platform.SELECT,
]


async def async_setup(hass: HomeAssistant, config: dict):
    """Set up the Ariston component."""
    hass.data.setdefault(DATA_ARISTON, {DEVICES: {}, CLIMATES: [], WATER_HEATERS: []})
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Set up Ariston from a config entry."""
    hass.data.setdefault(DATA_ARISTON, {DEVICES: {}, CLIMATES: [], WATER_HEATERS: []})
    
    name = entry.data.get(CONF_NAME, DEFAULT_NAME)
    username = entry.data[CONF_USERNAME]
    password = entry.data[CONF_PASSWORD]
    gw = entry.data.get(CONF_GW, "")
    
    # Get options with defaults
    options = entry.options
    period_get = options.get(CONF_PERIOD_GET, DEFAULT_PERIOD_GET)
    period_set = options.get(CONF_PERIOD_SET, DEFAULT_PERIOD_SET)
    max_retries = options.get(CONF_MAX_SET_RETRIES, DEFAULT_MAX_RETRIES)
    logging_level = options.get(CONF_LOG, entry.data.get(CONF_LOG, "WARNING"))
    num_ch_zones = options.get(CONF_CH_ZONES, 1)
    
    # Use default sensors, binary_sensors, switches, and selectors for UI config
    binary_sensors = list(binary_sensors_default)
    sensors = list(sensors_default)
    switches = list(switches_default)
    selectors = list(selects_deafult)
    
    _LOGGER.info("Setting up Ariston entry: name=%s, gw=%s", name, gw)

    api = AristonChecker(
        hass=hass,
        device=entry.data,
        name=name,
        username=username,
        password=password,
        sensors=sensors,
        binary_sensors=binary_sensors,
        switches=switches,
        selectors=selectors,
        gw=gw,
        logging=logging_level,
        period_set=period_set,
        period_get=period_get,
        retries=max_retries
    )
    
    # Start api execution
    api.ariston_api.start()
    _LOGGER.info("Ariston API started for %s", name)

    climates = []
    for zone in range(1, num_ch_zones + 1):
        climates.append(f'{name} Zone{zone}')
    
    def update_list(updated_list):
        if updated_list:
            if param in updated_list:
                updated_list.remove(param)
                for zone in range(1, num_ch_zones + 1):
                    updated_list.append(param_zoned(param, zone))
    
    params_temp = set()
    if sensors:
        params_temp.update(sensors)
    if binary_sensors:
        params_temp.update(binary_sensors)
    if switches:
        params_temp.update(switches)
    if selectors:
        params_temp.update(selectors)
    params = params_temp.intersection(ZONED_PARAMS)
    for param in params:
        update_list(switches)
        update_list(binary_sensors)
        update_list(sensors)
        update_list(selectors)
    
    # Forward entry setup to platforms
    _LOGGER.info("Forwarding entry to platforms: %s", ", ".join(p.value for p in PLATFORMS))
    try:
        await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    except Exception:  # If platform setup fails, stop API and clean up
        _LOGGER.exception("Error while forwarding entry setups for %s, stopping API and aborting setup", name)
        try:
            api.ariston_api.stop()
        except Exception:
            _LOGGER.debug("Failed to stop Ariston API during cleanup for %s", name)
        return False
    _LOGGER.info("Platforms setup forwarded for %s", name)

    # Store device only after platforms were successfully set up
    hass.data[DATA_ARISTON][DEVICES][name] = AristonDevice(api, entry.data)
    _LOGGER.info("Stored Ariston device: %s", name)

    # Register service
    async def set_ariston_data(call: ServiceCall):
        """Handle the service call to set the data."""
        entity_id = call.data.get(ATTR_ENTITY_ID, "")

        try:
            domain = entity_id.split(".")[0]
        except Exception:
            _LOGGER.warning("Invalid entity_id domain for Ariston")
            raise Exception("Invalid entity_id domain for Ariston")
        if domain.lower() not in {"climate", "water_heater"}:
            _LOGGER.warning("Invalid entity_id domain for Ariston")
            raise Exception("Invalid entity_id domain for Ariston")
        try:
            device_id = entity_id.split(".")[1]
        except Exception:
            _LOGGER.warning("Invalid entity_id device for Ariston")
            raise Exception("Invalid entity_id device for Ariston")

        api_name = api.name.replace(' ', '_').lower()
        if re.search(f'{api_name}_zone[1-9]$', device_id.lower()) or api_name == device_id.lower():
            parameter_list = {}

            params_to_set = {
                PARAM_MODE,
                PARAM_CH_MODE,
                PARAM_CH_SET_TEMPERATURE,
                PARAM_CH_AUTO_FUNCTION,
                PARAM_DHW_SET_TEMPERATURE,
                PARAM_DHW_COMFORT_FUNCTION,
                PARAM_THERMAL_CLEANSE_CYCLE,
                PARAM_THERMAL_CLEANSE_FUNCTION,
                PARAM_INTERNET_TIME,
                PARAM_INTERNET_WEATHER,
            }
            
            set_zoned_params = []
            for param in params_to_set:
                if param in ZONED_PARAMS:
                    for zone in range(1, 7):
                        set_zoned_params.append(param_zoned(param, zone))
                else:
                    set_zoned_params.append(param)

            for param in set_zoned_params:
                data = call.data.get(param, "")
                if data != "":
                    parameter_list[param] = str(data)

            _LOGGER.debug("Ariston device found, data to check and send")

            await hass.async_add_executor_job(api.ariston_api.set_http_data, **parameter_list)
            return

        raise Exception("Corresponding entity_id for Ariston not found")

    hass.services.async_register(DOMAIN, SERVICE_SET_DATA, set_ariston_data)

    # Register update listener for options
    entry.async_on_unload(entry.add_update_listener(async_reload_entry))

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Unload a config entry."""
    name = entry.data.get(CONF_NAME, DEFAULT_NAME)
    
    # Stop the API
    if name in hass.data[DATA_ARISTON][DEVICES]:
        device = hass.data[DATA_ARISTON][DEVICES][name]
        device.api.ariston_api.stop()
        hass.data[DATA_ARISTON][DEVICES].pop(name)
    
    # Unload platforms
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    
    return unload_ok


async def async_reload_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Reload config entry."""
    await async_unload_entry(hass, entry)
    await async_setup_entry(hass, entry)


class AristonChecker:
    """Ariston checker"""

    def __init__(
        self,
        hass,
        device,
        name,
        username,
        password,
        sensors,
        binary_sensors,
        switches,
        selectors,
        logging,
        gw,
        period_set,
        period_get,
        retries
    ):
        """Initialize."""

        self.device = device
        self._hass = hass
        self.name = name

        if not sensors:
            sensors = list()
        if not binary_sensors:
            binary_sensors = list()
        if not switches:
            switches = list()
        if not selectors:
            selectors = list()

        list_of_sensors = list({*sensors, *binary_sensors, *switches, *selectors})
        """ Some sensors or switches are not part of API """
        if PARAM_CHANGING_DATA in list_of_sensors:
            list_of_sensors.remove(PARAM_CHANGING_DATA)
        if PARAM_VERSION in list_of_sensors:
            list_of_sensors.remove(PARAM_VERSION)

        self.ariston_api = AristonHandler(
            username=username,
            password=password,
            sensors=list_of_sensors,
            logging_level=logging,
            gw=gw,
            set_max_retries=retries,
            period_get_request=period_get,
            period_set_request=period_set
        )


class AristonDevice:
    """Representation of a base Ariston discovery device."""

    def __init__(self, api, device):
        """Initialize the entity."""
        self.api = api
        self.device = device
