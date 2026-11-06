"""Config flow and options flow tests."""
from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest
from homeassistant.config_entries import SOURCE_USER
from homeassistant.const import CONF_HOST, CONF_PASSWORD, CONF_PORT
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from custom_components.breezart.const import (
    CONF_MODEL,
    CONF_PROTOCOL,
    CONF_SLAVE_ID,
    CONF_SPEED_MAX,
    CONF_TEMP_MAX,
    CONF_TEMP_MIN,
    DATA_COORDINATOR,
    DOMAIN,
    KEY_NOTIFY_POWER,
    PROTOCOL_AUTO,
    PROTOCOL_MODBUS_TCP,
    PROTOCOL_NATIVE_TCP,
)

from .conftest import HOST, FakeClient

DETECT = "custom_components.breezart.config_flow.async_detect_and_connect_client"
DISCOVER = "custom_components.breezart.config_flow.async_discover_breezart_devices"


def _options_input(**overrides) -> dict:
    data = {
        CONF_MODEL: "custom",
        CONF_PROTOCOL: PROTOCOL_NATIVE_TCP,
        CONF_SLAVE_ID: 1,
        CONF_SPEED_MAX: 10,
        CONF_TEMP_MIN: 5,
        CONF_TEMP_MAX: 35,
    }
    data.update(overrides)
    return data


async def test_user_flow_creates_entry(hass: HomeAssistant) -> None:
    """The user step stores the protocol and port that answered."""
    with patch(DISCOVER, AsyncMock(return_value=[])):
        result = await hass.config_entries.flow.async_init(DOMAIN, context={"source": SOURCE_USER})
    assert result["type"] is FlowResultType.FORM

    with patch(DETECT, AsyncMock(return_value=(FakeClient(), PROTOCOL_MODBUS_TCP, 502))), patch(
        "custom_components.breezart.async_setup_entry", return_value=True
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_MODEL: "custom",
                CONF_PROTOCOL: PROTOCOL_AUTO,
                CONF_HOST: HOST,
                CONF_PORT: 502,
                CONF_SLAVE_ID: 1,
                CONF_PASSWORD: "21579",
                CONF_SPEED_MAX: 10,
                CONF_TEMP_MIN: 5,
                CONF_TEMP_MAX: 35,
            },
        )

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["data"][CONF_PROTOCOL] == PROTOCOL_MODBUS_TCP
    assert result["data"][CONF_PORT] == 502


async def test_options_flow_opens(hass: HomeAssistant, setup_integration) -> None:
    """Regression: the options dialog opens (it crashed on HA 2025.12+)."""
    result = await hass.config_entries.options.async_init(setup_integration.entry_id)
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "init"


async def test_options_without_connection_change_skips_probe(
    hass: HomeAssistant, setup_integration
) -> None:
    """Changing only bounds/toggles does not open a test connection."""
    result = await hass.config_entries.options.async_init(setup_integration.entry_id)
    with patch(DETECT) as mock_detect:
        result = await hass.config_entries.options.async_configure(
            result["flow_id"], _options_input(**{CONF_TEMP_MAX: 30, KEY_NOTIFY_POWER: False})
        )
    await hass.async_block_till_done()

    mock_detect.assert_not_called()
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert setup_integration.options[CONF_TEMP_MAX] == 30
    assert CONF_PORT not in setup_integration.options


async def test_options_protocol_change_stores_verified_port(
    hass: HomeAssistant, setup_integration, mock_create_client
) -> None:
    """Switching protocol probes the device and stores the port that answered."""
    result = await hass.config_entries.options.async_init(setup_integration.entry_id)
    detect = AsyncMock(return_value=(FakeClient(), PROTOCOL_MODBUS_TCP, 502))
    with patch(DETECT, detect):
        result = await hass.config_entries.options.async_configure(
            result["flow_id"], _options_input(**{CONF_PROTOCOL: PROTOCOL_MODBUS_TCP})
        )
    await hass.async_block_till_done()

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert detect.call_args.kwargs["protocol"] == PROTOCOL_MODBUS_TCP
    assert detect.call_args.kwargs["port"] == 1560
    assert setup_integration.options[CONF_PROTOCOL] == PROTOCOL_MODBUS_TCP
    assert setup_integration.options[CONF_PORT] == 502
    # The entry reloaded and the new client got the verified port.
    assert mock_create_client.call_args.kwargs["port"] == 502


@pytest.mark.parametrize(
    ("error", "expected"),
    [
        (ConnectionError("refused"), "cannot_connect"),
        (TimeoutError(), "cannot_connect"),
        (PermissionError("VEPas"), "invalid_auth"),
        (RuntimeError("boom"), "unknown"),
    ],
)
async def test_options_protocol_change_reports_errors(
    hass: HomeAssistant, setup_integration, error: Exception, expected: str
) -> None:
    """A failed probe keeps the form open with an error and changes nothing."""
    result = await hass.config_entries.options.async_init(setup_integration.entry_id)
    with patch(DETECT, AsyncMock(side_effect=error)):
        result = await hass.config_entries.options.async_configure(
            result["flow_id"], _options_input(**{CONF_PROTOCOL: PROTOCOL_MODBUS_TCP})
        )

    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {"base": expected}
    assert CONF_PROTOCOL not in setup_integration.options


async def test_options_probe_releases_running_connection(
    hass: HomeAssistant, setup_integration, fake_client
) -> None:
    """The probe runs with the integration's socket closed and polling paused.

    Controllers that accept a single TCP client would otherwise refuse the probe.
    """
    entry = setup_integration
    coordinator = hass.data[DOMAIN][entry.entry_id][DATA_COORDINATOR]
    assert fake_client.is_connected
    seen: dict[str, bool] = {}

    async def probe(**_):
        seen["connected"] = fake_client.is_connected
        seen["polling_paused"] = coordinator._update_lock.locked()
        raise ConnectionError("refused")

    result = await hass.config_entries.options.async_init(entry.entry_id)
    with patch(DETECT, probe):
        result = await hass.config_entries.options.async_configure(
            result["flow_id"], _options_input(**{CONF_PROTOCOL: PROTOCOL_MODBUS_TCP})
        )

    assert seen == {"connected": False, "polling_paused": True}
    assert result["errors"] == {"base": "cannot_connect"}

    # After a failed probe the integration reconnects on its next poll.
    await coordinator.async_refresh()
    assert fake_client.is_connected
    assert coordinator.last_update_success


async def test_user_flow_autodiscovery_prefills_and_selects_device(hass: HomeAssistant) -> None:
    """Auto-discovery pre-fills the first found device and lets the user pick another from the dropdown."""
    from custom_components.breezart.const import CONF_DISCOVERED_DEVICE
    from custom_components.breezart.coordinator import DiscoveredBreezartDevice

    discovered = [
        DiscoveredBreezartDevice(
            host="192.168.1.55",
            port=502,
            protocol=PROTOCOL_MODBUS_TCP,
            firmware_ver="204.1.7",
        ),
        DiscoveredBreezartDevice(
            host="192.168.1.88",
            port=1560,
            protocol=PROTOCOL_NATIVE_TCP,
            requires_password=True,
        ),
    ]

    with patch(
        "custom_components.breezart.config_flow.async_discover_breezart_devices",
        AsyncMock(return_value=discovered),
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": SOURCE_USER}
        )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"

    # Select the second discovered unit via CONF_DISCOVERED_DEVICE dropdown
    with patch(
        DETECT, AsyncMock(return_value=(FakeClient(), PROTOCOL_NATIVE_TCP, 1560))
    ) as mock_detect, patch(
        "custom_components.breezart.async_setup_entry", return_value=True
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_DISCOVERED_DEVICE: "192.168.1.88:1560",
                CONF_MODEL: "custom",
                CONF_PROTOCOL: PROTOCOL_MODBUS_TCP,
                CONF_HOST: "192.168.1.55",
                CONF_PORT: 502,
                CONF_SLAVE_ID: 1,
                CONF_PASSWORD: "21579",
                CONF_SPEED_MAX: 10,
                CONF_TEMP_MIN: 5,
                CONF_TEMP_MAX: 35,
            },
        )

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert mock_detect.call_args.kwargs["host"] == "192.168.1.88"
    assert mock_detect.call_args.kwargs["port"] == 1560
    assert mock_detect.call_args.kwargs["protocol"] == PROTOCOL_NATIVE_TCP
    assert result["data"][CONF_HOST] == "192.168.1.88"
    assert result["data"][CONF_PORT] == 1560
    assert result["data"][CONF_PROTOCOL] == PROTOCOL_NATIVE_TCP


async def test_reconfigure_flow_updates_host_and_reloads(
    hass: HomeAssistant, setup_integration
) -> None:
    """Reconfigure flow updates host/port/protocol/password, migrates registries, and reloads the entry."""
    from homeassistant.helpers import device_registry as dr, entity_registry as er

    entry = setup_integration
    ent_reg = er.async_get(hass)
    dev_reg = dr.async_get(hass)
    climate_entity_id = "climate.breezart_custom_auto_climate"
    old_entry = ent_reg.async_get(climate_entity_id)
    assert old_entry is not None
    assert old_entry.unique_id == f"{DOMAIN}_{HOST}_climate"

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": "reconfigure", "entry_id": entry.entry_id},
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "reconfigure"

    detect = AsyncMock(return_value=(FakeClient(), PROTOCOL_MODBUS_TCP, 502))
    with patch(DETECT, detect), patch.object(
        hass.config_entries, "async_reload", AsyncMock(return_value=True)
    ) as mock_reload:
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_HOST: "192.168.1.200",
                CONF_PORT: 502,
                CONF_PROTOCOL: PROTOCOL_MODBUS_TCP,
                CONF_SLAVE_ID: 2,
                CONF_PASSWORD: "99999",
                CONF_MODEL: "1000_lux",
            },
        )
        await hass.async_block_till_done()

    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "reconfigure_successful"
    assert entry.data[CONF_HOST] == "192.168.1.200"
    assert entry.data[CONF_PORT] == 502
    assert entry.data[CONF_PROTOCOL] == PROTOCOL_MODBUS_TCP
    assert entry.data[CONF_SLAVE_ID] == 2
    assert entry.data[CONF_PASSWORD] == "99999"
    assert entry.data[CONF_MODEL] == "1000_lux"
    migrated_entry = ent_reg.async_get(climate_entity_id)
    assert migrated_entry is not None
    assert migrated_entry.unique_id == f"{DOMAIN}_192.168.1.200_climate"
    assert any(
        (DOMAIN, "192.168.1.200") in dev.identifiers
        for dev in dr.async_entries_for_config_entry(dev_reg, entry.entry_id)
    )
    mock_reload.assert_called_once_with(entry.entry_id)


async def test_reconfigure_flow_reports_errors(
    hass: HomeAssistant, setup_integration
) -> None:
    """Reconfigure flow keeps form open when connection or authentication fails."""
    entry = setup_integration
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": "reconfigure", "entry_id": entry.entry_id},
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "reconfigure"

    with patch(DETECT, AsyncMock(side_effect=ConnectionError("unreachable"))):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_HOST: "192.168.1.250",
                CONF_PORT: 1560,
                CONF_PROTOCOL: PROTOCOL_NATIVE_TCP,
                CONF_SLAVE_ID: 1,
                CONF_PASSWORD: "21579",
                CONF_MODEL: "custom",
            },
        )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "reconfigure"
    assert result["errors"] == {"base": "cannot_connect"}
    assert entry.data[CONF_HOST] == HOST


async def test_reauth_flow_updates_password_and_reloads(
    hass: HomeAssistant, setup_integration
) -> None:
    """Reauth flow prompts for a new password, verifies it, updates entry, and reloads."""
    entry = setup_integration
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": "reauth", "entry_id": entry.entry_id},
        data=entry.data,
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "reauth_confirm"

    # First attempt with wrong password keeps form open with invalid_auth
    with patch(DETECT, AsyncMock(side_effect=PermissionError("VEPas"))):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {CONF_PASSWORD: "00000"},
        )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "reauth_confirm"
    assert result["errors"] == {"base": "invalid_auth"}

    # Second attempt with valid password updates entry and aborts with reauth_successful
    detect = AsyncMock(return_value=(FakeClient(), PROTOCOL_NATIVE_TCP, 1560))
    with patch(DETECT, detect), patch.object(
        hass.config_entries, "async_reload", AsyncMock(return_value=True)
    ) as mock_reload:
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {CONF_PASSWORD: "54321"},
        )
        await hass.async_block_till_done()

    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "reauth_successful"
    assert entry.data[CONF_PASSWORD] == "54321"
    mock_reload.assert_called_once_with(entry.entry_id)


async def test_coordinator_permission_error_raises_config_entry_auth_failed(
    hass: HomeAssistant, setup_integration, fake_client
) -> None:
    """A PermissionError (VEPas) during polling raises ConfigEntryAuthFailed to trigger reauth."""
    from homeassistant.exceptions import ConfigEntryAuthFailed

    entry = setup_integration
    coordinator = hass.data[DOMAIN][entry.entry_id][DATA_COORDINATOR]

    with patch.object(
        fake_client, "get_state", AsyncMock(side_effect=PermissionError("VEPas_bad_pass"))
    ):
        with pytest.raises(ConfigEntryAuthFailed):
            await coordinator._async_update_data()

