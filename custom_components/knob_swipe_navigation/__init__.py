"""Local Knob Swipe Navigation integration."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

import voluptuous as vol

from homeassistant.components import frontend, websocket_api
from homeassistant.components.http import StaticPathConfig
from homeassistant.components.websocket_api import ActiveConnection
from homeassistant.const import CONF_DEVICE_ID
from homeassistant.core import HomeAssistant, callback
from homeassistant.exceptions import ConfigEntryError
from homeassistant.helpers import device_registry as dr, issue_registry as ir

from .const import (
    DEFAULT_NAME,
    DOMAIN,
    FRONTEND_MODULE_URL,
    FRONTEND_URL_PATH,
    REPAIR_ISSUE_DEVICE_NOT_ZHA,
    WS_TYPE_CONFIG,
)
from .helpers import configured_device_id, is_zha_device
from .models import KnobSwipeNavigationConfigEntry, KnobSwipeNavigationRuntimeData

_LOGGER = logging.getLogger(__name__)


async def async_setup(hass: HomeAssistant, config: dict[str, Any]) -> bool:
    """Set up the integration."""
    websocket_api.async_register_command(hass, websocket_config)
    return True


async def async_setup_entry(
    hass: HomeAssistant, entry: KnobSwipeNavigationConfigEntry
) -> bool:
    """Set up a config entry."""
    device_id = configured_device_id(entry)
    if not device_id or not is_zha_device(hass, device_id):
        ir.async_create_issue(
            hass,
            DOMAIN,
            REPAIR_ISSUE_DEVICE_NOT_ZHA,
            is_fixable=False,
            issue_domain=DOMAIN,
            severity=ir.IssueSeverity.ERROR,
            translation_key=REPAIR_ISSUE_DEVICE_NOT_ZHA,
        )
        raise ConfigEntryError(
            translation_domain=DOMAIN,
            translation_key=REPAIR_ISSUE_DEVICE_NOT_ZHA,
        )

    ir.async_delete_issue(hass, DOMAIN, REPAIR_ISSUE_DEVICE_NOT_ZHA)
    entry.runtime_data = KnobSwipeNavigationRuntimeData(device_id=device_id)
    _async_register_service_device(hass, entry)

    www_path = Path(__file__).parent / "www"
    try:
        await hass.http.async_register_static_paths(
            [StaticPathConfig(FRONTEND_URL_PATH, str(www_path), True)]
        )
    except (RuntimeError, ValueError):
        _LOGGER.debug("Frontend static path already registered")
    frontend.add_extra_js_url(hass, FRONTEND_MODULE_URL, es5=False)

    return True


async def async_unload_entry(
    hass: HomeAssistant, entry: KnobSwipeNavigationConfigEntry
) -> bool:
    """Unload a config entry."""
    frontend.remove_extra_js_url(hass, FRONTEND_MODULE_URL, es5=False)
    return True


async def async_migrate_entry(
    hass: HomeAssistant, entry: KnobSwipeNavigationConfigEntry
) -> bool:
    """Migrate old config entries."""
    if entry.version > 1:
        return False

    if entry.minor_version < 2:
        data = dict(entry.data)
        if device_id := configured_device_id(entry):
            data[CONF_DEVICE_ID] = device_id
        hass.config_entries.async_update_entry(
            entry,
            data=data,
            options={},
            version=1,
            minor_version=2,
        )

    return True


async def async_remove_config_entry_device(
    hass: HomeAssistant,
    config_entry: KnobSwipeNavigationConfigEntry,
    device_entry: dr.DeviceEntry,
) -> bool:
    """Allow removal of the integration's service device."""
    return (DOMAIN, config_entry.entry_id) in device_entry.identifiers


def _async_register_service_device(
    hass: HomeAssistant, entry: KnobSwipeNavigationConfigEntry
) -> None:
    """Register the frontend navigation service device."""
    device_entry = dr.async_get(hass).async_get_or_create(
        config_entry_id=entry.entry_id,
        entry_type=dr.DeviceEntryType.SERVICE,
        identifiers={(DOMAIN, entry.entry_id)},
        manufacturer="moryoav",
        model="Frontend dashboard navigation bridge",
        translation_key="navigation_bridge",
    )
    entry.runtime_data.service_device_id = device_entry.id


def _configured_device_id(hass: HomeAssistant) -> str | None:
    """Return the configured knob device id."""
    entries = hass.config_entries.async_entries(DOMAIN)
    if not entries:
        return None

    for entry in entries:
        runtime_data = getattr(entry, "runtime_data", None)
        if runtime_data and runtime_data.device_id:
            return runtime_data.device_id
        if device_id := configured_device_id(entry):
            return device_id

    return None


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
