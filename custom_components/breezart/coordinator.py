"""Breezart TCP client and data coordinator."""
from __future__ import annotations

import asyncio
import logging
from datetime import timedelta
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import (
    BIT_CHANGE_FILTER,
    BIT_COLOR_IND_END,
    BIT_COLOR_IND_START,
    BIT_COLOR_MSG_END,
    BIT_COLOR_MSG_START,
    BIT_DANGER_OVERHEAT,
    BIT_FATAL_ERR,
    BIT_FORMAT_16,
    BIT_HIGH_BYTE_END,
    BIT_HIGH_BYTE_START,
    BIT_IS_COOLER,
    BIT_IS_HUMIDIFIER,
    BIT_LOW_BYTE_END,
    BIT_LOW_BYTE_START,
    BIT_MODE_END,
    BIT_MODE_SET_END,
    BIT_MODE_SET_START,
    BIT_MODE_START,
    BIT_PWR_BTN,
    BIT_SPEED_CUR_END,
    BIT_SPEED_CUR_START,
    BIT_SPEED_TGT_END,
    BIT_SPEED_TGT_START,
    BIT_UNIT_STATE_END,
    BIT_UNIT_STATE_START,
    BIT_WARN_ERR,
    DEFAULT_MODEL,
    DEFAULT_NAME,
    DEFAULT_TIMEOUT,
    DELIMITER,
    DOMAIN,
    ERROR_PREFIX,
    HEX_FORMAT_LOWER,
    HEX_ZERO,
    KEY_CHANGE_FILTER,
    KEY_CO2,
    KEY_COLOR_IND,
    KEY_COLOR_MSG,
    KEY_DANGER_OVERHEAT,
    KEY_FILTER1_POLLUTION,
    KEY_FILTER2_POLLUTION,
    KEY_FILTER3_POLLUTION,
    KEY_FILTER4_POLLUTION,
    KEY_FILTER_DUST,
    KEY_FIRMWARE_VER,
    KEY_HAS_COOLER,
    KEY_HAS_HUMIDIFIER,
    KEY_HUMIDITY,
    KEY_HUMIDITY_OUTDOOR,
    KEY_HUMIDITY_ROOM,
    KEY_HUMIDITY_SUPPLY,
    KEY_IS_FATAL_ERR,
    KEY_IS_WARN_ERR,
    KEY_MODE,
    KEY_MODE_SET,
    KEY_MSG,
    KEY_POWER,
    KEY_POWER_CONSUMPTION,
    KEY_PROTOCOL_VER,
    KEY_SPEED,
    KEY_SPEED_FACT,
    KEY_SPEED_MAX,
    KEY_SPEED_MIN,
    KEY_SPEED_TARGET,
    KEY_TEMP_MAX,
    KEY_TEMP_MIN,
    KEY_TEMP_OUTDOOR,
    KEY_TEMP_ROOM,
    KEY_TEMP_SUPPLY,
    KEY_TEMP_WATER,
    KEY_TEMPERATURE,
    KEY_TEMPERATURE_TARGET,
    KEY_UNIT_STATE,
    KEY_VOC,
    MANUFACTURER,
    MAX_UINT16,
    MODEL_CUSTOM,
    NO_DATA_BYTE,
    NO_DATA_HEX,
    POWER_OFF,
    POWER_ON,
    READ_BUFFER_SIZE,
    READ_DELAY_SECONDS,
    REQ_GET_PROPERTIES,
    REQ_GET_SENSORS,
    REQ_GET_STATE,
    REQ_SET_FAN_SPEED,
    REQ_SET_MODE,
    REQ_SET_POWER,
    REQ_SET_TEMP,
    RESP_OK,
    RESP_PROPERTIES,
    RESP_SENSORS,
    RESP_STATE,
    SENSORS_UPDATE_INTERVAL,
    SIGN_BIT_MASK,
    SIGN_BIT_OFFSET,
    SIGNED_BYTE_OFFSET,
    SIGNED_BYTE_THRESHOLD,
    STATE_UPDATE_INTERVAL,
    TEMP_DIVISOR,
    VPR07_IDX_FW,
    VPR07_IDX_MISC,
    VPR07_IDX_PROT,
    VPR07_IDX_SPEED,
    VPR07_IDX_TEMPR,
    VSENS_IDX_CO2,
    VSENS_IDX_FILTER1,
    VSENS_IDX_FILTER2,
    VSENS_IDX_FILTER3,
    VSENS_IDX_FILTER4,
    VSENS_IDX_HUMID_OUTDOOR,
    VSENS_IDX_HUMID_ROOM,
    VSENS_IDX_HUMID_SUPPLY,
    VSENS_IDX_POWER_CONSUMPTION,
    VSENS_IDX_TEMP_OUTDOOR,
    VSENS_IDX_TEMP_ROOM,
    VSENS_IDX_TEMP_SUPPLY,
    VSENS_IDX_TEMP_WATER,
    VSENS_IDX_VOC,
    VST07_IDX_HUMID,
    VST07_IDX_MISC,
    VST07_IDX_MODE,
    VST07_IDX_MSG,
    VST07_IDX_SPEED,
    VST07_IDX_STATE,
    VST07_IDX_TEMPR,
    get_model_preset,
)

_LOGGER = logging.getLogger(__name__)


def _dec_to_hex(value: int) -> str:
    """Convert decimal integer to hex string (like breezart-client decToHex)."""
    if not isinstance(value, int) or value < 0 or value > MAX_UINT16:
        raise ValueError(f"Value must be a positive integer <= {MAX_UINT16}, got {value}")
    return format(value, HEX_FORMAT_LOWER)


def _hex_to_dec(hex_str: str) -> int:
    """Convert hex string to unsigned decimal."""
    return int(hex_str, 16)


def _hex_to_dec_sign(hex_str: str) -> int:
    """Convert hex string to signed decimal (signed 16-bit)."""
    val = int(hex_str, 16)
    if val & SIGN_BIT_MASK:
        val -= SIGN_BIT_OFFSET
    return val


def _parse_bits(hex_str: str, from_bit: int, to_bit: int | None = None) -> int:
    """Extract bits from a hex string (like breezart-client parceBits)."""
    if to_bit is None:
        to_bit = from_bit
    if hex_str == HEX_ZERO:
        return 0
    num = int(hex_str, 16)
    bits = format(num, BIT_FORMAT_16)[::-1]
    extracted = bits[from_bit : to_bit + 1][::-1]
    return int(extracted, 2)


class BreezartTCPClient:
    """TCP client for Breezart ventilation system (native protocol, port 1560)."""

    def __init__(
        self,
        host: str,
        port: int,
        password: int | str,
        timeout: int = DEFAULT_TIMEOUT,
        model: str = DEFAULT_MODEL,
    ) -> None:
        """Initialize the TCP client with model preset defaults."""
        self.host = host
        self.port = port
        self.password = int(password)
        self.timeout = timeout
        self.model = model
        self._reader: asyncio.StreamReader | None = None
        self._writer: asyncio.StreamWriter | None = None

        preset = get_model_preset(model)
        self.temp_min: int = int(preset["temp_min"])
        self.temp_max: int = int(preset["temp_max"])
        self.speed_min: int = int(preset["speed_min"])
        self.speed_max: int = int(preset["speed_max"])
        self.has_cooler: bool = bool(preset["has_cooler"])
        self.has_humidifier: bool = bool(preset["has_humidifier"])
        self.firmware_ver: int | None = None
        self.protocol_ver: str | None = None

    def _build_request(self, request_type: str, data: int | None = None) -> str:
        """Build a request string: requestType_password[_data]."""
        parts = [request_type, _dec_to_hex(self.password)]
        if data is not None:
            parts.append(_dec_to_hex(data))
        return DELIMITER.join(parts)

    def _split_response(self, message: str) -> list[str]:
        """Split response by delimiter, removing empty parts."""
        return [v for v in message.split(DELIMITER) if v]

    def _check_error(self, parts: list[str]) -> None:
        """Raise if response indicates an error."""
        if parts and parts[0] in ERROR_PREFIX:
            raise PermissionError(
                f"Breezart error: {ERROR_PREFIX[parts[0]]} ({DELIMITER.join(parts)})"
            )

    async def connect(self) -> None:
        """Open TCP connection."""
        try:
            self._reader, self._writer = await asyncio.wait_for(
                asyncio.open_connection(self.host, self.port),
                timeout=self.timeout,
            )
            _LOGGER.info("Connected to Breezart at %s:%d", self.host, self.port)
        except (OSError, asyncio.TimeoutError) as err:
            _LOGGER.error("Failed to connect to Breezart: %s", err)
            raise

    async def disconnect(self) -> None:
        """Close TCP connection."""
        if self._writer:
            try:
                self._writer.close()
                await self._writer.wait_closed()
            except Exception:
                pass
            self._writer = None
            self._reader = None

    async def _send(self, request: str) -> list[str]:
        """Send a request and return split response."""
        if not self._writer or not self._reader:
            raise ConnectionError("Not connected to Breezart")

        _LOGGER.debug("Breezart TX: %s", request)
        self._writer.write(request.encode())
        await self._writer.drain()

        await asyncio.sleep(READ_DELAY_SECONDS)

        response = ""
        try:
            raw = await asyncio.wait_for(
                self._reader.read(READ_BUFFER_SIZE),
                timeout=self.timeout,
            )
            if not raw:
                raise TimeoutError(f"No response for request: {request}")
            response = raw.decode().strip()
        except asyncio.TimeoutError as err:
            raise TimeoutError(f"No response for request: {request}") from err
        except Exception as err:
            raise ConnectionError(f"Error reading response: {err}") from err

        if not response:
            raise TimeoutError(f"Empty response for request: {request}")

        _LOGGER.debug("Breezart RX: %s", response)
        parts = self._split_response(response)
        self._check_error(parts)
        return parts

    async def get_properties(self) -> None:
        """Read device properties (VPr07). Called once after connect."""
        req = self._build_request(REQ_GET_PROPERTIES)
        parts = await self._send(req)

        if not parts or parts[0] != RESP_PROPERTIES:
            raise ValueError(f"Unexpected properties response: {parts}")

        hw_temp_min = _parse_bits(parts[VPR07_IDX_TEMPR], BIT_LOW_BYTE_START, BIT_LOW_BYTE_END)
        hw_temp_max = _parse_bits(parts[VPR07_IDX_TEMPR], BIT_HIGH_BYTE_START, BIT_HIGH_BYTE_END)
        hw_speed_min = _parse_bits(parts[VPR07_IDX_SPEED], BIT_LOW_BYTE_START, BIT_LOW_BYTE_END)
        hw_speed_max = _parse_bits(parts[VPR07_IDX_SPEED], BIT_HIGH_BYTE_START, BIT_HIGH_BYTE_END)
        hw_cooler = bool(_parse_bits(parts[VPR07_IDX_MISC], BIT_IS_COOLER))
        hw_humid = bool(_parse_bits(parts[VPR07_IDX_MISC], BIT_IS_HUMIDIFIER))

        # Apply hardware values if in custom mode or if valid ranges are returned
        if self.model == MODEL_CUSTOM:
            if hw_temp_max > hw_temp_min:
                self.temp_min = hw_temp_min
                self.temp_max = hw_temp_max
            if hw_speed_max >= hw_speed_min > 0:
                self.speed_min = hw_speed_min
                self.speed_max = hw_speed_max
            self.has_cooler = hw_cooler
            self.has_humidifier = hw_humid
        else:
            preset = get_model_preset(self.model)
            self.temp_min = hw_temp_min if hw_temp_max > hw_temp_min else int(preset["temp_min"])
            self.temp_max = hw_temp_max if hw_temp_max > hw_temp_min else int(preset["temp_max"])
            self.speed_min = int(preset["speed_min"])
            self.speed_max = int(preset["speed_max"])
            self.has_cooler = bool(preset["has_cooler"]) or hw_cooler
            self.has_humidifier = bool(preset["has_humidifier"]) or hw_humid

        sub = _parse_bits(parts[VPR07_IDX_PROT], BIT_LOW_BYTE_START, BIT_LOW_BYTE_END)
        major = _parse_bits(parts[VPR07_IDX_PROT], BIT_HIGH_BYTE_START, BIT_HIGH_BYTE_END)
        self.protocol_ver = f"{major}.{sub}"
        self.firmware_ver = _hex_to_dec(parts[VPR07_IDX_FW])

        _LOGGER.info(
            "Breezart (%s) properties: T=%d..%d°C, Speed=%d..%d, fw=%s, proto=%s",
            self.model,
            self.temp_min,
            self.temp_max,
            self.speed_min,
            self.speed_max,
            self.firmware_ver,
            self.protocol_ver,
        )

    async def get_state(self) -> dict[str, Any]:
        """Read current state (VSt07)."""
        req = self._build_request(REQ_GET_STATE)
        parts = await self._send(req)

        if not parts or parts[0] != RESP_STATE:
            raise ValueError(f"Unexpected state response: {parts}")

        pwr_btn_state = _parse_bits(parts[VST07_IDX_STATE], BIT_PWR_BTN)
        is_warn_err = bool(_parse_bits(parts[VST07_IDX_STATE], BIT_WARN_ERR))
        is_fatal_err = bool(_parse_bits(parts[VST07_IDX_STATE], BIT_FATAL_ERR))
        danger_overheat = bool(_parse_bits(parts[VST07_IDX_STATE], BIT_DANGER_OVERHEAT))
        change_filter = bool(_parse_bits(parts[VST07_IDX_STATE], BIT_CHANGE_FILTER))
        mode_set = _parse_bits(parts[VST07_IDX_STATE], BIT_MODE_SET_START, BIT_MODE_SET_END)

        unit_state = _parse_bits(parts[VST07_IDX_MODE], BIT_UNIT_STATE_START, BIT_UNIT_STATE_END)
        mode = _parse_bits(parts[VST07_IDX_MODE], BIT_MODE_START, BIT_MODE_END)

        tempr_raw = _parse_bits(parts[VST07_IDX_TEMPR], BIT_LOW_BYTE_START, BIT_LOW_BYTE_END)
        tempr = (
            tempr_raw
            if tempr_raw < SIGNED_BYTE_THRESHOLD
            else tempr_raw - SIGNED_BYTE_OFFSET
        )
        temper_target = _parse_bits(parts[VST07_IDX_TEMPR], BIT_HIGH_BYTE_START, BIT_HIGH_BYTE_END)

        humid_raw = _parse_bits(parts[VST07_IDX_HUMID], BIT_LOW_BYTE_START, BIT_LOW_BYTE_END)
        humid = None if humid_raw == NO_DATA_BYTE else humid_raw

        speed = _parse_bits(parts[VST07_IDX_SPEED], BIT_SPEED_CUR_START, BIT_SPEED_CUR_END)
        speed_target = _parse_bits(parts[VST07_IDX_SPEED], BIT_SPEED_TGT_START, BIT_SPEED_TGT_END)
        speed_fact_raw = _parse_bits(
            parts[VST07_IDX_SPEED], BIT_HIGH_BYTE_START, BIT_HIGH_BYTE_END
        )
        speed_fact = None if speed_fact_raw == NO_DATA_BYTE else speed_fact_raw

        color_msg = _parse_bits(parts[VST07_IDX_MISC], BIT_COLOR_MSG_START, BIT_COLOR_MSG_END)
        color_ind = _parse_bits(parts[VST07_IDX_MISC], BIT_COLOR_IND_START, BIT_COLOR_IND_END)
        filter_dust_raw = _parse_bits(
            parts[VST07_IDX_MISC], BIT_HIGH_BYTE_START, BIT_HIGH_BYTE_END
        )
        filter_dust = None if filter_dust_raw == NO_DATA_BYTE else filter_dust_raw

        msg = parts[VST07_IDX_MSG] if len(parts) > VST07_IDX_MSG else None

        return {
            KEY_POWER: bool(pwr_btn_state),
            KEY_UNIT_STATE: unit_state,
            KEY_MODE: mode,
            KEY_MODE_SET: mode_set,
            KEY_TEMPERATURE: float(tempr),
            KEY_TEMPERATURE_TARGET: float(temper_target),
            KEY_HUMIDITY: humid,
            KEY_SPEED: speed,
            KEY_SPEED_TARGET: speed_target,
            KEY_SPEED_FACT: speed_fact,
            KEY_FILTER_DUST: filter_dust,
            KEY_IS_WARN_ERR: is_warn_err,
            KEY_IS_FATAL_ERR: is_fatal_err,
            KEY_DANGER_OVERHEAT: danger_overheat,
            KEY_CHANGE_FILTER: change_filter,
            KEY_COLOR_MSG: color_msg,
            KEY_COLOR_IND: color_ind,
            KEY_MSG: msg,
        }

    async def get_sensors(self) -> dict[str, Any]:
        """Read sensor values (VSens)."""
        req = self._build_request(REQ_GET_SENSORS)
        parts = await self._send(req)

        if not parts or parts[0] != RESP_SENSORS:
            raise ValueError(f"Unexpected sensors response: {parts}")

        _LOGGER.debug("VSens parts count: %d, parts: %s", len(parts), parts)

        def _parse_temp_sensor(val: str) -> float | None:
            if val.lower() == NO_DATA_HEX:
                return None
            return _hex_to_dec_sign(val) / TEMP_DIVISOR

        def _parse_sensor(val: str) -> float | None:
            if val.lower() == NO_DATA_HEX:
                return None
            return float(_hex_to_dec(val))

        def _get(idx: int, is_temp: bool = False) -> float | None:
            if len(parts) <= idx:
                return None
            return _parse_temp_sensor(parts[idx]) if is_temp else _parse_sensor(parts[idx])

        return {
            KEY_TEMP_SUPPLY: _get(VSENS_IDX_TEMP_SUPPLY, is_temp=True),
            KEY_HUMIDITY_SUPPLY: _get(VSENS_IDX_HUMID_SUPPLY),
            KEY_TEMP_ROOM: _get(VSENS_IDX_TEMP_ROOM),
            KEY_HUMIDITY_ROOM: _get(VSENS_IDX_HUMID_ROOM),
            KEY_TEMP_OUTDOOR: _get(VSENS_IDX_TEMP_OUTDOOR, is_temp=True),
            KEY_HUMIDITY_OUTDOOR: _get(VSENS_IDX_HUMID_OUTDOOR),
            KEY_TEMP_WATER: _get(VSENS_IDX_TEMP_WATER),
            KEY_POWER_CONSUMPTION: _get(VSENS_IDX_POWER_CONSUMPTION),
            KEY_CO2: _get(VSENS_IDX_CO2),
            KEY_VOC: _get(VSENS_IDX_VOC),
            KEY_FILTER1_POLLUTION: _get(VSENS_IDX_FILTER1),
            KEY_FILTER2_POLLUTION: _get(VSENS_IDX_FILTER2),
            KEY_FILTER3_POLLUTION: _get(VSENS_IDX_FILTER3),
            KEY_FILTER4_POLLUTION: _get(VSENS_IDX_FILTER4),
        }

    async def set_power(self, on: bool) -> None:
        """Turn device on or off (VWPwr)."""
        data = POWER_ON if on else POWER_OFF
        req = self._build_request(REQ_SET_POWER, data)
        parts = await self._send(req)
        if not parts or parts[0] != RESP_OK:
            raise ValueError(f"Unexpected set_power response: {parts}")

    async def set_temperature(self, temperature: int) -> None:
        """Set target temperature (VWTmp). Must be integer degrees."""
        req = self._build_request(REQ_SET_TEMP, temperature)
        parts = await self._send(req)
        if not parts or parts[0] != RESP_OK:
            raise ValueError(f"Unexpected set_temperature response: {parts}")

    async def set_fan_speed(self, speed: int) -> None:
        """Set fan speed (VWSpd)."""
        req = self._build_request(REQ_SET_FAN_SPEED, speed)
        parts = await self._send(req)
        if not parts or parts[0] != RESP_OK:
            raise ValueError(f"Unexpected set_fan_speed response: {parts}")

    async def set_mode(self, mode: int) -> None:
        """Set work mode (VWFtr). 1=Heat, 2=Cool, 3=Auto, 4=Vent."""
        req = self._build_request(REQ_SET_MODE, mode)
        parts = await self._send(req)
        if not parts or parts[0] != RESP_OK:
            raise ValueError(f"Unexpected set_mode response: {parts}")


class BreezartDataCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Coordinator that polls Breezart for state and sensor data."""

    def __init__(
        self,
        hass: HomeAssistant,
        client: BreezartTCPClient,
        model: str = DEFAULT_MODEL,
    ) -> None:
        """Initialize the coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=STATE_UPDATE_INTERVAL),
        )
        self.client = client
        self.model = model
        self.preset = get_model_preset(model)
        self._properties_loaded = False
        self._cached_sensors: dict[str, Any] = {}
        self._sensors_update_counter = 0

    @property
    def model_name(self) -> str:
        """Return display model name from preset."""
        return str(self.preset["name"])

    @property
    def device_info(self) -> DeviceInfo:
        """Return shared DeviceInfo for all Breezart entities."""
        return DeviceInfo(
            identifiers={(DOMAIN, self.client.host)},
            name=f"{DEFAULT_NAME} {self.model_name}",
            manufacturer=MANUFACTURER,
            model=self.model_name,
            sw_version=str(self.client.firmware_ver or ""),
        )

    async def _async_update_data(self) -> dict[str, Any]:
        """Fetch latest data from Breezart."""
        try:
            if not self.client._writer:
                await self.client.connect()

            if not self._properties_loaded:
                await self.client.get_properties()
                self._properties_loaded = True

            state = await self.client.get_state()

            self._sensors_update_counter += 1
            cycles_per_sensor_update = max(1, SENSORS_UPDATE_INTERVAL // STATE_UPDATE_INTERVAL)
            if (
                self._sensors_update_counter >= cycles_per_sensor_update
                or not self._cached_sensors
            ):
                self._cached_sensors = await self.client.get_sensors()
                self._sensors_update_counter = 0
                _LOGGER.debug("Breezart sensors refreshed")

            data = {**state, **self._cached_sensors}

            data[KEY_TEMP_MIN] = self.client.temp_min
            data[KEY_TEMP_MAX] = self.client.temp_max
            data[KEY_SPEED_MIN] = self.client.speed_min
            data[KEY_SPEED_MAX] = self.client.speed_max
            data[KEY_HAS_COOLER] = self.client.has_cooler
            data[KEY_HAS_HUMIDIFIER] = self.client.has_humidifier
            data[KEY_FIRMWARE_VER] = self.client.firmware_ver
            data[KEY_PROTOCOL_VER] = self.client.protocol_ver

            _LOGGER.debug(
                "Breezart state update: power=%s temp=%s speed=%s",
                data.get(KEY_POWER),
                data.get(KEY_TEMPERATURE_TARGET),
                data.get(KEY_SPEED_TARGET),
            )
            return data

        except (ConnectionError, OSError, TimeoutError) as err:
            self._properties_loaded = False
            self._cached_sensors = {}
            await self.client.disconnect()
            raise UpdateFailed(f"Connection error: {err}") from err
        except Exception as err:
            raise UpdateFailed(f"Error communicating with Breezart: {err}") from err
