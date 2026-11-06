"""Config flow for Breezart integration with model presets and Modbus TCP / Native TCP support."""
from __future__ import annotations

import logging
from collections.abc import Mapping
from contextlib import nullcontext
from typing import Any

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.const import CONF_HOST, CONF_PASSWORD, CONF_PORT
from homeassistant.core import callback
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers.selector import (
    SelectOptionDict,
    SelectSelector,
    SelectSelectorConfig,
    SelectSelectorMode,
)

from .const import (
    ABORT_ALREADY_CONFIGURED,
    ABORT_REAUTH_SUCCESSFUL,
    ABORT_RECONFIGURE_SUCCESSFUL,
    CONF_DISCOVERED_DEVICE,
    CONF_MODEL,
    CONF_NOTIFY_SERVICE,
    CONF_PROTOCOL,
    CONF_SLAVE_ID,
    CONF_SPEED_MAX,
    CONF_TEMP_MAX,
    CONF_TEMP_MIN,
    CONF_VAV_ZONES,
    CONFIG_FLOW_VERSION,
    DATA_COORDINATOR,
    DATA_RELOAD_SNAPSHOT,
    DEFAULT_HOST,
    DEFAULT_MODBUS_PORT,
    DEFAULT_MODEL,
    DEFAULT_NAME,
    DEFAULT_NOTIFY_SERVICE,
    DEFAULT_PASSWORD,
    DEFAULT_PORT,
    DEFAULT_PROTOCOL,
    DEFAULT_SLAVE_ID,
    DEFAULT_SPEED_MAX,
    DEFAULT_TEMP_MAX,
    DEFAULT_TEMP_MIN,
    DEFAULT_VAV_ZONES,
    DISCOVERY_MANUAL,
    DOMAIN,
    ERR_CANNOT_CONNECT,
    ERR_INVALID_AUTH,
    ERR_UNKNOWN,
    MAX_ALLOWED_SPEED_MAX,
    MAX_ALLOWED_TEMP_BOUND,
    MAX_ALLOWED_VAV_ZONES,
    MIN_ALLOWED_SPEED_MAX,
    MIN_ALLOWED_TEMP_BOUND,
    MIN_ALLOWED_VAV_ZONES,
    MODEL_CUSTOM,
    MODEL_OPTIONS,
    NOTIFICATION_SETTING_KEYS,
    PROTOCOL_OPTIONS,
    STEP_INIT,
    STEP_REAUTH,
    STEP_REAUTH_CONFIRM,
    STEP_RECONFIGURE,
    STEP_USER,
    get_model_preset,
)
from .coordinator import (
    DiscoveredBreezartDevice,
    async_detect_and_connect_client,
    async_discover_breezart_devices,
)

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
        self._discovered: list[DiscoveredBreezartDevice] | None = None

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> config_entries.OptionsFlow:
        """Create the options flow for switching model preset, protocol, fan speeds, and temperature bounds."""
        return BreezartOptionsFlowHandler()

    def _configured_hosts(self) -> set[str]:
        """Return set of IP/host strings already configured for this domain."""
        return {
            str(entry.data.get(CONF_HOST)).strip()
            for entry in self._async_current_entries()
            if entry.data.get(CONF_HOST)
        }

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step with automatic LAN discovery of Breezart controllers."""
        errors: dict[str, str] = {}

        if self._discovered is None and user_input is None:
            self._discovered = await async_discover_breezart_devices(
                exclude_hosts=self._configured_hosts()
            )
            if self._discovered and self._host is None:
                first = self._discovered[0]
                self._host = first.host
                self._port = first.port
                self._protocol = first.protocol

        if user_input is not None:
            by_key = {dev.key: dev for dev in (self._discovered or [])}
            chosen_key = str(user_input.get(CONF_DISCOVERED_DEVICE, "")).strip()
            submitted_host = str(user_input.get(CONF_HOST, "")).strip()

            if chosen_key in by_key and chosen_key != DISCOVERY_MANUAL:
                chosen = by_key[chosen_key]
                # Use the selected discovered unit unless the user kept the default dropdown
                # item while typing a different custom IP address into CONF_HOST.
                if chosen.host != self._host or submitted_host in ("", self._host):
                    self._host = chosen.host
                    self._port = chosen.port
                    self._protocol = chosen.protocol
                else:
                    self._host = submitted_host
                    self._port = int(user_input[CONF_PORT])
                    self._protocol = str(user_input.get(CONF_PROTOCOL, DEFAULT_PROTOCOL))
            elif submitted_host.lower() in ("", "auto"):
                found = await async_discover_breezart_devices(
                    exclude_hosts=self._configured_hosts()
                )
                self._discovered = found
                if found:
                    self._host = found[0].host
                    self._port = found[0].port
                    self._protocol = found[0].protocol
                else:
                    self._host = DEFAULT_HOST
                    self._port = int(user_input.get(CONF_PORT, DEFAULT_MODBUS_PORT))
                    self._protocol = str(user_input.get(CONF_PROTOCOL, DEFAULT_PROTOCOL))
            else:
                self._host = submitted_host
                self._port = int(user_input[CONF_PORT])
                self._protocol = str(user_input.get(CONF_PROTOCOL, DEFAULT_PROTOCOL))

            self._password = str(user_input.get(CONF_PASSWORD, DEFAULT_PASSWORD)).strip() or DEFAULT_PASSWORD
            self._model = str(user_input.get(CONF_MODEL, DEFAULT_MODEL))
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
                        CONF_NOTIFY_SERVICE: str(
                            user_input.get(CONF_NOTIFY_SERVICE, DEFAULT_NOTIFY_SERVICE)
                        ).strip()
                        or DEFAULT_NOTIFY_SERVICE,
                        **{key: True for key in NOTIFICATION_SETTING_KEYS},
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

        schema_fields: dict[Any, Any] = {}
        if self._discovered:
            current_key = f"{self._host}:{self._port}"
            known_keys = {dev.key for dev in self._discovered}
            default_disc_key = (
                current_key if current_key in known_keys else self._discovered[0].key
            )
            discovered_options = [
                SelectOptionDict(value=dev.key, label=dev.format_label())
                for dev in self._discovered
            ]
            discovered_options.append(
                SelectOptionDict(value=DISCOVERY_MANUAL, label="Manual IP / Вручную")
            )
            schema_fields[
                vol.Optional(CONF_DISCOVERED_DEVICE, default=default_disc_key)
            ] = SelectSelector(
                SelectSelectorConfig(
                    options=discovered_options,
                    mode=SelectSelectorMode.DROPDOWN,
                )
            )

        schema_fields.update(
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
        )

        return self.async_show_form(
            step_id=STEP_USER,
            data_schema=vol.Schema(schema_fields),
            errors=errors,
        )

    def _get_target_entry(self) -> config_entries.ConfigEntry:
        """Resolve the target ConfigEntry for reconfigure or reauth flows."""
        entry_id = self.context.get("entry_id")
        if entry_id and hasattr(self, "hass") and self.hass is not None:
            entry = self.hass.config_entries.async_get_entry(entry_id)
            if entry is not None:
                return entry
        if hasattr(self, "_get_reconfigure_entry") and self.context.get("source") == STEP_RECONFIGURE:
            return self._get_reconfigure_entry()
        if hasattr(self, "_get_reauth_entry"):
            return self._get_reauth_entry()
        raise ValueError("Target config entry not found in flow context")

    def _release_entry_connection(self, entry: config_entries.ConfigEntry) -> Any:
        """Return async context manager that temporarily releases a running single-client socket."""
        if not hasattr(self, "hass") or self.hass is None:
            return nullcontext()
        entry_data = self.hass.data.get(DOMAIN, {}).get(entry.entry_id)
        if entry_data and DATA_COORDINATOR in entry_data:
            return entry_data[DATA_COORDINATOR].async_release_connection()
        return nullcontext()

    def _migrate_host_references(
        self,
        entry: config_entries.ConfigEntry,
        old_host: str,
        new_host: str,
    ) -> None:
        """Migrate entity unique_ids, device identifiers, and Repairs issues when host changes."""
        if not old_host or not new_host or old_host == new_host:
            return
        if not hasattr(self, "hass") or self.hass is None:
            return

        from homeassistant.helpers import (
            device_registry as dr,
            entity_registry as er,
            issue_registry as ir,
        )
        from .const import REPAIR_ISSUE_KEYS

        old_prefix = f"{DOMAIN}_{old_host}_"
        new_prefix = f"{DOMAIN}_{new_host}_"
        ent_reg = er.async_get(self.hass)
        for ent in er.async_entries_for_config_entry(ent_reg, entry.entry_id):
            if ent.unique_id.startswith(old_prefix):
                new_uid = f"{new_prefix}{ent.unique_id[len(old_prefix):]}"
                if ent_reg.async_get_entity_id(ent.domain, ent.platform, new_uid) is None:
                    ent_reg.async_update_entity(ent.entity_id, new_unique_id=new_uid)

        dev_reg = dr.async_get(self.hass)
        old_device = dev_reg.async_get_device(identifiers={(DOMAIN, old_host)})
        if old_device is not None and dev_reg.async_get_device(identifiers={(DOMAIN, new_host)}) is None:
            new_identifiers = {
                (DOMAIN, new_host) if ident == (DOMAIN, old_host) else ident
                for ident in old_device.identifiers
            }
            dev_reg.async_update_device(old_device.id, new_identifiers=new_identifiers)

        for issue_key in REPAIR_ISSUE_KEYS:
            ir.async_delete_issue(self.hass, DOMAIN, f"{old_host}_{issue_key}")

    async def _async_update_and_reload_entry(
        self, entry: config_entries.ConfigEntry, **update_kwargs: Any
    ) -> None:
        """Update config entry and reload it exactly once.

        When the entry is loaded, `entry.add_update_listener(async_reload_entry)`
        is already attached and `async_update_entry` schedules `async_reload_entry`,
        which calls `async_reload(entry.entry_id)`. Clearing `DATA_RELOAD_SNAPSHOT`
        ensures the listener reloads even if the user submitted unchanged values.
        When the entry is not loaded, no update listener is attached, so we call
        `async_reload(entry.entry_id)` directly.
        """
        entry_data = self.hass.data.get(DOMAIN, {}).get(entry.entry_id)
        if entry_data is not None:
            entry_data[DATA_RELOAD_SNAPSHOT] = None
        self.hass.config_entries.async_update_entry(entry, **update_kwargs)
        if entry_data is None:
            await self.hass.config_entries.async_reload(entry.entry_id)

    async def async_step_reconfigure(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle reconfiguration of IP/host, port, protocol, slave ID, password, and model."""
        entry = self._get_target_entry()
        current = {**entry.data, **entry.options}
        errors: dict[str, str] = {}

        if user_input is not None:
            host = str(user_input.get(CONF_HOST, current.get(CONF_HOST, DEFAULT_HOST))).strip()
            port = int(user_input.get(CONF_PORT, current.get(CONF_PORT, DEFAULT_PORT)))
            protocol = str(user_input.get(CONF_PROTOCOL, current.get(CONF_PROTOCOL, DEFAULT_PROTOCOL)))
            slave_id = int(user_input.get(CONF_SLAVE_ID, current.get(CONF_SLAVE_ID, DEFAULT_SLAVE_ID)))
            password = (
                str(user_input.get(CONF_PASSWORD, current.get(CONF_PASSWORD, DEFAULT_PASSWORD))).strip()
                or DEFAULT_PASSWORD
            )
            model = str(user_input.get(CONF_MODEL, current.get(CONF_MODEL, DEFAULT_MODEL)))

            try:
                async with self._release_entry_connection(entry):
                    client, resolved_protocol, resolved_port = await async_detect_and_connect_client(
                        host=host,
                        port=port,
                        password=password,
                        model=model,
                        protocol=protocol,
                        slave_id=slave_id,
                    )
                    await client.disconnect()
            except PermissionError as err:
                _LOGGER.error("Reconfigure authentication error: %s", err)
                errors["base"] = ERR_INVALID_AUTH
            except (TimeoutError, ConnectionError, OSError, ValueError) as err:
                _LOGGER.error("Reconfigure connection error: %s", err)
                errors["base"] = ERR_CANNOT_CONNECT
            except Exception as err:
                _LOGGER.exception("Unexpected error during reconfigure test: %s", err)
                errors["base"] = ERR_UNKNOWN
            else:
                new_unique_id = f"{DOMAIN}_{host}_{resolved_port}"
                for existing in self._async_current_entries():
                    if existing.entry_id != entry.entry_id and existing.unique_id == new_unique_id:
                        return self.async_abort(reason=ABORT_ALREADY_CONFIGURED)

                old_host = str(entry.data.get(CONF_HOST, "")).strip()
                self._migrate_host_references(entry, old_host, host)

                preset = get_model_preset(model)
                new_title = f"{DEFAULT_NAME} {preset['name']} ({host})"
                updated_data = {
                    **entry.data,
                    CONF_HOST: host,
                    CONF_PORT: resolved_port,
                    CONF_PASSWORD: password,
                    CONF_MODEL: model,
                    CONF_PROTOCOL: resolved_protocol,
                    CONF_SLAVE_ID: slave_id,
                }
                updated_options = dict(entry.options)
                if CONF_PORT in updated_options:
                    updated_options[CONF_PORT] = resolved_port
                if CONF_PROTOCOL in updated_options:
                    updated_options[CONF_PROTOCOL] = resolved_protocol
                if CONF_SLAVE_ID in updated_options:
                    updated_options[CONF_SLAVE_ID] = slave_id
                if CONF_MODEL in updated_options:
                    updated_options[CONF_MODEL] = model

                await self._async_update_and_reload_entry(
                    entry,
                    unique_id=new_unique_id,
                    title=new_title,
                    data=updated_data,
                    options=updated_options,
                )
                return self.async_abort(reason=ABORT_RECONFIGURE_SUCCESSFUL)

            current = {**current, **user_input}

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

        schema = vol.Schema(
            {
                vol.Required(
                    CONF_MODEL, default=current.get(CONF_MODEL, DEFAULT_MODEL)
                ): model_selector,
                vol.Required(
                    CONF_PROTOCOL, default=current.get(CONF_PROTOCOL, DEFAULT_PROTOCOL)
                ): protocol_selector,
                vol.Required(
                    CONF_HOST, default=str(current.get(CONF_HOST, DEFAULT_HOST))
                ): str,
                vol.Required(
                    CONF_PORT, default=int(current.get(CONF_PORT, DEFAULT_PORT))
                ): int,
                vol.Optional(
                    CONF_SLAVE_ID, default=int(current.get(CONF_SLAVE_ID, DEFAULT_SLAVE_ID))
                ): int,
                vol.Optional(
                    CONF_PASSWORD, default=str(current.get(CONF_PASSWORD, DEFAULT_PASSWORD))
                ): str,
            }
        )
        return self.async_show_form(
            step_id=STEP_RECONFIGURE,
            data_schema=schema,
            errors=errors,
            description_placeholders={
                "host": str(entry.data.get(CONF_HOST, DEFAULT_HOST)),
                "device": entry.title,
            },
        )

    async def async_step_reauth(
        self, entry_data: Mapping[str, Any]
    ) -> FlowResult:
        """Initiate reauthentication when the remote access password becomes invalid."""
        return await self.async_step_reauth_confirm()

    async def async_step_reauth_confirm(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle password update and verification during reauthentication."""
        entry = self._get_target_entry()
        current = {**entry.data, **entry.options}
        errors: dict[str, str] = {}

        if user_input is not None:
            password = str(user_input.get(CONF_PASSWORD, "")).strip() or DEFAULT_PASSWORD
            host = str(current.get(CONF_HOST, DEFAULT_HOST))
            port = int(current.get(CONF_PORT, DEFAULT_PORT))
            protocol = str(current.get(CONF_PROTOCOL, DEFAULT_PROTOCOL))
            slave_id = int(current.get(CONF_SLAVE_ID, DEFAULT_SLAVE_ID))
            model = str(current.get(CONF_MODEL, DEFAULT_MODEL))

            try:
                async with self._release_entry_connection(entry):
                    client, _, _ = await async_detect_and_connect_client(
                        host=host,
                        port=port,
                        password=password,
                        model=model,
                        protocol=protocol,
                        slave_id=slave_id,
                    )
                    await client.disconnect()
            except PermissionError as err:
                _LOGGER.error("Reauth authentication error: %s", err)
                errors["base"] = ERR_INVALID_AUTH
            except (TimeoutError, ConnectionError, OSError, ValueError) as err:
                _LOGGER.error("Reauth connection error: %s", err)
                errors["base"] = ERR_CANNOT_CONNECT
            except Exception as err:
                _LOGGER.exception("Unexpected error during reauth test: %s", err)
                errors["base"] = ERR_UNKNOWN
            else:
                await self._async_update_and_reload_entry(
                    entry,
                    data={**entry.data, CONF_PASSWORD: password},
                )
                return self.async_abort(reason=ABORT_REAUTH_SUCCESSFUL)

        default_pwd = (
            str(user_input.get(CONF_PASSWORD))
            if user_input and CONF_PASSWORD in user_input
            else str(current.get(CONF_PASSWORD, DEFAULT_PASSWORD))
        )
        return self.async_show_form(
            step_id=STEP_REAUTH_CONFIRM,
            data_schema=vol.Schema(
                {vol.Required(CONF_PASSWORD, default=default_pwd): str}
            ),
            errors=errors,
            description_placeholders={
                "host": str(current.get(CONF_HOST, DEFAULT_HOST)),
                "device": entry.title,
            },
        )


class BreezartOptionsFlowHandler(config_entries.OptionsFlow):
    """Handle Breezart options for changing model preset, protocol, fan speeds, and temperature limits."""

    def _current(self) -> dict[str, Any]:
        """Return the effective settings: options override the original entry data."""
        return {**self.config_entry.data, **self.config_entry.options}

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Manage the Breezart options, verifying the connection when it changes."""
        current = self._current()
        errors: dict[str, str] = {}

        if user_input is not None:
            raw_t_min = int(user_input.get(CONF_TEMP_MIN, DEFAULT_TEMP_MIN))
            raw_t_max = int(user_input.get(CONF_TEMP_MAX, DEFAULT_TEMP_MAX))
            t_min = max(MIN_ALLOWED_TEMP_BOUND, min(MAX_ALLOWED_TEMP_BOUND - 1, raw_t_min))
            t_max = max(t_min + 1, min(MAX_ALLOWED_TEMP_BOUND, raw_t_max))
            s_max = max(
                MIN_ALLOWED_SPEED_MAX,
                min(MAX_ALLOWED_SPEED_MAX, int(user_input.get(CONF_SPEED_MAX, DEFAULT_SPEED_MAX))),
            )
            vav_z = max(
                MIN_ALLOWED_VAV_ZONES,
                min(
                    MAX_ALLOWED_VAV_ZONES,
                    int(user_input.get(CONF_VAV_ZONES, current.get(CONF_VAV_ZONES, DEFAULT_VAV_ZONES))),
                ),
            )
            cleaned: dict[str, Any] = {
                **user_input,
                CONF_SPEED_MAX: s_max,
                CONF_TEMP_MIN: t_min,
                CONF_TEMP_MAX: t_max,
                CONF_VAV_ZONES: vav_z,
            }

            protocol = cleaned.get(CONF_PROTOCOL, DEFAULT_PROTOCOL)
            slave_id = int(cleaned.get(CONF_SLAVE_ID, DEFAULT_SLAVE_ID))
            port = int(current.get(CONF_PORT, DEFAULT_PORT))
            connection_changed = protocol != current.get(
                CONF_PROTOCOL, DEFAULT_PROTOCOL
            ) or slave_id != int(current.get(CONF_SLAVE_ID, DEFAULT_SLAVE_ID))

            if connection_changed:
                # Probe the new protocol and store the port it actually answered on,
                # so switching e.g. Native (1560) -> Modbus doesn't keep port 1560.
                # Controllers that accept a single TCP client would refuse the probe
                # while the running integration holds its socket, so release it first.
                entry_data = self.hass.data.get(DOMAIN, {}).get(self.config_entry.entry_id)
                release = (
                    entry_data[DATA_COORDINATOR].async_release_connection()
                    if entry_data
                    else nullcontext()
                )
                try:
                    async with release:
                        client, resolved_protocol, resolved_port = (
                            await async_detect_and_connect_client(
                                host=self.config_entry.data[CONF_HOST],
                                port=port,
                                password=current.get(CONF_PASSWORD, DEFAULT_PASSWORD),
                                model=cleaned.get(CONF_MODEL, DEFAULT_MODEL),
                                protocol=protocol,
                                slave_id=slave_id,
                            )
                        )
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
                    cleaned[CONF_PROTOCOL] = resolved_protocol
                    cleaned[CONF_PORT] = resolved_port
            elif CONF_PORT in self.config_entry.options:
                cleaned[CONF_PORT] = self.config_entry.options[CONF_PORT]

            if not errors:
                return self.async_create_entry(title="", data=cleaned)
            # Re-show the form with what the user entered.
            current = {**current, **user_input}

        preset = get_model_preset(current.get(CONF_MODEL, DEFAULT_MODEL))
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

        schema: dict[Any, Any] = {
            vol.Required(
                CONF_MODEL, default=current.get(CONF_MODEL, DEFAULT_MODEL)
            ): model_selector,
            vol.Required(
                CONF_PROTOCOL, default=current.get(CONF_PROTOCOL, DEFAULT_PROTOCOL)
            ): protocol_selector,
            vol.Optional(
                CONF_SLAVE_ID, default=int(current.get(CONF_SLAVE_ID, DEFAULT_SLAVE_ID))
            ): int,
            vol.Required(
                CONF_SPEED_MAX,
                default=int(current.get(CONF_SPEED_MAX, preset["speed_max"])),
            ): vol.All(
                vol.Coerce(int),
                vol.Range(min=MIN_ALLOWED_SPEED_MAX, max=MAX_ALLOWED_SPEED_MAX),
            ),
            vol.Required(
                CONF_TEMP_MIN,
                default=int(current.get(CONF_TEMP_MIN, preset["temp_min"])),
            ): vol.All(
                vol.Coerce(int),
                vol.Range(min=MIN_ALLOWED_TEMP_BOUND, max=MAX_ALLOWED_TEMP_BOUND - 1),
            ),
            vol.Required(
                CONF_TEMP_MAX,
                default=int(current.get(CONF_TEMP_MAX, preset["temp_max"])),
            ): vol.All(
                vol.Coerce(int),
                vol.Range(min=MIN_ALLOWED_TEMP_BOUND + 1, max=MAX_ALLOWED_TEMP_BOUND),
            ),
            vol.Optional(
                CONF_VAV_ZONES,
                default=int(current.get(CONF_VAV_ZONES, DEFAULT_VAV_ZONES)),
            ): vol.All(
                vol.Coerce(int),
                vol.Range(min=MIN_ALLOWED_VAV_ZONES, max=MAX_ALLOWED_VAV_ZONES),
            ),
            vol.Optional(
                CONF_NOTIFY_SERVICE,
                default=str(current.get(CONF_NOTIFY_SERVICE, DEFAULT_NOTIFY_SERVICE)),
            ): str,
        }
        for key in NOTIFICATION_SETTING_KEYS:
            schema[vol.Optional(key, default=bool(current.get(key, True)))] = bool

        return self.async_show_form(
            step_id=STEP_INIT,
            data_schema=vol.Schema(schema),
            errors=errors,
        )
