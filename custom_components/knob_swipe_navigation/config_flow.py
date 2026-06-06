"""Config flow for Knob Swipe Navigation."""

from __future__ import annotations

from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import CONF_DEVICE_ID
from homeassistant.helpers import selector

from .const import (
    CONF_COOLDOWN_MS,
    CONF_DASHBOARD_PATH,
    CONF_NAVIGATION_ENABLED,
    CONF_OVERLAY_ENABLED,
    CONF_OVERLAY_TIMEOUT_MS,
    CONF_REQUIRE_QUERY_PARAM,
    CONF_WRAP_ENABLED,
    DEFAULT_NAME,
    DOMAIN,
    MAX_COOLDOWN_MS,
    MAX_OVERLAY_TIMEOUT_MS,
    MIN_COOLDOWN_MS,
    MIN_OVERLAY_TIMEOUT_MS,
)
from .helpers import (
    configured_device_id,
    is_zha_device,
    settings_from_entry,
    settings_from_mapping,
    settings_to_options,
)
from .models import KnobSwipeNavigationConfigEntry, KnobSwipeNavigationSettings


def _settings_schema(settings: KnobSwipeNavigationSettings) -> dict[Any, Any]:
    """Return the navigation settings schema."""
    return {
        vol.Required(CONF_DASHBOARD_PATH, default=settings.dashboard_path): str,
        vol.Required(
            CONF_NAVIGATION_ENABLED, default=settings.navigation_enabled
        ): bool,
        vol.Required(CONF_OVERLAY_ENABLED, default=settings.overlay_enabled): bool,
        vol.Required(
            CONF_OVERLAY_TIMEOUT_MS, default=settings.overlay_timeout_ms
        ): vol.All(
            vol.Coerce(int),
            vol.Range(min=MIN_OVERLAY_TIMEOUT_MS, max=MAX_OVERLAY_TIMEOUT_MS),
        ),
        vol.Required(CONF_COOLDOWN_MS, default=settings.cooldown_ms): vol.All(
            vol.Coerce(int),
            vol.Range(min=MIN_COOLDOWN_MS, max=MAX_COOLDOWN_MS),
        ),
        vol.Required(CONF_WRAP_ENABLED, default=settings.wrap_enabled): bool,
        vol.Optional(
            CONF_REQUIRE_QUERY_PARAM, default=settings.require_query_param
        ): str,
    }


def _entry_schema(
    settings: KnobSwipeNavigationSettings, default_device_id: str | None = None
) -> vol.Schema:
    """Return the setup/reconfigure schema."""
    device_key = (
        vol.Required(CONF_DEVICE_ID, default=default_device_id)
        if default_device_id
        else vol.Required(CONF_DEVICE_ID)
    )
    return vol.Schema(
        {
            device_key: selector.DeviceSelector({"filter": {"integration": "zha"}}),
            **_settings_schema(settings),
        }
    )


def _options_schema(settings: KnobSwipeNavigationSettings) -> vol.Schema:
    """Return the options schema."""
    return vol.Schema(_settings_schema(settings))


class KnobSwipeNavigationConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Knob Swipe Navigation."""

    VERSION = 1
    MINOR_VERSION = 3

    @staticmethod
    def async_get_options_flow(
        config_entry: KnobSwipeNavigationConfigEntry,
    ) -> config_entries.OptionsFlow:
        """Create the options flow."""
        return KnobSwipeNavigationOptionsFlow()

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
                settings = settings_from_mapping(user_input)
                return self.async_create_entry(
                    title=DEFAULT_NAME,
                    data={CONF_DEVICE_ID: device_id},
                    options=settings_to_options(settings),
                )

        return self.async_show_form(
            step_id="user",
            data_schema=_entry_schema(settings_from_mapping({})),
            errors=errors,
        )

    async def async_step_reconfigure(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.ConfigFlowResult:
        """Handle reconfiguration."""
        errors: dict[str, str] = {}
        entry = self._get_reconfigure_entry()
        current_device_id = configured_device_id(entry)
        current_settings = settings_from_entry(entry)

        if user_input is not None:
            device_id = user_input[CONF_DEVICE_ID]
            if not is_zha_device(self.hass, device_id):
                errors[CONF_DEVICE_ID] = "not_zha_device"
            else:
                await self.async_set_unique_id(DOMAIN)
                self._abort_if_unique_id_mismatch()
                self.hass.config_entries.async_update_entry(
                    entry,
                    options=settings_to_options(settings_from_mapping(user_input)),
                )
                return self.async_update_reload_and_abort(
                    entry,
                    data_updates={CONF_DEVICE_ID: device_id},
                )

        return self.async_show_form(
            step_id="reconfigure",
            data_schema=_entry_schema(current_settings, current_device_id),
            errors=errors,
        )


class KnobSwipeNavigationOptionsFlow(config_entries.OptionsFlowWithReload):
    """Handle options for Knob Swipe Navigation."""

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.ConfigFlowResult:
        """Manage options."""
        if user_input is not None:
            return self.async_create_entry(
                data=settings_to_options(settings_from_mapping(user_input))
            )

        return self.async_show_form(
            step_id="init",
            data_schema=_options_schema(settings_from_entry(self.config_entry)),
        )
