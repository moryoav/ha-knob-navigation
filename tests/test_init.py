"""Tests for Knob Swipe Navigation setup."""

from __future__ import annotations

from unittest.mock import AsyncMock, Mock, patch

import pytest

from homeassistant.const import CONF_DEVICE_ID
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryError
from homeassistant.helpers import device_registry as dr, issue_registry as ir
from homeassistant.helpers.dispatcher import async_dispatcher_send
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.knob_swipe_navigation import (
    async_migrate_entry,
    async_setup_entry,
    async_unload_entry,
    websocket_config,
    websocket_navigation_result,
    websocket_subscribe_rotations,
)
from custom_components.knob_swipe_navigation.const import (
    CONF_CAPABILITY_PROFILE,
    CONF_COOLDOWN_MS,
    CONF_DASHBOARD_PATH,
    CONF_NAVIGATION_ENABLED,
    CONF_OVERLAY_TIMEOUT_MS,
    DEFAULT_CAPABILITY_PROFILE,
    DEFAULT_COOLDOWN_MS,
    DEFAULT_DASHBOARD_PATH,
    DOMAIN,
    ENTITY_NAVIGATION_ENABLED,
    EVENT_ZHA,
    REPAIR_ISSUE_DEVICE_NOT_ZHA,
    ROTATION_NEXT,
    ROTATION_PREVIOUS,
    WS_TYPE_CONFIG,
    WS_TYPE_NAVIGATION_RESULT,
    WS_TYPE_SUBSCRIBE_ROTATIONS,
)
from custom_components.knob_swipe_navigation.helpers import rotation_signal
from custom_components.knob_swipe_navigation.models import (
    KnobSwipeNavigationRuntimeData,
    KnobSwipeNavigationSettings,
    RotationEventData,
)


def _create_device(
    hass: HomeAssistant, *, domain: str = "zha", name: str = "Rotary knob"
) -> dr.DeviceEntry:
    """Create a device linked to a config entry."""
    entry = MockConfigEntry(domain=domain)
    entry.add_to_hass(hass)
    return dr.async_get(hass).async_get_or_create(
        config_entry_id=entry.entry_id,
        identifiers={(domain, name.lower().replace(" ", "_"))},
        name=name,
    )


async def test_setup_entry_registers_runtime_data_and_service_device(
    hass: HomeAssistant,
) -> None:
    """Test setup registers runtime data and the service device."""
    device = _create_device(hass)
    entry = MockConfigEntry(
        domain=DOMAIN,
        unique_id=DOMAIN,
        data={CONF_DEVICE_ID: device.id},
    )
    entry.add_to_hass(hass)
    hass.http = Mock()
    hass.http.async_register_static_paths = AsyncMock()

    with (
        patch.object(
            hass.config_entries,
            "async_forward_entry_setups",
            AsyncMock(return_value=True),
        ) as forward_entry_setups,
        patch(
            "custom_components.knob_swipe_navigation.frontend.add_extra_js_url"
        ) as add_extra_js_url,
    ):
        assert await async_setup_entry(hass, entry)

    assert entry.runtime_data.device_id == device.id
    assert entry.runtime_data.settings.dashboard_path == DEFAULT_DASHBOARD_PATH
    forward_entry_setups.assert_awaited_once()
    add_extra_js_url.assert_called_once()

    service_device = dr.async_get(hass).async_get_device(
        identifiers={(DOMAIN, entry.entry_id)}
    )
    assert service_device is not None
    assert service_device.entry_type is dr.DeviceEntryType.SERVICE


async def test_setup_entry_tracks_selected_knob_rotation(
    hass: HomeAssistant,
) -> None:
    """Test setup registers a backend ZHA event listener."""
    device = _create_device(hass)
    entry = MockConfigEntry(
        domain=DOMAIN,
        unique_id=DOMAIN,
        data={CONF_DEVICE_ID: device.id},
    )
    entry.add_to_hass(hass)
    hass.http = Mock()
    hass.http.async_register_static_paths = AsyncMock()

    with (
        patch.object(
            hass.config_entries,
            "async_forward_entry_setups",
            AsyncMock(return_value=True),
        ),
        patch("custom_components.knob_swipe_navigation.frontend.add_extra_js_url"),
    ):
        assert await async_setup_entry(hass, entry)

    hass.bus.async_fire(
        EVENT_ZHA,
        {
            "device_id": device.id,
            "command": "rotate_type",
            "params": {"rotate_type": 0},
            "args": [0],
        },
    )
    await hass.async_block_till_done()

    assert entry.runtime_data.last_rotation == ROTATION_NEXT
    assert entry.runtime_data.last_rotation_value == 0


async def test_setup_entry_tracks_multiple_knobs_independently(
    hass: HomeAssistant,
) -> None:
    """Test rotation events update only the matching knob entry."""
    kitchen_device = _create_device(hass, name="Kitchen knob")
    bedroom_device = _create_device(hass, name="Bedroom knob")
    kitchen_entry = MockConfigEntry(
        domain=DOMAIN,
        unique_id="zha:kitchen_knob",
        data={CONF_DEVICE_ID: kitchen_device.id},
    )
    bedroom_entry = MockConfigEntry(
        domain=DOMAIN,
        unique_id="zha:bedroom_knob",
        data={CONF_DEVICE_ID: bedroom_device.id},
    )
    kitchen_entry.add_to_hass(hass)
    bedroom_entry.add_to_hass(hass)
    hass.http = Mock()
    hass.http.async_register_static_paths = AsyncMock()

    with (
        patch.object(
            hass.config_entries,
            "async_forward_entry_setups",
            AsyncMock(return_value=True),
        ),
        patch("custom_components.knob_swipe_navigation.frontend.add_extra_js_url"),
    ):
        assert await async_setup_entry(hass, kitchen_entry)
        assert await async_setup_entry(hass, bedroom_entry)

    hass.bus.async_fire(
        EVENT_ZHA,
        {
            "device_id": bedroom_device.id,
            "command": "rotate_type",
            "params": {"rotate_type": 1},
            "args": [1],
        },
    )
    await hass.async_block_till_done()

    assert kitchen_entry.runtime_data.last_rotation is None
    assert bedroom_entry.runtime_data.last_rotation == ROTATION_PREVIOUS
    assert bedroom_entry.runtime_data.last_rotation_value == 1


async def test_setup_entry_raises_and_creates_repair_issue_for_invalid_device(
    hass: HomeAssistant,
) -> None:
    """Test setup fails with a repair issue when the selected device is invalid."""
    device = _create_device(hass, domain="mqtt")
    entry = MockConfigEntry(
        domain=DOMAIN,
        unique_id=DOMAIN,
        data={CONF_DEVICE_ID: device.id},
    )
    entry.add_to_hass(hass)

    with pytest.raises(ConfigEntryError):
        await async_setup_entry(hass, entry)

    issue = ir.async_get(hass).async_get_issue(
        DOMAIN, f"{REPAIR_ISSUE_DEVICE_NOT_ZHA}_{entry.entry_id}"
    )
    assert issue is not None


async def test_unload_entry_removes_frontend_resource(hass: HomeAssistant) -> None:
    """Test unload removes the frontend module."""
    entry = MockConfigEntry(domain=DOMAIN, unique_id=DOMAIN)
    entry.add_to_hass(hass)
    hass.data[DOMAIN] = {
        "frontend_registered": True,
        "loaded_entry_ids": {entry.entry_id},
    }

    with (
        patch.object(
            hass.config_entries,
            "async_unload_platforms",
            AsyncMock(return_value=True),
        ) as unload_platforms,
        patch(
            "custom_components.knob_swipe_navigation.frontend.remove_extra_js_url"
        ) as remove_extra_js_url,
    ):
        assert await async_unload_entry(hass, entry)

    unload_platforms.assert_awaited_once()
    remove_extra_js_url.assert_called_once()


async def test_migrate_entry_moves_options_device_to_data(
    hass: HomeAssistant,
) -> None:
    """Test migration moves legacy option data into config entry data."""
    device = _create_device(hass)
    entry = MockConfigEntry(
        domain=DOMAIN,
        unique_id=DOMAIN,
        data={},
        options={CONF_DEVICE_ID: device.id},
        minor_version=1,
    )
    entry.add_to_hass(hass)

    assert await async_migrate_entry(hass, entry)
    assert entry.data == {
        CONF_DEVICE_ID: device.id,
        CONF_CAPABILITY_PROFILE: DEFAULT_CAPABILITY_PROFILE,
    }
    assert entry.options[CONF_DASHBOARD_PATH] == DEFAULT_DASHBOARD_PATH
    assert entry.options[CONF_COOLDOWN_MS] == DEFAULT_COOLDOWN_MS
    assert entry.options[CONF_NAVIGATION_ENABLED] is True
    assert entry.minor_version == 4


def test_websocket_config_returns_runtime_settings(hass: HomeAssistant) -> None:
    """Test the frontend config websocket command returns settings and entity IDs."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        unique_id=DOMAIN,
        data={CONF_DEVICE_ID: "device-id"},
        options={
            CONF_DASHBOARD_PATH: "dashboard-home",
            CONF_OVERLAY_TIMEOUT_MS: 1800,
        },
    )
    entry.runtime_data = KnobSwipeNavigationRuntimeData(
        device_id="device-id",
        settings=KnobSwipeNavigationSettings(
            dashboard_path="dashboard-home",
            overlay_timeout_ms=1800,
        ),
    )
    entry.runtime_data.entity_ids[ENTITY_NAVIGATION_ENABLED] = (
        "switch.knob_navigation_enabled"
    )
    entry.add_to_hass(hass)
    connection = Mock()

    websocket_config(hass, connection, {"id": 1, "type": WS_TYPE_CONFIG})

    result = connection.send_result.call_args.args[1]
    assert result["rotation_subscription_type"] == WS_TYPE_SUBSCRIBE_ROTATIONS
    assert len(result["entries"]) == 1
    entry_config = result["entries"][0]
    assert entry_config["entry_id"] == entry.entry_id
    assert entry_config["device_id"] == "device-id"
    assert entry_config["dashboard_path"] == "dashboard-home"
    assert entry_config["overlay_timeout_ms"] == 1800
    assert entry_config["capability_profile"]["id"] == DEFAULT_CAPABILITY_PROFILE
    assert entry_config["capability_profile"]["rotate"] == {
        "0": ROTATION_NEXT,
        "1": "previous",
    }
    assert entry_config["entities"][ENTITY_NAVIGATION_ENABLED] == (
        "switch.knob_navigation_enabled"
    )


def test_websocket_subscribe_rotations_forwards_backend_events(
    hass: HomeAssistant,
) -> None:
    """Test browsers can subscribe to selected-knob backend rotations."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        unique_id=DOMAIN,
        data={CONF_DEVICE_ID: "device-id"},
    )
    entry.runtime_data = KnobSwipeNavigationRuntimeData(
        device_id="device-id",
        settings=KnobSwipeNavigationSettings(),
    )
    entry.add_to_hass(hass)
    connection = Mock()
    connection.subscriptions = {}

    websocket_subscribe_rotations(
        hass,
        connection,
        {"id": 7, "type": WS_TYPE_SUBSCRIBE_ROTATIONS},
    )

    assert 7 in connection.subscriptions
    connection.send_result.assert_called_once_with(7)

    async_dispatcher_send(
        hass,
        rotation_signal(entry.entry_id),
        RotationEventData(
            direction=ROTATION_NEXT,
            value=0,
            value_attribute="rotate_type",
            capability_profile=DEFAULT_CAPABILITY_PROFILE,
            event_data={},
        ),
    )

    message = connection.send_message.call_args.args[0]
    assert message["id"] == 7
    assert message["type"] == "event"
    assert message["event"] == {
        "entry_id": entry.entry_id,
        "device_id": "device-id",
        "direction": ROTATION_NEXT,
        "value": 0,
        "value_attribute": "rotate_type",
        "capability_profile": DEFAULT_CAPABILITY_PROFILE,
        "rotate_type": 0,
    }


def test_websocket_navigation_result_updates_runtime_data(
    hass: HomeAssistant,
) -> None:
    """Test frontend navigation results update runtime diagnostics."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        unique_id=DOMAIN,
        data={CONF_DEVICE_ID: "device-id"},
    )
    entry.runtime_data = KnobSwipeNavigationRuntimeData(
        device_id="device-id",
        settings=KnobSwipeNavigationSettings(),
    )
    entry.add_to_hass(hass)
    connection = Mock()

    websocket_navigation_result(
        hass,
        connection,
        {
            "id": 1,
            "type": WS_TYPE_NAVIGATION_RESULT,
            "result": "navigated",
            "dashboard_path": "lovelace",
            "from_view": "home",
            "to_view": "lights",
        },
    )

    assert entry.runtime_data.last_navigation_result == "navigated"
    assert entry.runtime_data.last_navigation_details == {
        "dashboard_path": "lovelace",
        "from_view": "home",
        "to_view": "lights",
    }
    connection.send_result.assert_called_once()
