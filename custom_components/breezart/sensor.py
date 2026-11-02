"""Sensor platform for Breezart integration."""
from __future__ import annotations

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import PERCENTAGE, UnitOfPower, UnitOfTemperature
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    ATTR_FILTER_STATUS,
    ATTR_FILTER_STATUS_KEY,
    COLOR_IND_MAP,
    COLOR_MSG_MAP,
    DATA_COORDINATOR,
    DOMAIN,
    KEY_CO2,
    KEY_COLOR_IND,
    KEY_COLOR_MSG,
    KEY_FILTER1_POLLUTION,
    KEY_FILTER2_POLLUTION,
    KEY_FILTER3_POLLUTION,
    KEY_FILTER4_POLLUTION,
    KEY_FILTER_DUST,
    KEY_FIRMWARE_VER,
    KEY_HUMIDITY,
    KEY_HUMIDITY_OUTDOOR,
    KEY_HUMIDITY_ROOM,
    KEY_HUMIDITY_SUPPLY,
    KEY_MODE,
    KEY_MODE_SET,
    KEY_MSG,
    KEY_POWER_CONSUMPTION,
    KEY_PROTOCOL_VER,
    KEY_SPEED,
    KEY_SPEED_FACT,
    KEY_SPEED_TARGET,
    KEY_TEMP_OUTDOOR,
    KEY_TEMP_ROOM,
    KEY_TEMP_SUPPLY,
    KEY_TEMP_WATER,
    KEY_TEMPERATURE,
    KEY_TEMPERATURE_TARGET,
    KEY_UNIT_STATE,
    KEY_VOC,
    MODE_MAP,
    MODE_SET_MAP,
    STATE_KEY_UNKNOWN,
    UNIT_PPB,
    UNIT_PPM,
    UNIT_STATE_MAP,
    classify_filter_pollution,
    translate_value,
)
from .coordinator import BreezartDataCoordinator


class BreezartSensor(CoordinatorEntity[BreezartDataCoordinator], SensorEntity):
    """Base class for Breezart sensors with full i18n support."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: BreezartDataCoordinator,
        key: str,
        device_class: SensorDeviceClass | None = None,
        unit: str | None = None,
        entity_category: EntityCategory | None = None,
        state_class: SensorStateClass | None = SensorStateClass.MEASUREMENT,
        enabled_default: bool = True,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._attr_unique_id = f"{DOMAIN}_{coordinator.client.host}_{key}"
        self._attr_translation_key = key
        self._attr_device_class = device_class
        self._attr_native_unit_of_measurement = unit
        self._attr_entity_category = entity_category
        self._attr_state_class = state_class
        self._attr_entity_registry_enabled_default = enabled_default
        self._key = key

    @property
    def native_value(self) -> float | int | str | None:
        """Return the sensor value from coordinator data."""
        if not self.coordinator.data:
            return None
        return self.coordinator.data.get(self._key)

    @property
    def device_info(self) -> DeviceInfo:
        """Return device information."""
        return self.coordinator.device_info


class BreezartTextSensor(BreezartSensor):
    """Enum sensor that maps numeric protocol codes to translated state keys."""

    def __init__(
        self,
        coordinator: BreezartDataCoordinator,
        key: str,
        value_map: dict[int, str],
        entity_category: EntityCategory | None = None,
        enabled_default: bool = True,
    ) -> None:
        """Initialize the enum text sensor."""
        super().__init__(
            coordinator,
            key=key,
            device_class=SensorDeviceClass.ENUM,
            entity_category=entity_category,
            state_class=None,
            enabled_default=enabled_default,
        )
        self._value_map = value_map
        self._attr_options = [*list(dict.fromkeys(value_map.values())), STATE_KEY_UNKNOWN]

    @property
    def native_value(self) -> str | None:
        """Return the canonical state key for Home Assistant i18n translation."""
        if not self.coordinator.data:
            return None
        raw_value = self.coordinator.data.get(self._key)
        if raw_value is None:
            return None
        return self._value_map.get(raw_value, STATE_KEY_UNKNOWN)


class BreezartFilterSensor(BreezartSensor):
    """Sensor for filter pollution status with localized status attribute."""

    def __init__(
        self,
        coordinator: BreezartDataCoordinator,
        key: str,
        enabled_default: bool = False,
    ) -> None:
        """Initialize the filter sensor."""
        super().__init__(
            coordinator,
            key=key,
            unit=PERCENTAGE,
            entity_category=EntityCategory.DIAGNOSTIC,
            enabled_default=enabled_default,
        )

    @property
    def native_value(self) -> float | None:
        """Return the numeric pollution value."""
        if not self.coordinator.data:
            return None
        return self.coordinator.data.get(self._key)

    @property
    def extra_state_attributes(self) -> dict[str, str] | None:
        """Return additional state attributes with localized and canonical status."""
        if not self.coordinator.data:
            return None

        pollution = self.coordinator.data.get(self._key)
        status_key = classify_filter_pollution(pollution)
        lang = getattr(getattr(self.hass, "config", None), "language", "en")
        localized_status = translate_value("filter_status", status_key, lang)

        return {
            ATTR_FILTER_STATUS: localized_status,
            ATTR_FILTER_STATUS_KEY: status_key,
        }


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Breezart sensor entities with model-aware default activation."""
    coordinator: BreezartDataCoordinator = hass.data[DOMAIN][entry.entry_id][
        DATA_COORDINATOR
    ]
    enabled_set = set(coordinator.preset.get("enabled_sensors", ()))

    def _is_enabled(key: str) -> bool:
        return key in enabled_set

    entities: list[SensorEntity] = [
        # --- Temperatures ---
        BreezartSensor(
            coordinator,
            KEY_TEMPERATURE,
            SensorDeviceClass.TEMPERATURE,
            UnitOfTemperature.CELSIUS,
            enabled_default=_is_enabled(KEY_TEMPERATURE),
        ),
        BreezartSensor(
            coordinator,
            KEY_TEMP_SUPPLY,
            SensorDeviceClass.TEMPERATURE,
            UnitOfTemperature.CELSIUS,
            enabled_default=_is_enabled(KEY_TEMP_SUPPLY),
        ),
        BreezartSensor(
            coordinator,
            KEY_TEMP_ROOM,
            SensorDeviceClass.TEMPERATURE,
            UnitOfTemperature.CELSIUS,
            enabled_default=_is_enabled(KEY_TEMP_ROOM),
        ),
        BreezartSensor(
            coordinator,
            KEY_TEMP_OUTDOOR,
            SensorDeviceClass.TEMPERATURE,
            UnitOfTemperature.CELSIUS,
            enabled_default=_is_enabled(KEY_TEMP_OUTDOOR),
        ),
        BreezartSensor(
            coordinator,
            KEY_TEMP_WATER,
            SensorDeviceClass.TEMPERATURE,
            UnitOfTemperature.CELSIUS,
            enabled_default=_is_enabled(KEY_TEMP_WATER),
        ),
        BreezartSensor(
            coordinator,
            KEY_TEMPERATURE_TARGET,
            SensorDeviceClass.TEMPERATURE,
            UnitOfTemperature.CELSIUS,
            entity_category=EntityCategory.DIAGNOSTIC,
            enabled_default=_is_enabled(KEY_TEMPERATURE_TARGET),
        ),
        # --- Fan Speed ---
        BreezartSensor(
            coordinator,
            KEY_SPEED,
            unit=None,
            enabled_default=_is_enabled(KEY_SPEED),
        ),
        BreezartSensor(
            coordinator,
            KEY_SPEED_TARGET,
            unit=None,
            entity_category=EntityCategory.DIAGNOSTIC,
            enabled_default=_is_enabled(KEY_SPEED_TARGET),
        ),
        BreezartSensor(
            coordinator,
            KEY_SPEED_FACT,
            unit=PERCENTAGE,
            enabled_default=_is_enabled(KEY_SPEED_FACT),
        ),
        # --- Power Consumption ---
        BreezartSensor(
            coordinator,
            KEY_POWER_CONSUMPTION,
            SensorDeviceClass.POWER,
            UnitOfPower.WATT,
            enabled_default=_is_enabled(KEY_POWER_CONSUMPTION),
        ),
        # --- Filter Dust ---
        BreezartSensor(
            coordinator,
            KEY_FILTER_DUST,
            unit=PERCENTAGE,
            entity_category=EntityCategory.DIAGNOSTIC,
            enabled_default=_is_enabled(KEY_FILTER_DUST),
        ),
        # --- Humidity ---
        BreezartSensor(
            coordinator,
            KEY_HUMIDITY,
            SensorDeviceClass.HUMIDITY,
            PERCENTAGE,
            enabled_default=_is_enabled(KEY_HUMIDITY),
        ),
        # --- Enum State Sensors ---
        BreezartTextSensor(
            coordinator,
            KEY_UNIT_STATE,
            UNIT_STATE_MAP,
            entity_category=EntityCategory.DIAGNOSTIC,
            enabled_default=_is_enabled(KEY_UNIT_STATE),
        ),
        BreezartTextSensor(
            coordinator,
            KEY_MODE,
            MODE_MAP,
            enabled_default=_is_enabled(KEY_MODE),
        ),
        BreezartTextSensor(
            coordinator,
            KEY_MODE_SET,
            MODE_SET_MAP,
            entity_category=EntityCategory.DIAGNOSTIC,
            enabled_default=_is_enabled(KEY_MODE_SET),
        ),
        BreezartTextSensor(
            coordinator,
            KEY_COLOR_IND,
            COLOR_IND_MAP,
            entity_category=EntityCategory.DIAGNOSTIC,
            enabled_default=_is_enabled(KEY_COLOR_IND),
        ),
        BreezartTextSensor(
            coordinator,
            KEY_COLOR_MSG,
            COLOR_MSG_MAP,
            entity_category=EntityCategory.DIAGNOSTIC,
            enabled_default=_is_enabled(KEY_COLOR_MSG),
        ),
        # --- Device Message & Versions ---
        BreezartSensor(
            coordinator,
            KEY_MSG,
            state_class=None,
            entity_category=EntityCategory.DIAGNOSTIC,
            enabled_default=_is_enabled(KEY_MSG),
        ),
        BreezartSensor(
            coordinator,
            KEY_FIRMWARE_VER,
            state_class=None,
            entity_category=EntityCategory.DIAGNOSTIC,
            enabled_default=_is_enabled(KEY_FIRMWARE_VER),
        ),
        BreezartSensor(
            coordinator,
            KEY_PROTOCOL_VER,
            state_class=None,
            entity_category=EntityCategory.DIAGNOSTIC,
            enabled_default=_is_enabled(KEY_PROTOCOL_VER),
        ),
        # --- Additional Humidity ---
        BreezartSensor(
            coordinator,
            KEY_HUMIDITY_SUPPLY,
            SensorDeviceClass.HUMIDITY,
            PERCENTAGE,
            enabled_default=_is_enabled(KEY_HUMIDITY_SUPPLY),
        ),
        BreezartSensor(
            coordinator,
            KEY_HUMIDITY_ROOM,
            SensorDeviceClass.HUMIDITY,
            PERCENTAGE,
            enabled_default=_is_enabled(KEY_HUMIDITY_ROOM),
        ),
        BreezartSensor(
            coordinator,
            KEY_HUMIDITY_OUTDOOR,
            SensorDeviceClass.HUMIDITY,
            PERCENTAGE,
            enabled_default=_is_enabled(KEY_HUMIDITY_OUTDOOR),
        ),
        # --- Air Quality ---
        BreezartSensor(
            coordinator,
            KEY_CO2,
            SensorDeviceClass.CO2,
            UNIT_PPM,
            enabled_default=_is_enabled(KEY_CO2),
        ),
        BreezartSensor(
            coordinator,
            KEY_VOC,
            unit=UNIT_PPB,
            enabled_default=_is_enabled(KEY_VOC),
        ),
        # --- Filter Pollution Stages 1-4 ---
        BreezartFilterSensor(
            coordinator,
            KEY_FILTER1_POLLUTION,
            enabled_default=_is_enabled(KEY_FILTER1_POLLUTION),
        ),
        BreezartFilterSensor(
            coordinator,
            KEY_FILTER2_POLLUTION,
            enabled_default=_is_enabled(KEY_FILTER2_POLLUTION),
        ),
        BreezartFilterSensor(
            coordinator,
            KEY_FILTER3_POLLUTION,
            enabled_default=_is_enabled(KEY_FILTER3_POLLUTION),
        ),
        BreezartFilterSensor(
            coordinator,
            KEY_FILTER4_POLLUTION,
            enabled_default=_is_enabled(KEY_FILTER4_POLLUTION),
        ),
    ]

    async_add_entities(entities)
