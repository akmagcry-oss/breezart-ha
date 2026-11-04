"""Breezart Native TCP (port 1560) and Modbus TCP (port 502, JLV135/JL204c7) clients and coordinator."""
from __future__ import annotations

import asyncio
import logging
import struct
import time
from collections.abc import Iterable
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
    BIT_DANGER_FREEZE,
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
    CMD_MODE_HEAT,
    CMD_MODE_TO_MODBUS_HC,
    COLOR_IND_OFF,
    COLOR_IND_ON,
    COLOR_IND_TRANSITION,
    COLOR_MSG_ERROR,
    COLOR_MSG_NORMAL,
    COLOR_MSG_WARNING,
    DEFAULT_MODBUS_PORT,
    DEFAULT_MODEL,
    DEFAULT_NAME,
    DEFAULT_NOTIFY_SERVICE,
    DEFAULT_PASSWORD,
    DEFAULT_PORT,
    DEFAULT_PROTOCOL,
    DEFAULT_SLAVE_ID,
    DEFAULT_TIMEOUT,
    DELIMITER,
    DOMAIN,
    ERROR_PREFIX,
    EVENT_BREEZART_NOTIFICATION,
    FILTER_POLLUTION_REPLACE_MAX,
    FREEZE_OUTDOOR_TEMP_THRESHOLD,
    FREEZE_SUPPLY_TEMP_THRESHOLD,
    HEX_FORMAT_LOWER,
    HEX_ZERO,
    KEY_CHANGE_FILTER,
    KEY_CO2,
    KEY_COLOR_IND,
    KEY_COLOR_MSG,
    KEY_DANGER_FREEZE,
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
    KEY_NOTIFY_FILTER,
    KEY_NOTIFY_FREEZE,
    KEY_NOTIFY_OFFLINE,
    KEY_NOTIFY_ONLINE,
    KEY_NOTIFY_OTHER_ERRORS,
    KEY_NOTIFY_OVERHEAT,
    KEY_NOTIFY_POWER,
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
    MODBUS_ALARM_BIT_FILTER,
    MODBUS_ALARM_BIT_FREEZE,
    MODBUS_ALARM_BIT_OVERHEAT,
    MODBUS_EXC_ILLEGAL_DATA_ADDRESS,
    MODBUS_EXC_ILLEGAL_FUNCTION,
    MODBUS_EXCEPTION_MASK,
    MODBUS_FC_READ_HOLDING,
    MODBUS_FC_READ_INPUT,
    MODBUS_FC_WRITE_SINGLE,
    MODBUS_HC_AUTO,
    MODBUS_HC_COOL,
    MODBUS_HC_HEAT,
    MODBUS_HC_TO_CMD_MODE,
    MODBUS_HC_VENT,
    MODBUS_HR_BLOCK_COUNT,
    MODBUS_HR_BLOCK_START,
    MODBUS_HR_FAN_SPEED,
    MODBUS_HR_HUMID_TARGET,
    MODBUS_HR_MODE_HC,
    MODBUS_HR_POWER_STATE,
    MODBUS_HR_TEMP_TARGET,
    MODBUS_INVALID_VALUES,
    MODBUS_IR_FAN_BLOCK_COUNT,
    MODBUS_IR_FAN_BLOCK_START,
    MODBUS_IR_FILTER1_POLLUTION,
    MODBUS_IR_FILTER2_POLLUTION,
    MODBUS_IR_INFO_BLOCK_COUNT,
    MODBUS_IR_INFO_BLOCK_START,
    MODBUS_IR_SENSORS_BLOCK_COUNT,
    MODBUS_IR_SENSORS_BLOCK_START,
    MODBUS_IR_STATUS_BLOCK_COUNT,
    MODBUS_IR_STATUS_BLOCK_START,
    MODBUS_KW_TO_W_MULTIPLIER,
    MODBUS_MAX_PERCENT_RAW,
    MODBUS_MBAP_HEADER_LEN,
    MODBUS_OPTIONAL_BLOCK_MAX_FAILURES,
    MODBUS_PERCENT_MULTIPLIER,
    MODBUS_PROTOCOL_ID,
    MODBUS_READ_DELAY_SECONDS,
    MODBUS_READ_PDU_LEN,
    MODBUS_STATUS_BIT_COOLING,
    MODBUS_STATUS_BIT_FATAL,
    MODBUS_STATUS_BIT_HEATING,
    MODBUS_STATUS_BIT_OVERHEAT_BLOW,
    MODBUS_STATUS_BIT_POWER,
    MODBUS_STATUS_BIT_TRANSITION,
    MODBUS_STATUS_BIT_WARN,
    MODBUS_STATUS_BIT_WINTER,
    MODBUS_WRITE_SINGLE_PDU_LEN,
    MODE_AUTO_COOL,
    MODE_AUTO_HEAT,
    MODE_COOL,
    MODE_HEAT,
    MODE_OFF,
    MODE_VENT,
    MODEL_CUSTOM,
    MOBILE_APP_SERVICE_PREFIX,
    NO_DATA_BYTE,
    NO_DATA_HEX,
    NOTIFICATION_SETTING_KEYS,
    NOTIFY_COOLDOWN_SECONDS,
    NOTIFY_DOMAIN,
    NOTIFY_EVENT_FILTER,
    NOTIFY_EVENT_FREEZE,
    NOTIFY_EVENT_OFFLINE,
    NOTIFY_EVENT_ONLINE,
    NOTIFY_EVENT_OTHER_ERRORS,
    NOTIFY_EVENT_OVERHEAT,
    NOTIFY_EVENT_POWER_OFF,
    NOTIFY_EVENT_POWER_ON,
    NOTIFY_OFFLINE_FAILURE_THRESHOLD,
    NOTIFY_POWER_COOLDOWN_SECONDS,
    PERSISTENT_NOTIFICATION_DOMAIN,
    POWER_OFF,
    POWER_ON,
    PROTOCOL_AUTO,
    PROTOCOL_MODBUS_TCP,
    PROTOCOL_NATIVE_TCP,
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
    SERVICE_CREATE,
    SIGN_BIT_MASK,
    SIGN_BIT_OFFSET,
    SIGNED_BYTE_OFFSET,
    SIGNED_BYTE_THRESHOLD,
    STATE_UPDATE_INTERVAL,
    TEMP_DIVISOR,
    UNIT_STATE_OFF,
    UNIT_STATE_ON,
    UNIT_STATE_SHUTDOWN,
    UNIT_STATE_STARTUP,
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
    translate_value,
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


def _to_signed16(val: int) -> int:
    """Convert unsigned 16-bit integer to signed 16-bit integer."""
    if val & SIGN_BIT_MASK:
        return val - SIGN_BIT_OFFSET
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


def _parse_io_data(
    val_word: int,
    status_word: int,
    *,
    is_signed: bool = True,
    divisor: float = TEMP_DIVISOR,
) -> float | None:
    """Parse a 2-register JL204c7 IO_DATA pair (value register + reliability status register)."""
    if val_word in MODBUS_INVALID_VALUES:
        return None
    # In JL204c7 IO_DATA, status_word != 0 indicates sensor disconnected / fault
    if status_word != 0:
        return None
    raw = _to_signed16(val_word) if is_signed else val_word
    return round(raw / divisor, 1)


def _detect_freeze_hazard(
    *,
    hw_freeze_flag: bool,
    power: bool,
    mode: int,
    control_temp: float | None,
    supply_temp: float | None,
    outdoor_temp: float | None,
    water_temp: float | None,
) -> bool:
    """Return True if hardware freeze alarm is set or temperatures indicate freeze hazard."""
    if hw_freeze_flag:
        return True
    if supply_temp is not None and supply_temp < FREEZE_SUPPLY_TEMP_THRESHOLD:
        return True
    if water_temp is not None and water_temp < FREEZE_SUPPLY_TEMP_THRESHOLD:
        return True
    if power and control_temp is not None and control_temp < FREEZE_SUPPLY_TEMP_THRESHOLD:
        return True
    if (
        power
        and outdoor_temp is not None
        and outdoor_temp < FREEZE_OUTDOOR_TEMP_THRESHOLD
        and mode in (MODE_VENT, MODE_COOL, MODE_AUTO_COOL)
    ):
        return True
    return False


class ModbusExceptionError(ValueError):
    """The device answered with a Modbus exception frame (the connection is still in sync)."""

    def __init__(self, code: int, message: str) -> None:
        """Store the Modbus exception code."""
        super().__init__(message)
        self.code = code


class BreezartTCPClient:
    """TCP client for Breezart ventilation system (native ASCII protocol, port 1560)."""

    protocol_type: str = PROTOCOL_NATIVE_TCP

    def __init__(
        self,
        host: str,
        port: int = DEFAULT_PORT,
        password: int | str = DEFAULT_PASSWORD,
        timeout: int = DEFAULT_TIMEOUT,
        model: str = DEFAULT_MODEL,
        *,
        speed_max: int | None = None,
        temp_min: int | None = None,
        temp_max: int | None = None,
    ) -> None:
        """Initialize the native TCP client with model preset defaults and optional user bounds."""
        self.host = host
        self.port = port
        self.password = int(password) if str(password).strip().isdigit() else int(DEFAULT_PASSWORD)
        self.timeout = timeout
        self.model = model
        self._reader: asyncio.StreamReader | None = None
        self._writer: asyncio.StreamWriter | None = None
        self._lock = asyncio.Lock()

        preset = get_model_preset(model)
        self._user_temp_min: int | None = int(temp_min) if temp_min is not None else None
        self._user_temp_max: int | None = int(temp_max) if temp_max is not None else None
        self._user_speed_max: int | None = int(speed_max) if speed_max is not None else None

        self.temp_min: int = (
            self._user_temp_min if self._user_temp_min is not None else int(preset["temp_min"])
        )
        self.temp_max: int = (
            self._user_temp_max if self._user_temp_max is not None else int(preset["temp_max"])
        )
        self.speed_min: int = int(preset["speed_min"])
        self.speed_max: int = (
            self._user_speed_max if self._user_speed_max is not None else int(preset["speed_max"])
        )
        self.has_cooler: bool = bool(preset["has_cooler"])
        self.has_humidifier: bool = bool(preset["has_humidifier"])
        self.firmware_ver: int | str | None = None
        self.protocol_ver: str | None = None
        self._last_temp_supply: float | None = None
        self._last_temp_outdoor: float | None = None
        self._last_temp_water: float | None = None

    @property
    def is_connected(self) -> bool:
        """Return True if TCP stream writer is active."""
        return self._writer is not None

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
            _LOGGER.info("Connected to Breezart (Native TCP) at %s:%d", self.host, self.port)
        except (OSError, asyncio.TimeoutError) as err:
            _LOGGER.error("Failed to connect to Breezart (Native TCP): %s", err)
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

    def _drop_connection(self) -> None:
        """Close the socket without waiting so a desynced stream is never reused."""
        if self._writer:
            self._writer.close()
        self._writer = None
        self._reader = None

    async def _read_response(self) -> bytes:
        """Read one reply, tolerating replies split across several TCP segments.

        The native protocol has no terminator, so after the first chunk keep reading
        until the device has been silent for READ_DELAY_SECONDS.
        """
        assert self._reader is not None
        raw = await asyncio.wait_for(
            self._reader.read(READ_BUFFER_SIZE), timeout=self.timeout
        )
        if not raw:
            raise ConnectionError("Connection closed by Breezart")
        while len(raw) < READ_BUFFER_SIZE:
            try:
                chunk = await asyncio.wait_for(
                    self._reader.read(READ_BUFFER_SIZE - len(raw)),
                    timeout=READ_DELAY_SECONDS,
                )
            except asyncio.TimeoutError:
                break
            if not chunk:
                break
            raw += chunk
        return raw

    async def _send(self, request: str) -> list[str]:
        """Send a request and return split response."""
        async with self._lock:
            if not self._writer or not self._reader:
                raise ConnectionError("Not connected to Breezart")

            _LOGGER.debug("Breezart Native TX: %s", request)
            try:
                self._writer.write(request.encode())
                await self._writer.drain()
                raw = await self._read_response()
            except asyncio.TimeoutError as err:
                # A late reply would be read as the answer to the next request.
                self._drop_connection()
                raise TimeoutError(f"No response for request: {request}") from err
            except BaseException as err:
                self._drop_connection()
                if isinstance(err, Exception) and not isinstance(err, ConnectionError):
                    raise ConnectionError(f"Error reading response: {err}") from err
                raise

            response = raw.decode(errors="ignore").strip()
            if not response:
                self._drop_connection()
                raise TimeoutError(f"Empty response for request: {request}")

            _LOGGER.debug("Breezart Native RX: %s", response)
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

        preset = get_model_preset(self.model)
        if 5 <= hw_temp_min < hw_temp_max <= 45:
            if self._user_temp_min is None:
                self.temp_min = hw_temp_min
            if self._user_temp_max is None:
                self.temp_max = hw_temp_max
        if 1 <= hw_speed_min < hw_speed_max <= 10:
            self.speed_min = hw_speed_min
            if self._user_speed_max is None:
                self.speed_max = hw_speed_max

        if self.model == MODEL_CUSTOM:
            self.has_cooler = hw_cooler
            self.has_humidifier = hw_humid
        else:
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
        bit_danger_freeze = bool(_parse_bits(parts[VST07_IDX_STATE], BIT_DANGER_FREEZE))
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
        power = bool(pwr_btn_state)
        danger_freeze = _detect_freeze_hazard(
            hw_freeze_flag=bit_danger_freeze,
            power=power,
            mode=mode,
            control_temp=float(tempr),
            supply_temp=self._last_temp_supply,
            outdoor_temp=self._last_temp_outdoor,
            water_temp=self._last_temp_water,
        )

        return {
            KEY_POWER: power,
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
            KEY_DANGER_FREEZE: danger_freeze,
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

        temp_supply = _get(VSENS_IDX_TEMP_SUPPLY, is_temp=True)
        temp_outdoor = _get(VSENS_IDX_TEMP_OUTDOOR, is_temp=True)
        temp_water = _get(VSENS_IDX_TEMP_WATER, is_temp=True)
        self._last_temp_supply = temp_supply
        self._last_temp_outdoor = temp_outdoor
        self._last_temp_water = temp_water

        return {
            KEY_TEMP_SUPPLY: temp_supply,
            KEY_HUMIDITY_SUPPLY: _get(VSENS_IDX_HUMID_SUPPLY),
            KEY_TEMP_ROOM: _get(VSENS_IDX_TEMP_ROOM, is_temp=True),
            KEY_HUMIDITY_ROOM: _get(VSENS_IDX_HUMID_ROOM),
            KEY_TEMP_OUTDOOR: temp_outdoor,
            KEY_HUMIDITY_OUTDOOR: _get(VSENS_IDX_HUMID_OUTDOOR),
            KEY_TEMP_WATER: temp_water,
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


class BreezartModbusClient:
    """Modbus TCP client for Breezart JLV135 panel & JL204c7 controller (port 502)."""

    protocol_type: str = PROTOCOL_MODBUS_TCP

    def __init__(
        self,
        host: str,
        port: int = DEFAULT_MODBUS_PORT,
        slave_id: int = DEFAULT_SLAVE_ID,
        timeout: int = DEFAULT_TIMEOUT,
        model: str = DEFAULT_MODEL,
        *,
        speed_max: int | None = None,
        temp_min: int | None = None,
        temp_max: int | None = None,
    ) -> None:
        """Initialize the Modbus TCP client with model preset defaults and optional user bounds."""
        self.host = host
        self.port = port
        self.slave_id = int(slave_id)
        self.timeout = timeout
        self.model = model
        self._reader: asyncio.StreamReader | None = None
        self._writer: asyncio.StreamWriter | None = None
        self._lock = asyncio.Lock()
        self._tx_id: int = 0
        # Optional register blocks: start address -> consecutive failures / disabled set
        self._optional_failures: dict[int, int] = {}
        self._unsupported_blocks: set[int] = set()
        self._last_filter1_dust: float | None = None
        self._last_temp_supply: float | None = None
        self._last_temp_outdoor: float | None = None
        self._last_temp_water: float | None = None

        preset = get_model_preset(model)
        self._user_temp_min: int | None = int(temp_min) if temp_min is not None else None
        self._user_temp_max: int | None = int(temp_max) if temp_max is not None else None
        self._user_speed_max: int | None = int(speed_max) if speed_max is not None else None

        self.temp_min: int = (
            self._user_temp_min if self._user_temp_min is not None else int(preset["temp_min"])
        )
        self.temp_max: int = (
            self._user_temp_max if self._user_temp_max is not None else int(preset["temp_max"])
        )
        self.speed_min: int = int(preset["speed_min"])
        self.speed_max: int = (
            self._user_speed_max if self._user_speed_max is not None else int(preset["speed_max"])
        )
        self.has_cooler: bool = bool(preset["has_cooler"])
        self.has_humidifier: bool = bool(preset["has_humidifier"])
        self.firmware_ver: int | str | None = None
        self.protocol_ver: str | None = f"Modbus TCP (ID={self.slave_id})"

    @property
    def is_connected(self) -> bool:
        """Return True if TCP stream writer is active."""
        return self._writer is not None

    def _next_tx_id(self) -> int:
        """Return next 16-bit Modbus transaction identifier."""
        self._tx_id = (self._tx_id % MAX_UINT16) + 1
        return self._tx_id

    async def connect(self) -> None:
        """Open Modbus TCP connection on port 502."""
        try:
            self._reader, self._writer = await asyncio.wait_for(
                asyncio.open_connection(self.host, self.port),
                timeout=self.timeout,
            )
            _LOGGER.info(
                "Connected to Breezart (Modbus TCP) at %s:%d (slave_id=%d)",
                self.host,
                self.port,
                self.slave_id,
            )
        except (OSError, asyncio.TimeoutError) as err:
            _LOGGER.error("Failed to connect to Breezart (Modbus TCP): %s", err)
            raise

    async def disconnect(self) -> None:
        """Close Modbus TCP connection."""
        if self._writer:
            try:
                self._writer.close()
                await self._writer.wait_closed()
            except Exception:
                pass
            self._writer = None
            self._reader = None

    def _drop_connection(self) -> None:
        """Close the socket without waiting so a desynced stream is never reused."""
        if self._writer:
            self._writer.close()
        self._writer = None
        self._reader = None

    async def _transact(self, frame: bytes, tx_id: int) -> bytes:
        """Send an MBAP frame and return the matching response PDU.

        Must be called with self._lock held. Any transport-level failure (timeout,
        short read, transaction ID mismatch) drops the connection, because the
        stream position is no longer known and a late reply would otherwise be
        taken as the answer to the next request. Modbus exception replies are
        complete frames, so they leave the connection intact.
        """
        if not self._writer or not self._reader:
            raise ConnectionError("Not connected to Breezart Modbus TCP")
        try:
            self._writer.write(frame)
            await self._writer.drain()
            await asyncio.sleep(MODBUS_READ_DELAY_SECONDS)

            header = await asyncio.wait_for(
                self._reader.readexactly(MODBUS_MBAP_HEADER_LEN),
                timeout=self.timeout,
            )
            rx_tx_id, _rx_proto, rx_len, _rx_unit = struct.unpack(">HHHB", header)
            pdu = await asyncio.wait_for(
                self._reader.readexactly(max(0, rx_len - 1)),
                timeout=self.timeout,
            )
        except BaseException:
            self._drop_connection()
            raise

        _LOGGER.debug("Modbus RX (tx=%d): %s %s", rx_tx_id, header.hex(" "), pdu.hex(" "))
        if rx_tx_id != tx_id:
            self._drop_connection()
            raise ConnectionError(
                f"Modbus transaction ID mismatch: sent {tx_id}, received {rx_tx_id}"
            )
        if not pdu:
            self._drop_connection()
            raise ConnectionError(f"Empty Modbus PDU for tx={tx_id}")
        return pdu

    async def _read_registers(
        self, func_code: int, start_addr: int, count: int
    ) -> list[int]:
        """Read Holding (0x03) or Input (0x04) registers via MBAP framing."""
        async with self._lock:
            tx_id = self._next_tx_id()
            frame = struct.pack(
                ">HHHBBHH",
                tx_id,
                MODBUS_PROTOCOL_ID,
                MODBUS_READ_PDU_LEN,
                self.slave_id,
                func_code,
                start_addr,
                count,
            )
            _LOGGER.debug(
                "Modbus TX (FC=0x%02x addr=%d count=%d): %s",
                func_code,
                start_addr,
                count,
                frame.hex(" "),
            )
            pdu = await self._transact(frame, tx_id)

        if pdu[0] & MODBUS_EXCEPTION_MASK:
            exc_code = pdu[1] if len(pdu) > 1 else 0
            raise ModbusExceptionError(
                exc_code,
                f"Modbus exception 0x{exc_code:02x} on FC 0x{func_code:02x} addr={start_addr}",
            )

        expected_bytes = count * 2
        if len(pdu) < 2 or pdu[1] < expected_bytes or len(pdu) < 2 + expected_bytes:
            raise ValueError(
                f"Short Modbus payload: got {max(0, len(pdu) - 2)} bytes, expected {expected_bytes}"
            )

        return list(struct.unpack(f">{count}H", pdu[2 : 2 + expected_bytes]))

    async def _write_register(self, reg_addr: int, value: int) -> None:
        """Write a single Holding register (FC 0x06) via MBAP framing."""
        async with self._lock:
            tx_id = self._next_tx_id()
            raw_val = value & MAX_UINT16
            frame = struct.pack(
                ">HHHBBHH",
                tx_id,
                MODBUS_PROTOCOL_ID,
                MODBUS_WRITE_SINGLE_PDU_LEN,
                self.slave_id,
                MODBUS_FC_WRITE_SINGLE,
                reg_addr,
                raw_val,
            )
            _LOGGER.debug(
                "Modbus Write TX (FC=0x06 reg=%d val=%d): %s",
                reg_addr,
                value,
                frame.hex(" "),
            )
            pdu = await self._transact(frame, tx_id)

        if pdu[0] & MODBUS_EXCEPTION_MASK:
            exc_code = pdu[1] if len(pdu) > 1 else 0
            raise ModbusExceptionError(
                exc_code, f"Modbus write exception 0x{exc_code:02x} on reg={reg_addr}"
            )

    async def _read_optional_block(
        self, start_addr: int, count: int, label: str
    ) -> list[int] | None:
        """Read an Input register block that not every controller provides.

        Returns None when the block is unavailable. A Modbus "illegal function/address"
        reply disables the block at once; other failures (including a device that stays
        silent) disable it after MODBUS_OPTIONAL_BLOCK_MAX_FAILURES consecutive attempts.
        Disabled blocks are skipped until the integration is reloaded, so a silent
        register no longer costs a timeout and a reconnect on every poll.
        """
        if start_addr in self._unsupported_blocks:
            return None
        if not self.is_connected:
            # An earlier read in this poll dropped the socket; don't blame this block.
            await self.connect()
        try:
            regs = await self._read_registers(MODBUS_FC_READ_INPUT, start_addr, count)
        except ModbusExceptionError as err:
            definitive = err.code in (
                MODBUS_EXC_ILLEGAL_FUNCTION,
                MODBUS_EXC_ILLEGAL_DATA_ADDRESS,
            )
            self._record_optional_failure(start_addr, label, err, definitive=definitive)
            return None
        except ValueError as err:
            self._record_optional_failure(start_addr, label, err, definitive=False)
            return None
        except (TimeoutError, ConnectionError, OSError, asyncio.IncompleteReadError) as err:
            self._record_optional_failure(start_addr, label, err, definitive=False)
            # _transact dropped the desynced socket; reconnect so the rest of this poll
            # can continue. If the device is really gone, connect() raises to the caller.
            if not self.is_connected:
                await self.connect()
            return None
        self._optional_failures.pop(start_addr, None)
        return regs

    def _record_optional_failure(
        self, start_addr: int, label: str, err: Exception, *, definitive: bool
    ) -> None:
        """Count a failed optional read and disable the block when appropriate."""
        failures = self._optional_failures.get(start_addr, 0) + 1
        self._optional_failures[start_addr] = failures
        if definitive or failures >= MODBUS_OPTIONAL_BLOCK_MAX_FAILURES:
            self._unsupported_blocks.add(start_addr)
            _LOGGER.info(
                "Breezart Modbus: %s (INPUT[%d]) unavailable, no longer polling it: %s",
                label,
                start_addr,
                err,
            )
        else:
            _LOGGER.debug(
                "Breezart Modbus: %s (INPUT[%d]) read failed (%d/%d): %s",
                label,
                start_addr,
                failures,
                MODBUS_OPTIONAL_BLOCK_MAX_FAILURES,
                err,
            )

    def _apply_hw_temp_bounds(self, min_task_raw: int, max_task_raw: int) -> None:
        """Decode and apply hardware min/max temperature bounds from INPUT[70..71] if not overridden."""
        if (
            min_task_raw in MODBUS_INVALID_VALUES
            or max_task_raw in MODBUS_INVALID_VALUES
            or min_task_raw == 0
            or max_task_raw == 0
        ):
            return
        min_signed = _to_signed16(min_task_raw)
        max_signed = _to_signed16(max_task_raw)
        if min_signed >= 50 and max_signed >= 100:
            hw_min = int(round(min_signed / TEMP_DIVISOR))
            hw_max = int(round(max_signed / TEMP_DIVISOR))
        else:
            hw_min = int(min_signed)
            hw_max = int(max_signed)
        if 5 <= hw_min < hw_max <= 45:
            if self._user_temp_min is None:
                self.temp_min = hw_min
            if self._user_temp_max is None:
                self.temp_max = hw_max

    async def get_properties(self) -> None:
        """Read JL204c7 hardware/firmware signature and verify Modbus responsiveness."""
        # First verify Holding[0..8] can be read (core control block)
        await self._read_registers(
            MODBUS_FC_READ_HOLDING,
            MODBUS_HR_BLOCK_START,
            MODBUS_HR_BLOCK_COUNT,
        )

        # Read INPUT[50..71] to check if hardware temperature limits (INPUT[70..71]) are available
        try:
            sensors_ir = await self._read_registers(
                MODBUS_FC_READ_INPUT,
                MODBUS_IR_SENSORS_BLOCK_START,
                MODBUS_IR_SENSORS_BLOCK_COUNT,
            )
            if len(sensors_ir) >= 14:
                self._last_temp_supply = _parse_io_data(sensors_ir[0], sensors_ir[1], is_signed=True)
                self._last_temp_outdoor = _parse_io_data(sensors_ir[8], sensors_ir[9], is_signed=True)
                self._last_temp_water = _parse_io_data(sensors_ir[12], sensors_ir[13], is_signed=True)
            if len(sensors_ir) >= 22:
                self._apply_hw_temp_bounds(sensors_ir[20], sensors_ir[21])
        except Exception as err:
            _LOGGER.debug("Optional JL204c7 sensor/limit block (50..71) not read during init: %s", err)

        # Optionally read system signature block INPUT[65000..65014]
        info_regs = await self._read_optional_block(
            MODBUS_IR_INFO_BLOCK_START, MODBUS_IR_INFO_BLOCK_COUNT, "system info block"
        )
        if info_regs is None:
            if not self.firmware_ver:
                self.firmware_ver = "JL204c7"
        else:
            hw_sig = info_regs[0]  # INPUT[65000] Sign_hard_ID
            sw_ver = info_regs[12]  # INPUT[65012] Sign_soft_vers
            proj_ver = info_regs[14]  # INPUT[65014] Sign_proj_vers
            if sw_ver > 0:
                major = (sw_ver >> 8) & 0xFF
                minor = sw_ver & 0xFF
                if major > 0:
                    self.firmware_ver = (
                        f"{major}.{minor}.{proj_ver}" if proj_ver > 0 else f"{major}.{minor}"
                    )
                else:
                    self.firmware_ver = str(sw_ver)
            if hw_sig > 0:
                self.protocol_ver = f"Modbus TCP (JL{hw_sig}, ID={self.slave_id})"

        _LOGGER.info(
            "Breezart Modbus (%s) properties: T=%d..%d°C, Speed=%d..%d, fw=%s, proto=%s",
            self.model,
            self.temp_min,
            self.temp_max,
            self.speed_min,
            self.speed_max,
            self.firmware_ver,
            self.protocol_ver,
        )

    async def get_state(self) -> dict[str, Any]:
        """Read current state from JL204c7 Holding[0..8] and Input[10..23]."""
        hr = await self._read_registers(
            MODBUS_FC_READ_HOLDING,
            MODBUS_HR_BLOCK_START,
            MODBUS_HR_BLOCK_COUNT,
        )
        ir = await self._read_registers(
            MODBUS_FC_READ_INPUT,
            MODBUS_IR_STATUS_BLOCK_START,
            MODBUS_IR_STATUS_BLOCK_COUNT,
        )

        # Parse Holding[0..8] setpoints
        fan_task_raw = hr[MODBUS_HR_FAN_SPEED]  # % * 100 (0..10000)
        temp_target = round(_to_signed16(hr[MODBUS_HR_TEMP_TARGET]) / TEMP_DIVISOR, 1)
        power_reg = hr[MODBUS_HR_POWER_STATE]  # 0=Off, 1=Working, 2=Standby
        mode_hc = hr[MODBUS_HR_MODE_HC]        # 0=Vent, 1=Heat, 2=Cool, 3=Auto

        mode_set = MODBUS_HC_TO_CMD_MODE.get(mode_hc, CMD_MODE_HEAT)
        speed_target = (
            0
            if fan_task_raw == 0
            else max(
                self.speed_min,
                min(
                    self.speed_max,
                    round((fan_task_raw / MODBUS_MAX_PERCENT_RAW) * self.speed_max),
                ),
            )
        )

        # Parse Input[10..23] real-time status & regulation sensors
        # Offset relative to MODBUS_IR_STATUS_BLOCK_START (10):
        # ir[0]=INPUT[10] Cur_mode, ir[1]=INPUT[11] Status_low, ir[2]=INPUT[12] Status_high
        # ir[3..4]=INPUT[13..14] Cur_t, ir[5..6]=INPUT[15..16] Cur_h, ir[7..8]=INPUT[17..18] Cur_f
        # ir[9..10]=INPUT[19..20] Errors, ir[11..12]=INPUT[21..22] Warnings
        cur_mode_reg = ir[0]
        status_low = ir[1]
        cur_t = _parse_io_data(ir[3], ir[4], is_signed=True, divisor=TEMP_DIVISOR)
        cur_h = _parse_io_data(ir[5], ir[6], is_signed=False, divisor=TEMP_DIVISOR)
        cur_f = _parse_io_data(
            ir[7], ir[8], is_signed=False, divisor=MODBUS_PERCENT_MULTIPLIER
        )
        errors_low = ir[9]
        warnings_low = ir[11]

        bit_power = bool(status_low & (1 << MODBUS_STATUS_BIT_POWER))
        bit_trans = bool(status_low & (1 << MODBUS_STATUS_BIT_TRANSITION))
        bit_winter = bool(status_low & (1 << MODBUS_STATUS_BIT_WINTER))
        is_warn_err = bool(status_low & (1 << MODBUS_STATUS_BIT_WARN)) or (warnings_low > 0)
        is_fatal_err = bool(status_low & (1 << MODBUS_STATUS_BIT_FATAL)) or (errors_low > 0)
        bit_heating = bool(status_low & (1 << MODBUS_STATUS_BIT_HEATING))
        bit_cooling = bool(status_low & (1 << MODBUS_STATUS_BIT_COOLING))
        bit_overheat_blow = bool(status_low & (1 << MODBUS_STATUS_BIT_OVERHEAT_BLOW))

        alarm_mask = errors_low | warnings_low
        danger_overheat = bit_overheat_blow or bool(
            alarm_mask & (1 << MODBUS_ALARM_BIT_OVERHEAT)
        )
        hw_freeze_flag = bool(alarm_mask & (1 << MODBUS_ALARM_BIT_FREEZE))
        change_filter = bool(alarm_mask & (1 << MODBUS_ALARM_BIT_FILTER))

        # HOLDING[3] (power_reg) is the authoritative target power switch state (0=Off, 1=Working, 2=Standby).
        # During startup/shutdown transitions (bit_trans=True), cur_mode_reg and bit_power lag while dampers/blowdown run.
        power = bool(power_reg > 0) if power_reg in (0, 1, 2) else bool(cur_mode_reg > 0 or bit_power)
        if bit_trans or (not power and (cur_mode_reg > 0 or bit_power)):
            unit_state = UNIT_STATE_STARTUP if power else UNIT_STATE_SHUTDOWN
            color_ind = COLOR_IND_TRANSITION
        else:
            unit_state = UNIT_STATE_ON if power else UNIT_STATE_OFF
            color_ind = COLOR_IND_ON if power else COLOR_IND_OFF

        if not power and unit_state == UNIT_STATE_OFF:
            mode = MODE_OFF
        elif mode_hc == MODBUS_HC_AUTO:
            mode = MODE_AUTO_COOL if bit_cooling else MODE_AUTO_HEAT
        elif mode_hc == MODBUS_HC_HEAT or bit_heating or bit_winter:
            mode = MODE_HEAT
        elif mode_hc == MODBUS_HC_COOL or bit_cooling:
            mode = MODE_COOL
        else:
            mode = MODE_VENT

        danger_freeze = _detect_freeze_hazard(
            hw_freeze_flag=hw_freeze_flag,
            power=power,
            mode=mode,
            control_temp=cur_t,
            supply_temp=self._last_temp_supply,
            outdoor_temp=self._last_temp_outdoor,
            water_temp=self._last_temp_water,
        )

        if cur_f is not None:
            speed_fact = round(cur_f)
        else:
            speed_fact = round(fan_task_raw / MODBUS_PERCENT_MULTIPLIER) if power else 0

        speed = (
            0
            if not power
            else max(
                self.speed_min,
                min(self.speed_max, round((speed_fact / 100.0) * self.speed_max)),
            )
        )

        if is_fatal_err:
            color_msg = COLOR_MSG_ERROR
            msg = f"Err: 0x{errors_low:04X}"
        elif is_warn_err:
            color_msg = COLOR_MSG_WARNING
            msg = f"Warn: 0x{warnings_low:04X}"
        else:
            color_msg = COLOR_MSG_NORMAL
            msg = "OK"

        return {
            KEY_POWER: power,
            KEY_UNIT_STATE: unit_state,
            KEY_MODE: mode,
            KEY_MODE_SET: mode_set,
            KEY_TEMPERATURE: cur_t,
            KEY_TEMPERATURE_TARGET: temp_target,
            KEY_HUMIDITY: round(cur_h) if cur_h is not None else None,
            KEY_SPEED: speed,
            KEY_SPEED_TARGET: speed_target if speed_target > 0 else self.speed_min,
            KEY_SPEED_FACT: speed_fact,
            KEY_FILTER_DUST: (
                round(self._last_filter1_dust)
                if self._last_filter1_dust is not None
                else None
            ),
            KEY_IS_WARN_ERR: is_warn_err,
            KEY_IS_FATAL_ERR: is_fatal_err,
            KEY_DANGER_OVERHEAT: danger_overheat,
            KEY_DANGER_FREEZE: danger_freeze,
            KEY_CHANGE_FILTER: change_filter,
            KEY_COLOR_MSG: color_msg,
            KEY_COLOR_IND: color_ind,
            KEY_MSG: msg,
        }

    async def get_sensors(self) -> dict[str, Any]:
        """Read JL204c7 physical sensors from Input[50..71], [10001..10004], and [12005]."""
        sensors_ir = await self._read_registers(
            MODBUS_FC_READ_INPUT,
            MODBUS_IR_SENSORS_BLOCK_START,
            MODBUS_IR_SENSORS_BLOCK_COUNT,
        )

        # Offsets relative to MODBUS_IR_SENSORS_BLOCK_START (50):
        # 50..51: Pu_out_air_t, 52..53: Pu_out_air_h, 54..55: Room_air_t, 56..57: Room_air_h
        # 58..59: Ext_air_t, 60..61: Ext_air_h, 62..63: Hot_water_t
        # 70: Min_task, 71: Max_task
        temp_supply = _parse_io_data(sensors_ir[0], sensors_ir[1], is_signed=True)
        humidity_supply = _parse_io_data(sensors_ir[2], sensors_ir[3], is_signed=False)
        temp_room = _parse_io_data(sensors_ir[4], sensors_ir[5], is_signed=True)
        humidity_room = _parse_io_data(sensors_ir[6], sensors_ir[7], is_signed=False)
        temp_outdoor = _parse_io_data(sensors_ir[8], sensors_ir[9], is_signed=True)
        humidity_outdoor = _parse_io_data(sensors_ir[10], sensors_ir[11], is_signed=False)
        temp_water = _parse_io_data(sensors_ir[12], sensors_ir[13], is_signed=True)

        self._last_temp_supply = temp_supply
        self._last_temp_outdoor = temp_outdoor
        self._last_temp_water = temp_water

        # Update dynamic min/max temperature limits from INPUT[70..71] if not overridden by user
        if len(sensors_ir) >= 22:
            self._apply_hw_temp_bounds(sensors_ir[20], sensors_ir[21])

        power_consumption: float | None = None
        fan_ir = await self._read_optional_block(
            MODBUS_IR_FAN_BLOCK_START, MODBUS_IR_FAN_BLOCK_COUNT, "fan power block"
        )
        if fan_ir is not None:
            raw_kw_x100 = fan_ir[3]  # INPUT[10004] Fan0_power (kW x 100)
            if raw_kw_x100 not in MODBUS_INVALID_VALUES:
                power_consumption = round(raw_kw_x100 * MODBUS_KW_TO_W_MULTIPLIER, 1)

        filter1_pollution: float | None = None
        filter2_pollution: float | None = None
        f1_ir = await self._read_optional_block(
            MODBUS_IR_FILTER1_POLLUTION, 1, "filter 1 pollution register"
        )
        if f1_ir is not None and f1_ir[0] not in MODBUS_INVALID_VALUES:
            filter1_pollution = round(f1_ir[0] / MODBUS_PERCENT_MULTIPLIER, 1)
            self._last_filter1_dust = filter1_pollution

        f2_ir = await self._read_optional_block(
            MODBUS_IR_FILTER2_POLLUTION, 1, "filter 2 pollution register"
        )
        if f2_ir is not None and f2_ir[0] not in MODBUS_INVALID_VALUES:
            filter2_pollution = round(f2_ir[0] / MODBUS_PERCENT_MULTIPLIER, 1)

        return {
            KEY_TEMP_SUPPLY: temp_supply,
            KEY_HUMIDITY_SUPPLY: humidity_supply,
            KEY_TEMP_ROOM: temp_room,
            KEY_HUMIDITY_ROOM: humidity_room,
            KEY_TEMP_OUTDOOR: temp_outdoor,
            KEY_HUMIDITY_OUTDOOR: humidity_outdoor,
            KEY_TEMP_WATER: temp_water,
            KEY_POWER_CONSUMPTION: power_consumption,
            KEY_CO2: None,
            KEY_VOC: None,
            KEY_FILTER1_POLLUTION: filter1_pollution,
            KEY_FILTER2_POLLUTION: filter2_pollution,
            KEY_FILTER3_POLLUTION: None,
            KEY_FILTER4_POLLUTION: None,
        }

    async def set_power(self, on: bool) -> None:
        """Turn device on or off via Holding[3] (on_off)."""
        await self._write_register(MODBUS_HR_POWER_STATE, POWER_ON if on else POWER_OFF)

    async def set_temperature(self, temperature: int | float) -> None:
        """Set target temperature via Holding[1] (t_task, °C x 10)."""
        raw_deci = int(round(float(temperature) * TEMP_DIVISOR))
        await self._write_register(MODBUS_HR_TEMP_TARGET, raw_deci)

    async def set_fan_speed(self, speed: int) -> None:
        """Set fan speed step via Holding[0] (fan_task, % x 100)."""
        clamped = max(self.speed_min, min(self.speed_max, int(speed)))
        raw_pct_100 = int(round((clamped / self.speed_max) * MODBUS_MAX_PERCENT_RAW))
        await self._write_register(MODBUS_HR_FAN_SPEED, raw_pct_100)

    async def set_mode(self, mode: int) -> None:
        """Set work mode via Holding[7] (mode_hc: 0=Vent, 1=Heat, 2=Cool, 3=Auto)."""
        modbus_hc = CMD_MODE_TO_MODBUS_HC.get(mode, MODBUS_HC_HEAT)
        await self._write_register(MODBUS_HR_MODE_HC, modbus_hc)


BreezartClientType = BreezartTCPClient | BreezartModbusClient


def create_breezart_client(
    host: str,
    port: int,
    password: int | str = DEFAULT_PASSWORD,
    model: str = DEFAULT_MODEL,
    protocol: str = DEFAULT_PROTOCOL,
    slave_id: int = DEFAULT_SLAVE_ID,
    timeout: int = DEFAULT_TIMEOUT,
    *,
    speed_max: int | None = None,
    temp_min: int | None = None,
    temp_max: int | None = None,
) -> BreezartClientType:
    """Create the appropriate Breezart client (Modbus TCP on 502 or Native TCP on 1560)."""
    if protocol == PROTOCOL_MODBUS_TCP or (
        protocol == PROTOCOL_AUTO and port == DEFAULT_MODBUS_PORT
    ):
        return BreezartModbusClient(
            host=host,
            port=port,
            slave_id=slave_id,
            timeout=timeout,
            model=model,
            speed_max=speed_max,
            temp_min=temp_min,
            temp_max=temp_max,
        )
    return BreezartTCPClient(
        host=host,
        port=port,
        password=password,
        timeout=timeout,
        model=model,
        speed_max=speed_max,
        temp_min=temp_min,
        temp_max=temp_max,
    )


async def async_detect_and_connect_client(
    host: str,
    port: int,
    password: int | str = DEFAULT_PASSWORD,
    model: str = DEFAULT_MODEL,
    protocol: str = DEFAULT_PROTOCOL,
    slave_id: int = DEFAULT_SLAVE_ID,
    timeout: int = DEFAULT_TIMEOUT,
    *,
    speed_max: int | None = None,
    temp_min: int | None = None,
    temp_max: int | None = None,
) -> tuple[BreezartClientType, str, int]:
    """Connect and verify device properties, with automatic fallback between port 502 (Modbus) and 1560 (Native)."""
    if protocol == PROTOCOL_MODBUS_TCP:
        target_port = port if port != DEFAULT_PORT else DEFAULT_MODBUS_PORT
        client = BreezartModbusClient(
            host=host,
            port=target_port,
            slave_id=slave_id,
            timeout=timeout,
            model=model,
            speed_max=speed_max,
            temp_min=temp_min,
            temp_max=temp_max,
        )
        await client.connect()
        await client.get_properties()
        return client, PROTOCOL_MODBUS_TCP, target_port

    if protocol == PROTOCOL_NATIVE_TCP:
        client = BreezartTCPClient(
            host=host,
            port=port,
            password=password,
            timeout=timeout,
            model=model,
            speed_max=speed_max,
            temp_min=temp_min,
            temp_max=temp_max,
        )
        await client.connect()
        await client.get_properties()
        return client, PROTOCOL_NATIVE_TCP, port

    # PROTOCOL_AUTO: Try Modbus TCP first if port == 502, otherwise try requested port then fallback to 502
    if port == DEFAULT_MODBUS_PORT:
        candidates: list[tuple[str, int]] = [
            (PROTOCOL_MODBUS_TCP, DEFAULT_MODBUS_PORT),
            (PROTOCOL_NATIVE_TCP, DEFAULT_PORT),
        ]
    else:
        candidates = [
            (PROTOCOL_NATIVE_TCP, port),
            (PROTOCOL_MODBUS_TCP, DEFAULT_MODBUS_PORT),
        ]
        if port != DEFAULT_PORT:
            candidates.insert(1, (PROTOCOL_MODBUS_TCP, port))

    last_err: Exception | None = None
    for cand_proto, cand_port in candidates:
        cand_client = create_breezart_client(
            host=host,
            port=cand_port,
            password=password,
            model=model,
            protocol=cand_proto,
            slave_id=slave_id,
            timeout=timeout,
            speed_max=speed_max,
            temp_min=temp_min,
            temp_max=temp_max,
        )
        try:
            await cand_client.connect()
            await cand_client.get_properties()
            _LOGGER.info(
                "Auto-detected Breezart protocol '%s' at %s:%d",
                cand_proto,
                host,
                cand_port,
            )
            return cand_client, cand_proto, cand_port
        except PermissionError:
            await cand_client.disconnect()
            raise
        except Exception as err:
            await cand_client.disconnect()
            last_err = err
            _LOGGER.debug(
                "Probe failed for protocol=%s at %s:%d: %s",
                cand_proto,
                host,
                cand_port,
                err,
            )

    if last_err is not None:
        raise last_err
    raise ConnectionError(f"Unable to connect to Breezart at {host}:{port}")


def _resolve_notify_targets(
    notify_service: str,
    available_services: Iterable[str],
) -> list[str]:
    """Resolve deduplicated notify.* service names without calling both notify.notify and mobile_app_*.

    In Home Assistant, `notify.notify` is a broadcast service that already forwards messages
    to all registered `notify.mobile_app_*` phone targets. Calling both `notify.notify` and
    `notify.mobile_app_<phone>` causes two identical push notifications to arrive on the phone.
    """
    available_set = set(available_services)
    mobile_targets = [
        svc for svc in available_services if svc.startswith(MOBILE_APP_SERVICE_PREFIX)
    ]

    raw_items = [
        item.strip()
        for item in (notify_service or "").split(",")
        if item.strip()
    ]

    # Default or empty configuration: prefer direct mobile_app_* targets; fallback to notify.notify only if none exist
    if not raw_items or (
        len(raw_items) == 1 and raw_items[0] in (DEFAULT_NOTIFY_SERVICE, NOTIFY_DOMAIN)
    ):
        if mobile_targets:
            return mobile_targets
        return [NOTIFY_DOMAIN] if NOTIFY_DOMAIN in available_set else []

    targets: list[str] = []
    for raw_target in raw_items:
        svc_name = (
            raw_target.split(".", 1)[1]
            if raw_target.startswith(f"{NOTIFY_DOMAIN}.")
            else raw_target
        )
        if svc_name in available_set and svc_name not in targets:
            targets.append(svc_name)

    # If both broadcast "notify" and specific "mobile_app_*" targets are present, drop "notify" to avoid duplicates
    if NOTIFY_DOMAIN in targets and any(
        t.startswith(MOBILE_APP_SERVICE_PREFIX) for t in targets
    ):
        targets.remove(NOTIFY_DOMAIN)

    return targets


class BreezartDataCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Coordinator that polls Breezart for state and sensor data and dispatches event notifications."""

    def __init__(
        self,
        hass: HomeAssistant,
        client: BreezartClientType,
        model: str = DEFAULT_MODEL,
        *,
        notify_settings: dict[str, bool] | None = None,
        notify_service: str = DEFAULT_NOTIFY_SERVICE,
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
        self.notify_service: str = (notify_service or DEFAULT_NOTIFY_SERVICE).strip()
        self.notify_settings: dict[str, bool] = {
            key: True for key in NOTIFICATION_SETTING_KEYS
        }
        if notify_settings:
            for key in NOTIFICATION_SETTING_KEYS:
                if key in notify_settings:
                    self.notify_settings[key] = bool(notify_settings[key])

        self._update_lock = asyncio.Lock()
        self._properties_loaded = False
        self._cached_sensors: dict[str, Any] = {}
        self._sensors_update_counter = 0

        # Edge-detection, debounce, and per-event cooldown state for notifications
        self._has_initial_snapshot = False
        self._was_online = True
        self._consecutive_failures: int = 0
        self._prev_power: bool | None = None
        self._prev_overheat = False
        self._prev_freeze = False
        self._prev_filter = False
        self._prev_other_err = False
        self._prev_err_msg: str | None = None
        self._last_notification_time: dict[str, float] = {}

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

    def is_notification_enabled(self, key: str) -> bool:
        """Return True if the specified notification toggle is enabled."""
        return bool(self.notify_settings.get(key, True))

    def set_notification_enabled(self, key: str, enabled: bool) -> None:
        """Enable or disable a specific notification event type."""
        if key in NOTIFICATION_SETTING_KEYS:
            self.notify_settings[key] = bool(enabled)

    def _should_send_throttled(self, throttle_key: str, cooldown_seconds: float) -> bool:
        """Return True if throttle_key has not been sent within cooldown_seconds, and record timestamp."""
        now = time.monotonic()
        last_sent = self._last_notification_time.get(throttle_key)
        if last_sent is not None and (now - last_sent) < cooldown_seconds:
            _LOGGER.debug(
                "Suppressing duplicate Breezart notification '%s' (%.1fs < %.1fs cooldown)",
                throttle_key,
                now - last_sent,
                cooldown_seconds,
            )
            return False
        self._last_notification_time[throttle_key] = now
        return True

    async def _async_send_notification(
        self,
        event_key: str,
        *,
        extra_detail: str | None = None,
    ) -> None:
        """Send a localized notification to mobile devices, HA persistent notifications, and the event bus."""
        cooldown = (
            NOTIFY_POWER_COOLDOWN_SECONDS
            if event_key in (NOTIFY_EVENT_POWER_ON, NOTIFY_EVENT_POWER_OFF)
            else NOTIFY_COOLDOWN_SECONDS
        )
        throttle_key = (
            f"{event_key}:{extra_detail}"
            if event_key == NOTIFY_EVENT_OTHER_ERRORS and extra_detail
            else event_key
        )
        if not self._should_send_throttled(throttle_key, cooldown):
            return

        language = getattr(getattr(self.hass, "config", None), "language", "ru")
        title = f"{DEFAULT_NAME} {self.model_name} ({self.client.host})"
        base_msg = translate_value("notifications", event_key, language)
        message = f"{base_msg}: {extra_detail}" if extra_detail else base_msg

        # 1) Fire Home Assistant bus event for custom automations
        try:
            self.hass.bus.async_fire(
                EVENT_BREEZART_NOTIFICATION,
                {
                    "host": self.client.host,
                    "model": self.model,
                    "event": event_key,
                    "title": title,
                    "message": message,
                },
            )
        except Exception as err:
            _LOGGER.debug("Failed to fire %s event: %s", EVENT_BREEZART_NOTIFICATION, err)

        # 2) Create persistent notification in Home Assistant UI
        try:
            if self.hass.services.has_service(PERSISTENT_NOTIFICATION_DOMAIN, SERVICE_CREATE):
                await self.hass.services.async_call(
                    PERSISTENT_NOTIFICATION_DOMAIN,
                    SERVICE_CREATE,
                    {
                        "title": title,
                        "message": message,
                        "notification_id": f"{DOMAIN}_{self.client.host}_{event_key}",
                    },
                    blocking=False,
                )
        except Exception as err:
            _LOGGER.debug("Failed to create persistent notification: %s", err)

        # 3) Send push notification to phone / configured notify.* service(s) without duplicate broadcast
        try:
            all_services = self.hass.services.async_services()
            notify_services = all_services.get(NOTIFY_DOMAIN, {})
            targets = _resolve_notify_targets(self.notify_service, notify_services.keys())

            for svc_name in targets:
                await self.hass.services.async_call(
                    NOTIFY_DOMAIN,
                    svc_name,
                    {"title": title, "message": message},
                    blocking=False,
                )
        except Exception as err:
            _LOGGER.debug("Failed to call notify service for %s: %s", event_key, err)

    async def _async_evaluate_notifications(self, data: dict[str, Any]) -> None:
        """Check for state transitions and dispatch enabled notifications."""
        # 1) Device came back online after a confirmed outage
        if not self._was_online:
            self._was_online = True
            if self.is_notification_enabled(KEY_NOTIFY_ONLINE):
                await self._async_send_notification(NOTIFY_EVENT_ONLINE)

        # 2) Overheat hazard (rising edge)
        cur_overheat = bool(data.get(KEY_DANGER_OVERHEAT, False))
        if cur_overheat and not self._prev_overheat:
            if self.is_notification_enabled(KEY_NOTIFY_OVERHEAT):
                await self._async_send_notification(NOTIFY_EVENT_OVERHEAT)
        self._prev_overheat = cur_overheat

        # 3) Freeze hazard (rising edge)
        cur_freeze = bool(data.get(KEY_DANGER_FREEZE, False))
        if cur_freeze and not self._prev_freeze:
            if self.is_notification_enabled(KEY_NOTIFY_FREEZE):
                await self._async_send_notification(NOTIFY_EVENT_FREEZE)
        self._prev_freeze = cur_freeze

        # 4) Filter replacement warning (rising edge)
        filter_dust = data.get(KEY_FILTER_DUST)
        cur_filter = bool(data.get(KEY_CHANGE_FILTER, False)) or (
            isinstance(filter_dust, (int, float))
            and filter_dust >= FILTER_POLLUTION_REPLACE_MAX
        )
        if cur_filter and not self._prev_filter:
            if self.is_notification_enabled(KEY_NOTIFY_FILTER):
                detail = f"{round(float(filter_dust))}%" if isinstance(filter_dust, (int, float)) else None
                await self._async_send_notification(
                    NOTIFY_EVENT_FILTER, extra_detail=detail
                )
        self._prev_filter = cur_filter

        # 5) Other controller warnings / fatal errors (rising edge or new error code)
        has_err_flag = bool(
            data.get(KEY_IS_WARN_ERR, False) or data.get(KEY_IS_FATAL_ERR, False)
        )
        raw_msg = str(data.get(KEY_MSG) or "").strip()
        cur_other_err = has_err_flag and not (cur_overheat or cur_freeze or cur_filter)
        if cur_other_err:
            if not self._prev_other_err or (raw_msg and raw_msg != self._prev_err_msg):
                if self.is_notification_enabled(KEY_NOTIFY_OTHER_ERRORS):
                    detail = raw_msg if raw_msg and raw_msg.upper() != "OK" else None
                    await self._async_send_notification(
                        NOTIFY_EVENT_OTHER_ERRORS, extra_detail=detail
                    )
            self._prev_other_err = True
            self._prev_err_msg = raw_msg
        else:
            self._prev_other_err = False
            self._prev_err_msg = None

        # 6) Unit power on / off transitions (after initial snapshot is established)
        cur_power = bool(data.get(KEY_POWER, False))
        if self._has_initial_snapshot and self._prev_power is not None and cur_power != self._prev_power:
            if self.is_notification_enabled(KEY_NOTIFY_POWER):
                await self._async_send_notification(
                    NOTIFY_EVENT_POWER_ON if cur_power else NOTIFY_EVENT_POWER_OFF
                )
        self._prev_power = cur_power
        self._has_initial_snapshot = True

    async def _async_update_data(self) -> dict[str, Any]:
        """Fetch latest data from Breezart with serialized polling and offline debounce."""
        async with self._update_lock:
            try:
                if not self.client.is_connected:
                    await self.client.connect()

                if not self._properties_loaded:
                    await self.client.get_properties()
                    self._properties_loaded = True

                # Refresh physical sensors BEFORE get_state() when due (including initial/reconnect poll)
                # so get_state() has up-to-date supply/outdoor/water temperatures and filter pollution.
                self._sensors_update_counter += 1
                cycles_per_sensor_update = max(1, SENSORS_UPDATE_INTERVAL // STATE_UPDATE_INTERVAL)
                if (
                    self._sensors_update_counter >= cycles_per_sensor_update
                    or not self._cached_sensors
                ):
                    self._cached_sensors = await self.client.get_sensors()
                    self._sensors_update_counter = 0
                    _LOGGER.debug("Breezart sensors refreshed")

                state = await self.client.get_state()

                data = {**state, **self._cached_sensors}
                if data.get(KEY_FILTER_DUST) is None and data.get(KEY_FILTER1_POLLUTION) is not None:
                    data[KEY_FILTER_DUST] = round(float(data[KEY_FILTER1_POLLUTION]))

                data[KEY_TEMP_MIN] = self.client.temp_min
                data[KEY_TEMP_MAX] = self.client.temp_max
                data[KEY_SPEED_MIN] = self.client.speed_min
                data[KEY_SPEED_MAX] = self.client.speed_max
                data[KEY_HAS_COOLER] = self.client.has_cooler
                data[KEY_HAS_HUMIDIFIER] = self.client.has_humidifier
                data[KEY_FIRMWARE_VER] = self.client.firmware_ver
                data[KEY_PROTOCOL_VER] = self.client.protocol_ver

                self._consecutive_failures = 0
                await self._async_evaluate_notifications(data)

                _LOGGER.debug(
                    "Breezart state update (%s): power=%s temp=%s speed=%s",
                    self.client.protocol_type,
                    data.get(KEY_POWER),
                    data.get(KEY_TEMPERATURE_TARGET),
                    data.get(KEY_SPEED_TARGET),
                )
                return data

            except (ConnectionError, OSError, TimeoutError, asyncio.IncompleteReadError) as err:
                self._properties_loaded = False
                self._cached_sensors = {}
                await self.client.disconnect()
                self._consecutive_failures += 1
                if (
                    self._was_online
                    and self._consecutive_failures >= NOTIFY_OFFLINE_FAILURE_THRESHOLD
                ):
                    self._was_online = False
                    if self.is_notification_enabled(KEY_NOTIFY_OFFLINE):
                        await self._async_send_notification(NOTIFY_EVENT_OFFLINE)
                raise UpdateFailed(f"Connection error: {err}") from err
            except Exception as err:
                # Unparseable/short replies mean the stream can't be trusted: reconnect next poll.
                self._properties_loaded = False
                self._cached_sensors = {}
                await self.client.disconnect()
                raise UpdateFailed(f"Error communicating with Breezart: {err}") from err

