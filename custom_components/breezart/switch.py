"""Switch platform for Breezart integration."""
from __future__ import annotations

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    DATA_COORDINATOR,
    DATA_SKIP_RELOAD,
    DOMAIN,
    KEY_POWER,
    NOTIFICATION_SETTING_KEYS,
    TRANSLATION_KEY_POWER_SWITCH,
)
from .coordinator import BreezartDataCoordinator


class BreezartPowerSwitch(CoordinatorEntity[BreezartDataCoordinator], SwitchEntity):
    """Power switch for Breezart ventilation unit."""

    _attr_has_entity_name = True
    _attr_translation_key = TRANSLATION_KEY_POWER_SWITCH

    def __init__(self, coordinator: BreezartDataCoordinator) -> None:
        """Initialize the switch."""
        super().__init__(coordinator)
        self._attr_unique_id = f"{DOMAIN}_{coordinator.client.host}_{TRANSLATION_KEY_POWER_SWITCH}"

    @property
    def is_on(self) -> bool:
        """Return True if the unit is on (PwrBtnState == 1)."""
        if not self.coordinator.data:
            return False
        return bool(self.coordinator.data.get(KEY_POWER, False))

    async def async_turn_on(self, **kwargs) -> None:
        """Turn the unit on."""
        await self.coordinator.client.set_power(True)
        await self.coordinator.async_request_refresh()

    async def async_turn_off(self, **kwargs) -> None:
        """Turn the unit off."""
        await self.coordinator.client.set_power(False)
        await self.coordinator.async_request_refresh()

    @property
    def device_info(self) -> DeviceInfo:
        """Return device information."""
        return self.coordinator.device_info


class BreezartNotificationSwitch(CoordinatorEntity[BreezartDataCoordinator], SwitchEntity):
    """Individual device configuration switch to enable/disable a specific Breezart notification."""

    _attr_has_entity_name = True
    _attr_entity_category = EntityCategory.CONFIG

    def __init__(
        self,
        coordinator: BreezartDataCoordinator,
        entry: ConfigEntry,
        key: str,
    ) -> None:
        """Initialize the notification configuration switch."""
        super().__init__(coordinator)
        self._entry = entry
        self._key = key
        self._attr_unique_id = f"{DOMAIN}_{coordinator.client.host}_{key}"
        self._attr_translation_key = key

    @property
    def is_on(self) -> bool:
        """Return True if notifications for this event type are enabled."""
        return self.coordinator.is_notification_enabled(self._key)

    async def _async_set_enabled(self, enabled: bool) -> None:
        """Update notification state in coordinator and persist to ConfigEntry options."""
        self.coordinator.set_notification_enabled(self._key, enabled)
        self.async_write_ha_state()
        entry_data = self.hass.data.get(DOMAIN, {}).get(self._entry.entry_id)
        if entry_data is not None:
            entry_data[DATA_SKIP_RELOAD] = True
        new_options = {**self._entry.options, self._key: enabled}
        self.hass.config_entries.async_update_entry(self._entry, options=new_options)

    async def async_turn_on(self, **kwargs) -> None:
        """Enable notification for this event."""
        await self._async_set_enabled(True)

    async def async_turn_off(self, **kwargs) -> None:
        """Disable notification for this event."""
        await self._async_set_enabled(False)

    @property
    def device_info(self) -> DeviceInfo:
        """Return device information."""
        return self.coordinator.device_info


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Breezart power and notification configuration switch entities."""
    coordinator: BreezartDataCoordinator = hass.data[DOMAIN][entry.entry_id][
        DATA_COORDINATOR
    ]
    entities: list[SwitchEntity] = [BreezartPowerSwitch(coordinator)]
    for notify_key in NOTIFICATION_SETTING_KEYS:
        entities.append(BreezartNotificationSwitch(coordinator, entry, notify_key))
    async_add_entities(entities)
