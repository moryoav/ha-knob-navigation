"""Local Knob Swipe Navigation integration."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, Callable

import voluptuous as vol

from homeassistant.components import frontend, websocket_api
from homeassistant.components.http import StaticPathConfig
from homeassistant.components.websocket_api import ActiveConnection
from homeassistant.const import CONF_DEVICE_ID, Platform
from homeassistant.core import Event, HomeAssistant, callback
from homeassistant.exceptions import ConfigEntryError
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers import device_registry as dr, issue_registry as ir
from homeassistant.helpers.dispatcher import async_dispatcher_send
from homeassistant.util import dt as dt_util

from .const import (
    COMMAND_ROTATE_TYPE,
    DOMAIN,
    ENTITY_COOLDOWN_MS,
    ENTITY_LAST_NAVIGATION_RESULT,
    ENTITY_LAST_ROTATION,
    ENTITY_NAVIGATION_ENABLED,
    ENTITY_OVERLAY_ENABLED,
    ENTITY_OVERLAY_TIMEOUT_MS,
    ENTITY_ROTATION,
    ENTITY_WRAP_ENABLED,
    EVENT_ZHA,
    FRONTEND_MODULE_URL,
    FRONTEND_URL_PATH,
    REPAIR_ISSUE_DEVICE_NOT_ZHA,
    ROTATION_NEXT,
    ROTATION_PREVIOUS,
    WS_TYPE_CONFIG,
    WS_TYPE_NAVIGATION_RESULT,
)
from .helpers import (
    configured_device_id,
    is_zha_device,
    navigation_result_signal,
    rotation_signal,
    settings_from_entry,
    settings_to_options,
)
from .models import (
    KnobSwipeNavigationConfigEntry,
    KnobSwipeNavigationRuntimeData,
    NavigationResultData,
    RotationEventData,
)

_LOGGER = logging.getLogger(__name__)

CONFIG_SCHEMA = cv.config_entry_only_config_schema(DOMAIN)
PLATFORMS = [
    Platform.SWITCH,
    Platform.NUMBER,
    Platform.EVENT,
    Platform.SENSOR,
]


async def async_setup(hass: HomeAssistant, config: dict[str, Any]) -> bool:
    """Set up the integration."""
    websocket_api.async_register_command(hass, websocket_config)
    websocket_api.async_register_command(hass, websocket_navigation_result)
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
    entry.runtime_data = KnobSwipeNavigationRuntimeData(
        device_id=device_id,
        settings=settings_from_entry(entry),
    )
    _async_register_service_device(hass, entry)
    entry.async_on_unload(_async_register_zha_event_listener(hass, entry))

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

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
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        frontend.remove_extra_js_url(hass, FRONTEND_MODULE_URL, es5=False)
    return unload_ok


async def async_migrate_entry(
    hass: HomeAssistant, entry: KnobSwipeNavigationConfigEntry
) -> bool:
    """Migrate old config entries."""
    if entry.version > 1:
        return False

    data = dict(entry.data)
    options = dict(entry.options)

    if entry.minor_version < 2:
        if device_id := configured_device_id(entry):
            data[CONF_DEVICE_ID] = device_id

    if entry.minor_version < 3:
        options = settings_to_options(settings_from_entry(entry))

    hass.config_entries.async_update_entry(
        entry,
        data=data,
        options=options,
        version=1,
        minor_version=3,
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


def _configured_entry(hass: HomeAssistant) -> KnobSwipeNavigationConfigEntry | None:
    """Return the configured entry."""
    entries = hass.config_entries.async_entries(DOMAIN)
    if not entries:
        return None

    for entry in entries:
        runtime_data = getattr(entry, "runtime_data", None)
        if runtime_data and runtime_data.device_id:
            return entry
        if device_id := configured_device_id(entry):
            return entry

    return None


def _rotation_value(event_data: dict[str, Any]) -> int | None:
    """Return the rotate_type value from a ZHA event."""
    params = event_data.get("params")
    if isinstance(params, dict) and "rotate_type" in params:
        try:
            return int(params["rotate_type"])
        except (TypeError, ValueError):
            return None

    args = event_data.get("args")
    if isinstance(args, list) and args:
        try:
            return int(args[0])
        except (TypeError, ValueError):
            return None

    return None


def _rotation_direction(rotate_type: int | None) -> str | None:
    """Return the navigation direction for a rotate_type value."""
    if rotate_type == 0:
        return ROTATION_NEXT
    if rotate_type == 1:
        return ROTATION_PREVIOUS
    return None


def _async_register_zha_event_listener(
    hass: HomeAssistant, entry: KnobSwipeNavigationConfigEntry
) -> Callable[[], None]:
    """Register the backend listener for selected knob rotation events."""

    @callback
    def _handle_zha_event(event: Event) -> None:
        data = event.data
        if data.get("device_id") != entry.runtime_data.device_id:
            return
        if data.get("command") != COMMAND_ROTATE_TYPE:
            return

        rotate_type = _rotation_value(data)
        direction = _rotation_direction(rotate_type)
        if direction is None or rotate_type is None:
            return

        runtime_data = entry.runtime_data
        runtime_data.last_rotation = direction
        runtime_data.last_rotation_value = rotate_type
        runtime_data.last_rotation_at = dt_util.utcnow()
        async_dispatcher_send(
            hass,
            rotation_signal(entry.entry_id),
            RotationEventData(
                direction=direction,
                rotate_type=rotate_type,
                event_data=dict(data),
            ),
        )

    return hass.bus.async_listen(EVENT_ZHA, _handle_zha_event)


def _entity_ids(entry: KnobSwipeNavigationConfigEntry) -> dict[str, str]:
    """Return known frontend control entity IDs."""
    return {
        key: entity_id
        for key, entity_id in {
            ENTITY_NAVIGATION_ENABLED: entry.runtime_data.entity_ids.get(
                ENTITY_NAVIGATION_ENABLED
            ),
            ENTITY_OVERLAY_ENABLED: entry.runtime_data.entity_ids.get(
                ENTITY_OVERLAY_ENABLED
            ),
            ENTITY_WRAP_ENABLED: entry.runtime_data.entity_ids.get(ENTITY_WRAP_ENABLED),
            ENTITY_OVERLAY_TIMEOUT_MS: entry.runtime_data.entity_ids.get(
                ENTITY_OVERLAY_TIMEOUT_MS
            ),
            ENTITY_COOLDOWN_MS: entry.runtime_data.entity_ids.get(ENTITY_COOLDOWN_MS),
            ENTITY_ROTATION: entry.runtime_data.entity_ids.get(ENTITY_ROTATION),
            ENTITY_LAST_ROTATION: entry.runtime_data.entity_ids.get(
                ENTITY_LAST_ROTATION
            ),
            ENTITY_LAST_NAVIGATION_RESULT: entry.runtime_data.entity_ids.get(
                ENTITY_LAST_NAVIGATION_RESULT
            ),
        }.items()
        if entity_id
    }


@callback
@websocket_api.websocket_command({vol.Required("type"): WS_TYPE_CONFIG})
def websocket_config(
    hass: HomeAssistant,
    connection: ActiveConnection,
    msg: dict[str, Any],
) -> None:
    """Return frontend configuration."""
    entry = _configured_entry(hass)
    if not entry:
        connection.send_error(
            msg["id"], "not_configured", "Knob Swipe Navigation is not configured"
        )
        return

    runtime_data = getattr(entry, "runtime_data", None)
    device_id = runtime_data.device_id if runtime_data else configured_device_id(entry)
    settings = runtime_data.settings if runtime_data else settings_from_entry(entry)

    connection.send_result(
        msg["id"],
        {
            "device_id": device_id,
            "event_type": EVENT_ZHA,
            "command": COMMAND_ROTATE_TYPE,
            "rotate": {
                "0": ROTATION_NEXT,
                "1": ROTATION_PREVIOUS,
            },
            "dashboard_path": settings.dashboard_path,
            "navigation_enabled": settings.navigation_enabled,
            "overlay_enabled": settings.overlay_enabled,
            "overlay_timeout_ms": settings.overlay_timeout_ms,
            "cooldown_ms": settings.cooldown_ms,
            "wrap_enabled": settings.wrap_enabled,
            "require_query_param": settings.require_query_param,
            "entities": _entity_ids(entry) if runtime_data else {},
        },
    )


@callback
@websocket_api.websocket_command(
    {
        vol.Required("type"): WS_TYPE_NAVIGATION_RESULT,
        vol.Required("result"): str,
        vol.Optional("dashboard_path"): str,
        vol.Optional("direction"): str,
        vol.Optional("from_view"): str,
        vol.Optional("to_view"): str,
        vol.Optional("reason"): str,
    }
)
def websocket_navigation_result(
    hass: HomeAssistant,
    connection: ActiveConnection,
    msg: dict[str, Any],
) -> None:
    """Record frontend navigation results."""
    entry = _configured_entry(hass)
    if not entry:
        connection.send_error(
            msg["id"], "not_configured", "Knob Swipe Navigation is not configured"
        )
        return

    result = msg["result"].strip() or "unknown"
    details = {
        key: value
        for key, value in msg.items()
        if key not in {"id", "type", "result"} and value is not None
    }
    runtime_data = entry.runtime_data
    runtime_data.last_navigation_result = result
    runtime_data.last_navigation_details = details
    runtime_data.last_navigation_result_at = dt_util.utcnow()
    async_dispatcher_send(
        hass,
        navigation_result_signal(entry.entry_id),
        NavigationResultData(result=result, details=details),
    )
    connection.send_result(msg["id"], {"ok": True})
