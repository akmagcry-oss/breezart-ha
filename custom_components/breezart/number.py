"""Number platform for Breezart integration."""
from __future__ import annotations

from homeassistant.components.number import NumberDeviceClass, NumberEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import PERCENTAGE, UnitOfTemperature
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    DATA_COORDINATOR,
    DEFAULT_HUMID_MAX,
    DEFAULT_HUMID_MIN,
    DEFAULT_HUMID_STEP,
    DEFAULT_SPEED_STEP,
    DEFAULT_TEMP_STEP,
    DOMAIN,
    KEY_HUMIDITY_TARGET,
    KEY_SPEED_TARGET,
    KEY_TEMPERATURE_TARGET,
    TRANSLATION_KEY_FAN_SPEED,
    TRANSLATION_KEY_TARGET_HUMIDITY,
    TRANSLATION_KEY_TARGET_TEMP,
    KEY_VAV_ZONES,
    MAX_ALLOWED_VAV_ZONES,
    vav_zone_key,
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


class BreezartTargetHumidity(CoordinatorEntity[BreezartDataCoordinator], NumberEntity):
    """Target relative humidity control for Breezart."""

    _attr_has_entity_name = True
    _attr_translation_key = TRANSLATION_KEY_TARGET_HUMIDITY
    _attr_device_class = NumberDeviceClass.HUMIDITY
    _attr_native_unit_of_measurement = PERCENTAGE
    _attr_native_step = DEFAULT_HUMID_STEP

    def __init__(self, coordinator: BreezartDataCoordinator) -> None:
        """Initialize."""
        super().__init__(coordinator)
        self._attr_unique_id = (
            f"{DOMAIN}_{coordinator.client.host}_{TRANSLATION_KEY_TARGET_HUMIDITY}"
        )

    @property
    def native_min_value(self) -> float:
        """Return minimum target humidity (%) from client/controller."""
        return float(getattr(self.coordinator.client, "humid_min", DEFAULT_HUMID_MIN))

    @property
    def native_max_value(self) -> float:
        """Return maximum target humidity (%) from client/controller."""
        return float(getattr(self.coordinator.client, "humid_max", DEFAULT_HUMID_MAX))

    @property
    def native_value(self) -> float | None:
        """Return the current target relative humidity (%)."""
        if not self.coordinator.data:
            return None
        return self.coordinator.data.get(KEY_HUMIDITY_TARGET)

    async def async_set_native_value(self, value: float) -> None:
        """Set target relative humidity via protocol."""
        await self.coordinator.async_command(
            self.coordinator.client.set_humidity(int(round(value)))
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


class BreezartVavZoneSpeed(CoordinatorEntity[BreezartDataCoordinator], NumberEntity):
    """Per-zone VAV damper / airflow speed control for Breezart VAV systems."""

    _attr_has_entity_name = True
    _attr_native_step = DEFAULT_SPEED_STEP
    _attr_icon = "mdi:air-filter"

    def __init__(self, coordinator: BreezartDataCoordinator, zone: int) -> None:
        """Initialize the VAV zone speed entity."""
        super().__init__(coordinator)
        self._zone = int(zone)
        self._key = vav_zone_key(self._zone)
        self._attr_unique_id = f"{DOMAIN}_{coordinator.client.host}_{self._key}"
        self._attr_translation_key = self._key

    @property
    def native_min_value(self) -> float:
        """Return minimum zone speed (0 = zone damper closed / minimum)."""
        return 0.0

    @property
    def native_max_value(self) -> float:
        """Return maximum zone speed step from controller."""
        return float(self.coordinator.client.speed_max)

    @property
    def native_value(self) -> float | None:
        """Return current speed step for this VAV zone."""
        if not self.coordinator.data:
            return None
        direct = self.coordinator.data.get(self._key)
        if direct is not None:
            return float(direct)
        zones_map = self.coordinator.data.get(KEY_VAV_ZONES)
        if isinstance(zones_map, dict) and self._zone in zones_map:
            return float(zones_map[self._zone])
        return None

    async def async_set_native_value(self, value: float) -> None:
        """Set target speed for this VAV zone via protocol."""
        await self.coordinator.async_command(
            self.coordinator.client.set_vav_zone_speed(self._zone, int(round(value)))
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

    entities: list[NumberEntity] = [
        BreezartTargetTemperature(coordinator),
        BreezartTargetHumidity(coordinator),
        BreezartFanSpeed(coordinator),
    ]
    client = coordinator.client
    if getattr(client, "has_vav", False) and getattr(client, "vav_zones", 0) > 0:
        num_zones = min(int(client.vav_zones), MAX_ALLOWED_VAV_ZONES)
        for zone_idx in range(1, num_zones + 1):
            entities.append(BreezartVavZoneSpeed(coordinator, zone_idx))

    async_add_entities(entities)
