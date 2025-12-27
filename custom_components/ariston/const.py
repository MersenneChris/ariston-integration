""" Constants for the integration """
PARAM_ACCOUNT_CH_ELECTRICITY = "account_ch_electricity"
PARAM_ACCOUNT_DHW_ELECTRICITY = "account_dhw_electricity"
PARAM_CH_ANTIFREEZE_TEMPERATURE = "ch_antifreeze_temperature"
PARAM_CH_MODE = "ch_mode"
PARAM_CH_SET_TEMPERATURE = "ch_set_temperature"
PARAM_CH_SET_TEMPERATURE_MIN = "ch_set_temperature_min"
PARAM_CH_SET_TEMPERATURE_MAX = "ch_set_temperature_max"
PARAM_CH_COMFORT_TEMPERATURE = "ch_comfort_temperature"
PARAM_CH_ECONOMY_TEMPERATURE = "ch_economy_temperature"
PARAM_CH_DETECTED_TEMPERATURE = "ch_detected_temperature"
PARAM_CH_PROGRAM = "ch_program"
PARAM_ERRORS_COUNT = "errors_count"
PARAM_DHW_COMFORT_FUNCTION = "dhw_comfort_function"
PARAM_DHW_MODE = "dhw_mode"
PARAM_DHW_PROGRAM = "dhw_program"
PARAM_DHW_SET_TEMPERATURE = "dhw_set_temperature"
PARAM_DHW_SET_TEMPERATURE_MIN = "dhw_set_temperature_min"
PARAM_DHW_SET_TEMPERATURE_MAX = "dhw_set_temperature_max"
PARAM_DHW_STORAGE_TEMPERATURE = "dhw_storage_temperature"
PARAM_DHW_COMFORT_TEMPERATURE = "dhw_comfort_temperature"
PARAM_DHW_ECONOMY_TEMPERATURE = "dhw_economy_temperature"
PARAM_HEATING_LAST_24H = "heating_last_24h"
PARAM_HEATING_LAST_7D = "heating_last_7d"
PARAM_HEATING_LAST_30D = "heating_last_30d"
PARAM_HEATING_LAST_365D = "heating_last_365d"
PARAM_HEATING_LAST_24H_LIST = "heating_last_24h_list"
PARAM_HEATING_LAST_7D_LIST = "heating_last_7d_list"
PARAM_HEATING_LAST_30D_LIST = "heating_last_30d_list"
PARAM_HEATING_LAST_365D_LIST = "heating_last_365d_list"
PARAM_HEATING_TODAY = "heating_today"
PARAM_MODE = "mode"
PARAM_OUTSIDE_TEMPERATURE = "outside_temperature"
PARAM_SIGNAL_STRENGTH = "signal_strength"
PARAM_WATER_LAST_24H = "water_last_24h"
PARAM_WATER_LAST_7D = "water_last_7d"
PARAM_WATER_LAST_30D = "water_last_30d"
PARAM_WATER_LAST_365D = "water_last_365d"
PARAM_WATER_LAST_24H_LIST = "water_last_24h_list"
PARAM_WATER_LAST_7D_LIST = "water_last_7d_list"
PARAM_WATER_LAST_30D_LIST = "water_last_30d_list"
PARAM_WATER_LAST_365D_LIST = "water_last_365d_list"
PARAM_WATER_TODAY = "water_today"
PARAM_UNITS = "units"
PARAM_THERMAL_CLEANSE_CYCLE = "dhw_thermal_cleanse_cycle"
PARAM_ELECTRICITY_COST = "electricity_cost"
PARAM_ELECTRICITY_COST_UNIT = "electricity_cost_unit"
PARAM_CH_AUTO_FUNCTION = "ch_auto_function"
PARAM_HEAT_PUMP = "heat_pump"
PARAM_HOLIDAY_MODE = "holiday_mode"
PARAM_INTERNET_TIME = "internet_time"
PARAM_INTERNET_WEATHER = "internet_weather"
PARAM_CHANGING_DATA = "changing_data"
PARAM_THERMAL_CLEANSE_FUNCTION = "dhw_thermal_cleanse_function"
PARAM_CH_PILOT = "ch_pilot"
PARAM_UPDATE = "update"
PARAM_ONLINE_VERSION = "online_version"
PARAM_PRESSURE = "pressure"
PARAM_CH_FLOW_TEMP = 'ch_flow_temperature'
PARAM_CH_FIXED_TEMP = 'ch_fixed_temperature'
PARAM_CH_LAST_MONTH_ELECTRICITY = 'ch_electricity_last_month'
PARAM_DHW_LAST_MONTH_ELECTRICITY = 'dhw_electricity_last_month'
PARAM_CH_ENERGY_TODAY = 'ch_energy_today'
PARAM_DHW_ENERGY_TODAY = 'dhw_energy_today'
PARAM_CH_ENERGY2_TODAY = 'ch_energy2_today'
PARAM_DHW_ENERGY2_TODAY = 'dhw_energy2_today'
PARAM_HEATING_FLOW_TEMP = "ch_heating_flow_temp"
PARAM_HEATING_FLOW_OFFSET = "ch_heating_flow_offset"
PARAM_CH_DEROGA_TEMPERATURE = "ch_deroga_temperature"
PARAM_VERSION = 'integration_version'

ZONED_PARAMS = [
    PARAM_CH_MODE,
    PARAM_CH_SET_TEMPERATURE,
    PARAM_CH_DETECTED_TEMPERATURE,
    PARAM_CH_DEROGA_TEMPERATURE,
    PARAM_CH_COMFORT_TEMPERATURE,
    PARAM_CH_PILOT,
    PARAM_CH_ECONOMY_TEMPERATURE,
    PARAM_HEATING_FLOW_TEMP,
    PARAM_HEATING_FLOW_OFFSET,
]

VAL_MANUAL = "Manual"
VAL_PROGRAM = "Time program"
VAL_WINTER = "Winter"
VAL_SUMMER = "Summer"
VAL_OFF = "OFF"
VAL_ON = "ON"
VAL_OFFLINE = "Offline"
VAL_DISABLED = "Disabled"
VAL_HEATING_ONLY = "Heating only"
VAL_HOLIDAY = "Holiday"

CONF_LOG = "logging"
CONF_GW = "gw"
CONF_PERIOD_SET = "period_set"
CONF_PERIOD_GET = "period_get"
CONF_MAX_SET_RETRIES = "max_set_retries"
CONF_CH_ZONES = "num_ch_zones"

VALUE = "value"
UNITS = "units"
OPTIONS = 'options'
OPTIONS_TXT = 'options_text'
MIN = 'min'
MAX = 'max'
STEP = 'step'
ATTRIBUTES = "attributes"

DOMAIN = "ariston"
DATA_ARISTON = DOMAIN
DEVICES = "devices"
SERVICE_SET_DATA = "set_data"
CLIMATES = "climates"
WATER_HEATERS = "water_heaters"
CONF_CLIMATES = "climates"

def param_zoned(param, zone):
    if param in ZONED_PARAMS:
        return f'{param}_zone{zone}'
    else:
        return param
