"""Data coordinator for Oray Sunlogin."""

import logging
from datetime import timedelta
from typing import Any, Dict, List, Optional

import aiohttp
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .api import OraySunloginApi, OraySunloginApiError, OraySunloginAuthError
from .const import DEFAULT_SCAN_INTERVAL, DOMAIN

_LOGGER = logging.getLogger(__name__)


class OraySunloginDataUpdateCoordinator(DataUpdateCoordinator):
    """Data update coordinator for Oray Sunlogin."""

    def __init__(
        self,
        hass: HomeAssistant,
        entry: ConfigEntry,
    ):
        """Initialize the coordinator."""
        self.hass = hass
        self.entry = entry
        self.api: Optional[OraySunloginApi] = None
        self._devices: List[Dict[str, Any]] = []

        scan_interval = entry.options.get(
            "scan_interval", DEFAULT_SCAN_INTERVAL
        )

        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=scan_interval),
        )

    async def _async_setup(self):
        """Set up the coordinator."""
        account = self.entry.data.get("account")
        password = self.entry.data.get("password")
        access_token = self.entry.data.get("access_token")
        refresh_token = self.entry.data.get("refresh_token")

        session = self.hass.helpers.httpx_client.get_async_client()

        self.api = OraySunloginApi(
            session=session,
            account=account,
            password=password,
            access_token=access_token,
            refresh_token=refresh_token,
        )

        # Try to authenticate if no token
        if not access_token:
            try:
                await self.api.authenticate()
                # Save tokens to config entry
                self.hass.config_entries.async_update_entry(
                    self.entry,
                    data={
                        **self.entry.data,
                        "access_token": self.api.access_token,
                        "refresh_token": self.api.refresh_token,
                    },
                )
            except OraySunloginAuthError as e:
                _LOGGER.error(f"Authentication failed: {e}")
                raise

    async def _async_update_data(self) -> Dict[str, Any]:
        """Update device data."""
        if not self.api:
            await self._async_setup()

        try:
            # 获取设备列表
            devices = await self.api.getDevices()
            
            # 为每个设备获取状态和电量信息
            updated_devices = []
            for device in devices:
                sn = device.get("sn", "")
                remote_id = device.get("remote_id", 0)
                
                if not sn:
                    continue
                
                # 获取插座状态
                try:
                    status_data = await self.api.getSocketStatus(sn)
                    device.update(status_data)
                except OraySunloginApiError as e:
                    _LOGGER.warning(f"Failed to get status for {sn}: {e}")
                    device["online"] = False

                # 获取电量数据
                try:
                    electricity = await self.api.getElectricity(sn)
                    device.update(electricity)
                except OraySunloginApiError as e:
                    _LOGGER.debug(f"No electricity data for {sn}: {e}")

                updated_devices.append(device)

            self._devices = updated_devices
            return {"devices": updated_devices}

        except OraySunloginAuthError as e:
            _LOGGER.error(f"Authentication error during update: {e}")
            # Try to re-authenticate
            try:
                await self.api.authenticate()
            except OraySunloginAuthError:
                raise
        except OraySunloginApiError as e:
            _LOGGER.error(f"Error updating data: {e}")
            raise

    @property
    def devices(self) -> List[Dict[str, Any]]:
        """Return list of devices."""
        return self._devices

    async def async_turn_on(self, sn: str, index: int = 1) -> bool:
        """Turn on socket.
        
        Args:
            sn: 设备序列号
            index: 插座索引 (1-based)
        """
        if not self.api:
            await self._async_setup()

        try:
            result = await self.api.controlSocket(sn, index, 1)
            return result.get("success", False)
        except OraySunloginApiError as e:
            _LOGGER.error(f"Failed to turn on socket: {e}")
            return False

    async def async_turn_off(self, sn: str, index: int = 1) -> bool:
        """Turn off socket.
        
        Args:
            sn: 设备序列号
            index: 插座索引 (1-based)
        """
        if not self.api:
            await self._async_setup()

        try:
            result = await self.api.controlSocket(sn, index, 0)
            return result.get("success", False)
        except OraySunloginApiError as e:
            _LOGGER.error(f"Failed to turn off socket: {e}")
            return False
