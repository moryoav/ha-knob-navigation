"""Config flow for Knob Swipe Navigation."""

from __future__ import annotations

from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import CONF_DEVICE_ID
from homeassistant.helpers import selector

from .const import DEFAULT_NAME, DOMAIN
from .helpers import configured_device_id, is_zha_device


def _device_schema(default_device_id: str | None = None) -> vol.Schema:
    """Return the device selection schema."""
    key = (
        vol.Required(CONF_DEVICE_ID, default=default_device_id)
        if default_device_id
        else vol.Required(CONF_DEVICE_ID)
    )
    return vol.Schema({key: selector.DeviceSelector({"filter": {"integration": "zha"}})})


class KnobSwipeNavigationConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Knob Swipe Navigation."""

    VERSION = 1
    MINOR_VERSION = 2

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.ConfigFlowResult:
        """Handle the initial setup step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            device_id = user_input[CONF_DEVICE_ID]
            if not is_zha_device(self.hass, device_id):
                errors[CONF_DEVICE_ID] = "not_zha_device"
            else:
                await self.async_set_unique_id(DOMAIN)
                self._abort_if_unique_id_configured()
                return self.async_create_entry(
                    title=DEFAULT_NAME,
                    data={CONF_DEVICE_ID: device_id},
                )

        return self.async_show_form(
            step_id="user",
            data_schema=_device_schema(),
            errors=errors,
        )

    async def async_step_reconfigure(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.ConfigFlowResult:
        """Handle reconfiguration."""
        errors: dict[str, str] = {}
        entry = self._get_reconfigure_entry()
        current_device_id = configured_device_id(entry)

        if user_input is not None:
            device_id = user_input[CONF_DEVICE_ID]
            if not is_zha_device(self.hass, device_id):
                errors[CONF_DEVICE_ID] = "not_zha_device"
            else:
                await self.async_set_unique_id(DOMAIN)
                self._abort_if_unique_id_mismatch()
                return self.async_update_reload_and_abort(
                    entry,
                    data_updates={CONF_DEVICE_ID: device_id},
                )

        return self.async_show_form(
            step_id="reconfigure",
            data_schema=_device_schema(current_device_id),
            errors=errors,
        )
