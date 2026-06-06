"""Sensor entities for Knob Swipe Navigation."""

from __future__ import annotations

from typing import Any

from homeassistant.components.sensor import SensorEntity
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .const import ENTITY_LAST_NAVIGATION_RESULT, ENTITY_LAST_ROTATION
from .entity import KnobSwipeNavigationEntity
from .helpers import navigation_result_signal, rotation_signal
from .models import (
    KnobSwipeNavigationConfigEntry,
    NavigationResultData,
    RotationEventData,
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: KnobSwipeNavigationConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up sensor entities."""
    async_add_entities(
        [
            KnobSwipeNavigationLastRotationSensor(entry),
            KnobSwipeNavigationLastNavigationResultSensor(entry),
        ]
    )


class KnobSwipeNavigationLastRotationSensor(KnobSwipeNavigationEntity, SensorEntity):
    """Last selected-knob rotation sensor."""

    def __init__(self, entry: KnobSwipeNavigationConfigEntry) -> None:
        """Initialize the sensor."""
        super().__init__(
            entry, ENTITY_LAST_ROTATION, entity_category=EntityCategory.DIAGNOSTIC
        )

    async def async_added_to_hass(self) -> None:
        """Register callbacks."""
        await super().async_added_to_hass()
        self.async_on_remove(
            async_dispatcher_connect(
                self.hass,
                rotation_signal(self._entry.entry_id),
                self._handle_rotation,
            )
        )

    @property
    def native_value(self) -> str | None:
        """Return the last rotation direction."""
        return self._entry.runtime_data.last_rotation

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return diagnostic attributes."""
        runtime_data = self._entry.runtime_data
        attrs: dict[str, Any] = {}
        if runtime_data.last_rotation_value is not None:
            attrs["rotate_type"] = runtime_data.last_rotation_value
        if runtime_data.last_rotation_at is not None:
            attrs["last_seen"] = runtime_data.last_rotation_at.isoformat()
        return attrs

    @callback
    def _handle_rotation(self, data: RotationEventData) -> None:
        """Handle a rotation event."""
        self.async_write_ha_state()


class KnobSwipeNavigationLastNavigationResultSensor(
    KnobSwipeNavigationEntity, SensorEntity
):
    """Last frontend navigation result sensor."""

    def __init__(self, entry: KnobSwipeNavigationConfigEntry) -> None:
        """Initialize the sensor."""
        super().__init__(
            entry,
            ENTITY_LAST_NAVIGATION_RESULT,
            entity_category=EntityCategory.DIAGNOSTIC,
        )

    async def async_added_to_hass(self) -> None:
        """Register callbacks."""
        await super().async_added_to_hass()
        self.async_on_remove(
            async_dispatcher_connect(
                self.hass,
                navigation_result_signal(self._entry.entry_id),
                self._handle_navigation_result,
            )
        )

    @property
    def native_value(self) -> str | None:
        """Return the last navigation result."""
        return self._entry.runtime_data.last_navigation_result

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return diagnostic attributes."""
        runtime_data = self._entry.runtime_data
        attrs = dict(runtime_data.last_navigation_details or {})
        if runtime_data.last_navigation_result_at is not None:
            attrs["last_seen"] = runtime_data.last_navigation_result_at.isoformat()
        return attrs

    @callback
    def _handle_navigation_result(self, data: NavigationResultData) -> None:
        """Handle a navigation result."""
        self.async_write_ha_state()
