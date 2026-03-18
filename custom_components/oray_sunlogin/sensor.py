"""Sensor platform for Oray Sunlogin."""

import logging
from typing import Any, Dict

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .coordinator import OraySunloginDataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Oray Sunlogin sensor entities."""
    coordinator = hass.data[DOMAIN][entry.entry_id]

    entities = []
    for device in coordinator.devices:
        sn = device.get("sn", "")
        device_name = device.get("name", "Unknown")
        
        # Use sn as device_uid
        device_uid = sn

        # Add power sensor (功率)
        entities.append(
            OraySunloginPowerSensor(
                coordinator=coordinator,
                device_uid=device_uid,
                device_name=device_name,
                device_data=device,
            )
        )

        # Add voltage sensor (电压)
        entities.append(
            OraySunloginVoltageSensor(
                coordinator=coordinator,
                device_uid=device_uid,
                device_name=device_name,
                device_data=device,
            )
        )

        # Add current sensor (电流)
        entities.append(
            OraySunloginCurrentSensor(
                coordinator=coordinator,
                device_uid=device_uid,
                device_name=device_name,
                device_data=device,
            )
        )

    async_add_entities(entities)


class OraySunloginPowerSensor(SensorEntity):
    """Oray Sunlogin power sensor (功率)."""

    def __init__(
        self,
        coordinator: OraySunloginDataUpdateCoordinator,
        device_uid: str,
        device_name: str,
        device_data: Dict[str, Any],
    ) -> None:
        """Initialize the power sensor."""
        self.coordinator = coordinator
        self._device_uid = device_uid
        self._device_data = device_data

        self._attr_name = f"{device_name} 功率"
        self._attr_unique_id = f"{device_uid}_power"
        self._attr_native_unit_of_measurement = "W"
        self._attr_device_class = "power"
        self._attr_state_class = "measurement"

        self._update_attrs()

    def _update_attrs(self) -> None:
        """Update entity attributes from device data."""
        device = self._device_data

        # Get power value (sum_pwr is already converted to W in api.py)
        power = device.get("sum_pwr", 0)
        self._attr_native_value = float(power) if power else 0.0

        # Device info
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, self._device_uid)},
            name=device.get("name", "Unknown"),
            manufacturer="Oray",
            model="智能插座",
        )

    @property
    def device_info(self) -> DeviceInfo:
        """Return device information."""
        return self._attr_device_info

    async def async_update(self) -> None:
        """Update the entity."""
        await self.coordinator.async_refresh()

        for device in self.coordinator.devices:
            sn = device.get("sn", "")
            
            if sn == self._device_uid:
                self._device_data = device
                self._update_attrs()
                break


class OraySunloginVoltageSensor(SensorEntity):
    """Oray Sunlogin voltage sensor (电压)."""

    def __init__(
        self,
        coordinator: OraySunloginDataUpdateCoordinator,
        device_uid: str,
        device_name: str,
        device_data: Dict[str, Any],
    ) -> None:
        """Initialize the voltage sensor."""
        self.coordinator = coordinator
        self._device_uid = device_uid
        self._device_data = device_data

        self._attr_name = f"{device_name} 电压"
        self._attr_unique_id = f"{device_uid}_voltage"
        self._attr_native_unit_of_measurement = "V"
        self._attr_device_class = "voltage"
        self._attr_state_class = "measurement"

        self._update_attrs()

    def _update_attrs(self) -> None:
        """Update entity attributes from device data."""
        device = self._device_data

        # Get voltage value (sum_vol is already converted to V in api.py)
        voltage = device.get("sum_vol", 0)
        self._attr_native_value = float(voltage) if voltage else 0.0

        # Device info
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, self._device_uid)},
            name=device.get("name", "Unknown"),
            manufacturer="Oray",
            model="智能插座",
        )

    @property
    def device_info(self) -> DeviceInfo:
        """Return device information."""
        return self._attr_device_info

    async def async_update(self) -> None:
        """Update the entity."""
        await self.coordinator.async_refresh()

        for device in self.coordinator.devices:
            sn = device.get("sn", "")
            
            if sn == self._device_uid:
                self._device_data = device
                self._update_attrs()
                break


class OraySunloginCurrentSensor(SensorEntity):
    """Oray Sunlogin current sensor (电流)."""

    def __init__(
        self,
        coordinator: OraySunloginDataUpdateCoordinator,
        device_uid: str,
        device_name: str,
        device_data: Dict[str, Any],
    ) -> None:
        """Initialize the current sensor."""
        self.coordinator = coordinator
        self._device_uid = device_uid
        self._device_data = device_data

        self._attr_name = f"{device_name} 电流"
        self._attr_unique_id = f"{device_uid}_current"
        self._attr_native_unit_of_measurement = "mA"
        self._attr_device_class = "current"
        self._attr_state_class = "measurement"

        self._update_attrs()

    def _update_attrs(self) -> None:
        """Update entity attributes from device data."""
        device = self._device_data

        # Get current value (sum_cur is in mA)
        current = device.get("sum_cur", 0)
        self._attr_native_value = float(current) if current else 0.0

        # Device info
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, self._device_uid)},
            name=device.get("name", "Unknown"),
            manufacturer="Oray",
            model="智能插座",
        )

    @property
    def device_info(self) -> DeviceInfo:
        """Return device information."""
        return self._attr_device_info

    async def async_update(self) -> None:
        """Update the entity."""
        await self.coordinator.async_refresh()

        for device in self.coordinator.devices:
            sn = device.get("sn", "")
            
            if sn == self._device_uid:
                self._device_data = device
                self._update_attrs()
                break
