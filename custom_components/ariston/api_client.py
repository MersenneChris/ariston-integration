"""Ariston API client for HTTP communication."""
import logging
import threading
import requests


class AristonApiClient:
    """Handles all HTTP API communication with Ariston servers."""

    # API configuration
    _ARISTON_URL = "https://www.ariston-net.remotethermo.com"
    _TIMEOUT_MIN = 5
    _TIMEOUT_AV = 15
    _TIMEOUT_MAX = 25

    def __init__(self, logger):
        """Initialize API client with session and logger."""
        self._session = requests.Session()
        self._LOGGER = logger
        self._plant_id_lock = threading.Lock()
        self._data_lock = threading.Lock()

    def request_post(self, url, json_data, timeout=_TIMEOUT_MIN, error_msg=''):
        """Make a POST request."""
        try:
            resp = self._session.post(
                url,
                timeout=timeout,
                json=json_data,
                verify=True)
        except requests.exceptions.RequestException as ex:
            self._LOGGER.warning(f'{error_msg} exception: {ex}')
            raise Exception(f'{error_msg} exception: {ex}')
        if not resp.ok:
            self._LOGGER.warning(f'{error_msg} reply code: {resp.status_code}')
            self._LOGGER.warning(f'{resp.text}')
            raise Exception(f'{error_msg} reply code: {resp.status_code}')
        return resp

    def request_get(self, url, timeout=_TIMEOUT_MIN, error_msg='', ignore_errors=False):
        """Make a GET request."""
        try:
            resp = self._session.get(
                url,
                timeout=timeout,
                verify=True)
        except requests.exceptions.RequestException as ex:
            self._LOGGER.warning(f'{error_msg} exception: {ex}')
            if not ignore_errors:
                raise Exception(f'{error_msg} exception: {ex}')
        if not resp.ok:
            log_text = True
            if resp.status_code == 500:
                # Unsupported additional parameters are visible in the HTML reply
                log_text = False
            self._LOGGER.warning(f'{error_msg} reply code: {resp.status_code}')
            if log_text:
                self._LOGGER.warning(f'{resp.text}')
            if not ignore_errors:
                raise Exception(f'{error_msg} reply code: {resp.status_code}')
        return resp

    def login(self, username, password):
        """Login to Ariston API."""
        login_data = {
            "email": username,
            "password": password,
            "rememberMe": False,
            "language": "English_Us"
        }
        self.request_post(
            url=f'{self._ARISTON_URL}/R2/Account/Login',
            json_data=login_data,
            error_msg='Login'
        )

    def get_gateways(self):
        """Fetch list of available gateways."""
        resp = self.request_get(
            url=f'{self._ARISTON_URL}/api/v2/remote/plants/lite',
            error_msg='Gateways'
        )
        return [item['gwId'] for item in resp.json()]

    def get_plant_features(self, plant_id):
        """Fetch features for a specific plant/gateway."""
        resp = self.request_get(
            url=f'{self._ARISTON_URL}/api/v2/remote/plants/{plant_id}/features?eagerMode=True',
            error_msg='Features'
        )
        return resp.json()

    def get_main_data(self, plant_id, request_data):
        """Fetch main sensor data."""
        resp = self.request_post(
            url=f'{self._ARISTON_URL}/api/v2/remote/dataItems/{plant_id}/get?umsys=si',
            json_data=request_data,
            timeout=self._TIMEOUT_MAX,
            error_msg="Main read"
        )
        return resp

    def get_errors(self, plant_id):
        """Fetch bus errors."""
        resp = self.request_get(
            url=f'{self._ARISTON_URL}/api/v2/busErrors?gatewayId={plant_id}&blockingOnly=False&culture=en-US',
            timeout=self._TIMEOUT_AV,
            error_msg="Errors read"
        )
        return resp

    def get_ch_schedule(self, plant_id):
        """Fetch CH schedule."""
        resp = self.request_get(
            url=f'{self._ARISTON_URL}/api/v2/remote/timeProgs/{plant_id}/ChZn1?umsys=si',
            timeout=self._TIMEOUT_AV,
            error_msg="CH Schedule read"
        )
        return resp

    def get_dhw_schedule(self, plant_id):
        """Fetch DHW schedule."""
        resp = self.request_get(
            url=f'{self._ARISTON_URL}/api/v2/remote/timeProgs/{plant_id}/Dhw?umsys=si',
            timeout=self._TIMEOUT_AV,
            error_msg="DHW Schedule read"
        )
        return resp

    def get_additional_data(self, plant_id, param_ids):
        """Fetch additional parameters."""
        resp = self.request_get(
            url=f'{self._ARISTON_URL}/R2/PlantMenu/Refresh?id={plant_id}&paramIds={",".join(param_ids)}',
            timeout=self._TIMEOUT_AV,
            error_msg="Additional data read"
        )
        return resp

    def get_last_month_data(self, plant_id):
        """Fetch last month energy data."""
        resp = self.request_get(
            url=f'{self._ARISTON_URL}/api/v2/remote/reports/{plant_id}/energyAccount',
            timeout=self._TIMEOUT_AV,
            error_msg="Last month data read"
        )
        return resp

    def get_energy_data(self, plant_id):
        """Fetch energy consumption data."""
        resp = self.request_get(
            url=f'{self._ARISTON_URL}/api/v2/remote/reports/{plant_id}/consSequencesApi8?usages=Ch%2CDhw&hasSlp=False',
            timeout=self._TIMEOUT_AV,
            error_msg="Energy data read"
        )
        return resp

    # --- Set operations ---
    def set_plant_mode(self, plant_id, new_value, old_value):
        return self.request_post(
            url=f'{self._ARISTON_URL}/api/v2/remote/plantData/{plant_id}/mode',
            json_data={"new": new_value, "old": old_value},
            error_msg='Set Mode',
            timeout=self._TIMEOUT_AV,
        )

    def set_zone_mode(self, plant_id, zone, new_value, old_value):
        return self.request_post(
            url=f'{self._ARISTON_URL}/api/v2/remote/zones/{plant_id}/{zone}/mode',
            json_data={"new": new_value, "old": old_value},
            error_msg='Set CH Mode',
            timeout=self._TIMEOUT_AV,
        )

    def set_dhw_mode(self, plant_id, new_value, old_value):
        return self.request_post(
            url=f'{self._ARISTON_URL}/api/v2/remote/plantData/{plant_id}/dhwMode',
            json_data={"new": new_value, "old": old_value},
            error_msg='Set DHW Mode',
            timeout=self._TIMEOUT_AV,
        )

    def set_zone_temperatures(self, plant_id, zone, new_payload, old_payload):
        return self.request_post(
            url=f'{self._ARISTON_URL}/api/v2/remote/zones/{plant_id}/{zone}/temperatures?umsys=si',
            json_data={"new": new_payload, "old": old_payload},
            error_msg='Set CH Temperature',
            timeout=self._TIMEOUT_AV,
        )

    def set_dhw_temp(self, plant_id, new_value, old_value):
        return self.request_post(
            url=f'{self._ARISTON_URL}/api/v2/remote/plantData/{plant_id}/dhwTemp?umsys=si',
            json_data={"new": new_value, "old": old_value},
            error_msg='Set DHW Temperature',
            timeout=self._TIMEOUT_AV,
        )

    def set_dhw_timeprog_temps(self, plant_id, new_payload, old_payload):
        return self.request_post(
            url=f'{self._ARISTON_URL}/api/v2/remote/plantData/{plant_id}/dhwTimeProgTemperatures?umsys=si',
            json_data={"new": new_payload, "old": old_payload},
            error_msg='Set DHW Time Prog Temperatures',
            timeout=self._TIMEOUT_AV,
        )

    def submit_additional_params(self, plant_id, params_list):
        return self.request_post(
            url=f'{self._ARISTON_URL}/R2/PlantMenu/Submit/{plant_id}',
            json_data=params_list,
            error_msg='Set additional parameters',
            timeout=self._TIMEOUT_AV,
        )

    def logout(self):
        return self.request_get(
            url=f'{self._ARISTON_URL}/R2/Account/Logout',
            error_msg='Logout',
            ignore_errors=True,
        )

    def close(self):
        """Close the session."""
        self._session.close()
