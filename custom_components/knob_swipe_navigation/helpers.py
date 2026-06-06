"""Shared helpers for Knob Swipe Navigation."""

from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_DEVICE_ID
from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr

ZHA_DOMAIN = "zha"


def configured_device_id(entry: ConfigEntry) -> str | None:
    """Return the configured knob device id from a config entry."""
    return entry.data.get(CONF_DEVICE_ID) or entry.options.get(CONF_DEVICE_ID)


def is_zha_device(hass: HomeAssistant, device_id: str) -> bool:
    """Return true if the selected device belongs to ZHA."""
    device_registry = dr.async_get(hass)
    device = device_registry.async_get(device_id)
    if device is None:
        return False

    entries_by_id = {
        entry.entry_id: entry for entry in hass.config_entries.async_entries()
    }
    return any(
        entries_by_id[entry_id].domain == ZHA_DOMAIN
        for entry_id in device.config_entries
        if entry_id in entries_by_id
    )


def device_config_entry_domains(
    hass: HomeAssistant, device: dr.DeviceEntry | None
) -> list[str]:
    """Return sorted config entry domains for a device."""
    if device is None:
        return []

    entries_by_id = {
        entry.entry_id: entry for entry in hass.config_entries.async_entries()
    }
    return sorted(
        {
            entries_by_id[entry_id].domain
            for entry_id in device.config_entries
            if entry_id in entries_by_id
        }
    )
