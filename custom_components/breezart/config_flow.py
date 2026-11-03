"""Config flow for Breezart integration with model presets and Modbus TCP / Native TCP support."""
from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.const import CONF_HOST, CONF_PASSWORD, CONF_PORT
from homeassistant.core import callback
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers.selector import (
    SelectSelector,
    SelectSelectorConfig,
    SelectSelectorMode,
)

from .const import (
    CONF_MODEL,
    CONF_PROTOCOL,
    CONF_SLAVE_ID,
    CONF_SPEED_MAX,
    CONF_TEMP_MAX,
    CONF_TEMP_MIN,
    CONFIG_FLOW_VERSION,
    DEFAULT_HOST,
    DEFAULT_MODBUS_PORT,
    DEFAULT_MODEL,
    DEFAULT_NAME,
    DEFAULT_PASSWORD,
    DEFAULT_PORT,
    DEFAULT_PROTOCOL,
    DEFAULT_SLAVE_ID,
    DEFAULT_SPEED_MAX,
    DEFAULT_TEMP_MAX,
    DEFAULT_TEMP_MIN,
    DOMAIN,
    ERR_CANNOT_CONNECT,
    ERR_INVALID_AUTH,
    ERR_UNKNOWN,
    MAX_ALLOWED_SPEED_MAX,
    MAX_ALLOWED_TEMP_BOUND,
    MIN_ALLOWED_SPEED_MAX,
    MIN_ALLOWED_TEMP_BOUND,
    MODEL_CUSTOM,
    MODEL_OPTIONS,
    PROTOCOL_OPTIONS,
    STEP_INIT,
    STEP_USER,
    get_model_preset,
)
from .coordinator import async_detect_and_connect_client

_LOGGER = logging.getLogger(__name__)


class BreezartConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Breezart."""

    VERSION = CONFIG_FLOW_VERSION

    def __init__(self) -> None:
        """Initialize the config flow."""
        self._host: str | None = None
        self._port: int = DEFAULT_MODBUS_PORT
        self._password: str = DEFAULT_PASSWORD
        self._model: str = DEFAULT_MODEL
        self._protocol: str = DEFAULT_PROTOCOL
        self._slave_id: int = DEFAULT_SLAVE_ID
        self._speed_max: int = DEFAULT_SPEED_MAX
        self._temp_min: int = DEFAULT_TEMP_MIN
        self._temp_max: int = DEFAULT_TEMP_MAX

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> config_entries.OptionsFlow:
        """Create the options flow for switching model preset, protocol, fan speeds, and temperature bounds."""
        return BreezartOptionsFlowHandler(config_entry)

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            self._host = str(user_input[CONF_HOST]).strip()
            self._port = int(user_input[CONF_PORT])
            self._password = str(user_input.get(CONF_PASSWORD, DEFAULT_PASSWORD)).strip() or DEFAULT_PASSWORD
            self._model = str(user_input.get(CONF_MODEL, DEFAULT_MODEL))
            self._protocol = str(user_input.get(CONF_PROTOCOL, DEFAULT_PROTOCOL))
            self._slave_id = int(user_input.get(CONF_SLAVE_ID, DEFAULT_SLAVE_ID))
            self._speed_max = max(
                MIN_ALLOWED_SPEED_MAX,
                min(MAX_ALLOWED_SPEED_MAX, int(user_input.get(CONF_SPEED_MAX, DEFAULT_SPEED_MAX))),
            )
            raw_t_min = int(user_input.get(CONF_TEMP_MIN, DEFAULT_TEMP_MIN))
            raw_t_max = int(user_input.get(CONF_TEMP_MAX, DEFAULT_TEMP_MAX))
            self._temp_min = max(MIN_ALLOWED_TEMP_BOUND, min(MAX_ALLOWED_TEMP_BOUND - 1, raw_t_min))
            self._temp_max = max(self._temp_min + 1, min(MAX_ALLOWED_TEMP_BOUND, raw_t_max))

            # Pass None in custom mode when defaults are untouched so hardware limits from VPr07/Modbus can auto-populate
            user_speed_override = (
                None
                if self._model == MODEL_CUSTOM and self._speed_max == DEFAULT_SPEED_MAX
                else self._speed_max
            )
            user_tmin_override = (
                None
                if self._model == MODEL_CUSTOM and self._temp_min == DEFAULT_TEMP_MIN
                else self._temp_min
            )
            user_tmax_override = (
                None
                if self._model == MODEL_CUSTOM and self._temp_max == DEFAULT_TEMP_MAX
                else self._temp_max
            )

            # Test connection (with auto-detection fallback between 502 Modbus and 1560 Native TCP)
            try:
                client, resolved_protocol, resolved_port = await async_detect_and_connect_client(
                    host=self._host,
                    port=self._port,
                    password=self._password,
                    model=self._model,
                    protocol=self._protocol,
                    slave_id=self._slave_id,
                    speed_max=user_speed_override,
                    temp_min=user_tmin_override,
                    temp_max=user_tmax_override,
                )
                resolved_speed_max = int(client.speed_max)
                resolved_temp_min = int(client.temp_min)
                resolved_temp_max = int(client.temp_max)
                await client.disconnect()
            except PermissionError as err:
                _LOGGER.error("Authentication error: %s", err)
                errors["base"] = ERR_INVALID_AUTH
            except (TimeoutError, ConnectionError, OSError, ValueError) as err:
                _LOGGER.error("Connection error: %s", err)
                errors["base"] = ERR_CANNOT_CONNECT
            except Exception as err:
                _LOGGER.exception("Unexpected error during connection test: %s", err)
                errors["base"] = ERR_UNKNOWN
            else:
                await self.async_set_unique_id(f"{DOMAIN}_{self._host}_{resolved_port}")
                self._abort_if_unique_id_configured()

                preset = get_model_preset(self._model)
                return self.async_create_entry(
                    title=f"{DEFAULT_NAME} {preset['name']} ({self._host})",
                    data={
                        CONF_HOST: self._host,
                        CONF_PORT: resolved_port,
                        CONF_PASSWORD: self._password,
                        CONF_MODEL: self._model,
                        CONF_PROTOCOL: resolved_protocol,
                        CONF_SLAVE_ID: self._slave_id,
                        CONF_SPEED_MAX: resolved_speed_max,
                        CONF_TEMP_MIN: resolved_temp_min,
                        CONF_TEMP_MAX: resolved_temp_max,
                    },
                )

        model_selector = SelectSelector(
            SelectSelectorConfig(
                options=MODEL_OPTIONS,
                mode=SelectSelectorMode.DROPDOWN,
                translation_key=CONF_MODEL,
            )
        )
        protocol_selector = SelectSelector(
            SelectSelectorConfig(
                options=PROTOCOL_OPTIONS,
                mode=SelectSelectorMode.DROPDOWN,
                translation_key=CONF_PROTOCOL,
            )
        )

        return self.async_show_form(
            step_id=STEP_USER,
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_MODEL, default=self._model): model_selector,
                    vol.Required(CONF_PROTOCOL, default=self._protocol): protocol_selector,
                    vol.Required(CONF_HOST, default=self._host or DEFAULT_HOST): str,
                    vol.Required(CONF_PORT, default=self._port): int,
                    vol.Optional(CONF_SLAVE_ID, default=self._slave_id): int,
                    vol.Optional(CONF_PASSWORD, default=self._password): str,
                    vol.Required(
                        CONF_SPEED_MAX, default=self._speed_max
                    ): vol.All(vol.Coerce(int), vol.Range(min=MIN_ALLOWED_SPEED_MAX, max=MAX_ALLOWED_SPEED_MAX)),
                    vol.Required(
                        CONF_TEMP_MIN, default=self._temp_min
                    ): vol.All(vol.Coerce(int), vol.Range(min=MIN_ALLOWED_TEMP_BOUND, max=MAX_ALLOWED_TEMP_BOUND - 1)),
                    vol.Required(
                        CONF_TEMP_MAX, default=self._temp_max
                    ): vol.All(vol.Coerce(int), vol.Range(min=MIN_ALLOWED_TEMP_BOUND + 1, max=MAX_ALLOWED_TEMP_BOUND)),
                }
            ),
            errors=errors,
        )


class BreezartOptionsFlowHandler(config_entries.OptionsFlow):
    """Handle Breezart options for changing model preset, protocol, fan speeds, and temperature limits."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        """Initialize options flow."""
        self.config_entry = config_entry

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Manage the Breezart options."""
        if user_input is not None:
            raw_t_min = int(user_input.get(CONF_TEMP_MIN, DEFAULT_TEMP_MIN))
            raw_t_max = int(user_input.get(CONF_TEMP_MAX, DEFAULT_TEMP_MAX))
            t_min = max(MIN_ALLOWED_TEMP_BOUND, min(MAX_ALLOWED_TEMP_BOUND - 1, raw_t_min))
            t_max = max(t_min + 1, min(MAX_ALLOWED_TEMP_BOUND, raw_t_max))
            s_max = max(
                MIN_ALLOWED_SPEED_MAX,
                min(MAX_ALLOWED_SPEED_MAX, int(user_input.get(CONF_SPEED_MAX, DEFAULT_SPEED_MAX))),
            )
            cleaned = {
                **user_input,
                CONF_SPEED_MAX: s_max,
                CONF_TEMP_MIN: t_min,
                CONF_TEMP_MAX: t_max,
            }
            return self.async_create_entry(title="", data=cleaned)

        current_model = self.config_entry.options.get(
            CONF_MODEL,
            self.config_entry.data.get(CONF_MODEL, DEFAULT_MODEL),
        )
        preset = get_model_preset(current_model)
        current_protocol = self.config_entry.options.get(
            CONF_PROTOCOL,
            self.config_entry.data.get(CONF_PROTOCOL, DEFAULT_PROTOCOL),
        )
        current_slave_id = int(
            self.config_entry.options.get(
                CONF_SLAVE_ID,
                self.config_entry.data.get(CONF_SLAVE_ID, DEFAULT_SLAVE_ID),
            )
        )
        current_speed_max = int(
            self.config_entry.options.get(
                CONF_SPEED_MAX,
                self.config_entry.data.get(CONF_SPEED_MAX, preset["speed_max"]),
            )
        )
        current_temp_min = int(
            self.config_entry.options.get(
                CONF_TEMP_MIN,
                self.config_entry.data.get(CONF_TEMP_MIN, preset["temp_min"]),
            )
        )
        current_temp_max = int(
            self.config_entry.options.get(
                CONF_TEMP_MAX,
                self.config_entry.data.get(CONF_TEMP_MAX, preset["temp_max"]),
            )
        )

        model_selector = SelectSelector(
            SelectSelectorConfig(
                options=MODEL_OPTIONS,
                mode=SelectSelectorMode.DROPDOWN,
                translation_key=CONF_MODEL,
            )
        )
        protocol_selector = SelectSelector(
            SelectSelectorConfig(
                options=PROTOCOL_OPTIONS,
                mode=SelectSelectorMode.DROPDOWN,
                translation_key=CONF_PROTOCOL,
            )
        )

        return self.async_show_form(
            step_id=STEP_INIT,
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_MODEL, default=current_model): model_selector,
                    vol.Required(CONF_PROTOCOL, default=current_protocol): protocol_selector,
                    vol.Optional(CONF_SLAVE_ID, default=current_slave_id): int,
                    vol.Required(
                        CONF_SPEED_MAX, default=current_speed_max
                    ): vol.All(vol.Coerce(int), vol.Range(min=MIN_ALLOWED_SPEED_MAX, max=MAX_ALLOWED_SPEED_MAX)),
                    vol.Required(
                        CONF_TEMP_MIN, default=current_temp_min
                    ): vol.All(vol.Coerce(int), vol.Range(min=MIN_ALLOWED_TEMP_BOUND, max=MAX_ALLOWED_TEMP_BOUND - 1)),
                    vol.Required(
                        CONF_TEMP_MAX, default=current_temp_max
                    ): vol.All(vol.Coerce(int), vol.Range(min=MIN_ALLOWED_TEMP_BOUND + 1, max=MAX_ALLOWED_TEMP_BOUND)),
                }
            ),
        )

