"""Switch platform for Oray Sunlogin."""

import logging
from typing import Any, Dict, Optional

from homeassistant.components.switch import SwitchEntity
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
    """Set up Oray Sunlogin switch entities."""
    coordinator = hass.data[DOMAIN][entry.entry_id]

    entities = []
    for device in coordinator.devices:
        sn = device.get("sn", "")
        device_name = device.get("name", "Unknown")

        # 从电量数据中获取插座数量
        sockets = device.get("sockets", [])
        
        if sockets:
            # 根据电量数据中的插孔数量创建实体 (index从1开始)
            for socket in sockets:
                index = socket.get("index", 1)
                entity_name = f"{device_name} 插孔{index}"
                
                entities.append(
                    OraySunloginSwitch(
                        coordinator=coordinator,
                        sn=sn,
                        device_name=entity_name,
                        index=index,
                        device_data=device,
                    )
                )
        else:
            # 没有电量数据时，默认创建一个插座实体 (索引为1)
            entities.append(
                OraySunloginSwitch(
                    coordinator=coordinator,
                    sn=sn,
                    device_name=device_name,
                    index=1,
                    device_data=device,
                )
            )

    async_add_entities(entities)


class OraySunloginSwitch(SwitchEntity):
    """Oray Sunlogin switch entity."""

    def __init__(
        self,
        coordinator: OraySunloginDataUpdateCoordinator,
        sn: str,
        device_name: str,
        index: int,
        device_data: Dict[str, Any],
    ) -> None:
        """Initialize the switch entity."""
        self.coordinator = coordinator
        self._sn = sn
        self._index = index
        self._attr_name = device_name
        self._attr_unique_id = f"{sn}_{index}"
        self._attr_is_on = False
        self._attr_available = True

        # Get device info
        self._device_data = device_data
        self._update_attrs()

    def _update_attrs(self) -> None:
        """Update entity attributes from device data."""
        device = self._device_data

        # Check if device is online
        online = device.get("online", True)
        self._attr_available = online

        # Get socket state from status array (1-based index)
        status_list = device.get("status", [])
        sockets = device.get("sockets", [])
        
        # 优先从status数组获取
        if status_list:
            for s in status_list:
                if s.get("index") == self._index:
                    self._attr_is_on = s.get("status", 0) == 1
                    break
        # 其次从sockets数组获取
        elif sockets:
            for socket in sockets:
                if socket.get("index") == self._index:
                    self._attr_is_on = socket.get("sw", 0) == 1
                    break

        # Device info
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, self._sn)},
            name=device.get("name", "Unknown"),
            manufacturer="Oray",
            model="智能插座",
            via_device=(DOMAIN, self._sn),
        )

    @property
    def device_info(self) -> DeviceInfo:
        """Return device information."""
        return self._attr_device_info

    @property
    def is_on(self) -> Optional[bool]:
        """Return true if switch is on."""
        return self._attr_is_on

    @property
    def available(self) -> bool:
        """Return True if entity is available."""
        return self._attr_available

    async def async_turn_on(self, **kwargs: Any) -> bool:
        """Turn on the switch."""
        success = await self.coordinator.async_turn_on(
            self._sn, self._index
        )
        if success:
            self._attr_is_on = True
            self.async_write_ha_state()
        return success

    async def async_turn_off(self, **kwargs: Any) -> bool:
        """Turn off the switch."""
        success = await self.coordinator.async_turn_off(
            self._sn, self._index
        )
        if success:
            self._attr_is_on = False
            self.async_write_ha_state()
        return success

    async def async_update(self) -> None:
        """Update the entity."""
        await self.coordinator.async_refresh()

        # Find the device data in coordinator
        for device in self.coordinator.devices:
            sn = device.get("sn", "")
            if sn == self._sn:
                self._device_data = device
                self._update_attrs()
                break
