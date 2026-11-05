"""Constants, model presets, and i18n dictionaries for Breezart integration."""
from __future__ import annotations

from typing import Any, Final

# Integration metadata
DOMAIN: Final[str] = "breezart"
DEFAULT_NAME: Final[str] = "Breezart"
MANUFACTURER: Final[str] = "Breezart"
CONFIG_FLOW_VERSION: Final[int] = 1

# Configuration & hass.data keys
CONF_MODEL: Final[str] = "model"
CONF_PROTOCOL: Final[str] = "protocol"
CONF_SLAVE_ID: Final[str] = "slave_id"
CONF_SPEED_MAX: Final[str] = "speed_max"
CONF_TEMP_MIN: Final[str] = "temp_min"
CONF_TEMP_MAX: Final[str] = "temp_max"
CONF_NOTIFY_SERVICE: Final[str] = "notify_service"
DATA_CLIENT: Final[str] = "client"
DATA_COORDINATOR: Final[str] = "coordinator"
DATA_MODEL: Final[str] = "model"
DATA_PROTOCOL: Final[str] = "protocol"
DATA_RELOAD_SNAPSHOT: Final[str] = "reload_snapshot"

# Supported transport protocols
PROTOCOL_AUTO: Final[str] = "auto"
PROTOCOL_MODBUS_TCP: Final[str] = "modbus_tcp"
PROTOCOL_NATIVE_TCP: Final[str] = "native_tcp"
DEFAULT_PROTOCOL: Final[str] = PROTOCOL_AUTO
PROTOCOL_OPTIONS: Final[list[str]] = [
    PROTOCOL_AUTO,
    PROTOCOL_MODBUS_TCP,
    PROTOCOL_NATIVE_TCP,
]

# Breezart TCP & Modbus TCP connection defaults
DEFAULT_HOST: Final[str] = "192.168.1.121"
DEFAULT_PORT: Final[int] = 1560
DEFAULT_MODBUS_PORT: Final[int] = 502
DEFAULT_SLAVE_ID: Final[int] = 1
DEFAULT_PASSWORD: Final[str] = "21579"
DEFAULT_TIMEOUT: Final[int] = 5
DEFAULT_SCAN_INTERVAL: Final[int] = 30
STATE_UPDATE_INTERVAL: Final[int] = 3
SENSORS_UPDATE_INTERVAL: Final[int] = 30
OPTIMISTIC_HOLD_SECONDS: Final[int] = 6
READ_DELAY_SECONDS: Final[float] = 0.03
MODBUS_READ_DELAY_SECONDS: Final[float] = 0.06
READ_BUFFER_SIZE: Final[int] = 4096

# Config flow error, discovery & abort keys
CONF_DISCOVERED_DEVICE: Final[str] = "discovered_device"
DISCOVERY_MANUAL: Final[str] = "manual"
DISCOVERY_CONNECT_TIMEOUT: Final[float] = 0.35
DISCOVERY_PROBE_TIMEOUT: Final[float] = 1.0
DISCOVERY_CONCURRENCY: Final[int] = 128
ERR_CANNOT_CONNECT: Final[str] = "cannot_connect"
ERR_INVALID_AUTH: Final[str] = "invalid_auth"
ERR_UNKNOWN: Final[str] = "unknown"
ABORT_ALREADY_CONFIGURED: Final[str] = "already_configured"
STEP_USER: Final[str] = "user"
STEP_INIT: Final[str] = "init"

# Protocol delimiter & formatting
DELIMITER: Final[str] = "_"
HEX_ZERO: Final[str] = "0"
HEX_FORMAT_LOWER: Final[str] = "x"
HEX_FORMAT_4DIGIT: Final[str] = "04x"
BIT_FORMAT_16: Final[str] = "016b"
MAX_UINT16: Final[int] = 0xFFFF
SIGN_BIT_MASK: Final[int] = 0x8000
SIGN_BIT_OFFSET: Final[int] = 0x10000
SIGNED_BYTE_THRESHOLD: Final[int] = 128
SIGNED_BYTE_OFFSET: Final[int] = 256
TEMP_DIVISOR: Final[float] = 10.0

# Request types (native Breezart TCP protocol)
REQ_GET_PROPERTIES: Final[str] = "VPr07"
REQ_GET_STATE: Final[str] = "VSt07"
REQ_GET_SENSORS: Final[str] = "VSens"
REQ_SET_POWER: Final[str] = "VWPwr"
REQ_SET_TEMP: Final[str] = "VWTmp"
REQ_SET_FAN_SPEED: Final[str] = "VWSpd"
REQ_SET_MODE: Final[str] = "VWFtr"

# Response types
RESP_STATE: Final[str] = "VSt07"
RESP_SENSORS: Final[str] = "VSens"
RESP_PROPERTIES: Final[str] = "VPr07"
RESP_OK: Final[str] = "OK"

# Error prefixes from Breezart device
ERR_PREFIX_WRONG_PASS: Final[str] = "VEPas"
ERR_PREFIX_WRONG_FMT: Final[str] = "VEFrm"
ERR_PREFIX_CMD1_NOT_FOUND: Final[str] = "VECd1"
ERR_PREFIX_CMD2_NOT_FOUND: Final[str] = "VECd2"
ERR_PREFIX_DATA_ERROR: Final[str] = "VEDat"

ERROR_PREFIX: Final[dict[str, str]] = {
    ERR_PREFIX_WRONG_PASS: "Wrong password",
    ERR_PREFIX_WRONG_FMT: "Wrong format of request",
    ERR_PREFIX_CMD1_NOT_FOUND: "Request of type 1 not found",
    ERR_PREFIX_CMD2_NOT_FOUND: "Request of type 2 not found",
    ERR_PREFIX_DATA_ERROR: "Error in request data",
}

# Power states
POWER_ON: Final[int] = 1
POWER_OFF: Final[int] = 0

# Sensor sentinel values indicating "no data"
NO_DATA_VALUE: Final[int] = 0xFB07
NO_DATA_HEX: Final[str] = "fb07"
NO_DATA_BYTE: Final[int] = 255

# Packet field indices and bit positions for VPr07 (Device Properties)
VPR07_IDX_TEMPR: Final[int] = 1
VPR07_IDX_SPEED: Final[int] = 2
VPR07_IDX_MISC: Final[int] = 4
VPR07_IDX_PROT: Final[int] = 5
VPR07_IDX_FW: Final[int] = 7
BIT_LOW_BYTE_START: Final[int] = 0
BIT_LOW_BYTE_END: Final[int] = 7
BIT_HIGH_BYTE_START: Final[int] = 8
BIT_HIGH_BYTE_END: Final[int] = 15
BIT_IS_HUMIDIFIER: Final[int] = 13
BIT_IS_COOLER: Final[int] = 14

# Packet field indices and bit positions for VSt07 (Current State)
VST07_IDX_STATE: Final[int] = 1
VST07_IDX_MODE: Final[int] = 2
VST07_IDX_TEMPR: Final[int] = 3
VST07_IDX_HUMID: Final[int] = 4
VST07_IDX_SPEED: Final[int] = 5
VST07_IDX_MISC: Final[int] = 6
VST07_IDX_MSG: Final[int] = 10

BIT_PWR_BTN: Final[int] = 0
BIT_WARN_ERR: Final[int] = 1
BIT_FATAL_ERR: Final[int] = 2
BIT_DANGER_OVERHEAT: Final[int] = 3
BIT_DANGER_FREEZE: Final[int] = 4
BIT_CHANGE_FILTER: Final[int] = 5
BIT_MODE_SET_START: Final[int] = 6
BIT_MODE_SET_END: Final[int] = 8

BIT_UNIT_STATE_START: Final[int] = 0
BIT_UNIT_STATE_END: Final[int] = 1
BIT_MODE_START: Final[int] = 3
BIT_MODE_END: Final[int] = 5

BIT_SPEED_CUR_START: Final[int] = 0
BIT_SPEED_CUR_END: Final[int] = 3
BIT_SPEED_TGT_START: Final[int] = 4
BIT_SPEED_TGT_END: Final[int] = 7

BIT_COLOR_MSG_START: Final[int] = 4
BIT_COLOR_MSG_END: Final[int] = 5
BIT_COLOR_IND_START: Final[int] = 6
BIT_COLOR_IND_END: Final[int] = 7

# Packet field indices for VSens (Sensors)
VSENS_IDX_TEMP_SUPPLY: Final[int] = 1
VSENS_IDX_HUMID_SUPPLY: Final[int] = 2
VSENS_IDX_TEMP_ROOM: Final[int] = 3
VSENS_IDX_HUMID_ROOM: Final[int] = 4
VSENS_IDX_TEMP_OUTDOOR: Final[int] = 5
VSENS_IDX_HUMID_OUTDOOR: Final[int] = 6
VSENS_IDX_TEMP_WATER: Final[int] = 7
VSENS_IDX_POWER_CONSUMPTION: Final[int] = 8
VSENS_IDX_CO2: Final[int] = 9
VSENS_IDX_VOC: Final[int] = 10
VSENS_IDX_FILTER1: Final[int] = 11
VSENS_IDX_FILTER2: Final[int] = 12
VSENS_IDX_FILTER3: Final[int] = 13
VSENS_IDX_FILTER4: Final[int] = 14

# Coordinator state & sensor dictionary keys
KEY_POWER: Final[str] = "power"
KEY_UNIT_STATE: Final[str] = "unit_state"
KEY_MODE: Final[str] = "mode"
KEY_MODE_SET: Final[str] = "mode_set"
KEY_TEMPERATURE: Final[str] = "temperature"
KEY_TEMPERATURE_TARGET: Final[str] = "temperature_target"
KEY_HUMIDITY: Final[str] = "humidity"
KEY_SPEED: Final[str] = "speed"
KEY_SPEED_TARGET: Final[str] = "speed_target"
KEY_SPEED_FACT: Final[str] = "speed_fact"
KEY_FILTER_DUST: Final[str] = "filter_dust"
KEY_IS_WARN_ERR: Final[str] = "is_warn_err"
KEY_IS_FATAL_ERR: Final[str] = "is_fatal_err"
KEY_DANGER_OVERHEAT: Final[str] = "danger_overheat"
KEY_DANGER_FREEZE: Final[str] = "danger_freeze"
KEY_CHANGE_FILTER: Final[str] = "change_filter"
KEY_COLOR_MSG: Final[str] = "color_msg"
KEY_COLOR_IND: Final[str] = "color_ind"
KEY_MSG: Final[str] = "msg"

KEY_TEMP_SUPPLY: Final[str] = "temp_supply"
KEY_HUMIDITY_SUPPLY: Final[str] = "humidity_supply"
KEY_TEMP_ROOM: Final[str] = "temp_room"
KEY_HUMIDITY_ROOM: Final[str] = "humidity_room"
KEY_TEMP_OUTDOOR: Final[str] = "temp_outdoor"
KEY_HUMIDITY_OUTDOOR: Final[str] = "humidity_outdoor"
KEY_TEMP_WATER: Final[str] = "temp_water"
KEY_POWER_CONSUMPTION: Final[str] = "power_consumption"
KEY_CO2: Final[str] = "co2"
KEY_VOC: Final[str] = "voc"
KEY_FILTER1_POLLUTION: Final[str] = "filter1_pollution"
KEY_FILTER2_POLLUTION: Final[str] = "filter2_pollution"
KEY_FILTER3_POLLUTION: Final[str] = "filter3_pollution"
KEY_FILTER4_POLLUTION: Final[str] = "filter4_pollution"

KEY_TEMP_MIN: Final[str] = "temp_min"
KEY_TEMP_MAX: Final[str] = "temp_max"
KEY_SPEED_MIN: Final[str] = "speed_min"
KEY_SPEED_MAX: Final[str] = "speed_max"
KEY_HAS_COOLER: Final[str] = "has_cooler"
KEY_HAS_HUMIDIFIER: Final[str] = "has_humidifier"
KEY_FIRMWARE_VER: Final[str] = "firmware_ver"
KEY_PROTOCOL_VER: Final[str] = "protocol_ver"

# Entity unique_id & translation keys
TRANSLATION_KEY_CLIMATE: Final[str] = "climate"
TRANSLATION_KEY_POWER_SWITCH: Final[str] = "power"
TRANSLATION_KEY_TARGET_TEMP: Final[str] = "target_temperature"
TRANSLATION_KEY_FAN_SPEED: Final[str] = "fan_speed"

# Notification settings & event keys (v1.2.0 / v1.2.1)
DEFAULT_NOTIFY_SERVICE: Final[str] = "notify.notify"
NOTIFY_DOMAIN: Final[str] = "notify"
PERSISTENT_NOTIFICATION_DOMAIN: Final[str] = "persistent_notification"
SERVICE_CREATE: Final[str] = "create"
MOBILE_APP_SERVICE_PREFIX: Final[str] = "mobile_app_"
EVENT_BREEZART_NOTIFICATION: Final[str] = "breezart_notification"
NOTIFY_COOLDOWN_SECONDS: Final[float] = 30.0
NOTIFY_POWER_COOLDOWN_SECONDS: Final[float] = 10.0
NOTIFY_OFFLINE_FAILURE_THRESHOLD: Final[int] = 2

KEY_NOTIFY_OVERHEAT: Final[str] = "notify_overheat"
KEY_NOTIFY_FREEZE: Final[str] = "notify_freeze"
KEY_NOTIFY_FILTER: Final[str] = "notify_filter"
KEY_NOTIFY_OFFLINE: Final[str] = "notify_offline"
KEY_NOTIFY_ONLINE: Final[str] = "notify_online"
KEY_NOTIFY_POWER: Final[str] = "notify_power"
KEY_NOTIFY_OTHER_ERRORS: Final[str] = "notify_other_errors"

NOTIFICATION_SETTING_KEYS: Final[tuple[str, ...]] = (
    KEY_NOTIFY_OVERHEAT,
    KEY_NOTIFY_FREEZE,
    KEY_NOTIFY_FILTER,
    KEY_NOTIFY_OFFLINE,
    KEY_NOTIFY_ONLINE,
    KEY_NOTIFY_POWER,
    KEY_NOTIFY_OTHER_ERRORS,
)

NOTIFY_EVENT_OVERHEAT: Final[str] = "overheat"
NOTIFY_EVENT_FREEZE: Final[str] = "freeze"
NOTIFY_EVENT_FILTER: Final[str] = "filter"
NOTIFY_EVENT_OFFLINE: Final[str] = "offline"
NOTIFY_EVENT_ONLINE: Final[str] = "online"
NOTIFY_EVENT_POWER_ON: Final[str] = "power_on"
NOTIFY_EVENT_POWER_OFF: Final[str] = "power_off"
NOTIFY_EVENT_OTHER_ERRORS: Final[str] = "other_errors"

# Measurement units & steps
UNIT_PPM: Final[str] = "ppm"
UNIT_PPB: Final[str] = "ppb"
DEFAULT_TEMP_STEP: Final[float] = 1.0
DEFAULT_SPEED_STEP: Final[float] = 1.0
DEFAULT_TEMP_MIN: Final[int] = 5
DEFAULT_TEMP_MAX: Final[int] = 35
DEFAULT_SPEED_MIN: Final[int] = 1
DEFAULT_SPEED_MAX: Final[int] = 10
MIN_ALLOWED_TEMP_BOUND: Final[int] = 5
MAX_ALLOWED_TEMP_BOUND: Final[int] = 45
MIN_ALLOWED_SPEED_MAX: Final[int] = 1
MAX_ALLOWED_SPEED_MAX: Final[int] = 10
FREEZE_SUPPLY_TEMP_THRESHOLD: Final[float] = 5.0
FREEZE_OUTDOOR_TEMP_THRESHOLD: Final[float] = 0.0

# UnitState protocol codes & canonical state keys
UNIT_STATE_OFF: Final[int] = 0
UNIT_STATE_ON: Final[int] = 1
UNIT_STATE_SHUTDOWN: Final[int] = 2
UNIT_STATE_STARTUP: Final[int] = 3

STATE_KEY_OFF: Final[str] = "off"
STATE_KEY_ON: Final[str] = "on"
STATE_KEY_SHUTDOWN: Final[str] = "turning_off"
STATE_KEY_STARTUP: Final[str] = "turning_on"
STATE_KEY_UNKNOWN: Final[str] = "unknown"

UNIT_STATE_MAP: Final[dict[int, str]] = {
    UNIT_STATE_OFF: STATE_KEY_OFF,
    UNIT_STATE_ON: STATE_KEY_ON,
    UNIT_STATE_SHUTDOWN: STATE_KEY_SHUTDOWN,
    UNIT_STATE_STARTUP: STATE_KEY_STARTUP,
}

# Active Mode protocol codes (from VSt07) & canonical state keys
MODE_HEAT: Final[int] = 0
MODE_COOL: Final[int] = 1
MODE_AUTO_HEAT: Final[int] = 2
MODE_AUTO_COOL: Final[int] = 3
MODE_VENT: Final[int] = 4
MODE_OFF: Final[int] = 5

MODE_KEY_HEAT: Final[str] = "heat"
MODE_KEY_COOL: Final[str] = "cool"
MODE_KEY_AUTO_HEAT: Final[str] = "auto_heat"
MODE_KEY_AUTO_COOL: Final[str] = "auto_cool"
MODE_KEY_VENT: Final[str] = "fan_only"
MODE_KEY_AUTO: Final[str] = "auto"

MODE_MAP: Final[dict[int, str]] = {
    MODE_HEAT: MODE_KEY_HEAT,
    MODE_COOL: MODE_KEY_COOL,
    MODE_AUTO_HEAT: MODE_KEY_AUTO_HEAT,
    MODE_AUTO_COOL: MODE_KEY_AUTO_COOL,
    MODE_VENT: MODE_KEY_VENT,
    MODE_OFF: STATE_KEY_OFF,
}

# ModeSet protocol codes (requested mode in VSt07 & VWFtr command)
CMD_MODE_HEAT: Final[int] = 1
CMD_MODE_COOL: Final[int] = 2
CMD_MODE_AUTO: Final[int] = 3
CMD_MODE_VENT: Final[int] = 4

MODE_SET_MAP: Final[dict[int, str]] = {
    CMD_MODE_HEAT: MODE_KEY_HEAT,
    CMD_MODE_COOL: MODE_KEY_COOL,
    CMD_MODE_AUTO: MODE_KEY_AUTO,
    CMD_MODE_VENT: MODE_KEY_VENT,
}

# ColorMsg / ColorInd protocol codes & canonical state keys
COLOR_MSG_NORMAL: Final[int] = 0
COLOR_MSG_WARNING: Final[int] = 1
COLOR_MSG_ERROR: Final[int] = 2

STATE_KEY_NORMAL: Final[str] = "normal"
STATE_KEY_WARNING: Final[str] = "warning"
STATE_KEY_ERROR: Final[str] = "error"

COLOR_MSG_MAP: Final[dict[int, str]] = {
    COLOR_MSG_NORMAL: STATE_KEY_NORMAL,
    COLOR_MSG_WARNING: STATE_KEY_WARNING,
    COLOR_MSG_ERROR: STATE_KEY_ERROR,
}

COLOR_IND_OFF: Final[int] = 0
COLOR_IND_TRANSITION: Final[int] = 1
COLOR_IND_ON: Final[int] = 2

STATE_KEY_TRANSITION: Final[str] = "transition"

COLOR_IND_MAP: Final[dict[int, str]] = {
    COLOR_IND_OFF: STATE_KEY_OFF,
    COLOR_IND_TRANSITION: STATE_KEY_TRANSITION,
    COLOR_IND_ON: STATE_KEY_ON,
}

# Filter pollution thresholds & canonical status keys
FILTER_POLLUTION_EXCELLENT_MAX: Final[int] = 30
FILTER_POLLUTION_GOOD_MAX: Final[int] = 60
FILTER_POLLUTION_REPLACE_MAX: Final[int] = 85

ATTR_FILTER_STATUS: Final[str] = "status"
ATTR_FILTER_STATUS_KEY: Final[str] = "status_key"
FILTER_STATUS_NO_DATA: Final[str] = "no_data"
FILTER_STATUS_EXCELLENT: Final[str] = "excellent"
FILTER_STATUS_GOOD: Final[str] = "good"
FILTER_STATUS_REPLACE_SOON: Final[str] = "replace_soon"
FILTER_STATUS_CLOGGED: Final[str] = "clogged"

# Modbus TCP (MBAP + PDU) constants for JLV135 / JL204c7 (v1.7.x)
MODBUS_PROTOCOL_ID: Final[int] = 0
MODBUS_MBAP_HEADER_LEN: Final[int] = 7
MODBUS_READ_PDU_LEN: Final[int] = 6
MODBUS_WRITE_SINGLE_PDU_LEN: Final[int] = 6
MODBUS_FC_READ_HOLDING: Final[int] = 0x03
MODBUS_FC_READ_INPUT: Final[int] = 0x04
MODBUS_FC_WRITE_SINGLE: Final[int] = 0x06
MODBUS_FC_WRITE_MULTIPLE: Final[int] = 0x10
MODBUS_EXCEPTION_MASK: Final[int] = 0x80
# Modbus exception codes meaning "this register/function does not exist on the device"
MODBUS_EXC_ILLEGAL_FUNCTION: Final[int] = 0x01
MODBUS_EXC_ILLEGAL_DATA_ADDRESS: Final[int] = 0x02
# Consecutive failures before an optional register block stops being polled
MODBUS_OPTIONAL_BLOCK_MAX_FAILURES: Final[int] = 3

MODBUS_PERCENT_MULTIPLIER: Final[float] = 100.0
MODBUS_MAX_PERCENT_RAW: Final[int] = 10000
MODBUS_KW_TO_W_MULTIPLIER: Final[float] = 10.0
MODBUS_INVALID_VALUES: Final[frozenset[int]] = frozenset({0x7FFF, 0x8000, 0xFB07, 0xFFFF})

# JL204c7 Holding Registers (FC 0x03 / 0x06)
MODBUS_HR_FAN_SPEED: Final[int] = 0        # fan_task (% x 100, UINT16)
MODBUS_HR_TEMP_TARGET: Final[int] = 1      # t_task (°C x 10, SINT16)
MODBUS_HR_HUMID_TARGET: Final[int] = 2     # h_task (% x 10, SINT16)
MODBUS_HR_POWER_STATE: Final[int] = 3      # on_off (0=Off, 1=Working, 2=Standby)
MODBUS_HR_MODE_HC: Final[int] = 7          # mode_hc (0=Vent/Summer, 1=Heat/Winter, 2=Cool/Summer, 3=Auto)
MODBUS_HR_BLOCK_START: Final[int] = 0
MODBUS_HR_BLOCK_COUNT: Final[int] = 9      # Reads HOLDING[0..8] in one request

# JL204c7 Input Registers (FC 0x04)
MODBUS_IR_STATUS_BLOCK_START: Final[int] = 10
MODBUS_IR_STATUS_BLOCK_COUNT: Final[int] = 14  # Reads INPUT[10..23]
MODBUS_IR_CUR_MODE: Final[int] = 10            # Cur_mode (0=Off, 1=Working, 2=Standby)
MODBUS_IR_STATUS_LOW: Final[int] = 11          # Status low 16 bits
MODBUS_IR_STATUS_HIGH: Final[int] = 12         # Status high 16 bits
MODBUS_IR_CUR_TEMP: Final[int] = 13            # Cur_t (°C x 10, IO_DATA: 13=val, 14=status)
MODBUS_IR_CUR_HUMID: Final[int] = 15           # Cur_h (% x 10, IO_DATA: 15=val, 16=status)
MODBUS_IR_CUR_FAN: Final[int] = 17             # Cur_f (% x 100, IO_DATA: 17=val, 18=status)
MODBUS_IR_ERRORS_LOW: Final[int] = 19          # Errors low 16 bits (Alarms bitmap)
MODBUS_IR_ERRORS_HIGH: Final[int] = 20
MODBUS_IR_WARNINGS_LOW: Final[int] = 21        # Warnings low 16 bits (Alarms bitmap)
MODBUS_IR_WARNINGS_HIGH: Final[int] = 22

MODBUS_IR_SENSORS_BLOCK_START: Final[int] = 50
MODBUS_IR_SENSORS_BLOCK_COUNT: Final[int] = 22  # Reads INPUT[50..71]
MODBUS_IR_TEMP_SUPPLY: Final[int] = 50          # Pu_out_air_t (°C x 10, IO_DATA: 50..51)
MODBUS_IR_HUMID_SUPPLY: Final[int] = 52         # Pu_out_air_h (% x 10, IO_DATA: 52..53)
MODBUS_IR_TEMP_ROOM: Final[int] = 54            # Room_air_t (°C x 10, IO_DATA: 54..55)
MODBUS_IR_HUMID_ROOM: Final[int] = 56           # Room_air_h (% x 10, IO_DATA: 56..57)
MODBUS_IR_TEMP_OUTDOOR: Final[int] = 58         # Ext_air_t (°C x 10, IO_DATA: 58..59)
MODBUS_IR_HUMID_OUTDOOR: Final[int] = 60        # Ext_air_h (% x 10, IO_DATA: 60..61)
MODBUS_IR_TEMP_WATER: Final[int] = 62           # Hot_water_t (°C x 10, IO_DATA: 62..63)
MODBUS_IR_MIN_TEMP_TASK: Final[int] = 70        # Min_task (°C x 10, UINT16)
MODBUS_IR_MAX_TEMP_TASK: Final[int] = 71        # Max_task (°C x 10, UINT16)

MODBUS_IR_FAN_BLOCK_START: Final[int] = 10001
MODBUS_IR_FAN_BLOCK_COUNT: Final[int] = 4       # Reads INPUT[10001..10004]
MODBUS_IR_FAN_WORK: Final[int] = 10001          # Fan0_cur_work (% x 100)
MODBUS_IR_FAN_POWER: Final[int] = 10004         # Fan0_power (kW x 100 -> * 10 = W)

MODBUS_IR_FILTER1_POLLUTION: Final[int] = 12005  # Filter0_cur_zagryaz (% x 100)
MODBUS_IR_FILTER2_POLLUTION: Final[int] = 12205  # Filter1_cur_zagryaz (% x 100)

MODBUS_IR_FAST_BLOCK_START: Final[int] = 64000
MODBUS_IR_FAST_BLOCK_COUNT: Final[int] = 8      # Reads INPUT[64000..64007]

MODBUS_IR_INFO_BLOCK_START: Final[int] = 65000
MODBUS_IR_INFO_BLOCK_COUNT: Final[int] = 15     # Reads INPUT[65000..65014]
MODBUS_IR_HW_SIGNATURE: Final[int] = 65000      # Sign_hard_ID (e.g. 204 for JL204)
MODBUS_IR_SW_ID: Final[int] = 65011             # Sign_soft_id
MODBUS_IR_SW_VERSION: Final[int] = 65012        # Sign_soft_vers
MODBUS_IR_PROJ_VERSION: Final[int] = 65014      # Sign_proj_vers

# JL204c7 Status bit positions (INPUT[11])
MODBUS_STATUS_BIT_POWER: Final[int] = 0
MODBUS_STATUS_BIT_TRANSITION: Final[int] = 1
MODBUS_STATUS_BIT_WINTER: Final[int] = 2
MODBUS_STATUS_BIT_WARN: Final[int] = 3
MODBUS_STATUS_BIT_FATAL: Final[int] = 4
MODBUS_STATUS_BIT_VENT: Final[int] = 5
MODBUS_STATUS_BIT_HEATING: Final[int] = 7
MODBUS_STATUS_BIT_COOLING: Final[int] = 8
MODBUS_STATUS_BIT_OVERHEAT_BLOW: Final[int] = 15

# JL204c7 Alarms bit positions (INPUT[19] Errors & INPUT[21] Warnings)
MODBUS_ALARM_BIT_FREEZE: Final[int] = 4
MODBUS_ALARM_BIT_OVERHEAT: Final[int] = 5
MODBUS_ALARM_BIT_FILTER: Final[int] = 9

# JL204c7 HOLDING[7] (mode_hc) values & mapping to/from internal CMD_MODE_*
MODBUS_HC_VENT: Final[int] = 0
MODBUS_HC_HEAT: Final[int] = 1
MODBUS_HC_COOL: Final[int] = 2
MODBUS_HC_AUTO: Final[int] = 3

MODBUS_HC_TO_CMD_MODE: Final[dict[int, int]] = {
    MODBUS_HC_VENT: CMD_MODE_VENT,
    MODBUS_HC_HEAT: CMD_MODE_HEAT,
    MODBUS_HC_COOL: CMD_MODE_COOL,
    MODBUS_HC_AUTO: CMD_MODE_AUTO,
}

CMD_MODE_TO_MODBUS_HC: Final[dict[int, int]] = {
    CMD_MODE_VENT: MODBUS_HC_VENT,
    CMD_MODE_HEAT: MODBUS_HC_HEAT,
    CMD_MODE_COOL: MODBUS_HC_COOL,
    CMD_MODE_AUTO: MODBUS_HC_AUTO,
}

# Model preset identifiers
MODEL_400_LUX: Final[str] = "400_lux"
MODEL_550_LUX: Final[str] = "550_lux"
MODEL_550_AQUA: Final[str] = "550_aqua"
MODEL_700_LUX: Final[str] = "700_lux"
MODEL_1000_LUX: Final[str] = "1000_lux"
MODEL_1000_AQUA: Final[str] = "1000_aqua"
MODEL_2000_LUX: Final[str] = "2000_lux"
MODEL_CUSTOM: Final[str] = "custom"

DEFAULT_MODEL: Final[str] = MODEL_550_LUX

BASE_ENABLED_SENSORS: Final[tuple[str, ...]] = (
    KEY_TEMPERATURE,
    KEY_TEMP_SUPPLY,
    KEY_TEMPERATURE_TARGET,
    KEY_SPEED,
    KEY_SPEED_TARGET,
    KEY_FILTER_DUST,
    KEY_UNIT_STATE,
    KEY_MODE,
    KEY_MODE_SET,
    KEY_COLOR_IND,
    KEY_COLOR_MSG,
    KEY_MSG,
    KEY_FIRMWARE_VER,
    KEY_PROTOCOL_VER,
)

# Model configuration presets for Breezart lineup
MODEL_PRESETS: Final[dict[str, dict[str, Any]]] = {
    MODEL_400_LUX: {
        "id": MODEL_400_LUX,
        "name": "400 Lux",
        "airflow_m3h": 400,
        "heater_type": "electric",
        "temp_min": DEFAULT_TEMP_MIN,
        "temp_max": DEFAULT_TEMP_MAX,
        "speed_min": DEFAULT_SPEED_MIN,
        "speed_max": DEFAULT_SPEED_MAX,
        "has_cooler": False,
        "has_humidifier": False,
        "has_water_heater": False,
        "enabled_sensors": (
            *BASE_ENABLED_SENSORS,
            KEY_POWER_CONSUMPTION,
            KEY_TEMP_OUTDOOR,
        ),
    },
    MODEL_550_LUX: {
        "id": MODEL_550_LUX,
        "name": "550 Lux",
        "airflow_m3h": 550,
        "heater_type": "electric",
        "temp_min": DEFAULT_TEMP_MIN,
        "temp_max": DEFAULT_TEMP_MAX,
        "speed_min": DEFAULT_SPEED_MIN,
        "speed_max": DEFAULT_SPEED_MAX,
        "has_cooler": False,
        "has_humidifier": False,
        "has_water_heater": False,
        "enabled_sensors": (
            *BASE_ENABLED_SENSORS,
            KEY_POWER_CONSUMPTION,
            KEY_TEMP_OUTDOOR,
        ),
    },
    MODEL_550_AQUA: {
        "id": MODEL_550_AQUA,
        "name": "550 Aqua",
        "airflow_m3h": 550,
        "heater_type": "water",
        "temp_min": DEFAULT_TEMP_MIN,
        "temp_max": DEFAULT_TEMP_MAX,
        "speed_min": DEFAULT_SPEED_MIN,
        "speed_max": DEFAULT_SPEED_MAX,
        "has_cooler": False,
        "has_humidifier": True,
        "has_water_heater": True,
        "enabled_sensors": (
            *BASE_ENABLED_SENSORS,
            KEY_HUMIDITY,
            KEY_TEMP_WATER,
            KEY_TEMP_OUTDOOR,
        ),
    },
    MODEL_700_LUX: {
        "id": MODEL_700_LUX,
        "name": "700 Lux",
        "airflow_m3h": 700,
        "heater_type": "electric",
        "temp_min": DEFAULT_TEMP_MIN,
        "temp_max": DEFAULT_TEMP_MAX,
        "speed_min": DEFAULT_SPEED_MIN,
        "speed_max": DEFAULT_SPEED_MAX,
        "has_cooler": True,
        "has_humidifier": False,
        "has_water_heater": False,
        "enabled_sensors": (
            *BASE_ENABLED_SENSORS,
            KEY_POWER_CONSUMPTION,
            KEY_TEMP_OUTDOOR,
            KEY_TEMP_ROOM,
        ),
    },
    MODEL_1000_LUX: {
        "id": MODEL_1000_LUX,
        "name": "1000 Lux",
        "airflow_m3h": 1000,
        "heater_type": "electric",
        "temp_min": DEFAULT_TEMP_MIN,
        "temp_max": DEFAULT_TEMP_MAX,
        "speed_min": DEFAULT_SPEED_MIN,
        "speed_max": DEFAULT_SPEED_MAX,
        "has_cooler": True,
        "has_humidifier": False,
        "has_water_heater": False,
        "enabled_sensors": (
            *BASE_ENABLED_SENSORS,
            KEY_POWER_CONSUMPTION,
            KEY_TEMP_OUTDOOR,
            KEY_TEMP_ROOM,
            KEY_SPEED_FACT,
        ),
    },
    MODEL_1000_AQUA: {
        "id": MODEL_1000_AQUA,
        "name": "1000 Aqua",
        "airflow_m3h": 1000,
        "heater_type": "water",
        "temp_min": DEFAULT_TEMP_MIN,
        "temp_max": DEFAULT_TEMP_MAX,
        "speed_min": DEFAULT_SPEED_MIN,
        "speed_max": DEFAULT_SPEED_MAX,
        "has_cooler": True,
        "has_humidifier": True,
        "has_water_heater": True,
        "enabled_sensors": (
            *BASE_ENABLED_SENSORS,
            KEY_HUMIDITY,
            KEY_TEMP_WATER,
            KEY_TEMP_OUTDOOR,
            KEY_TEMP_ROOM,
            KEY_SPEED_FACT,
        ),
    },
    MODEL_2000_LUX: {
        "id": MODEL_2000_LUX,
        "name": "2000 Lux",
        "airflow_m3h": 2000,
        "heater_type": "electric",
        "temp_min": DEFAULT_TEMP_MIN,
        "temp_max": DEFAULT_TEMP_MAX,
        "speed_min": DEFAULT_SPEED_MIN,
        "speed_max": DEFAULT_SPEED_MAX,
        "has_cooler": True,
        "has_humidifier": True,
        "has_water_heater": False,
        "enabled_sensors": (
            *BASE_ENABLED_SENSORS,
            KEY_HUMIDITY,
            KEY_POWER_CONSUMPTION,
            KEY_TEMP_OUTDOOR,
            KEY_TEMP_ROOM,
            KEY_SPEED_FACT,
            KEY_CO2,
        ),
    },
    MODEL_CUSTOM: {
        "id": MODEL_CUSTOM,
        "name": "Custom (Auto)",
        "airflow_m3h": 0,
        "heater_type": "auto",
        "temp_min": DEFAULT_TEMP_MIN,
        "temp_max": DEFAULT_TEMP_MAX,
        "speed_min": DEFAULT_SPEED_MIN,
        "speed_max": DEFAULT_SPEED_MAX,
        "has_cooler": True,
        "has_humidifier": True,
        "has_water_heater": True,
        "enabled_sensors": (
            *BASE_ENABLED_SENSORS,
            KEY_HUMIDITY,
        ),
    },
}

MODEL_OPTIONS: Final[list[str]] = list(MODEL_PRESETS.keys())


def get_model_preset(model_id: str | None) -> dict[str, Any]:
    """Return the configuration preset for a given model identifier."""
    if not model_id or model_id not in MODEL_PRESETS:
        return MODEL_PRESETS[DEFAULT_MODEL]
    return MODEL_PRESETS[model_id]


# Bilingual runtime translation tables (Russian & English)
TRANSLATIONS: Final[dict[str, dict[str, dict[str, str]]]] = {
    "ru": {
        "entities": {
            TRANSLATION_KEY_CLIMATE: "Климат",
            TRANSLATION_KEY_POWER_SWITCH: "Питание",
            TRANSLATION_KEY_TARGET_TEMP: "Заданная температура",
            TRANSLATION_KEY_FAN_SPEED: "Скорость вентилятора",
            KEY_TEMPERATURE: "Температура (точка регулирования)",
            KEY_TEMP_SUPPLY: "Температура подачи (выход установки)",
            KEY_TEMP_ROOM: "Температура в помещении",
            KEY_TEMP_OUTDOOR: "Температура на улице",
            KEY_TEMP_WATER: "Температура теплоносителя",
            KEY_TEMPERATURE_TARGET: "Заданная температура",
            KEY_SPEED: "Скорость вентилятора",
            KEY_SPEED_TARGET: "Заданная скорость",
            KEY_SPEED_FACT: "Фактическая скорость",
            KEY_POWER_CONSUMPTION: "Потребляемая мощность",
            KEY_FILTER_DUST: "Загрязнённость фильтра",
            KEY_HUMIDITY: "Влажность",
            KEY_UNIT_STATE: "Состояние установки",
            KEY_MODE: "Режим работы",
            KEY_MODE_SET: "Заданный режим",
            KEY_COLOR_IND: "Индикатор питания",
            KEY_COLOR_MSG: "Статус сообщения",
            KEY_MSG: "Сообщение устройства",
            KEY_FIRMWARE_VER: "Версия прошивки",
            KEY_PROTOCOL_VER: "Версия протокола",
            KEY_HUMIDITY_SUPPLY: "Влажность на притоке",
            KEY_HUMIDITY_ROOM: "Влажность в помещении",
            KEY_HUMIDITY_OUTDOOR: "Влажность уличного воздуха",
            KEY_CO2: "CO₂",
            KEY_VOC: "VOC (загрязнённость воздуха)",
            KEY_FILTER1_POLLUTION: "Фильтр 1",
            KEY_FILTER2_POLLUTION: "Фильтр 2",
            KEY_FILTER3_POLLUTION: "Фильтр 3",
            KEY_FILTER4_POLLUTION: "Фильтр 4",
            KEY_IS_WARN_ERR: "Предупреждение",
            KEY_IS_FATAL_ERR: "Критическая ошибка",
            KEY_DANGER_OVERHEAT: "Угроза перегрева",
            KEY_DANGER_FREEZE: "Угроза обморожения",
            KEY_CHANGE_FILTER: "Требуется замена фильтра",
            KEY_POWER: "Установка включена",
            KEY_NOTIFY_OVERHEAT: "Уведомление: Угроза перегрева",
            KEY_NOTIFY_FREEZE: "Уведомление: Угроза обморожения",
            KEY_NOTIFY_FILTER: "Уведомление: Замена фильтра",
            KEY_NOTIFY_OFFLINE: "Уведомление: Устройство не в сети",
            KEY_NOTIFY_ONLINE: "Уведомление: Устройство в сети",
            KEY_NOTIFY_POWER: "Уведомление: Включение и выключение",
            KEY_NOTIFY_OTHER_ERRORS: "Уведомление: Остальные ошибки",
        },
        "notifications": {
            NOTIFY_EVENT_OVERHEAT: "Обнаружена угроза перегрева калорифера! Проверьте работу вентилятора и чистоту фильтра.",
            NOTIFY_EVENT_FREEZE: "Обнаружена угроза обморожения! Слишком низкая температура воздуха или воды при выключенном или недостаточном обогреве.",
            NOTIFY_EVENT_FILTER: "Требуется замена воздушного фильтра (загрязнённость достигла порога замены).",
            NOTIFY_EVENT_OFFLINE: "Устройство не в сети (потеряна связь или отключено питание).",
            NOTIFY_EVENT_ONLINE: "Устройство снова в сети и отвечает на запросы.",
            NOTIFY_EVENT_POWER_ON: "Вентиляционная установка включена.",
            NOTIFY_EVENT_POWER_OFF: "Вентиляционная установка выключена.",
            NOTIFY_EVENT_OTHER_ERRORS: "Зафиксирована ошибка или предупреждение контроллера",
        },
        "unit_state": {
            STATE_KEY_OFF: "Выключено",
            STATE_KEY_ON: "Включено",
            STATE_KEY_SHUTDOWN: "Выключение",
            STATE_KEY_STARTUP: "Включение",
            STATE_KEY_UNKNOWN: "Неизвестно",
        },
        "mode": {
            MODE_KEY_HEAT: "Обогрев",
            MODE_KEY_COOL: "Охлаждение",
            MODE_KEY_AUTO_HEAT: "Авто-Обогрев",
            MODE_KEY_AUTO_COOL: "Авто-Охлаждение",
            MODE_KEY_VENT: "Вентиляция",
            MODE_KEY_AUTO: "Авто",
            STATE_KEY_OFF: "Выключено",
            STATE_KEY_UNKNOWN: "Неизвестно",
        },
        "color_msg": {
            STATE_KEY_NORMAL: "Норма",
            STATE_KEY_WARNING: "Предупреждение",
            STATE_KEY_ERROR: "Ошибка",
            STATE_KEY_UNKNOWN: "Неизвестно",
        },
        "color_ind": {
            STATE_KEY_OFF: "Выключено",
            STATE_KEY_TRANSITION: "Переходный процесс",
            STATE_KEY_ON: "Включено",
            STATE_KEY_UNKNOWN: "Неизвестно",
        },
        "filter_status": {
            FILTER_STATUS_NO_DATA: "Нет данных",
            FILTER_STATUS_EXCELLENT: "Отличное",
            FILTER_STATUS_GOOD: "Хорошее",
            FILTER_STATUS_REPLACE_SOON: "Требуется замена",
            FILTER_STATUS_CLOGGED: "Забит",
        },
        "models": {
            MODEL_400_LUX: "Breezart 400 Lux (Электрический, до 400 м³/ч)",
            MODEL_550_LUX: "Breezart 550 Lux (Электрический, до 550 м³/ч)",
            MODEL_550_AQUA: "Breezart 550 Aqua (Водяной + увлажнитель, до 550 м³/ч)",
            MODEL_700_LUX: "Breezart 700 Lux (Электрический + охлаждение, до 700 м³/ч)",
            MODEL_1000_LUX: "Breezart 1000 Lux (Электрический, 10 скоростей, до 1000 м³/ч)",
            MODEL_1000_AQUA: "Breezart 1000 Aqua (Водяной + увлажнитель, до 1000 м³/ч)",
            MODEL_2000_LUX: "Breezart 2000 Lux (Промышленный, до 2000 м³/ч)",
            MODEL_CUSTOM: "Пользовательский / Автоопределение (VPr07 / Modbus)",
        },
        "protocols": {
            PROTOCOL_AUTO: "Автоопределение (Modbus TCP 502 / Native TCP 1560)",
            PROTOCOL_MODBUS_TCP: "Modbus TCP (порт 502 — пульт JLV135 / JL204c7)",
            PROTOCOL_NATIVE_TCP: "Native TCP (порт 1560 — пульт TPD-283U-H)",
        },
    },
    "en": {
        "entities": {
            TRANSLATION_KEY_CLIMATE: "Climate",
            TRANSLATION_KEY_POWER_SWITCH: "Power",
            TRANSLATION_KEY_TARGET_TEMP: "Target temperature",
            TRANSLATION_KEY_FAN_SPEED: "Fan speed",
            KEY_TEMPERATURE: "Temperature (control point)",
            KEY_TEMP_SUPPLY: "Supply air temperature",
            KEY_TEMP_ROOM: "Room temperature",
            KEY_TEMP_OUTDOOR: "Outdoor air temperature",
            KEY_TEMP_WATER: "Heat carrier (water) temperature",
            KEY_TEMPERATURE_TARGET: "Target temperature",
            KEY_SPEED: "Fan speed",
            KEY_SPEED_TARGET: "Target fan speed",
            KEY_SPEED_FACT: "Actual fan speed",
            KEY_POWER_CONSUMPTION: "Power consumption",
            KEY_FILTER_DUST: "Filter pollution",
            KEY_HUMIDITY: "Humidity",
            KEY_UNIT_STATE: "Unit state",
            KEY_MODE: "Operating mode",
            KEY_MODE_SET: "Requested mode",
            KEY_COLOR_IND: "Power indicator",
            KEY_COLOR_MSG: "Message status",
            KEY_MSG: "Device message",
            KEY_FIRMWARE_VER: "Firmware version",
            KEY_PROTOCOL_VER: "Protocol version",
            KEY_HUMIDITY_SUPPLY: "Supply air humidity",
            KEY_HUMIDITY_ROOM: "Room humidity",
            KEY_HUMIDITY_OUTDOOR: "Outdoor air humidity",
            KEY_CO2: "CO₂",
            KEY_VOC: "VOC (air quality)",
            KEY_FILTER1_POLLUTION: "Filter 1",
            KEY_FILTER2_POLLUTION: "Filter 2",
            KEY_FILTER3_POLLUTION: "Filter 3",
            KEY_FILTER4_POLLUTION: "Filter 4",
            KEY_IS_WARN_ERR: "Warning",
            KEY_IS_FATAL_ERR: "Fatal error",
            KEY_DANGER_OVERHEAT: "Overheat hazard",
            KEY_DANGER_FREEZE: "Freeze hazard",
            KEY_CHANGE_FILTER: "Filter replacement required",
            KEY_POWER: "Unit running",
            KEY_NOTIFY_OVERHEAT: "Notification: Overheat hazard",
            KEY_NOTIFY_FREEZE: "Notification: Freeze hazard",
            KEY_NOTIFY_FILTER: "Notification: Filter replacement",
            KEY_NOTIFY_OFFLINE: "Notification: Device offline",
            KEY_NOTIFY_ONLINE: "Notification: Device online",
            KEY_NOTIFY_POWER: "Notification: Power on/off",
            KEY_NOTIFY_OTHER_ERRORS: "Notification: Other errors",
        },
        "notifications": {
            NOTIFY_EVENT_OVERHEAT: "Heater overheat hazard detected! Check fan operation and air filter condition.",
            NOTIFY_EVENT_FREEZE: "Freeze hazard detected! Air or water temperature is critically low with heating off or insufficient.",
            NOTIFY_EVENT_FILTER: "Air filter replacement required (filter pollution reached replacement threshold).",
            NOTIFY_EVENT_OFFLINE: "Device is offline (connection lost or power disconnected).",
            NOTIFY_EVENT_ONLINE: "Device is back online and responding.",
            NOTIFY_EVENT_POWER_ON: "Ventilation unit turned on.",
            NOTIFY_EVENT_POWER_OFF: "Ventilation unit turned off.",
            NOTIFY_EVENT_OTHER_ERRORS: "Controller error or warning detected",
        },
        "unit_state": {
            STATE_KEY_OFF: "Off",
            STATE_KEY_ON: "On",
            STATE_KEY_SHUTDOWN: "Turning off",
            STATE_KEY_STARTUP: "Turning on",
            STATE_KEY_UNKNOWN: "Unknown",
        },
        "mode": {
            MODE_KEY_HEAT: "Heating",
            MODE_KEY_COOL: "Cooling",
            MODE_KEY_AUTO_HEAT: "Auto Heating",
            MODE_KEY_AUTO_COOL: "Auto Cooling",
            MODE_KEY_VENT: "Ventilation",
            MODE_KEY_AUTO: "Auto",
            STATE_KEY_OFF: "Off",
            STATE_KEY_UNKNOWN: "Unknown",
        },
        "color_msg": {
            STATE_KEY_NORMAL: "Normal",
            STATE_KEY_WARNING: "Warning",
            STATE_KEY_ERROR: "Error",
            STATE_KEY_UNKNOWN: "Unknown",
        },
        "color_ind": {
            STATE_KEY_OFF: "Off",
            STATE_KEY_TRANSITION: "Transitioning",
            STATE_KEY_ON: "On",
            STATE_KEY_UNKNOWN: "Unknown",
        },
        "filter_status": {
            FILTER_STATUS_NO_DATA: "No data",
            FILTER_STATUS_EXCELLENT: "Excellent",
            FILTER_STATUS_GOOD: "Good",
            FILTER_STATUS_REPLACE_SOON: "Replace soon",
            FILTER_STATUS_CLOGGED: "Clogged",
        },
        "models": {
            MODEL_400_LUX: "Breezart 400 Lux (Electric, up to 400 m³/h)",
            MODEL_550_LUX: "Breezart 550 Lux (Electric, up to 550 m³/h)",
            MODEL_550_AQUA: "Breezart 550 Aqua (Water heater + humidifier, up to 550 m³/h)",
            MODEL_700_LUX: "Breezart 700 Lux (Electric + cooling, up to 700 m³/h)",
            MODEL_1000_LUX: "Breezart 1000 Lux (Electric, 10 speeds, up to 1000 m³/h)",
            MODEL_1000_AQUA: "Breezart 1000 Aqua (Water heater + humidifier, up to 1000 m³/h)",
            MODEL_2000_LUX: "Breezart 2000 Lux (Commercial, up to 2000 m³/h)",
            MODEL_CUSTOM: "Custom / Auto-detect (VPr07 / Modbus)",
        },
        "protocols": {
            PROTOCOL_AUTO: "Auto-detect (Modbus TCP 502 / Native TCP 1560)",
            PROTOCOL_MODBUS_TCP: "Modbus TCP (port 502 — JLV135 / JL204c7 panel)",
            PROTOCOL_NATIVE_TCP: "Native TCP (port 1560 — TPD-283U-H panel)",
        },
    },
}


def normalize_language(language: str | None) -> str:
    """Normalize Home Assistant language code to 'ru' or 'en'."""
    if language and language.lower().startswith("ru"):
        return "ru"
    return "en"


def translate_value(category: str, key: str, language: str | None = "en") -> str:
    """Return localized string for a given category and key in 'ru' or 'en'."""
    lang = normalize_language(language)
    cat_map = TRANSLATIONS.get(lang, TRANSLATIONS["en"]).get(category, {})
    return cat_map.get(key, key)


def classify_filter_pollution(pollution: float | int | None) -> str:
    """Classify filter pollution percentage into canonical status key."""
    if pollution is None:
        return FILTER_STATUS_NO_DATA
    if pollution < FILTER_POLLUTION_EXCELLENT_MAX:
        return FILTER_STATUS_EXCELLENT
    if pollution < FILTER_POLLUTION_GOOD_MAX:
        return FILTER_STATUS_GOOD
    if pollution < FILTER_POLLUTION_REPLACE_MAX:
        return FILTER_STATUS_REPLACE_SOON
    return FILTER_STATUS_CLOGGED
