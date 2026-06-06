"""Diagnostics support for Knob Swipe Navigation."""

from __future__ import annotations

from typing import Any

from homeassistant.components.diagnostics import async_redact_data
from homeassistant.const import CONF_DEVICE_ID
from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr

from .const import DOMAIN, FRONTEND_MODULE_URL
from .helpers import configured_device_id, device_config_entry_domains, settings_from_entry
from .models import KnobSwipeNavigationConfigEntry

TO_REDACT = {CONF_DEVICE_ID}


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant, entry: KnobSwipeNavigationConfigEntry
) -> dict[str, Any]:
    """Return diagnostics for a config entry."""
    device_id = configured_device_id(entry)
    device = dr.async_get(hass).async_get(device_id) if device_id else None
    runtime_data = getattr(entry, "runtime_data", None)
    settings = runtime_data.settings if runtime_data else settings_from_entry(entry)

    return {
        "entry": {
            "entry_id": entry.entry_id,
            "domain": DOMAIN,
            "title": entry.title,
            "version": entry.version,
            "minor_version": entry.minor_version,
            "data": async_redact_data(dict(entry.data), TO_REDACT),
            "options": async_redact_data(dict(entry.options), TO_REDACT),
        },
        "frontend": {
            "module_url": FRONTEND_MODULE_URL,
        },
        "settings": {
            "dashboard_path": settings.dashboard_path,
            "navigation_enabled": settings.navigation_enabled,
            "overlay_enabled": settings.overlay_enabled,
            "overlay_timeout_ms": settings.overlay_timeout_ms,
            "cooldown_ms": settings.cooldown_ms,
            "wrap_enabled": settings.wrap_enabled,
            "require_query_param": settings.require_query_param,
        },
        "entities": dict(runtime_data.entity_ids) if runtime_data else {},
        "selected_device": {
            "configured": device_id is not None,
            "found": device is not None,
            "name": device.name_by_user or device.name if device else None,
            "manufacturer": device.manufacturer if device else None,
            "model": device.model if device else None,
            "config_entry_domains": device_config_entry_domains(hass, device),
        },
    }
