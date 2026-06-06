"""Tests for Knob Swipe Navigation setup."""

from __future__ import annotations

from unittest.mock import AsyncMock, Mock, patch

import pytest

from homeassistant.const import CONF_DEVICE_ID
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryError
from homeassistant.helpers import device_registry as dr, issue_registry as ir
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.knob_swipe_navigation import (
    async_migrate_entry,
    async_setup_entry,
    async_unload_entry,
)
from custom_components.knob_swipe_navigation.const import (
    DOMAIN,
    REPAIR_ISSUE_DEVICE_NOT_ZHA,
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

    with patch(
        "custom_components.knob_swipe_navigation.frontend.add_extra_js_url"
    ) as add_extra_js_url:
        assert await async_setup_entry(hass, entry)

    assert entry.runtime_data.device_id == device.id
    add_extra_js_url.assert_called_once()

    service_device = dr.async_get(hass).async_get_device(
        identifiers={(DOMAIN, entry.entry_id)}
    )
    assert service_device is not None
    assert service_device.entry_type is dr.DeviceEntryType.SERVICE


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

    issue = ir.async_get(hass).async_get_issue(DOMAIN, REPAIR_ISSUE_DEVICE_NOT_ZHA)
    assert issue is not None


async def test_unload_entry_removes_frontend_resource(hass: HomeAssistant) -> None:
    """Test unload removes the frontend module."""
    entry = MockConfigEntry(domain=DOMAIN, unique_id=DOMAIN)

    with patch(
        "custom_components.knob_swipe_navigation.frontend.remove_extra_js_url"
    ) as remove_extra_js_url:
        assert await async_unload_entry(hass, entry)

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
    assert entry.data == {CONF_DEVICE_ID: device.id}
    assert entry.options == {}
    assert entry.minor_version == 2
