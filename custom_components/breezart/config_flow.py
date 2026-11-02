"""Config flow for Breezart integration with model presets."""
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
    CONFIG_FLOW_VERSION,
    DEFAULT_HOST,
    DEFAULT_MODEL,
    DEFAULT_NAME,
    DEFAULT_PASSWORD,
    DEFAULT_PORT,
    DOMAIN,
    ERR_CANNOT_CONNECT,
    ERR_INVALID_AUTH,
    ERR_UNKNOWN,
    MODEL_OPTIONS,
    STEP_INIT,
    STEP_USER,
    get_model_preset,
)
from .coordinator import BreezartTCPClient

_LOGGER = logging.getLogger(__name__)


class BreezartConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Breezart."""

    VERSION = CONFIG_FLOW_VERSION

    def __init__(self) -> None:
        """Initialize the config flow."""
        self._host: str | None = None
        self._port: int = DEFAULT_PORT
        self._password: str | None = None
        self._model: str = DEFAULT_MODEL

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> config_entries.OptionsFlow:
        """Create the options flow for switching model preset."""
        return BreezartOptionsFlowHandler(config_entry)

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            self._host = str(user_input[CONF_HOST]).strip()
            self._port = int(user_input[CONF_PORT])
            self._password = str(user_input[CONF_PASSWORD]).strip()
            self._model = str(user_input.get(CONF_MODEL, DEFAULT_MODEL))

            await self.async_set_unique_id(f"{DOMAIN}_{self._host}_{self._port}")
            self._abort_if_unique_id_configured()

            # Test connection
            try:
                client = BreezartTCPClient(
                    host=self._host,
                    port=self._port,
                    password=int(self._password),
                    model=self._model,
                )
                await client.connect()
                await client.get_properties()
                await client.disconnect()
            except PermissionError as err:
                _LOGGER.error("Authentication error: %s", err)
                errors["base"] = ERR_INVALID_AUTH
            except (TimeoutError, ConnectionError, OSError) as err:
                _LOGGER.error("Connection error: %s", err)
                errors["base"] = ERR_CANNOT_CONNECT
            except Exception as err:
                _LOGGER.exception("Unexpected error during connection test: %s", err)
                errors["base"] = ERR_UNKNOWN
            else:
                preset = get_model_preset(self._model)
                return self.async_create_entry(
                    title=f"{DEFAULT_NAME} {preset['name']} ({self._host})",
                    data={
                        CONF_HOST: self._host,
                        CONF_PORT: self._port,
                        CONF_PASSWORD: self._password,
                        CONF_MODEL: self._model,
                    },
                )

        model_selector = SelectSelector(
            SelectSelectorConfig(
                options=MODEL_OPTIONS,
                mode=SelectSelectorMode.DROPDOWN,
                translation_key=CONF_MODEL,
            )
        )

        return self.async_show_form(
            step_id=STEP_USER,
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_MODEL, default=self._model): model_selector,
                    vol.Required(CONF_HOST, default=DEFAULT_HOST): str,
                    vol.Required(CONF_PORT, default=DEFAULT_PORT): int,
                    vol.Required(CONF_PASSWORD, default=DEFAULT_PASSWORD): str,
                }
            ),
            errors=errors,
        )


class BreezartOptionsFlowHandler(config_entries.OptionsFlow):
    """Handle Breezart options for changing model preset."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        """Initialize options flow."""
        self.config_entry = config_entry

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Manage the Breezart options."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        current_model = self.config_entry.options.get(
            CONF_MODEL,
            self.config_entry.data.get(CONF_MODEL, DEFAULT_MODEL),
        )

        model_selector = SelectSelector(
            SelectSelectorConfig(
                options=MODEL_OPTIONS,
                mode=SelectSelectorMode.DROPDOWN,
                translation_key=CONF_MODEL,
            )
        )

        return self.async_show_form(
            step_id=STEP_INIT,
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_MODEL, default=current_model): model_selector,
                }
            ),
        )
