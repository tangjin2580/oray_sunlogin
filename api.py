"""Oray Sunlogin API client."""

import aiohttp
import logging
from typing import Any, Dict, Optional

from .const import (
    API_BASE_URL,
    AUTH_URL,
    DEFAULT_TIMEOUT,
    DEVICE_LIST_URL,
    SOCKET_STATUS_URL,
    SOCKET_CONTROL_URL,
    ELECTRICITY_URL,
    REFRESH_AUTH_URL,
)

_LOGGER = logging.getLogger(__name__)


class OraySunloginApiError(Exception):
    """Oray Sunlogin API Error."""

    pass


class OraySunloginAuthError(OraySunloginApiError):
    """Oray Sunlogin Authentication Error."""

    pass


class OraySunloginApi:
    """Oray Sunlogin API client."""

    def __init__(
        self,
        session: aiohttp.ClientSession,
        account: str,
        password: str,
        access_token: Optional[str] = None,
        refresh_token: Optional[str] = None,
    ):
        """Initialize the API client."""
        self._session = session
        self._account = account
        self._password = password
        self._access_token = access_token
        self._refresh_token = refresh_token
        self._timeout = DEFAULT_TIMEOUT
        # 存储设备列表，用于获取remoteid
        self._devices: list = []

    @property
    def access_token(self) -> Optional[str]:
        """Return access token."""
        return self._access_token

    @property
    def refresh_token(self) -> Optional[str]:
        """Return refresh token."""
        return self._refresh_token

    async def _request(
        self,
        method: str,
        url: str,
        headers: Optional[Dict[str, str]] = None,
        json: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Make an HTTP request."""
        request_headers = headers or {}
        if self._access_token:
            request_headers["Authorization"] = f"Bearer {self._access_token}"

        try:
            async with self._session.request(
                method,
                url,
                headers=request_headers,
                json=json,
                params=params,
                timeout=self._timeout,
            ) as response:
                # 尝试获取JSON响应
                try:
                    data = await response.json()
                except:
                    data = {}

                if response.status == 401:
                    _LOGGER.warning("Token expired, attempting to refresh")
                    await self.refreshAuthorization()
                    return await self._request(method, url, headers, json, params)

                if response.status not in [200, 201]:
                    _LOGGER.error(
                        f"API request failed: {response.status}, data: {data}"
                    )
                    raise OraySunloginApiError(
                        f"API request failed: {response.status}, {data}"
                    )

                return data

        except aiohttp.ClientError as e:
            _LOGGER.error(f"HTTP request error: {e}")
            raise OraySunloginApiError(f"HTTP request error: {e}") from e

    async def authenticate(self) -> Dict[str, Any]:
        """Authenticate and get access token."""
        _LOGGER.info("Authenticating with Oray Sunlogin API")

        payload = {"account": self._account, "password": self._password}

        data = await self._request("POST", AUTH_URL, json=payload)

        if "access_token" in data:
            self._access_token = data.get("access_token")
            self._refresh_token = data.get("refresh_token")
            _LOGGER.info("Authentication successful")
            return data
        else:
            _LOGGER.error(f"Authentication failed: {data}")
            raise OraySunloginAuthError(f"Authentication failed: {data}")

    async def refreshAuthorization(self) -> Dict[str, Any]:
        """Refresh the authorization token."""
        if not self._refresh_token:
            _LOGGER.error("No refresh token available")
            raise OraySunloginAuthError("No refresh token available")

        _LOGGER.info("Refreshing authorization token")

        headers = {"Authorization": f"Bearer {self._refresh_token}"}

        data = await self._request("POST", REFRESH_AUTH_URL, headers=headers)

        if "access_token" in data:
            self._access_token = data.get("access_token")
            self._refresh_token = data.get("refresh_token", self._refresh_token)
            _LOGGER.info("Token refresh successful")
            return data
        else:
            _LOGGER.error(f"Token refresh failed: {data}")
            raise OraySunloginAuthError(f"Token refresh failed: {data}")

    async def getDevices(self) -> list:
        """Get list of devices (主机列表).
        
        Returns:
            List of devices with sn, remote_id, name, etc.
        """
        _LOGGER.info("Fetching device list")
        
        # 获取主机列表
        data = await self._request("GET", DEVICE_LIST_URL)
        
        # 解析设备列表
        devices = []
        if isinstance(data, list):
            for device in data:
                # 过滤出智能插座设备
                # 智能插座通常在hostinfo.plugins中有smart-plug相关插件
                hostinfo = device.get("hostinfo", {})
                plugins = hostinfo.get("plugins", [])
                
                # 检查是否有智能插座插件
                has_smart_plug = False
                for plugin in plugins:
                    plugin_id = plugin.get("id", "")
                    if "smartplug" in plugin_id.lower() or "plug" in plugin_id.lower():
                        has_smart_plug = True
                        break
                
                if has_smart_plug or self._is_smart_plug_device(device):
                    devices.append({
                        "sn": device.get("mac", ""),  # MAC地址作为序列号
                        "remote_id": device.get("remote_id", 0),
                        "name": device.get("info", {}).get("name", "Unknown"),
                        "online": device.get("is_connected", False),
                    })
        
        self._devices = devices
        _LOGGER.info(f"Found {len(devices)} smart plug devices")
        return devices

    def _is_smart_plug_device(self, device: Dict) -> bool:
        """Check if device is a smart plug.
        
        通过设备特征判断是否为智能插座
        """
        # 智能插座设备的特征判断
        # 可以通过设备名称、类型等进行判断
        name = device.get("info", {}).get("name", "").lower()
        client = device.get("client", "").lower()
        
        # 常见的智能插座型号
        plug_keywords = ["c1", "c2", "c1pro", "p1", "p2", "p4", "p8", "插座", "plug", "socket"]
        
        for keyword in plug_keywords:
            if keyword in name or keyword in client:
                return True
        
        return False

    async def getSocketStatus(self, sn: str) -> Dict[str, Any]:
        """Get socket status.
        
        Args:
            sn: 设备序列号 (MAC地址)
            
        Returns:
            Dict with status array containing index, status, and action
        """
        _LOGGER.info(f"Getting socket status for {sn}")
        
        params = {
            "sn": sn,
        }
        
        data = await self._request("GET", SOCKET_STATUS_URL, params=params)
        
        # 解析状态数据
        result = {
            "online": True,
            "status": [],
        }
        
        # 获取状态数组
        status_list = data.get("status", [])
        for s in status_list:
            result["status"].append({
                "index": s.get("index", 1),  # 保持API的1-based索引
                "status": s.get("status", 0),  # 0=off, 1=on
                "action": s.get("action", 0),
            })
        
        return result

    async def controlSocket(
        self, sn: str, index: int, state: int
    ) -> Dict[str, Any]:
        """Control socket on/off.
        
        Args:
            sn: 设备序列号 (MAC地址)
            index: 插座索引 (1-based, 1 for single socket)
            state: 1 to turn on, 0 to turn off
            
        Returns:
            Dict with success status
        """
        _LOGGER.info(f"Controlling socket {sn}[{index}] to {'on' if state else 'off'}")
        
        params = {
            "sn": sn,
            "index": str(index),
            "status": str(state),
        }
        
        # POST请求，参数放在query中
        data = await self._request("POST", SOCKET_CONTROL_URL, params=params)
        
        # 检查是否成功 - API返回 "success" 字符串
        if data == "success":
            _LOGGER.info(f"Socket control successful")
            return {"success": True}
        else:
            _LOGGER.error(f"Socket control failed: {data}")
            return {"success": False, "error": str(data)}

    async def getElectricity(self, sn: str) -> Dict[str, Any]:
        """Get electricity consumption data.
        
        Args:
            sn: 设备序列号 (MAC地址)
            
        Returns:
            Dict with power, current, voltage data
        """
        _LOGGER.info(f"Getting electricity data for {sn}")
        
        params = {
            "sn": sn,
        }
        
        data = await self._request("GET", ELECTRICITY_URL, params=params)
        
        # 解析电量数据
        result = {
            "sum_pwr": 0,  # 总功率 (W)
            "sum_cur": 0,  # 总电流 (mA)
            "sum_vol": 0,  # 总电压 (mV -> V)
            "sockets": [],  # 各插孔数据
        }
        
        # sum_pwr, sum_cur, sum_vol 单位说明:
        # sum_vol: 原始值是mV，需要除以1000转换为V
        # sum_cur: 原始值可能是mA或A，需要根据实际情况判断
        # sum_pwr: 原始值可能是W或0.01W
        
        if "sum_pwr" in data:
            # 功率: 原始值可能是0.01W单位
            result["sum_pwr"] = data.get("sum_pwr", 0) / 100 if data.get("sum_pwr", 0) > 10000 else data.get("sum_pwr", 0)
            result["sum_cur"] = data.get("sum_cur", 0)
            result["sum_vol"] = data.get("sum_vol", 0) / 1000  # mV -> V
            
            # 解析各插孔数据 - index从1开始
            sub_cur = data.get("sub_cur", [])
            for socket in sub_cur:
                result["sockets"].append({
                    "index": socket.get("index", 1),  # 保持API的1-based索引
                    "cur": socket.get("cur", 0),
                    "pwr": socket.get("pwr", 0) / 100 if socket.get("pwr", 0) > 10000 else socket.get("pwr", 0),
                    "sw": socket.get("sw", 0),
                })
        
        return result

    async def turn_on_all(self, sn: str) -> Dict[str, Any]:
        """Turn on all sockets."""
        params = {"sn": sn}
        data = await self._request("POST", f"{API_BASE_URL}/sl/v1/smart-plug/v2/all-on", params=params)
        return {"success": data == "success" or data.get("code") == 0}

    async def turn_off_all(self, sn: str) -> Dict[str, Any]:
        """Turn off all sockets."""
        params = {"sn": sn}
        data = await self._request("POST", f"{API_BASE_URL}/sl/v1/smart-plug/v2/all-off", params=params)
        return {"success": data == "success" or data.get("code") == 0}
