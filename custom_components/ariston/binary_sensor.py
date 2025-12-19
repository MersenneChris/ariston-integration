"""Suppoort for Ariston binary sensors."""
import logging
from datetime import timedelta
from copy import deepcopy
from homeassistant.components.binary_sensor import (
    BinarySensorEntity,
)
from homeassistant.const import CONF_BINARY_SENSORS, CONF_NAME

from .const import param_zoned
from .const import (
    DATA_ARISTON,
    DOMAIN,
    DEVICES,
    PARAM_HOLIDAY_MODE,
    PARAM_HEAT_PUMP,
    PARAM_INTERNET_TIME,
    PARAM_INTERNET_WEATHER,
    PARAM_CH_AUTO_FUNCTION,
    PARAM_THERMAL_CLEANSE_FUNCTION,
    VALUE,
    VAL_ON,
    ZONED_PARAMS
)

BINARY_SENSOR_CH_AUTO_FUNCTION = "CH Auto Function"
BINARY_SENSOR_HOLIDAY_MODE = "Holiday Mode"
BINARY_SENSOR_HEAT_PUMP = "Heat Pump"
BINARY_SENSOR_INTERNET_TIME = "Internet Time"
BINARY_SENSOR_INTERNET_WEATHER = "Internet Weather"
BINARY_SENSOR_THERMAL_CLEANSE_FUNCTION = "Thermal Cleanse Function"

SCAN_INTERVAL = timedelta(seconds=2)

_LOGGER = logging.getLogger(__name__)

# Binary sensor types are defined like: Name, device class
binary_sensors_default = {
    PARAM_CH_AUTO_FUNCTION: (BINARY_SENSOR_CH_AUTO_FUNCTION, None, "mdi:radiator"),
    PARAM_HOLIDAY_MODE: (BINARY_SENSOR_HOLIDAY_MODE, None, "mdi:island"),
    PARAM_HEAT_PUMP: (BINARY_SENSOR_HEAT_PUMP, None, "mdi:fan"),
    PARAM_INTERNET_TIME: (BINARY_SENSOR_INTERNET_TIME, None, "mdi:update"),
    PARAM_INTERNET_WEATHER: (
        BINARY_SENSOR_INTERNET_WEATHER,
        None,
        "mdi:weather-partly-cloudy",
    ),
    PARAM_THERMAL_CLEANSE_FUNCTION: (
        BINARY_SENSOR_THERMAL_CLEANSE_FUNCTION,
        None,
        "mdi:allergy",
    ),
}
BINARY_SENSORS = deepcopy(binary_sensors_default)
for param in binary_sensors_default:
    if param in ZONED_PARAMS:
        for zone in range (1, 7):
            BINARY_SENSORS[param_zoned(param, zone)] = (
                BINARY_SENSORS[param][0] + f' Zone{zone}',
                BINARY_SENSORS[param][1],
                BINARY_SENSORS[param][2]
            )
        del BINARY_SENSORS[param]


async def async_setup_entry(hass, entry, async_add_entities):
    """Set up Ariston binary sensors from a config entry."""
    name = entry.data.get(CONF_NAME, "Ariston")
    device = hass.data[DATA_ARISTON][DEVICES][name]
    
    # Filter binary sensors to only those available in the API
    api = device.api.ariston_api
    binary_sensors = [s for s in binary_sensors_default.keys() if s in api.sensor_values]
    _LOGGER.info("Adding %d binary sensors for %s", len(binary_sensors), name)
    
    async_add_entities(
        [AristonBinarySensor(name, device, sensor_type) for sensor_type in binary_sensors],
        True,
    )


def setup_platform(hass, config, add_entities, discovery_info=None):
    """Set up a binary sensor for Ariston."""
    if discovery_info is None:
        return

    name = discovery_info[CONF_NAME]
    device = hass.data[DATA_ARISTON][DEVICES][name]
    add_entities(
        [
            AristonBinarySensor(name, device, sensor_type)
            for sensor_type in discovery_info[CONF_BINARY_SENSORS]
        ],
        True,
    )


class AristonBinarySensor(BinarySensorEntity):
    """Binary sensor for Ariston."""

    def __init__(self, name, device, sensor_type):
        """Initialize entity."""
        self._api = device.api.ariston_api
        self._attrs = {}
        self._device_class = BINARY_SENSORS[sensor_type][1]
        self._icon = BINARY_SENSORS[sensor_type][2]
        self._device_name = name
        self._name = "{} {}".format(name, BINARY_SENSORS[sensor_type][0])
        self._sensor_type = sensor_type
        self._state = None

    @property
    def unique_id(self):
        """Return the unique id."""
        return f"{self._name}-{self._sensor_type}"

    @property
    def extra_state_attributes(self):
        """Return the state attributes."""
        return self._attrs

    @property
    def should_poll(self):
        """Return True if entity has to be polled for state."""
        return True

    @property
    def name(self):
        """Return entity name."""
        return self._name

    @property
    def is_on(self):
        """Return if entity is on."""
        return self._state

    @property
    def device_class(self):
        """Return device class."""
        return self._device_class

    @property
    def device_info(self):
        """Return device information for device registry linking."""
        # Use gateway/plant_id when available; fall back to configured name
        identifier = self._api.plant_id or self._device_name
        return {
            "identifiers": {(DOMAIN, identifier)},
            "name": self._device_name,
            "manufacturer": "Ariston",
        }

    @property
    def available(self):
        return (
            self._api.available
            and not self._api.sensor_values[self._sensor_type][VALUE] is None
        )

    @property
    def icon(self):
        """Return the state attributes."""
        return self._icon

    def update(self):
        """Update entity."""
        try:
            if not self._api.available:
                return
            if self._api.sensor_values[self._sensor_type][VALUE] == VAL_ON:
                self._state = True
            else:
                self._state = False
        except KeyError:
            _LOGGER.warning("Problem updating binary_sensors for Ariston")
