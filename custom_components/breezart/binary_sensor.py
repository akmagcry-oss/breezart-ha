"""Binary sensor platform for Breezart integration."""
from __future__ import annotations

from typing import Any

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    ATTR_HAS_VAV,
    ATTR_VAV_ZONES,
    ATTR_ZONE_SPEEDS,
    DATA_COORDINATOR,
    DOMAIN,
    KEY_CHANGE_FILTER,
    KEY_DANGER_FREEZE,
    KEY_DANGER_OVERHEAT,
    KEY_IS_FATAL_ERR,
    KEY_IS_WARN_ERR,
    KEY_POWER,
    KEY_SCHEDULE_ACTIVE,
    KEY_VAV_MODE,
    KEY_VAV_ZONES,
)
from .coordinator import BreezartDataCoordinator


class BreezartBinarySensor(CoordinatorEntity[BreezartDataCoordinator], BinarySensorEntity):
    """Base binary sensor for Breezart with full i18n support."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: BreezartDataCoordinator,
        key: str,
        device_class: BinarySensorDeviceClass | None = None,
        entity_category: EntityCategory | None = None,
    ) -> None:
        """Initialize."""
        super().__init__(coordinator)
        self._attr_unique_id = f"{DOMAIN}_{coordinator.client.host}_{key}"
        self._attr_translation_key = key
        self._attr_device_class = device_class
        self._attr_entity_category = entity_category
        self._key = key

    @property
    def is_on(self) -> bool | None:
        """Return True if the binary sensor is on."""
        if not self.coordinator.data:
            return None
        return bool(self.coordinator.data.get(self._key, False))

    @property
    def device_info(self) -> DeviceInfo:
        """Return device information."""
        return self.coordinator.device_info


class BreezartVavBinarySensor(BreezartBinarySensor):
    """Diagnostic binary sensor indicating active VAV zoning mode and per-zone speed attributes."""

    def __init__(self, coordinator: BreezartDataCoordinator) -> None:
        """Initialize the VAV mode binary sensor."""
        super().__init__(
            coordinator,
            KEY_VAV_MODE,
            None,
            EntityCategory.DIAGNOSTIC,
        )

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return VAV hardware support flag, configured zone count, and current zone speeds."""
        client = self.coordinator.client
        zones_raw = (
            self.coordinator.data.get(KEY_VAV_ZONES)
            if self.coordinator.data
            else None
        )
        zone_speeds = (
            {int(k): int(v) for k, v in zones_raw.items()}
            if isinstance(zones_raw, dict)
            else {}
        )
        return {
            ATTR_HAS_VAV: bool(getattr(client, "has_vav", False)),
            ATTR_VAV_ZONES: int(getattr(client, "vav_zones", 0)),
            ATTR_ZONE_SPEEDS: zone_speeds,
        }


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Breezart binary sensor entities."""
    coordinator: BreezartDataCoordinator = hass.data[DOMAIN][entry.entry_id][
        DATA_COORDINATOR
    ]

    async_add_entities(
        [
            BreezartBinarySensor(
                coordinator,
                KEY_IS_WARN_ERR,
                BinarySensorDeviceClass.PROBLEM,
                EntityCategory.DIAGNOSTIC,
            ),
            BreezartBinarySensor(
                coordinator,
                KEY_IS_FATAL_ERR,
                BinarySensorDeviceClass.PROBLEM,
                EntityCategory.DIAGNOSTIC,
            ),
            BreezartBinarySensor(
                coordinator,
                KEY_DANGER_OVERHEAT,
                BinarySensorDeviceClass.HEAT,
                EntityCategory.DIAGNOSTIC,
            ),
            BreezartBinarySensor(
                coordinator,
                KEY_DANGER_FREEZE,
                BinarySensorDeviceClass.COLD,
                EntityCategory.DIAGNOSTIC,
            ),
            BreezartBinarySensor(
                coordinator,
                KEY_CHANGE_FILTER,
                BinarySensorDeviceClass.PROBLEM,
                EntityCategory.DIAGNOSTIC,
            ),
            BreezartBinarySensor(
                coordinator,
                KEY_POWER,
                BinarySensorDeviceClass.RUNNING,
            ),
            BreezartBinarySensor(
                coordinator,
                KEY_SCHEDULE_ACTIVE,
                None,
                EntityCategory.DIAGNOSTIC,
            ),
            BreezartVavBinarySensor(coordinator),
        ]
    )
