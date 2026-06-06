"""Config flow for Knob Swipe Navigation."""

from __future__ import annotations

from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import CONF_DEVICE_ID
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers import device_registry as dr, selector

from .const import DEFAULT_NAME, DOMAIN


def _is_zha_device(hass: HomeAssistant, device_id: str) -> bool:
    """Return true if the selected device belongs to ZHA."""
    device_registry = dr.async_get(hass)
    device = device_registry.async_get(device_id)
    if device is None:
        return False

    entries_by_id = {
        entry.entry_id: entry for entry in hass.config_entries.async_entries()
    }
    return any(
        entries_by_id[entry_id].domain == "zha"
        for entry_id in device.config_entries
        if entry_id in entries_by_id
    )


def _device_schema(default_device_id: str | None = None) -> vol.Schema:
    """Return the device selection schema."""
    key = (
        vol.Required(CONF_DEVICE_ID, default=default_device_id)
        if default_device_id
        else vol.Required(CONF_DEVICE_ID)
    )
    return vol.Schema({key: selector.DeviceSelector()})


class KnobSwipeNavigationConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Knob Swipe Navigation."""

    VERSION = 1

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> config_entries.OptionsFlow:
        """Create the options flow."""
        return KnobSwipeNavigationOptionsFlow(config_entry)

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.ConfigFlowResult:
        """Handle the initial setup step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            device_id = user_input[CONF_DEVICE_ID]
            if not _is_zha_device(self.hass, device_id):
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


class KnobSwipeNavigationOptionsFlow(config_entries.OptionsFlow):
    """Handle Knob Swipe Navigation options."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        """Initialize options flow."""
        self._config_entry = config_entry

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.ConfigFlowResult:
        """Manage options."""
        errors: dict[str, str] = {}
        current_device_id = self._config_entry.options.get(
            CONF_DEVICE_ID, self._config_entry.data.get(CONF_DEVICE_ID)
        )

        if user_input is not None:
            device_id = user_input[CONF_DEVICE_ID]
            if not _is_zha_device(self.hass, device_id):
                errors[CONF_DEVICE_ID] = "not_zha_device"
            else:
                return self.async_create_entry(
                    title="",
                    data={CONF_DEVICE_ID: device_id},
                )

        return self.async_show_form(
            step_id="init",
            data_schema=_device_schema(current_device_id),
            errors=errors,
        )
