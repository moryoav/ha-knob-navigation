"""Tests for the Knob Swipe Navigation config flow."""

from __future__ import annotations

from unittest.mock import patch

from homeassistant import config_entries
from homeassistant.const import CONF_DEVICE_ID
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from homeassistant.helpers import device_registry as dr
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.knob_swipe_navigation.const import DEFAULT_NAME, DOMAIN


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


async def test_user_flow_creates_entry_for_zha_device(hass: HomeAssistant) -> None:
    """Test the user flow stores the selected ZHA device."""
    device = _create_device(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_USER},
    )

    assert result["type"] is FlowResultType.FORM

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_DEVICE_ID: device.id},
    )

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == DEFAULT_NAME
    assert result["data"] == {CONF_DEVICE_ID: device.id}


async def test_user_flow_rejects_non_zha_device(hass: HomeAssistant) -> None:
    """Test the user flow rejects devices not linked to ZHA."""
    device = _create_device(hass, domain="mqtt")

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_USER},
    )

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_DEVICE_ID: device.id},
    )

    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {CONF_DEVICE_ID: "not_zha_device"}


async def test_user_flow_enforces_single_config_entry(
    hass: HomeAssistant,
) -> None:
    """Test the user flow prevents duplicate setup."""
    device = _create_device(hass)
    entry = MockConfigEntry(
        domain=DOMAIN,
        unique_id=DOMAIN,
        data={CONF_DEVICE_ID: device.id},
    )
    entry.add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_USER},
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_DEVICE_ID: device.id},
    )

    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "already_configured"


async def test_reconfigure_flow_updates_existing_entry(
    hass: HomeAssistant,
) -> None:
    """Test reconfigure updates the existing entry and reloads it."""
    old_device = _create_device(hass, name="Old knob")
    new_device = _create_device(hass, name="New knob")
    entry = MockConfigEntry(
        domain=DOMAIN,
        unique_id=DOMAIN,
        data={CONF_DEVICE_ID: old_device.id},
    )
    entry.add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={
            "source": config_entries.SOURCE_RECONFIGURE,
            "entry_id": entry.entry_id,
        },
    )

    assert result["type"] is FlowResultType.FORM

    with patch.object(hass.config_entries, "async_schedule_reload") as schedule_reload:
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {CONF_DEVICE_ID: new_device.id},
        )

    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "reconfigure_successful"
    assert entry.data[CONF_DEVICE_ID] == new_device.id
    schedule_reload.assert_called_once_with(entry.entry_id)
