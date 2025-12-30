"""Suppoort for Ariston sensors."""
import logging
from datetime import timedelta, datetime
from copy import deepcopy
import calendar

from homeassistant.const import CONF_NAME
from homeassistant.helpers.entity import Entity

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorStateClass,
    SensorEntity,
)

from .const import param_zoned
from .const import (
    DATA_ARISTON,
    DEVICES,
    DOMAIN,
    OPTIONS,
    PARAM_CH_ANTIFREEZE_TEMPERATURE,
    PARAM_CH_MODE,
    PARAM_CH_SET_TEMPERATURE,
    PARAM_CH_COMFORT_TEMPERATURE,
    PARAM_CH_ECONOMY_TEMPERATURE,
    PARAM_CH_DETECTED_TEMPERATURE,
    PARAM_CH_PROGRAM,
    PARAM_ERRORS_COUNT,
    PARAM_DHW_COMFORT_FUNCTION,
    PARAM_DHW_MODE,
    PARAM_DHW_SET_TEMPERATURE,
    PARAM_DHW_STORAGE_TEMPERATURE,
    PARAM_DHW_COMFORT_TEMPERATURE,
    PARAM_DHW_ECONOMY_TEMPERATURE,
    PARAM_MODE,
    PARAM_OUTSIDE_TEMPERATURE,
    PARAM_SIGNAL_STRENGTH,
    PARAM_THERMAL_CLEANSE_CYCLE,
    PARAM_DHW_PROGRAM,
    PARAM_CH_FLOW_TEMP,
    PARAM_CH_FIXED_TEMP,
    PARAM_CH_ENERGY2_TODAY,
    PARAM_DHW_ENERGY2_TODAY,
    PARAM_HP_CH_PRODUCED_TODAY,
    PARAM_HP_DHW_PRODUCED_TODAY,
    PARAM_HP_CH_CONSUMED_TODAY,
    PARAM_HP_DHW_CONSUMED_TODAY,
    PARAM_HP_CH_COP,
    PARAM_HP_DHW_COP,
    PARAM_HP_TOTAL_PRODUCED_TODAY,
    PARAM_HP_TOTAL_CONSUMED_TODAY,
    PARAM_HP_TOTAL_COP,
    PARAM_VERSION,
    VALUE,
    UNITS,
    ATTRIBUTES,
    MIN,
    MAX,
    STEP,
    OPTIONS_TXT,
    ZONED_PARAMS
)

SCAN_INTERVAL = timedelta(seconds=2)

STATE_AVAILABLE = "available"

SENSOR_CH_ANTIFREEZE_TEMPERATURE = "CH Antifreeze Temperature"
SENSOR_CH_DETECTED_TEMPERATURE = "CH Detected Temperature"
SENSOR_CH_MODE = "CH Mode"
SENSOR_CH_SET_TEMPERATURE = "CH Set Temperature"
SENSOR_CH_PROGRAM = "CH Time Program"
SENSOR_CH_COMFORT_TEMPERATURE = "CH Comfort Temperature"
SENSOR_CH_ECONOMY_TEMPERATURE = "CH Economy Temperature"
SENSOR_CH_FLOW_SETPOINT_TEMPERATURE = "CH Flow Setpoint Temperature"
SENSOR_CH_FIXED_TEMPERATURE = "CH Fixed Temperature"
SENSOR_DHW_COMFORT_FUNCTION = "DHW Comfort Function"
SENSOR_DHW_PROGRAM = "DHW Time Program"
SENSOR_DHW_SET_TEMPERATURE = "DHW Set Temperature"
SENSOR_DHW_STORAGE_TEMPERATURE = "DHW Storage Temperature"
SENSOR_DHW_COMFORT_TEMPERATURE = "DHW Comfort Temperature"
SENSOR_DHW_ECONOMY_TEMPERATURE = "DHW Economy Temperature"
SENSOR_DHW_MODE = "DHW Mode"
SENSOR_ERRORS = "Active Errors"
SENSOR_MODE = "Mode"
SENSOR_OUTSIDE_TEMPERATURE = "Outside Temperature"
SENSOR_SIGNAL_STRENGTH = "Signal Strength"
SENSOR_THERMAL_CLEANSE_CYCLE = "Thermal Cleanse Cycle"
SENSOR_ELECTRICITY_COST = "Electricity Cost"
SENSOR_CH_ENERGY2_TODAY = 'CH energy 2 today'
SENSOR_DHW_ENERGY2_TODAY = 'DHW energy 2 today'
SENSOR_HP_CH_PRODUCED_TODAY = 'HP CH produced energy today'
SENSOR_HP_DHW_PRODUCED_TODAY = 'HP DHW produced energy today'
SENSOR_HP_CH_CONSUMED_TODAY = 'HP CH consumed energy today'
SENSOR_HP_DHW_CONSUMED_TODAY = 'HP DHW consumed energy today'
SENSOR_HP_CH_COP = 'HP CH COP'
SENSOR_HP_DHW_COP = 'HP DHW COP'
SENSOR_HP_TOTAL_PRODUCED_TODAY = 'HP total produced energy today'
SENSOR_HP_TOTAL_CONSUMED_TODAY = 'HP total consumed energy today'
SENSOR_HP_TOTAL_COP = 'HP total COP'
SENSOR_VERSION = 'Integration local version'

_LOGGER = logging.getLogger(__name__)

# Sensor types are defined like: Name, units, icon
sensors_default = {
    PARAM_CH_ANTIFREEZE_TEMPERATURE: [SENSOR_CH_ANTIFREEZE_TEMPERATURE, SensorDeviceClass.TEMPERATURE, "mdi:radiator", None],
    PARAM_CH_DETECTED_TEMPERATURE: [SENSOR_CH_DETECTED_TEMPERATURE, SensorDeviceClass.TEMPERATURE, "mdi:thermometer", None],
    PARAM_CH_MODE: [SENSOR_CH_MODE, None, "mdi:radiator", None],
    PARAM_CH_SET_TEMPERATURE: [SENSOR_CH_SET_TEMPERATURE, SensorDeviceClass.TEMPERATURE, "mdi:radiator", None],
    PARAM_CH_PROGRAM: [SENSOR_CH_PROGRAM, None, "mdi:calendar-month", None],
    PARAM_CH_COMFORT_TEMPERATURE: [SENSOR_CH_COMFORT_TEMPERATURE, SensorDeviceClass.TEMPERATURE, "mdi:radiator", None],
    PARAM_CH_ECONOMY_TEMPERATURE: [SENSOR_CH_ECONOMY_TEMPERATURE, SensorDeviceClass.TEMPERATURE, "mdi:radiator", None],
    PARAM_CH_FLOW_TEMP: [SENSOR_CH_FLOW_SETPOINT_TEMPERATURE, SensorDeviceClass.TEMPERATURE, "mdi:radiator", None],
    PARAM_CH_FIXED_TEMP: [SENSOR_CH_FIXED_TEMPERATURE, SensorDeviceClass.TEMPERATURE, "mdi:radiator", None],
    PARAM_DHW_PROGRAM: [SENSOR_DHW_PROGRAM, None, "mdi:calendar-month", None],
    PARAM_DHW_COMFORT_FUNCTION: [SENSOR_DHW_COMFORT_FUNCTION, None, "mdi:water-pump", None],
    PARAM_DHW_SET_TEMPERATURE: [SENSOR_DHW_SET_TEMPERATURE, SensorDeviceClass.TEMPERATURE, "mdi:water-pump", None],
    PARAM_DHW_STORAGE_TEMPERATURE: [SENSOR_DHW_STORAGE_TEMPERATURE, SensorDeviceClass.TEMPERATURE, "mdi:water-pump", None],
    PARAM_DHW_COMFORT_TEMPERATURE: [SENSOR_DHW_COMFORT_TEMPERATURE, SensorDeviceClass.TEMPERATURE, "mdi:water-pump", None],
    PARAM_DHW_ECONOMY_TEMPERATURE: [SENSOR_DHW_ECONOMY_TEMPERATURE, SensorDeviceClass.TEMPERATURE, "mdi:water-pump", None],
    PARAM_DHW_MODE: [SENSOR_DHW_MODE, None, "mdi:water-pump", None],
    PARAM_ERRORS_COUNT: [SENSOR_ERRORS, None, "mdi:alert-outline", None],
    PARAM_MODE: [SENSOR_MODE, None, "mdi:water-boiler", None],
    PARAM_OUTSIDE_TEMPERATURE: [SENSOR_OUTSIDE_TEMPERATURE, SensorDeviceClass.TEMPERATURE, "mdi:thermometer", None],
    PARAM_SIGNAL_STRENGTH: [SENSOR_SIGNAL_STRENGTH, SensorDeviceClass.SIGNAL_STRENGTH, "mdi:signal", None],
    PARAM_THERMAL_CLEANSE_CYCLE: [SENSOR_THERMAL_CLEANSE_CYCLE, None, "mdi:update", None],
    PARAM_CH_ENERGY2_TODAY: [SENSOR_CH_ENERGY2_TODAY, SensorDeviceClass.ENERGY, "mdi:cash", SensorStateClass.TOTAL_INCREASING],
    PARAM_DHW_ENERGY2_TODAY: [SENSOR_DHW_ENERGY2_TODAY, SensorDeviceClass.ENERGY, "mdi:cash", SensorStateClass.TOTAL_INCREASING],
    PARAM_HP_CH_PRODUCED_TODAY: [SENSOR_HP_CH_PRODUCED_TODAY, SensorDeviceClass.ENERGY, "mdi:flash", SensorStateClass.TOTAL_INCREASING],
    PARAM_HP_DHW_PRODUCED_TODAY: [SENSOR_HP_DHW_PRODUCED_TODAY, SensorDeviceClass.ENERGY, "mdi:flash", SensorStateClass.TOTAL_INCREASING],
    PARAM_HP_CH_CONSUMED_TODAY: [SENSOR_HP_CH_CONSUMED_TODAY, SensorDeviceClass.ENERGY, "mdi:flash", SensorStateClass.TOTAL_INCREASING],
    PARAM_HP_DHW_CONSUMED_TODAY: [SENSOR_HP_DHW_CONSUMED_TODAY, SensorDeviceClass.ENERGY, "mdi:flash", SensorStateClass.TOTAL_INCREASING],
    PARAM_HP_CH_COP: [SENSOR_HP_CH_COP, SensorDeviceClass.POWER_FACTOR, "mdi:gauge", SensorStateClass.MEASUREMENT],
    PARAM_HP_DHW_COP: [SENSOR_HP_DHW_COP, SensorDeviceClass.POWER_FACTOR, "mdi:gauge", SensorStateClass.MEASUREMENT],
    PARAM_HP_TOTAL_PRODUCED_TODAY: [SENSOR_HP_TOTAL_PRODUCED_TODAY, SensorDeviceClass.ENERGY, "mdi:flash", SensorStateClass.TOTAL_INCREASING],
    PARAM_HP_TOTAL_CONSUMED_TODAY: [SENSOR_HP_TOTAL_CONSUMED_TODAY, SensorDeviceClass.ENERGY, "mdi:flash", SensorStateClass.TOTAL_INCREASING],
    PARAM_HP_TOTAL_COP: [SENSOR_HP_TOTAL_COP, SensorDeviceClass.POWER_FACTOR, "mdi:gauge", SensorStateClass.MEASUREMENT],
    PARAM_VERSION: [SENSOR_VERSION, None, "mdi:package-down", None],
}
SENSORS = deepcopy(sensors_default)
for param in sensors_default:
    if param in ZONED_PARAMS:
        for zone in range (1, 7):
            SENSORS[param_zoned(param, zone)] = (
                SENSORS[param][0] + f' Zone{zone}',
                SENSORS[param][1],
                SENSORS[param][2],
                SENSORS[param][3],
            )
        del SENSORS[param]


async def async_setup_entry(hass, entry, async_add_entities):
    """Set up Ariston sensors from a config entry."""
    name = entry.data.get(CONF_NAME, "Ariston")
    device = hass.data[DATA_ARISTON][DEVICES][name]
    
    # Filter sensors to only those available in the API
    api = device.api.ariston_api
    sensors = [s for s in SENSORS.keys() if s in api.sensor_values]
    _LOGGER.info("Adding %d sensors for %s (available in API: %d)", len(sensors), name, len(api.sensor_values))
    
    async_add_entities(
        [AristonSensor(name, device, sensor_type) for sensor_type in sensors],
        True,
    )


class AristonSensor(SensorEntity):
    """A sensor implementation for Ariston."""

    def __init__(self, name, device, sensor_type):
        """Initialize a sensor for Ariston."""
        self._device_name = name
        self._name = "{} {}".format(name, SENSORS[sensor_type][0])
        self._signal_name = name
        self._api = device.api.ariston_api
        self._sensor_type = sensor_type
        self._state = None
        self._attrs = {}
        self._icon = SENSORS[sensor_type][2]
        self._device_class = SENSORS[sensor_type][1]
        self._state_class = SENSORS[sensor_type][3]

    @property
    def unique_id(self):
        """Return the unique id."""
        return f"{self._name}-{self._sensor_type}"

    @property
    def name(self):
        """Return the name of the sensor."""
        return self._name

    @property
    def state(self):
        """Return the state of the sensor."""
        return self._state

    @property
    def native_value(self):
        """Return value of sensor."""
        return self._state

    @property
    def state_class(self):
        """State class of sensor."""
        return self._state_class

    @property
    def native_unit_of_measurement(self):
        """Return unit of sensor."""
        try:
            return self._api.sensor_values[self._sensor_type][UNITS]
        except KeyError:
            return None

    @property
    def device_class(self):
        """Return device class."""
        return self._device_class

    @property
    def device_info(self):
        """Return device information for device registry linking."""
        identifier = self._api.plant_id or self._device_name
        return {
            "identifiers": {(DOMAIN, identifier)},
            "name": self._device_name,
            "manufacturer": "Ariston",
        }
        
    @property
    def extra_state_attributes(self):
        """Return the state attributes."""
        return self._attrs

    @property
    def icon(self):
        """Icon to use in the frontend, if any."""
        if self._sensor_type == PARAM_ERRORS_COUNT:
            try:
                if self._api.sensor_values[PARAM_ERRORS_COUNT][VALUE] == 0:
                    return "mdi:shield"
            except KeyError:
                pass
        return self._icon

    @property
    def unit_of_measurement(self):
        """Return the units of measurement."""
        try:
            return self._api.sensor_values[self._sensor_type][UNITS]
        except KeyError:
            return None

    @property
    def available(self):
        """Return True if entity is available."""
        if self._sensor_type == PARAM_VERSION:
            return True
        return (
            self._api.available
            and not self._api.sensor_values[self._sensor_type][VALUE] is None
        )


    def update(self):
        """Get the latest data and updates the state."""
        try:
            if self._sensor_type == PARAM_VERSION:
                self._state = self._api.version
                return
            if not self._api.available:
                return
            self._state = self._api.sensor_values[self._sensor_type][VALUE]
            self._attrs = self._api.sensor_values[self._sensor_type][ATTRIBUTES]
            if not self._attrs:
                if self._api.sensor_values[self._sensor_type][OPTIONS_TXT]:
                    self._attrs[OPTIONS_TXT] = self._api.sensor_values[self._sensor_type][OPTIONS_TXT]
                    self._attrs[OPTIONS] = self._api.sensor_values[self._sensor_type][OPTIONS]
                elif self._api.sensor_values[self._sensor_type][MIN] and \
                    self._api.sensor_values[self._sensor_type][MAX] and \
                    self._api.sensor_values[self._sensor_type][STEP]:
                    self._attrs[MIN] = self._api.sensor_values[self._sensor_type][MIN]
                    self._attrs[MAX] = self._api.sensor_values[self._sensor_type][MAX]
                    self._attrs[STEP] = self._api.sensor_values[self._sensor_type][STEP]
            if self._state_class:
                self._attrs["state_class"] = self._state_class

        except KeyError:
            _LOGGER.warning("Problem updating sensors for Ariston")
