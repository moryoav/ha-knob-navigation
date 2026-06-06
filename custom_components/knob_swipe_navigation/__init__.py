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
from homeassistant.helpers.dispatcher import (
    async_dispatcher_connect,
    async_dispatcher_send,
)
from homeassistant.util import dt as dt_util

from .const import (
    CONF_CAPABILITY_PROFILE,
    DEFAULT_CAPABILITY_PROFILE,
    DOMAIN,
    ENTITY_COOLDOWN_MS,
    ENTITY_LAST_NAVIGATION_RESULT,
    ENTITY_LAST_ROTATION,
    ENTITY_NAVIGATION_ENABLED,
    ENTITY_OVERLAY_ENABLED,
    ENTITY_OVERLAY_TIMEOUT_MS,
    ENTITY_ROTATION,
    ENTITY_WRAP_ENABLED,
    FRONTEND_MODULE_URL,
    FRONTEND_URL_PATH,
    REPAIR_ISSUE_DEVICE_NOT_ZHA,
    WS_TYPE_CONFIG,
    WS_TYPE_NAVIGATION_RESULT,
    WS_TYPE_SUBSCRIBE_ROTATIONS,
)
from .helpers import (
    capability_profile_from_entry,
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
from .profiles import profile_to_frontend, rotation_direction, rotation_value

_LOGGER = logging.getLogger(__name__)

CONFIG_SCHEMA = cv.config_entry_only_config_schema(DOMAIN)
DATA_FRONTEND_REGISTERED = "frontend_registered"
DATA_LOADED_ENTRY_IDS = "loaded_entry_ids"
PLATFORMS = [
    Platform.SWITCH,
    Platform.NUMBER,
    Platform.EVENT,
    Platform.SENSOR,
]


async def async_setup(hass: HomeAssistant, config: dict[str, Any]) -> bool:
    """Set up the integration."""
    websocket_api.async_register_command(hass, websocket_config)
    websocket_api.async_register_command(hass, websocket_subscribe_rotations)
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
            _repair_issue_id(entry),
            is_fixable=False,
            issue_domain=DOMAIN,
            severity=ir.IssueSeverity.ERROR,
            translation_key=REPAIR_ISSUE_DEVICE_NOT_ZHA,
        )
        raise ConfigEntryError(
            translation_domain=DOMAIN,
            translation_key=REPAIR_ISSUE_DEVICE_NOT_ZHA,
        )

    ir.async_delete_issue(hass, DOMAIN, _repair_issue_id(entry))
    entry.runtime_data = KnobSwipeNavigationRuntimeData(
        device_id=device_id,
        settings=settings_from_entry(entry),
        capability_profile=capability_profile_from_entry(entry),
    )
    _async_register_service_device(hass, entry)
    entry.async_on_unload(_async_register_profile_event_listener(hass, entry))

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    await _async_register_frontend(hass, entry)

    return True


async def _async_register_frontend(
    hass: HomeAssistant, entry: KnobSwipeNavigationConfigEntry
) -> None:
    """Register the frontend module once for all loaded entries."""
    data = hass.data.setdefault(DOMAIN, {})
    data.setdefault(DATA_LOADED_ENTRY_IDS, set()).add(entry.entry_id)
    if data.get(DATA_FRONTEND_REGISTERED):
        return

    www_path = Path(__file__).parent / "www"
    try:
        await hass.http.async_register_static_paths(
            [StaticPathConfig(FRONTEND_URL_PATH, str(www_path), True)]
        )
    except (RuntimeError, ValueError):
        _LOGGER.debug("Frontend static path already registered")
    frontend.add_extra_js_url(hass, FRONTEND_MODULE_URL, es5=False)
    data[DATA_FRONTEND_REGISTERED] = True


async def async_unload_entry(
    hass: HomeAssistant, entry: KnobSwipeNavigationConfigEntry
) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        data = hass.data.get(DOMAIN, {})
        loaded_entry_ids = data.get(DATA_LOADED_ENTRY_IDS, set())
        loaded_entry_ids.discard(entry.entry_id)
        if not loaded_entry_ids and data.get(DATA_FRONTEND_REGISTERED):
            frontend.remove_extra_js_url(hass, FRONTEND_MODULE_URL, es5=False)
            data[DATA_FRONTEND_REGISTERED] = False
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

    if entry.minor_version < 4:
        data.setdefault(CONF_CAPABILITY_PROFILE, DEFAULT_CAPABILITY_PROFILE)

    hass.config_entries.async_update_entry(
        entry,
        data=data,
        options=options,
        version=1,
        minor_version=4,
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


def _repair_issue_id(entry: KnobSwipeNavigationConfigEntry) -> str:
    """Return the per-entry repair issue id."""
    return f"{REPAIR_ISSUE_DEVICE_NOT_ZHA}_{entry.entry_id}"


def _configured_entries(hass: HomeAssistant) -> list[KnobSwipeNavigationConfigEntry]:
    """Return configured entries with a selected device."""
    return [
        entry
        for entry in hass.config_entries.async_entries(DOMAIN)
        if getattr(entry, "runtime_data", None) is not None
        or configured_device_id(entry)
    ]


def _configured_entry_from_message(
    hass: HomeAssistant, msg: dict[str, Any]
) -> KnobSwipeNavigationConfigEntry | None:
    """Return the config entry targeted by a websocket message."""
    entries = _configured_entries(hass)
    entry_id = msg.get("entry_id")
    if entry_id:
        return next((entry for entry in entries if entry.entry_id == entry_id), None)

    device_id = msg.get("device_id")
    if device_id:
        return next(
            (
                entry
                for entry in entries
                if getattr(entry, "runtime_data", None)
                and entry.runtime_data.device_id == device_id
            ),
            None,
        )

    return entries[0] if len(entries) == 1 else None


def _async_register_profile_event_listener(
    hass: HomeAssistant, entry: KnobSwipeNavigationConfigEntry
) -> Callable[[], None]:
    """Register the backend listener for selected knob rotation events."""
    profile = entry.runtime_data.capability_profile

    @callback
    def _handle_zha_event(event: Event) -> None:
        data = event.data
        if data.get("device_id") != entry.runtime_data.device_id:
            return
        if data.get("command") != profile.command:
            return

        value = rotation_value(profile, data)
        direction = rotation_direction(profile, value)
        if direction is None or value is None:
            return

        runtime_data = entry.runtime_data
        runtime_data.last_rotation = direction
        runtime_data.last_rotation_value = value
        runtime_data.last_rotation_value_attribute = profile.value_attribute
        runtime_data.last_rotation_capability_profile = profile.profile_id
        runtime_data.last_rotation_at = dt_util.utcnow()
        async_dispatcher_send(
            hass,
            rotation_signal(entry.entry_id),
            RotationEventData(
                direction=direction,
                value=value,
                value_attribute=profile.value_attribute,
                capability_profile=profile.profile_id,
                event_data=dict(data),
            ),
        )

    return hass.bus.async_listen(profile.event_type, _handle_zha_event)


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


def _entry_payload(entry: KnobSwipeNavigationConfigEntry) -> dict[str, Any]:
    """Return a frontend configuration payload for one config entry."""
    runtime_data = getattr(entry, "runtime_data", None)
    device_id = runtime_data.device_id if runtime_data else configured_device_id(entry)
    settings = runtime_data.settings if runtime_data else settings_from_entry(entry)
    profile = (
        runtime_data.capability_profile
        if runtime_data
        else capability_profile_from_entry(entry)
    )

    return {
        "entry_id": entry.entry_id,
        "unique_id": entry.unique_id,
        "title": entry.title,
        "device_id": device_id,
        "capability_profile": profile_to_frontend(profile),
        "dashboard_path": settings.dashboard_path,
        "navigation_enabled": settings.navigation_enabled,
        "overlay_enabled": settings.overlay_enabled,
        "overlay_timeout_ms": settings.overlay_timeout_ms,
        "cooldown_ms": settings.cooldown_ms,
        "wrap_enabled": settings.wrap_enabled,
        "require_query_param": settings.require_query_param,
        "entities": _entity_ids(entry) if runtime_data else {},
    }


def _rotation_payload(
    entry: KnobSwipeNavigationConfigEntry, data: RotationEventData
) -> dict[str, Any]:
    """Return a frontend rotation event payload."""
    payload = {
        "entry_id": entry.entry_id,
        "device_id": entry.runtime_data.device_id,
        "direction": data.direction,
        "value": data.value,
        "value_attribute": data.value_attribute,
        "capability_profile": data.capability_profile,
    }
    payload[data.value_attribute] = data.value
    return payload


@callback
@websocket_api.websocket_command({vol.Required("type"): WS_TYPE_CONFIG})
def websocket_config(
    hass: HomeAssistant,
    connection: ActiveConnection,
    msg: dict[str, Any],
) -> None:
    """Return frontend configuration."""
    entries = _configured_entries(hass)
    if not entries:
        connection.send_error(
            msg["id"], "not_configured", "Knob Swipe Navigation is not configured"
        )
        return

    connection.send_result(
        msg["id"],
        {
            "rotation_subscription_type": WS_TYPE_SUBSCRIBE_ROTATIONS,
            "navigation_result_type": WS_TYPE_NAVIGATION_RESULT,
            "entries": [_entry_payload(entry) for entry in entries],
        },
    )


@callback
@websocket_api.websocket_command({vol.Required("type"): WS_TYPE_SUBSCRIBE_ROTATIONS})
def websocket_subscribe_rotations(
    hass: HomeAssistant,
    connection: ActiveConnection,
    msg: dict[str, Any],
) -> None:
    """Subscribe a frontend browser to selected-knob rotation events."""
    entries = [
        entry
        for entry in _configured_entries(hass)
        if getattr(entry, "runtime_data", None) is not None
    ]
    if not entries:
        connection.send_error(
            msg["id"], "not_configured", "Knob Swipe Navigation is not configured"
        )
        return

    unsubscribers: list[Callable[[], None]] = []
    for entry in entries:

        @callback
        def _forward_rotation(
            data: RotationEventData, *, entry: KnobSwipeNavigationConfigEntry = entry
        ) -> None:
            connection.send_message(
                websocket_api.event_message(
                    msg["id"],
                    _rotation_payload(entry, data),
                )
            )

        unsubscribers.append(
            async_dispatcher_connect(
                hass,
                rotation_signal(entry.entry_id),
                _forward_rotation,
            )
        )

    def _unsubscribe() -> None:
        for unsubscribe in unsubscribers:
            unsubscribe()

    connection.subscriptions[msg["id"]] = _unsubscribe
    connection.send_result(msg["id"])


@callback
@websocket_api.websocket_command(
    {
        vol.Required("type"): WS_TYPE_NAVIGATION_RESULT,
        vol.Optional("entry_id"): str,
        vol.Optional("device_id"): str,
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
    entry = _configured_entry_from_message(hass, msg)
    if not entry:
        connection.send_error(
            msg["id"],
            "entry_not_found",
            "Knob Swipe Navigation entry was not found",
        )
        return
    runtime_data = getattr(entry, "runtime_data", None)
    if runtime_data is None:
        connection.send_error(
            msg["id"],
            "entry_not_loaded",
            "Knob Swipe Navigation entry is not loaded",
        )
        return

    result = msg["result"].strip() or "unknown"
    details = {
        key: value
        for key, value in msg.items()
        if key not in {"id", "type", "entry_id", "device_id", "result"}
        and value is not None
    }
    runtime_data.last_navigation_result = result
    runtime_data.last_navigation_details = details
    runtime_data.last_navigation_result_at = dt_util.utcnow()
    async_dispatcher_send(
        hass,
        navigation_result_signal(entry.entry_id),
        NavigationResultData(result=result, details=details),
    )
    connection.send_result(msg["id"], {"ok": True})
