"""Shared fixtures: a fake Breezart client and a config entry wired to it."""
from __future__ import annotations

from typing import Any
from unittest.mock import AsyncMock, patch

import pytest
from homeassistant.const import CONF_HOST, CONF_PASSWORD, CONF_PORT
from homeassistant.core import HomeAssistant
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.breezart.const import (
    CONF_MODEL,
    CONF_PROTOCOL,
    CONF_SLAVE_ID,
    DOMAIN,
    NOTIFICATION_SETTING_KEYS,
    PROTOCOL_NATIVE_TCP,
)

HOST = "192.0.2.10"


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations: None) -> None:
    """Allow loading custom_components/breezart in every test."""


class FakeClient:
    """Stand-in for BreezartTCPClient / BreezartModbusClient with mocked I/O."""

    def __init__(self, *, protocol_type: str = PROTOCOL_NATIVE_TCP, **_: Any) -> None:
        self.protocol_type = protocol_type
        self.host = HOST
        self.temp_min, self.temp_max = 5, 35
        self.speed_min, self.speed_max = 1, 10
        self.has_cooler = False
        self.has_humidifier = False
        self.firmware_ver = 100
        self.protocol_ver = "1.0"
        self.connected = False
        self.state: dict[str, Any] = {
            "power": True,
            "unit_state": 1,
            "mode": 1,
            "mode_set": 1,
            "temperature": 21.0,
            "temperature_target": 22.0,
            "humidity": None,
            "speed": 3,
            "speed_target": 3,
            "speed_fact": 30,
            "filter_dust": 10,
            "is_warn_err": False,
            "is_fatal_err": False,
            "danger_overheat": False,
            "danger_freeze": False,
            "change_filter": False,
            "color_msg": 0,
            "color_ind": 1,
            "msg": "OK",
        }
        self.sensors: dict[str, Any] = {"temp_supply": 20.5, "temp_room": 22.5}
        self.set_power = AsyncMock()
        self.set_temperature = AsyncMock()
        self.set_fan_speed = AsyncMock()
        self.set_mode = AsyncMock()

    @property
    def is_connected(self) -> bool:
        return self.connected

    async def connect(self) -> None:
        self.connected = True

    async def disconnect(self) -> None:
        self.connected = False

    async def get_properties(self) -> None:
        return None

    async def get_state(self) -> dict[str, Any]:
        return dict(self.state)

    async def get_sensors(self) -> dict[str, Any]:
        return dict(self.sensors)


@pytest.fixture
def fake_client() -> FakeClient:
    """Return the client instance the integration will receive."""
    return FakeClient()


@pytest.fixture
def mock_create_client(fake_client: FakeClient):
    """Make async_setup_entry use the fake client; exposes the call args."""
    with patch(
        "custom_components.breezart.create_breezart_client", return_value=fake_client
    ) as mock:
        yield mock


@pytest.fixture
def config_entry(hass: HomeAssistant) -> MockConfigEntry:
    """A native-TCP entry as created by the config flow."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        unique_id=f"{DOMAIN}_{HOST}_1560",
        data={
            CONF_HOST: HOST,
            CONF_PORT: 1560,
            CONF_PASSWORD: "21579",
            CONF_MODEL: "custom",
            CONF_PROTOCOL: PROTOCOL_NATIVE_TCP,
            CONF_SLAVE_ID: 1,
            **{key: True for key in NOTIFICATION_SETTING_KEYS},
        },
    )
    entry.add_to_hass(hass)
    return entry


@pytest.fixture
async def setup_integration(
    hass: HomeAssistant, config_entry: MockConfigEntry, mock_create_client
) -> MockConfigEntry:
    """Set up the integration with the fake client."""
    assert await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()
    return config_entry


def entity_id_for(hass: HomeAssistant, platform: str, key: str) -> str:
    """Resolve an entity_id from the integration's unique_id pattern."""
    from homeassistant.helpers import entity_registry as er

    entity_id = er.async_get(hass).async_get_entity_id(platform, DOMAIN, f"{DOMAIN}_{HOST}_{key}")
    assert entity_id is not None, f"no {platform} entity for key {key}"
    return entity_id
