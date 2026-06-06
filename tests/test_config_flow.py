"""Tests for the Knob Swipe Navigation config flow."""

from __future__ import annotations

from unittest.mock import patch

from homeassistant import config_entries
from homeassistant.const import CONF_DEVICE_ID
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from homeassistant.helpers import device_registry as dr
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.knob_swipe_navigation.config_flow import (
    FORM_COOLDOWN_MS,
    FORM_DASHBOARD_PATH,
    FORM_DEVICE_ID,
    FORM_NAVIGATION_ENABLED,
    FORM_OVERLAY_ENABLED,
    FORM_OVERLAY_TIMEOUT_MS,
    FORM_REQUIRE_QUERY_PARAM,
    FORM_WRAP_ENABLED,
)
from custom_components.knob_swipe_navigation.const import (
    CONF_CAPABILITY_PROFILE,
    CONF_COOLDOWN_MS,
    CONF_DASHBOARD_PATH,
    CONF_NAVIGATION_ENABLED,
    CONF_OVERLAY_TIMEOUT_MS,
    CONF_REQUIRE_QUERY_PARAM,
    CONF_WRAP_ENABLED,
    DEFAULT_CAPABILITY_PROFILE,
    DEFAULT_NAME,
    DOMAIN,
)


def _schema_keys(result: config_entries.ConfigFlowResult) -> set[str]:
    """Return user-facing schema keys from a form result."""
    return {key.schema for key in result["data_schema"].schema}


def _settings_input() -> dict[str, object]:
    """Return valid settings input."""
    return {
        FORM_DASHBOARD_PATH: "/dashboard-home/default_view?kiosk",
        FORM_NAVIGATION_ENABLED: True,
        FORM_OVERLAY_ENABLED: True,
        FORM_OVERLAY_TIMEOUT_MS: 1800,
        FORM_COOLDOWN_MS: 250,
        FORM_WRAP_ENABLED: False,
        FORM_REQUIRE_QUERY_PARAM: "kiosk",
    }


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
    schema_keys = _schema_keys(result)
    assert FORM_DEVICE_ID in schema_keys
    assert FORM_NAVIGATION_ENABLED in schema_keys
    assert CONF_DEVICE_ID not in schema_keys
    assert CONF_NAVIGATION_ENABLED not in schema_keys

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {FORM_DEVICE_ID: device.id, **_settings_input()},
    )

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == f"{DEFAULT_NAME}: Rotary knob"
    assert result["data"] == {
        CONF_DEVICE_ID: device.id,
        CONF_CAPABILITY_PROFILE: DEFAULT_CAPABILITY_PROFILE,
    }
    options = result.get("options") or result["result"].options
    assert options[CONF_DASHBOARD_PATH] == "dashboard-home"
    assert options[CONF_OVERLAY_TIMEOUT_MS] == 1800
    assert options[CONF_COOLDOWN_MS] == 250
    assert options[CONF_WRAP_ENABLED] is False
    assert options[CONF_REQUIRE_QUERY_PARAM] == "kiosk"


async def test_user_flow_rejects_non_zha_device(hass: HomeAssistant) -> None:
    """Test the user flow rejects devices not linked to ZHA."""
    device = _create_device(hass, domain="mqtt")

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_USER},
    )

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {FORM_DEVICE_ID: device.id, **_settings_input()},
    )

    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {FORM_DEVICE_ID: "not_zha_device"}


async def test_user_flow_rejects_duplicate_knob(
    hass: HomeAssistant,
) -> None:
    """Test the user flow prevents duplicate setup for one physical knob."""
    device = _create_device(hass)
    entry = MockConfigEntry(
        domain=DOMAIN,
        unique_id="zha:rotary_knob",
        data={CONF_DEVICE_ID: device.id},
    )
    entry.add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_USER},
    )

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {FORM_DEVICE_ID: device.id, **_settings_input()},
    )

    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {FORM_DEVICE_ID: "already_configured"}


async def test_user_flow_allows_multiple_different_knobs(
    hass: HomeAssistant,
) -> None:
    """Test the user flow allows multiple physical knobs."""
    existing_device = _create_device(hass, name="Kitchen knob")
    new_device = _create_device(hass, name="Bedroom knob")
    entry = MockConfigEntry(
        domain=DOMAIN,
        unique_id="zha:kitchen_knob",
        data={CONF_DEVICE_ID: existing_device.id},
    )
    entry.add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_USER},
    )

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {FORM_DEVICE_ID: new_device.id, **_settings_input()},
    )

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == f"{DEFAULT_NAME}: Bedroom knob"


async def test_reconfigure_flow_updates_existing_entry(
    hass: HomeAssistant,
) -> None:
    """Test reconfigure updates the existing entry and reloads it."""
    old_device = _create_device(hass, name="Old knob")
    new_device = _create_device(hass, name="New knob")
    entry = MockConfigEntry(
        domain=DOMAIN,
        unique_id="zha:old_knob",
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
            {
                FORM_DEVICE_ID: new_device.id,
                **{
                    **_settings_input(),
                    FORM_DASHBOARD_PATH: "lovelace/tablet",
                    FORM_OVERLAY_TIMEOUT_MS: 3200,
                },
            },
        )

    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "reconfigure_successful"
    assert entry.data[CONF_DEVICE_ID] == new_device.id
    assert entry.data[CONF_CAPABILITY_PROFILE] == DEFAULT_CAPABILITY_PROFILE
    assert entry.unique_id == "zha:new_knob"
    assert entry.options[CONF_DASHBOARD_PATH] == "lovelace"
    assert entry.options[CONF_OVERLAY_TIMEOUT_MS] == 3200
    schedule_reload.assert_called_once_with(entry.entry_id)


async def test_options_flow_updates_navigation_options(hass: HomeAssistant) -> None:
    """Test options flow stores normalized settings."""
    device = _create_device(hass)
    entry = MockConfigEntry(
        domain=DOMAIN,
        unique_id="zha:rotary_knob",
        data={CONF_DEVICE_ID: device.id},
    )
    entry.add_to_hass(hass)

    result = await hass.config_entries.options.async_init(entry.entry_id)

    assert result["type"] is FlowResultType.FORM

    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        {
            **_settings_input(),
            FORM_DASHBOARD_PATH: "http://homeassistant.local:8123/kitchen/0",
            FORM_NAVIGATION_ENABLED: False,
        },
    )

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["data"][CONF_DASHBOARD_PATH] == "kitchen"
    assert result["data"][CONF_NAVIGATION_ENABLED] is False
