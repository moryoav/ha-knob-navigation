"""Config flow for Knob Swipe Navigation."""

from __future__ import annotations

from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import CONF_DEVICE_ID
from homeassistant.core import HomeAssistant
from homeassistant.helpers import selector

from .const import (
    CONF_CAPABILITY_PROFILE,
    CONF_COOLDOWN_MS,
    CONF_DASHBOARD_PATH,
    CONF_IDLE_RETURN_ENABLED,
    CONF_IDLE_RETURN_TIMEOUT_SECONDS,
    CONF_NAVIGATION_ENABLED,
    CONF_OVERLAY_ENABLED,
    CONF_OVERLAY_TIMEOUT_MS,
    CONF_REQUIRE_QUERY_PARAM,
    CONF_WRAP_ENABLED,
    DEFAULT_CAPABILITY_PROFILE,
    DEFAULT_NAME,
    DOMAIN,
    MAX_COOLDOWN_MS,
    MAX_IDLE_RETURN_TIMEOUT_SECONDS,
    MAX_OVERLAY_TIMEOUT_MS,
    MIN_COOLDOWN_MS,
    MIN_IDLE_RETURN_TIMEOUT_SECONDS,
    MIN_OVERLAY_TIMEOUT_MS,
)
from .helpers import (
    configured_device_id,
    device_name,
    device_unique_id,
    is_zha_device,
    settings_from_entry,
    settings_from_mapping,
    settings_to_options,
)
from .models import KnobSwipeNavigationConfigEntry, KnobSwipeNavigationSettings

FORM_DEVICE_ID = "ZHA knob device"
FORM_DASHBOARD_PATH = "Dashboard path"
FORM_NAVIGATION_ENABLED = "Enable knob navigation"
FORM_OVERLAY_ENABLED = "Show tab overlay"
FORM_OVERLAY_TIMEOUT_MS = "Overlay display time"
FORM_COOLDOWN_MS = "Rotation cooldown"
FORM_WRAP_ENABLED = "Wrap from last tab to first"
FORM_REQUIRE_QUERY_PARAM = "Required URL query parameter"
FORM_IDLE_RETURN_ENABLED = "Return to first tab after inactivity"
FORM_IDLE_RETURN_TIMEOUT_SECONDS = "Inactivity return delay"

_SETTINGS_FORM_TO_OPTION_KEYS = {
    FORM_DASHBOARD_PATH: CONF_DASHBOARD_PATH,
    FORM_NAVIGATION_ENABLED: CONF_NAVIGATION_ENABLED,
    FORM_OVERLAY_ENABLED: CONF_OVERLAY_ENABLED,
    FORM_OVERLAY_TIMEOUT_MS: CONF_OVERLAY_TIMEOUT_MS,
    FORM_COOLDOWN_MS: CONF_COOLDOWN_MS,
    FORM_WRAP_ENABLED: CONF_WRAP_ENABLED,
    FORM_REQUIRE_QUERY_PARAM: CONF_REQUIRE_QUERY_PARAM,
    FORM_IDLE_RETURN_ENABLED: CONF_IDLE_RETURN_ENABLED,
    FORM_IDLE_RETURN_TIMEOUT_SECONDS: CONF_IDLE_RETURN_TIMEOUT_SECONDS,
}


def _input_value(
    user_input: dict[str, Any], form_key: str, option_key: str
) -> Any:
    """Return a value submitted with either the friendly or stored key."""
    if form_key in user_input:
        return user_input[form_key]
    return user_input[option_key]


def _device_id_from_input(user_input: dict[str, Any]) -> str:
    """Return the selected device id from form input."""
    return str(_input_value(user_input, FORM_DEVICE_ID, CONF_DEVICE_ID))


def _settings_from_input(user_input: dict[str, Any]) -> KnobSwipeNavigationSettings:
    """Return settings from user input with friendly form keys."""
    return settings_from_mapping(
        {
            option_key: _input_value(user_input, form_key, option_key)
            for form_key, option_key in _SETTINGS_FORM_TO_OPTION_KEYS.items()
            if form_key in user_input or option_key in user_input
        }
    )


def _settings_schema(settings: KnobSwipeNavigationSettings) -> dict[Any, Any]:
    """Return the navigation settings schema."""
    return {
        vol.Required(FORM_DASHBOARD_PATH, default=settings.dashboard_path): str,
        vol.Required(
            FORM_NAVIGATION_ENABLED, default=settings.navigation_enabled
        ): bool,
        vol.Required(FORM_OVERLAY_ENABLED, default=settings.overlay_enabled): bool,
        vol.Required(
            FORM_OVERLAY_TIMEOUT_MS, default=settings.overlay_timeout_ms
        ): vol.All(
            vol.Coerce(int),
            vol.Range(min=MIN_OVERLAY_TIMEOUT_MS, max=MAX_OVERLAY_TIMEOUT_MS),
        ),
        vol.Required(FORM_COOLDOWN_MS, default=settings.cooldown_ms): vol.All(
            vol.Coerce(int),
            vol.Range(min=MIN_COOLDOWN_MS, max=MAX_COOLDOWN_MS),
        ),
        vol.Required(FORM_WRAP_ENABLED, default=settings.wrap_enabled): bool,
        vol.Optional(
            FORM_REQUIRE_QUERY_PARAM, default=settings.require_query_param
        ): str,
        vol.Required(
            FORM_IDLE_RETURN_ENABLED, default=settings.idle_return_enabled
        ): bool,
        vol.Required(
            FORM_IDLE_RETURN_TIMEOUT_SECONDS,
            default=settings.idle_return_timeout_seconds,
        ): vol.All(
            vol.Coerce(int),
            vol.Range(
                min=MIN_IDLE_RETURN_TIMEOUT_SECONDS,
                max=MAX_IDLE_RETURN_TIMEOUT_SECONDS,
            ),
        ),
    }


def _entry_schema(
    settings: KnobSwipeNavigationSettings, default_device_id: str | None = None
) -> vol.Schema:
    """Return the setup/reconfigure schema."""
    device_key = (
        vol.Required(FORM_DEVICE_ID, default=default_device_id)
        if default_device_id
        else vol.Required(FORM_DEVICE_ID)
    )
    return vol.Schema(
        {
            device_key: selector.DeviceSelector({"filter": {"integration": "zha"}}),
            **_settings_schema(settings),
        }
    )


def _entry_title(hass: HomeAssistant, device_id: str) -> str:
    """Return a readable config entry title for a selected knob."""
    name = device_name(hass, device_id)
    return f"{DEFAULT_NAME}: {name}" if name else DEFAULT_NAME


def _device_already_configured(
    hass: HomeAssistant,
    *,
    device_id: str,
    unique_id: str,
    current_entry_id: str | None = None,
) -> bool:
    """Return true if another entry already uses this physical knob."""
    return any(
        entry.entry_id != current_entry_id
        and (
            entry.unique_id == unique_id
            or configured_device_id(entry) == device_id
        )
        for entry in hass.config_entries.async_entries(DOMAIN)
    )


def _options_schema(settings: KnobSwipeNavigationSettings) -> vol.Schema:
    """Return the options schema."""
    return vol.Schema(_settings_schema(settings))


class KnobSwipeNavigationConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Knob Swipe Navigation."""

    VERSION = 1
    MINOR_VERSION = 5

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
            device_id = _device_id_from_input(user_input)
            if not is_zha_device(self.hass, device_id):
                errors[FORM_DEVICE_ID] = "not_zha_device"
            elif _device_already_configured(
                self.hass,
                device_id=device_id,
                unique_id=device_unique_id(self.hass, device_id),
            ):
                errors[FORM_DEVICE_ID] = "already_configured"
            else:
                unique_id = device_unique_id(self.hass, device_id)
                await self.async_set_unique_id(unique_id)
                self._abort_if_unique_id_configured()
                settings = _settings_from_input(user_input)
                return self.async_create_entry(
                    title=_entry_title(self.hass, device_id),
                    data={
                        CONF_DEVICE_ID: device_id,
                        CONF_CAPABILITY_PROFILE: DEFAULT_CAPABILITY_PROFILE,
                    },
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
            device_id = _device_id_from_input(user_input)
            if not is_zha_device(self.hass, device_id):
                errors[FORM_DEVICE_ID] = "not_zha_device"
            elif _device_already_configured(
                self.hass,
                device_id=device_id,
                unique_id=device_unique_id(self.hass, device_id),
                current_entry_id=entry.entry_id,
            ):
                errors[FORM_DEVICE_ID] = "already_configured"
            else:
                unique_id = device_unique_id(self.hass, device_id)
                data = dict(entry.data)
                data[CONF_DEVICE_ID] = device_id
                data[CONF_CAPABILITY_PROFILE] = DEFAULT_CAPABILITY_PROFILE
                self.hass.config_entries.async_update_entry(
                    entry,
                    data=data,
                    options=settings_to_options(_settings_from_input(user_input)),
                    title=_entry_title(self.hass, device_id),
                    unique_id=unique_id,
                )
                return self.async_update_reload_and_abort(entry)

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
                data=settings_to_options(_settings_from_input(user_input))
            )

        return self.async_show_form(
            step_id="init",
            data_schema=_options_schema(settings_from_entry(self.config_entry)),
        )
