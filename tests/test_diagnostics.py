"""Tests for Knob Swipe Navigation diagnostics."""

from __future__ import annotations

from homeassistant.const import CONF_DEVICE_ID
from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.knob_swipe_navigation.const import DOMAIN
from custom_components.knob_swipe_navigation.diagnostics import (
    async_get_config_entry_diagnostics,
)


def _create_device(hass: HomeAssistant) -> dr.DeviceEntry:
    """Create a ZHA device linked to a config entry."""
    zha_entry = MockConfigEntry(domain="zha")
    zha_entry.add_to_hass(hass)
    return dr.async_get(hass).async_get_or_create(
        config_entry_id=zha_entry.entry_id,
        identifiers={("zha", "rotary_knob")},
        manufacturer="Example",
        model="Rotary knob",
        name="Kitchen knob",
    )


async def test_diagnostics_redacts_configured_device_id(
    hass: HomeAssistant,
) -> None:
    """Test diagnostics include safe entry and selected device information."""
    device = _create_device(hass)
    entry = MockConfigEntry(
        domain=DOMAIN,
        unique_id=DOMAIN,
        data={CONF_DEVICE_ID: device.id},
    )
    entry.add_to_hass(hass)

    diagnostics = await async_get_config_entry_diagnostics(hass, entry)

    assert diagnostics["entry"]["data"][CONF_DEVICE_ID] == "**REDACTED**"
    assert diagnostics["selected_device"]["found"] is True
    assert diagnostics["selected_device"]["manufacturer"] == "Example"
    assert diagnostics["selected_device"]["model"] == "Rotary knob"
    assert diagnostics["selected_device"]["config_entry_domains"] == ["zha"]
