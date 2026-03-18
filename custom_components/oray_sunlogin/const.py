"""Constants for Oray Sunlogin integration."""

from homeassistant.components.switch import (
    DOMAIN as SWITCH_DOMAIN,
)
from homeassistant.components.sensor import (
    DOMAIN as SENSOR_DOMAIN,
)

DOMAIN = "oray_sunlogin"

PLATFORMS = [SWITCH_DOMAIN, SENSOR_DOMAIN]

# API Base URL
API_BASE_URL = "https://api.oraydev.cn"

# Auth API
AUTH_URL = f"{API_BASE_URL}/common/v1/authorization"
REFRESH_AUTH_URL = f"{API_BASE_URL}/common/v1/authorization/refresh"

# Device API (获取主机列表)
DEVICE_LIST_URL = f"{API_BASE_URL}/sl/v1/remotes"

# Smart Plug API (插座/插线板)
SOCKET_STATUS_URL = f"{API_BASE_URL}/sl/v1/smart-plug/get-status"
SOCKET_CONTROL_URL = f"{API_BASE_URL}/sl/v1/smart-plug/v2/status"
ELECTRICITY_URL = f"{API_BASE_URL}/sl/v1/smart-plug/v2/get-electric"

# 全开/全关插座
SOCKET_ALL_ON_URL = f"{API_BASE_URL}/sl/v1/smart-plug/v2/all-on"
SOCKET_ALL_OFF_URL = f"{API_BASE_URL}/sl/v1/smart-plug/v2/all-off"

# Default values
DEFAULT_SCAN_INTERVAL = 30  # seconds
DEFAULT_TIMEOUT = 10  # seconds

# Device types
DEVICE_TYPE_SOCKET = "socket"
DEVICE_TYPE_PLUG = "plug"
DEVICE_TYPE_PDU = "pdu"

# Socket states
SOCKET_STATE_ON = 1
SOCKET_STATE_OFF = 0
