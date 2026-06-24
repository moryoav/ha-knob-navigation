"""Shared helpers for Knob Swipe Navigation."""

from __future__ import annotations

from typing import Any
from urllib.parse import urlparse

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_DEVICE_ID
from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr

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
    DEFAULT_COOLDOWN_MS,
    DEFAULT_DASHBOARD_PATH,
    DEFAULT_IDLE_RETURN_ENABLED,
    DEFAULT_IDLE_RETURN_TIMEOUT_SECONDS,
    DEFAULT_NAVIGATION_ENABLED,
    DEFAULT_OVERLAY_ENABLED,
    DEFAULT_OVERLAY_TIMEOUT_MS,
    DEFAULT_REQUIRE_QUERY_PARAM,
    DEFAULT_WRAP_ENABLED,
    MAX_COOLDOWN_MS,
    MAX_IDLE_RETURN_TIMEOUT_SECONDS,
    MAX_OVERLAY_TIMEOUT_MS,
    MIN_COOLDOWN_MS,
    MIN_IDLE_RETURN_TIMEOUT_SECONDS,
    MIN_OVERLAY_TIMEOUT_MS,
    SIGNAL_NAVIGATION_RESULT,
    SIGNAL_ROTATION,
)
from .models import KnobSwipeNavigationConfigEntry, KnobSwipeNavigationSettings
from .profiles import RotationCapabilityProfile, capability_profile_from_id

ZHA_DOMAIN = "zha"


def configured_device_id(entry: ConfigEntry) -> str | None:
    """Return the configured knob device id from a config entry."""
    return entry.data.get(CONF_DEVICE_ID) or entry.options.get(CONF_DEVICE_ID)


def configured_capability_profile_id(entry: ConfigEntry) -> str | None:
    """Return the stored capability profile id from a config entry."""
    return entry.data.get(CONF_CAPABILITY_PROFILE) or entry.options.get(
        CONF_CAPABILITY_PROFILE
    )


def capability_profile_from_entry(
    entry: ConfigEntry,
) -> RotationCapabilityProfile:
    """Return the capability profile stored for a config entry."""
    return capability_profile_from_id(configured_capability_profile_id(entry))


def device_unique_id(hass: HomeAssistant, device_id: str) -> str:
    """Return the config-entry unique id for a ZHA device."""
    device = dr.async_get(hass).async_get(device_id)
    if device is not None:
        zha_identifiers = sorted(
            str(identifier)
            for domain, identifier in device.identifiers
            if domain == ZHA_DOMAIN
        )
        if zha_identifiers:
            return f"{ZHA_DOMAIN}:{zha_identifiers[0]}"

    return f"device:{device_id}"


def device_name(hass: HomeAssistant, device_id: str) -> str | None:
    """Return a friendly device name for a Home Assistant device id."""
    device = dr.async_get(hass).async_get(device_id)
    if device is None:
        return None
    return device.name_by_user or device.name


def normalize_dashboard_path(value: Any) -> str:
    """Normalize a dashboard URL/path to the first URL path segment."""
    if not isinstance(value, str):
        return DEFAULT_DASHBOARD_PATH

    raw_value = value.strip()
    if not raw_value:
        return DEFAULT_DASHBOARD_PATH

    parsed = urlparse(raw_value)
    path = parsed.path if parsed.scheme or parsed.netloc else raw_value
    path = path.split("?", 1)[0].split("#", 1)[0].strip("/")
    return path.split("/", 1)[0] or DEFAULT_DASHBOARD_PATH


def _coerce_bool(value: Any, default: bool) -> bool:
    """Return a bool from stored options."""
    if isinstance(value, bool):
        return value
    return default


def _coerce_int(value: Any, default: int, minimum: int, maximum: int) -> int:
    """Return a clamped integer from stored options."""
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        return default
    return max(minimum, min(maximum, parsed))


def settings_from_mapping(options: dict[str, Any]) -> KnobSwipeNavigationSettings:
    """Return normalized navigation settings from an options mapping."""
    query_param = options.get(CONF_REQUIRE_QUERY_PARAM, DEFAULT_REQUIRE_QUERY_PARAM)
    if not isinstance(query_param, str):
        query_param = DEFAULT_REQUIRE_QUERY_PARAM

    return KnobSwipeNavigationSettings(
        dashboard_path=normalize_dashboard_path(options.get(CONF_DASHBOARD_PATH)),
        navigation_enabled=_coerce_bool(
            options.get(CONF_NAVIGATION_ENABLED), DEFAULT_NAVIGATION_ENABLED
        ),
        overlay_enabled=_coerce_bool(
            options.get(CONF_OVERLAY_ENABLED), DEFAULT_OVERLAY_ENABLED
        ),
        overlay_timeout_ms=_coerce_int(
            options.get(CONF_OVERLAY_TIMEOUT_MS),
            DEFAULT_OVERLAY_TIMEOUT_MS,
            MIN_OVERLAY_TIMEOUT_MS,
            MAX_OVERLAY_TIMEOUT_MS,
        ),
        cooldown_ms=_coerce_int(
            options.get(CONF_COOLDOWN_MS),
            DEFAULT_COOLDOWN_MS,
            MIN_COOLDOWN_MS,
            MAX_COOLDOWN_MS,
        ),
        wrap_enabled=_coerce_bool(options.get(CONF_WRAP_ENABLED), DEFAULT_WRAP_ENABLED),
        require_query_param=query_param.strip(),
        idle_return_enabled=_coerce_bool(
            options.get(CONF_IDLE_RETURN_ENABLED), DEFAULT_IDLE_RETURN_ENABLED
        ),
        idle_return_timeout_seconds=_coerce_int(
            options.get(CONF_IDLE_RETURN_TIMEOUT_SECONDS),
            DEFAULT_IDLE_RETURN_TIMEOUT_SECONDS,
            MIN_IDLE_RETURN_TIMEOUT_SECONDS,
            MAX_IDLE_RETURN_TIMEOUT_SECONDS,
        ),
    )


def settings_from_entry(
    entry: KnobSwipeNavigationConfigEntry,
) -> KnobSwipeNavigationSettings:
    """Return normalized navigation settings from a config entry."""
    return settings_from_mapping(dict(entry.options))


def settings_to_options(settings: KnobSwipeNavigationSettings) -> dict[str, Any]:
    """Return config entry options from settings."""
    return {
        CONF_DASHBOARD_PATH: settings.dashboard_path,
        CONF_NAVIGATION_ENABLED: settings.navigation_enabled,
        CONF_OVERLAY_ENABLED: settings.overlay_enabled,
        CONF_OVERLAY_TIMEOUT_MS: settings.overlay_timeout_ms,
        CONF_COOLDOWN_MS: settings.cooldown_ms,
        CONF_WRAP_ENABLED: settings.wrap_enabled,
        CONF_REQUIRE_QUERY_PARAM: settings.require_query_param,
        CONF_IDLE_RETURN_ENABLED: settings.idle_return_enabled,
        CONF_IDLE_RETURN_TIMEOUT_SECONDS: settings.idle_return_timeout_seconds,
    }


def update_runtime_settings(entry: KnobSwipeNavigationConfigEntry) -> None:
    """Refresh runtime settings from config entry options."""
    entry.runtime_data.settings = settings_from_entry(entry)


def rotation_signal(entry_id: str) -> str:
    """Return the rotation dispatcher signal for a config entry."""
    return f"{SIGNAL_ROTATION}_{entry_id}"


def navigation_result_signal(entry_id: str) -> str:
    """Return the navigation-result dispatcher signal for a config entry."""
    return f"{SIGNAL_NAVIGATION_RESULT}_{entry_id}"


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
