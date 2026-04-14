"""Support for Ariston."""
import logging
import re
from datetime import datetime, timedelta
from typing import Optional

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.util import slugify, dt as dt_util
from homeassistant.const import (
    ATTR_ENTITY_ID,
    CONF_NAME,
    CONF_PASSWORD,
    CONF_USERNAME,
    Platform,
)

try:
    from homeassistant.components.recorder.statistics import async_import_statistics, get_last_statistics
    from homeassistant.components.recorder.models import StatisticData, StatisticMetaData
    from homeassistant.components.recorder import get_instance as _get_recorder_instance
    _RECORDER_STATS_AVAILABLE = True
except Exception:
    _RECORDER_STATS_AVAILABLE = False

from .ariston import AristonHandler
from .const import param_zoned

from .binary_sensor import binary_sensors_default
from .const import (
    DOMAIN,
    DATA_ARISTON,
    DEVICES,
    SERVICE_SET_DATA,
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
    PARAM_HP_CH_PRODUCED_TODAY,
    PARAM_HP_DHW_PRODUCED_TODAY,
    PARAM_HP_CH_CONSUMED_TODAY,
    PARAM_HP_DHW_CONSUMED_TODAY,
)
from .sensor import sensors_default
from .switch import switches_default
from .select import selects_deafult

DEFAULT_NAME = "Ariston"
DEFAULT_MAX_RETRIES = 5
DEFAULT_PERIOD_GET = 30
DEFAULT_PERIOD_SET = 30

_LOGGER = logging.getLogger(__name__)

_HP_STATS_PARAMS = (
    PARAM_HP_CH_PRODUCED_TODAY,
    PARAM_HP_DHW_PRODUCED_TODAY,
    PARAM_HP_CH_CONSUMED_TODAY,
    PARAM_HP_DHW_CONSUMED_TODAY,
)

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
    hass.data.setdefault(DATA_ARISTON, {DEVICES: {}})
    return True


def _parse_slot_start_from_range(slot_label: str, now: Optional[datetime] = None) -> Optional[datetime]:
    """Convert labels like '02-04 AM' into a datetime at the slot start."""
    match = re.match(r"^\s*(\d{1,2})\s*-\s*(\d{1,2})\s*([AP]M)\s*$", str(slot_label), re.IGNORECASE)
    if not match:
        return None

    start_hour = int(match.group(1))
    period = match.group(3).upper()

    if period == "PM" and start_hour != 12:
        start_hour += 12
    elif period == "AM" and start_hour == 12:
        start_hour = 0

    if now is None:
        now = dt_util.now()
    start_dt = now.replace(hour=start_hour, minute=0, second=0, microsecond=0)

    # API reports at end-of-window. If parsed start is in the future, treat as previous day.
    if start_dt > now:
        start_dt -= timedelta(days=1)

    return start_dt


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Set up Ariston from a config entry."""
    hass.data.setdefault(DATA_ARISTON, {DEVICES: {}})
    
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
        retries=max_retries,
        num_ch_zones=num_ch_zones,
    )
    
    # Start api execution
    api.ariston_api.start()
    _LOGGER.info("Ariston API started for %s", name)

    if _RECORDER_STATS_AVAILABLE:
        imported_slots_by_stat_id = {}
        running_sum_by_stat_id = {}

        def _statistic_id_from_param(sensor_param: str) -> str:
            sensor_name = sensors_default[sensor_param][0]
            return f"sensor.{slugify(f'{name} {sensor_name}')}"

        async def _get_db_baseline_sum(statistic_id: str) -> float:
            """Return the last cumulative sum stored before today's midnight.

            Queried directly from the recorder DB so the value survives HA restarts.
            Falls back to 0.0 when no prior data exists (first-ever run).
            """
            today_midnight_utc = dt_util.as_utc(
                dt_util.now().replace(hour=0, minute=0, second=0, microsecond=0)
            )
            today_midnight_ts = today_midnight_utc.timestamp()
            try:
                last_stats = await _get_recorder_instance(hass).async_add_executor_job(
                    get_last_statistics, hass, 24, statistic_id, False, {"sum", "start"}
                )
            except Exception as ex:  # noqa: BLE001
                _LOGGER.warning("Could not query DB baseline for %s: %s", statistic_id, ex)
                return 0.0

            entries = last_stats.get(statistic_id, [])
            if not entries:
                return 0.0

            # Find the most recent entry whose slot started before today midnight (UTC).
            # 'start' may be a datetime or a float epoch depending on HA version.
            def _entry_ts(entry):
                s = entry.get("start")
                if s is None:
                    return float("inf")
                return s.timestamp() if hasattr(s, "timestamp") else float(s)

            prev_entries = [e for e in entries if _entry_ts(e) < today_midnight_ts]
            if not prev_entries:
                return 0.0

            prev_entries.sort(key=_entry_ts, reverse=True)
            baseline = float(prev_entries[0].get("sum") or 0.0)
            _LOGGER.debug("DB baseline for %s: %.6f", statistic_id, baseline)
            return baseline

        async def _async_import_hp_slot_statistics(changed_data: dict):
            if "recorder" not in hass.config.components:
                return

            if not any(sensor in changed_data for sensor in _HP_STATS_PARAMS):
                return

            sensor_values = api.ariston_api.sensor_values

            for sensor_param in _HP_STATS_PARAMS:
                sensor_data = sensor_values.get(sensor_param, {})
                attributes = sensor_data.get("attributes") or {}
                if not isinstance(attributes, dict):
                    continue

                now = dt_util.now()
                slot_points = []
                for key, raw_value in attributes.items():
                    slot_start = _parse_slot_start_from_range(key, now)
                    if slot_start is None:
                        continue
                    try:
                        slot_value = float(raw_value)
                    except (TypeError, ValueError):
                        continue
                    if slot_value < 0:
                        continue
                    slot_points.append((slot_start, slot_value))

                if not slot_points:
                    continue

                slot_points.sort(key=lambda item: item[0])

                statistic_id = _statistic_id_from_param(sensor_param)
                imported_starts = imported_slots_by_stat_id.setdefault(statistic_id, set())

                if statistic_id not in running_sum_by_stat_id:
                    # Seed from the last sum written to the recorder DB before today.
                    # Using the live sensor value here is unreliable after HA restarts
                    # because the sensor starts at 0 until the first API poll completes.
                    running_sum_by_stat_id[statistic_id] = await _get_db_baseline_sum(statistic_id)

                stats_payload = []
                for slot_start, slot_value in slot_points:
                    slot_key = slot_start.isoformat()
                    if slot_key in imported_starts:
                        continue

                    running_sum_by_stat_id[statistic_id] = round(
                        running_sum_by_stat_id[statistic_id] + slot_value,
                        6,
                    )
                    imported_starts.add(slot_key)
                    stats_payload.append(
                        StatisticData(
                            start=slot_start,
                            state=slot_value,
                            sum=running_sum_by_stat_id[statistic_id],
                        )
                    )

                if not stats_payload:
                    continue

                metadata = StatisticMetaData(
                    has_mean=False,
                    has_sum=True,
                    name=None,
                    source="recorder",
                    statistic_id=statistic_id,
                    unit_of_measurement="kWh",
                )
                async_import_statistics(hass, metadata, stats_payload)

        def _schedule_hp_statistics_import(changed_data, *_args, **_kwargs):
            hass.loop.call_soon_threadsafe(
                hass.async_create_task,
                _async_import_hp_slot_statistics(changed_data),
            )

        api.ariston_api.subscribe_sensors(_schedule_hp_statistics_import)
    else:
        _LOGGER.warning("Recorder statistics helpers are unavailable; HP slot LTS import is disabled")

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
    
    # Store device
    hass.data[DATA_ARISTON][DEVICES][name] = AristonDevice(api, entry.data)
    _LOGGER.info("Stored Ariston device: %s", name)
    
    # Forward entry setup to platforms
    _LOGGER.info("Forwarding entry to platforms: %s", ", ".join(p.value for p in PLATFORMS))
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    _LOGGER.info("Platforms setup forwarded for %s", name)
    
    # Register service
    async def set_ariston_data(call: ServiceCall):
        """Handle the service call to set the data."""
        entity_id = call.data.get(ATTR_ENTITY_ID, "")

        try:
            domain = entity_id.split(".")[0]
        except:
            _LOGGER.warning("Invalid entity_id domain for Ariston")
            raise Exception("Invalid entity_id domain for Ariston")
        if domain.lower() not in {"climate", "water_heater"}:
            _LOGGER.warning("Invalid entity_id domain for Ariston")
            raise Exception("Invalid entity_id domain for Ariston")
        try:
            device_id = entity_id.split(".")[1]
        except:
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
                    for zone in range(1, num_ch_zones + 1):
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
        retries,
        num_ch_zones=1
    ):
        """Initialize."""

        self.device = device
        self._hass = hass
        self.name = name
        self.num_ch_zones = num_ch_zones

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
            period_set_request=period_set,
            max_zones=num_ch_zones,
        )


class AristonDevice:
    """Representation of a base Ariston discovery device."""

    def __init__(self, api, device):
        """Initialize the entity."""
        self.api = api
        self.device = device
