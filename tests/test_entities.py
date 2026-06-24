"""Tests for Knob Swipe Navigation entities."""

from __future__ import annotations

from unittest.mock import Mock

from homeassistant.const import CONF_DEVICE_ID
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import EntityCategory
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.knob_swipe_navigation.const import (
    CONF_COOLDOWN_MS,
    CONF_IDLE_RETURN_ENABLED,
    CONF_IDLE_RETURN_TIMEOUT_SECONDS,
    CONF_NAVIGATION_ENABLED,
    DEFAULT_CAPABILITY_PROFILE,
    DOMAIN,
    ENTITY_COOLDOWN_MS,
    ENTITY_IDLE_RETURN_ENABLED,
    ENTITY_IDLE_RETURN_TIMEOUT_SECONDS,
    ENTITY_LAST_NAVIGATION_RESULT,
    ENTITY_LAST_ROTATION,
    ENTITY_NAVIGATION_ENABLED,
    ENTITY_ROTATION,
    ROTATION_NEXT,
)
from custom_components.knob_swipe_navigation.event import (
    KnobSwipeNavigationRotationEvent,
    async_setup_entry as async_setup_event_entry,
)
from custom_components.knob_swipe_navigation.models import (
    KnobSwipeNavigationRuntimeData,
    KnobSwipeNavigationSettings,
    NavigationResultData,
    RotationEventData,
)
from custom_components.knob_swipe_navigation.number import (
    KnobSwipeNavigationNumber,
    async_setup_entry as async_setup_number_entry,
)
from custom_components.knob_swipe_navigation.sensor import (
    KnobSwipeNavigationLastNavigationResultSensor,
    KnobSwipeNavigationLastRotationSensor,
    async_setup_entry as async_setup_sensor_entry,
)
from custom_components.knob_swipe_navigation.switch import (
    KnobSwipeNavigationSwitch,
    async_setup_entry as async_setup_switch_entry,
)


def _entry(hass: HomeAssistant) -> MockConfigEntry:
    """Return a loaded mock entry."""
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
    return entry


async def test_switch_setup_and_state_updates(hass: HomeAssistant) -> None:
    """Test switch entities expose and persist boolean settings."""
    entry = _entry(hass)
    entities: list[object] = []

    await async_setup_switch_entry(hass, entry, entities.extend)

    assert len(entities) == 4
    switch = entities[0]
    assert isinstance(switch, KnobSwipeNavigationSwitch)
    switch.hass = hass
    switch.async_write_ha_state = Mock()

    assert switch.is_on is True
    await switch.async_turn_off()

    assert entry.options[CONF_NAVIGATION_ENABLED] is False
    assert entry.runtime_data.settings.navigation_enabled is False
    assert switch.is_on is False

    idle_switch = entities[3]
    assert isinstance(idle_switch, KnobSwipeNavigationSwitch)
    idle_switch.hass = hass
    idle_switch.async_write_ha_state = Mock()

    await idle_switch.async_turn_off()

    assert entry.options[CONF_IDLE_RETURN_ENABLED] is False
    assert entry.runtime_data.settings.idle_return_enabled is False


async def test_number_setup_and_state_updates(hass: HomeAssistant) -> None:
    """Test number entities expose and persist numeric settings."""
    entry = _entry(hass)
    entities: list[object] = []

    await async_setup_number_entry(hass, entry, entities.extend)

    assert len(entities) == 3
    number = entities[1]
    assert isinstance(number, KnobSwipeNavigationNumber)
    number.hass = hass
    number.async_write_ha_state = Mock()

    await number.async_set_native_value(300)

    assert entry.options[CONF_COOLDOWN_MS] == 300
    assert entry.runtime_data.settings.cooldown_ms == 300
    assert number.native_value == 300

    idle_number = entities[2]
    assert isinstance(idle_number, KnobSwipeNavigationNumber)
    idle_number.hass = hass
    idle_number.async_write_ha_state = Mock()

    await idle_number.async_set_native_value(90)

    assert entry.options[CONF_IDLE_RETURN_TIMEOUT_SECONDS] == 90
    assert entry.runtime_data.settings.idle_return_timeout_seconds == 90
    assert idle_number.native_value == 90


async def test_event_entity_triggers_rotation_event(hass: HomeAssistant) -> None:
    """Test the event entity fires selected knob rotations."""
    entry = _entry(hass)
    entities: list[object] = []

    await async_setup_event_entry(hass, entry, entities.extend)

    event = entities[0]
    assert isinstance(event, KnobSwipeNavigationRotationEvent)
    event._trigger_event = Mock()
    event.async_write_ha_state = Mock()

    event._handle_rotation(
        RotationEventData(
            direction=ROTATION_NEXT,
            value=0,
            value_attribute="rotate_type",
            capability_profile=DEFAULT_CAPABILITY_PROFILE,
            event_data={},
        )
    )

    event._trigger_event.assert_called_once_with(
        ROTATION_NEXT,
        {
            "rotate_type": 0,
            "capability_profile": DEFAULT_CAPABILITY_PROFILE,
        },
    )
    event.async_write_ha_state.assert_called_once()


async def test_sensor_setup_and_values(hass: HomeAssistant) -> None:
    """Test diagnostic sensors expose runtime data."""
    entry = _entry(hass)
    entry.runtime_data.last_rotation = ROTATION_NEXT
    entry.runtime_data.last_rotation_value = 0
    entry.runtime_data.last_rotation_value_attribute = "rotate_type"
    entry.runtime_data.last_rotation_capability_profile = DEFAULT_CAPABILITY_PROFILE
    entry.runtime_data.last_navigation_result = "navigated"
    entry.runtime_data.last_navigation_details = {"dashboard_path": "lovelace"}
    entities: list[object] = []

    await async_setup_sensor_entry(hass, entry, entities.extend)

    rotation_sensor = entities[0]
    result_sensor = entities[1]
    assert isinstance(rotation_sensor, KnobSwipeNavigationLastRotationSensor)
    assert isinstance(result_sensor, KnobSwipeNavigationLastNavigationResultSensor)
    assert rotation_sensor.native_value == ROTATION_NEXT
    assert rotation_sensor.extra_state_attributes["rotate_type"] == 0
    assert (
        rotation_sensor.extra_state_attributes["capability_profile"]
        == DEFAULT_CAPABILITY_PROFILE
    )
    assert result_sensor.native_value == "navigated"
    assert result_sensor.extra_state_attributes["dashboard_path"] == "lovelace"


async def test_entity_registration_tracks_entity_ids(hass: HomeAssistant) -> None:
    """Test common entity hooks register frontend-visible entity IDs."""
    entry = _entry(hass)
    switch = KnobSwipeNavigationSwitch(
        entry,
        ENTITY_NAVIGATION_ENABLED,
        CONF_NAVIGATION_ENABLED,
        None,
    )
    switch.entity_id = "switch.knob_navigation_enabled"

    await switch.async_added_to_hass()
    assert entry.runtime_data.entity_ids[ENTITY_NAVIGATION_ENABLED] == (
        "switch.knob_navigation_enabled"
    )

    await switch.async_will_remove_from_hass()
    assert ENTITY_NAVIGATION_ENABLED not in entry.runtime_data.entity_ids


def test_entity_metadata(hass: HomeAssistant) -> None:
    """Test representative entity metadata."""
    entry = _entry(hass)
    number = KnobSwipeNavigationNumber(
        entry,
        ENTITY_COOLDOWN_MS,
        CONF_COOLDOWN_MS,
        0,
        10000,
        100,
    )
    idle_switch = KnobSwipeNavigationSwitch(
        entry,
        ENTITY_IDLE_RETURN_ENABLED,
        CONF_IDLE_RETURN_ENABLED,
        EntityCategory.CONFIG,
    )
    idle_number = KnobSwipeNavigationNumber(
        entry,
        ENTITY_IDLE_RETURN_TIMEOUT_SECONDS,
        CONF_IDLE_RETURN_TIMEOUT_SECONDS,
        1,
        86400,
        1,
        "s",
    )
    sensor = KnobSwipeNavigationLastRotationSensor(entry)
    event = KnobSwipeNavigationRotationEvent(entry)

    assert number.entity_category is EntityCategory.CONFIG
    assert sensor.entity_category is EntityCategory.DIAGNOSTIC
    assert event.translation_key == ENTITY_ROTATION
    assert number.device_info["identifiers"] == {(DOMAIN, entry.entry_id)}
    assert idle_switch.translation_key == ENTITY_IDLE_RETURN_ENABLED
    assert idle_number.native_unit_of_measurement == "s"
    assert sensor.translation_key == ENTITY_LAST_ROTATION
    assert ENTITY_LAST_NAVIGATION_RESULT == "last_navigation_result"
