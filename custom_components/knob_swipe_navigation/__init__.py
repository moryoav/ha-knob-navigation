"""Local Knob Swipe Navigation integration."""

from __future__ import annotations

from pathlib import Path
import logging
from typing import Any

import voluptuous as vol

from homeassistant.components import frontend, websocket_api
from homeassistant.components.websocket_api import ActiveConnection
from homeassistant.components.http import StaticPathConfig
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_DEVICE_ID
from homeassistant.core import HomeAssistant, callback

from .const import DOMAIN, FRONTEND_MODULE_URL, FRONTEND_URL_PATH, WS_TYPE_CONFIG

_LOGGER = logging.getLogger(__name__)

KnobSwipeNavigationConfigEntry = ConfigEntry


async def async_setup(hass: HomeAssistant, config: dict[str, Any]) -> bool:
    """Set up the integration."""
    hass.data.setdefault(DOMAIN, {})
    websocket_api.async_register_command(hass, websocket_config)
    return True


async def async_setup_entry(
    hass: HomeAssistant, entry: KnobSwipeNavigationConfigEntry
) -> bool:
    """Set up a config entry."""
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = entry

    www_path = Path(__file__).parent / "www"
    try:
        await hass.http.async_register_static_paths(
            [StaticPathConfig(FRONTEND_URL_PATH, str(www_path), True)]
        )
    except (RuntimeError, ValueError):
        _LOGGER.debug("Frontend static path already registered")
    frontend.add_extra_js_url(hass, FRONTEND_MODULE_URL, es5=False)

    entry.async_on_unload(entry.add_update_listener(_async_update_listener))
    return True


async def async_unload_entry(
    hass: HomeAssistant, entry: KnobSwipeNavigationConfigEntry
) -> bool:
    """Unload a config entry."""
    hass.data.get(DOMAIN, {}).pop(entry.entry_id, None)
    frontend.remove_extra_js_url(hass, FRONTEND_MODULE_URL, es5=False)
    return True


async def _async_update_listener(
    hass: HomeAssistant, entry: KnobSwipeNavigationConfigEntry
) -> None:
    """Reload the integration after options change."""
    await hass.config_entries.async_reload(entry.entry_id)


def _configured_device_id(hass: HomeAssistant) -> str | None:
    """Return the configured knob device id."""
    entries = hass.config_entries.async_entries(DOMAIN)
    if not entries:
        return None
    entry = entries[0]
    return entry.options.get(CONF_DEVICE_ID) or entry.data.get(CONF_DEVICE_ID)


@callback
@websocket_api.websocket_command({vol.Required("type"): WS_TYPE_CONFIG})
def websocket_config(
    hass: HomeAssistant,
    connection: ActiveConnection,
    msg: dict[str, Any],
) -> None:
    """Return frontend configuration."""
    device_id = _configured_device_id(hass)
    if not device_id:
        connection.send_error(
            msg["id"], "not_configured", "Knob Swipe Navigation is not configured"
        )
        return

    connection.send_result(
        msg["id"],
        {
            "device_id": device_id,
            "event_type": "zha_event",
            "command": "rotate_type",
            "rotate": {
                "0": "next",
                "1": "previous",
            },
        },
    )
