"""Number platform for Breezart integration."""
from __future__ import annotations

from homeassistant.components.number import NumberDeviceClass, NumberEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import UnitOfTemperature
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    DATA_COORDINATOR,
    DEFAULT_SPEED_STEP,
    DEFAULT_TEMP_STEP,
    DOMAIN,
    KEY_SPEED_TARGET,
    KEY_TEMPERATURE_TARGET,
    TRANSLATION_KEY_FAN_SPEED,
    TRANSLATION_KEY_TARGET_TEMP,
)
from .coordinator import BreezartDataCoordinator


class BreezartTargetTemperature(CoordinatorEntity[BreezartDataCoordinator], NumberEntity):
    """Target temperature control for Breezart."""

    _attr_has_entity_name = True
    _attr_translation_key = TRANSLATION_KEY_TARGET_TEMP
    _attr_device_class = NumberDeviceClass.TEMPERATURE
    _attr_native_unit_of_measurement = UnitOfTemperature.CELSIUS
    _attr_native_step = DEFAULT_TEMP_STEP

    def __init__(self, coordinator: BreezartDataCoordinator) -> None:
        """Initialize."""
        super().__init__(coordinator)
        self._attr_unique_id = f"{DOMAIN}_{coordinator.client.host}_target_temp"

    @property
    def native_min_value(self) -> float:
        """Return minimum target temperature from client/controller."""
        return float(self.coordinator.client.temp_min)

    @property
    def native_max_value(self) -> float:
        """Return maximum target temperature from client/controller."""
        return float(self.coordinator.client.temp_max)

    @property
    def native_value(self) -> float | None:
        """Return the current target temperature."""
        if not self.coordinator.data:
            return None
        return self.coordinator.data.get(KEY_TEMPERATURE_TARGET)

    async def async_set_native_value(self, value: float) -> None:
        """Set target temperature via protocol."""
        await self.coordinator.async_command(
            self.coordinator.client.set_temperature(int(value))
        )

    @property
    def device_info(self) -> DeviceInfo:
        """Return device info."""
        return self.coordinator.device_info


class BreezartFanSpeed(CoordinatorEntity[BreezartDataCoordinator], NumberEntity):
    """Fan speed control for Breezart."""

    _attr_has_entity_name = True
    _attr_translation_key = TRANSLATION_KEY_FAN_SPEED
    _attr_native_step = DEFAULT_SPEED_STEP

    def __init__(self, coordinator: BreezartDataCoordinator) -> None:
        """Initialize."""
        super().__init__(coordinator)
        self._attr_unique_id = f"{DOMAIN}_{coordinator.client.host}_fan_speed"

    @property
    def native_min_value(self) -> float:
        """Return minimum fan speed step."""
        return float(self.coordinator.client.speed_min)

    @property
    def native_max_value(self) -> float:
        """Return maximum fan speed step."""
        return float(self.coordinator.client.speed_max)

    @property
    def native_value(self) -> float | None:
        """Return the current fan speed target."""
        if not self.coordinator.data:
            return None
        return self.coordinator.data.get(KEY_SPEED_TARGET)

    async def async_set_native_value(self, value: float) -> None:
        """Set fan speed via protocol."""
        await self.coordinator.async_command(
            self.coordinator.client.set_fan_speed(int(value))
        )

    @property
    def device_info(self) -> DeviceInfo:
        """Return device info."""
        return self.coordinator.device_info


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Breezart number entities."""
    coordinator: BreezartDataCoordinator = hass.data[DOMAIN][entry.entry_id][
        DATA_COORDINATOR
    ]

    async_add_entities(
        [
            BreezartTargetTemperature(coordinator),
            BreezartFanSpeed(coordinator),
        ]
    )
