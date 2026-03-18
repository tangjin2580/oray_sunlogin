"""Config flow for Oray Sunlogin."""

import logging
from typing import Any, Dict

import aiohttp
import voluptuous as vol
from homeassistant import config_entries
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME
from homeassistant.core import HomeAssistant
from homeassistant.helpers import httpx_client

from .api import OraySunloginApi, OraySunloginAuthError, OraySunloginApiError
from .const import DEFAULT_SCAN_INTERVAL, DOMAIN

_LOGGER = logging.getLogger(__name__)

STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_USERNAME): str,
        vol.Required(CONF_PASSWORD): str,
    }
)

STEP_OPTIONS_DATA_SCHEMA = vol.Schema(
    {
        vol.Optional("scan_interval", default=DEFAULT_SCAN_INTERVAL): int,
    }
)


class OraySunloginConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Oray Sunlogin config flow."""

    VERSION = 1

    async def async_step_user(
        self, user_input: Dict[str, Any] = None
    ) -> config_entries.FlowResult:
        """Handle the initial step."""
        errors: Dict[str, str] = {}

        if user_input is not None:
            username = user_input[CONF_USERNAME]
            password = user_input[CONF_PASSWORD]

            # Validate credentials
            try:
                session = httpx_client.get_async_client()
                api = OraySunloginApi(
                    session=session,
                    account=username,
                    password=password,
                )
                auth_data = await api.authenticate()

                await self.async_set_unique_id(username)

                return self.async_create_entry(
                    title=f"Oray Sunlogin ({username})",
                    data={
                        "account": username,
                        "password": password,
                        "access_token": api.access_token,
                        "refresh_token": api.refresh_token,
                    },
                    options={
                        "scan_interval": DEFAULT_SCAN_INTERVAL,
                    },
                )

            except OraySunloginAuthError:
                errors["base"] = "invalid_auth"
            except OraySunloginApiError:
                errors["base"] = "cannot_connect"
            except Exception as e:  # pylint: disable=broad-except
                _LOGGER.exception(f"Unexpected error: {e}")
                errors["base"] = "unknown"

        return self.async_show_form(
            step_id="user",
            data_schema=STEP_USER_DATA_SCHEMA,
            errors=errors,
        )

    async def async_step_options(
        self, user_input: Dict[str, Any] = None
    ) -> config_entries.FlowResult:
        """Handle options flow."""
        if user_input is not None:
            return self.async_create_entry(
                title=self.entry.title,
                data=user_input,
            )

        return self.async_show_form(
            step_id="options",
            data_schema=STEP_OPTIONS_DATA_SCHEMA,
        )

    @staticmethod
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> config_entries.OptionsFlow:
        """Get options flow."""
        return OraySunloginOptionsFlow(config_entry)


class OraySunloginOptionsFlow(config_entries.OptionsFlow):
    """Oray Sunlogin options flow."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        """Initialize options flow."""
        self.config_entry = config_entry

    async def async_step_init(
        self, user_input: Dict[str, Any] = None
    ) -> config_entries.FlowResult:
        """Manage options."""
        if user_input is not None:
            return self.async_create_entry(
                title=self.config_entry.title,
                data=user_input,
            )

        options_schema = vol.Schema(
            {
                vol.Optional(
                    "scan_interval",
                    default=self.config_entry.options.get(
                        "scan_interval", DEFAULT_SCAN_INTERVAL
                    ),
                ): int,
            }
        )

        return self.async_show_form(
            step_id="init",
            data_schema=options_schema,
        )
