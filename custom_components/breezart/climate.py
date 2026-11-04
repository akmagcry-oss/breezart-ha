"""Climate platform for Breezart integration."""
from __future__ import annotations

import logging
import time
from typing import Any

from homeassistant.components.climate import (
    ClimateEntity,
    ClimateEntityFeature,
    HVACAction,
    HVACMode,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import ATTR_TEMPERATURE, UnitOfTemperature
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    CMD_MODE_AUTO,
    CMD_MODE_COOL,
    CMD_MODE_HEAT,
    CMD_MODE_VENT,
    DATA_COORDINATOR,
    DEFAULT_TEMP_STEP,
    DOMAIN,
    KEY_MODE,
    KEY_POWER,
    KEY_SPEED_TARGET,
    KEY_TEMP_SUPPLY,
    KEY_TEMPERATURE,
    KEY_TEMPERATURE_TARGET,
    KEY_UNIT_STATE,
    MODE_AUTO_COOL,
    MODE_AUTO_HEAT,
    MODE_COOL,
    MODE_HEAT,
    OPTIMISTIC_HOLD_SECONDS,
    TRANSLATION_KEY_CLIMATE,
    UNIT_STATE_OFF,
    UNIT_STATE_ON,
)
from .coordinator import BreezartDataCoordinator

_LOGGER = logging.getLogger(__name__)


class BreezartClimate(CoordinatorEntity[BreezartDataCoordinator], ClimateEntity):
    """Breezart climate entity (thermostat)."""

    _attr_has_entity_name = True
    _attr_translation_key = TRANSLATION_KEY_CLIMATE
    _attr_temperature_unit = UnitOfTemperature.CELSIUS
    _attr_supported_features = (
        ClimateEntityFeature.TARGET_TEMPERATURE
        | ClimateEntityFeature.FAN_MODE
        | ClimateEntityFeature.TURN_ON
        | ClimateEntityFeature.TURN_OFF
    )

    def __init__(self, coordinator: BreezartDataCoordinator) -> None:
        """Initialize the climate entity with model preset and configured ranges."""
        super().__init__(coordinator)
        self._attr_unique_id = f"{DOMAIN}_{coordinator.client.host}_{TRANSLATION_KEY_CLIMATE}"
        self._attr_target_temperature_step = DEFAULT_TEMP_STEP

        hvac_modes = [HVACMode.OFF, HVACMode.FAN_ONLY, HVACMode.HEAT, HVACMode.AUTO]
        if coordinator.client.has_cooler:
            hvac_modes.insert(3, HVACMode.COOL)
        self._attr_hvac_modes = hvac_modes

        self._optimistic_target_temp: float | None = None
        self._optimistic_fan_mode: str | None = None
        self._optimistic_hvac_mode: HVACMode | None = None
        self._optimistic_set_time: float = 0.0

    @property
    def min_temp(self) -> float:
        """Return minimum target temperature from client/controller."""
        return float(self.coordinator.client.temp_min)

    @property
    def max_temp(self) -> float:
        """Return maximum target temperature from client/controller."""
        return float(self.coordinator.client.temp_max)

    @property
    def fan_modes(self) -> list[str]:
        """Return available fan speed steps (e.g. 1..10)."""
        speed_min = int(self.coordinator.client.speed_min)
        speed_max = int(self.coordinator.client.speed_max)
        return [str(s) for s in range(speed_min, speed_max + 1)]

    def _handle_coordinator_update(self) -> None:
        """Clear optimistic state only after hold period expires."""
        if time.monotonic() - self._optimistic_set_time > OPTIMISTIC_HOLD_SECONDS:
            self._optimistic_target_temp = None
            self._optimistic_fan_mode = None
            self._optimistic_hvac_mode = None
        super()._handle_coordinator_update()

    @property
    def current_temperature(self) -> float | None:
        """Return the current temperature (prefer supply air temperature)."""
        if not self.coordinator.data:
            return None
        temp_supply = self.coordinator.data.get(KEY_TEMP_SUPPLY)
        if temp_supply is not None:
            return temp_supply
        return self.coordinator.data.get(KEY_TEMPERATURE)

    @property
    def target_temperature(self) -> float | None:
        """Return the target temperature."""
        if self._optimistic_target_temp is not None:
            return self._optimistic_target_temp
        if not self.coordinator.data:
            return None
        return self.coordinator.data.get(KEY_TEMPERATURE_TARGET)

    @property
    def hvac_mode(self) -> HVACMode:
        """Return current HVAC mode using protocol numeric constants."""
        if self._optimistic_hvac_mode is not None:
            return self._optimistic_hvac_mode
        if not self.coordinator.data:
            return HVACMode.OFF

        power = self.coordinator.data.get(KEY_POWER, False)
        if not power:
            return HVACMode.OFF

        mode = self.coordinator.data.get(KEY_MODE, MODE_HEAT)
        if mode == MODE_HEAT:
            return HVACMode.HEAT
        if mode == MODE_COOL:
            return HVACMode.COOL
        if mode in (MODE_AUTO_HEAT, MODE_AUTO_COOL):
            return HVACMode.AUTO
        return HVACMode.FAN_ONLY

    @property
    def hvac_action(self) -> HVACAction | None:
        """Return current HVAC action using protocol numeric constants."""
        if not self.coordinator.data:
            return None

        power = self.coordinator.data.get(KEY_POWER, False)
        if not power:
            return HVACAction.OFF

        unit_state = self.coordinator.data.get(KEY_UNIT_STATE, UNIT_STATE_OFF)
        if unit_state == UNIT_STATE_OFF:
            return HVACAction.OFF
        if unit_state == UNIT_STATE_ON:
            mode = self.coordinator.data.get(KEY_MODE, MODE_HEAT)
            if mode in (MODE_HEAT, MODE_AUTO_HEAT):
                return HVACAction.HEATING
            if mode in (MODE_COOL, MODE_AUTO_COOL):
                return HVACAction.COOLING
            return HVACAction.FAN
        return HVACAction.IDLE

    @property
    def fan_mode(self) -> str | None:
        """Return current fan mode (speed)."""
        if self._optimistic_fan_mode is not None:
            return self._optimistic_fan_mode
        if not self.coordinator.data:
            return None
        speed = self.coordinator.data.get(KEY_SPEED_TARGET)
        if speed is not None:
            return str(speed)
        return None

    async def async_set_temperature(self, **kwargs: Any) -> None:
        """Set new target temperature."""
        if (temperature := kwargs.get(ATTR_TEMPERATURE)) is None:
            return
        self._optimistic_target_temp = float(temperature)
        self._optimistic_set_time = time.monotonic()
        self.async_write_ha_state()
        try:
            await self.coordinator.client.set_temperature(int(temperature))
            _LOGGER.debug("Set temperature to %d°C", int(temperature))
        except Exception as err:
            self._optimistic_target_temp = None
            self.async_write_ha_state()
            raise HomeAssistantError(f"Breezart: failed to set temperature: {err}") from err
        await self.coordinator.async_request_refresh()

    async def async_set_hvac_mode(self, hvac_mode: HVACMode) -> None:
        """Set new HVAC mode using protocol command constants."""
        self._optimistic_hvac_mode = hvac_mode
        self._optimistic_set_time = time.monotonic()
        self.async_write_ha_state()
        try:
            if hvac_mode == HVACMode.OFF:
                await self.coordinator.client.set_power(False)
            else:
                if not self.coordinator.data or not self.coordinator.data.get(KEY_POWER, False):
                    await self.coordinator.client.set_power(True)
                if hvac_mode == HVACMode.HEAT:
                    await self.coordinator.client.set_mode(CMD_MODE_HEAT)
                elif hvac_mode == HVACMode.COOL:
                    await self.coordinator.client.set_mode(CMD_MODE_COOL)
                elif hvac_mode == HVACMode.AUTO:
                    await self.coordinator.client.set_mode(CMD_MODE_AUTO)
                elif hvac_mode == HVACMode.FAN_ONLY:
                    await self.coordinator.client.set_mode(CMD_MODE_VENT)
        except Exception as err:
            self._optimistic_hvac_mode = None
            self.async_write_ha_state()
            raise HomeAssistantError(f"Breezart: failed to set HVAC mode: {err}") from err
        await self.coordinator.async_request_refresh()

    async def async_set_fan_mode(self, fan_mode: str) -> None:
        """Set new fan mode (speed)."""
        try:
            speed = int(fan_mode)
        except ValueError:
            return
        self._optimistic_fan_mode = fan_mode
        self._optimistic_set_time = time.monotonic()
        self.async_write_ha_state()
        try:
            await self.coordinator.client.set_fan_speed(speed)
            _LOGGER.debug("Set fan speed to %d", speed)
        except Exception as err:
            self._optimistic_fan_mode = None
            self.async_write_ha_state()
            raise HomeAssistantError(f"Breezart: failed to set fan speed: {err}") from err
        await self.coordinator.async_request_refresh()

    async def async_turn_on(self) -> None:
        """Turn on."""
        self._optimistic_hvac_mode = HVACMode.HEAT
        self._optimistic_set_time = time.monotonic()
        self.async_write_ha_state()
        try:
            await self.coordinator.client.set_power(True)
        except Exception as err:
            self._optimistic_hvac_mode = None
            self.async_write_ha_state()
            raise HomeAssistantError(f"Breezart: failed to turn on: {err}") from err
        await self.coordinator.async_request_refresh()

    async def async_turn_off(self) -> None:
        """Turn off."""
        self._optimistic_hvac_mode = HVACMode.OFF
        self._optimistic_set_time = time.monotonic()
        self.async_write_ha_state()
        try:
            await self.coordinator.client.set_power(False)
        except Exception as err:
            self._optimistic_hvac_mode = None
            self.async_write_ha_state()
            raise HomeAssistantError(f"Breezart: failed to turn off: {err}") from err
        await self.coordinator.async_request_refresh()

    @property
    def device_info(self) -> DeviceInfo:
        """Return device information."""
        return self.coordinator.device_info


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Breezart climate entity."""
    coordinator: BreezartDataCoordinator = hass.data[DOMAIN][entry.entry_id][
        DATA_COORDINATOR
    ]
    async_add_entities([BreezartClimate(coordinator)])
