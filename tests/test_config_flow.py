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
