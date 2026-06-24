"""Shared entity helpers for Knob Swipe Navigation."""

from __future__ import annotations

from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo, Entity, EntityCategory

from .const import (
    DOMAIN,
    ENTITY_COOLDOWN_MS,
    ENTITY_IDLE_RETURN_ENABLED,
    ENTITY_IDLE_RETURN_TIMEOUT_SECONDS,
    ENTITY_LAST_NAVIGATION_RESULT,
    ENTITY_LAST_ROTATION,
    ENTITY_NAVIGATION_ENABLED,
    ENTITY_OVERLAY_ENABLED,
    ENTITY_OVERLAY_TIMEOUT_MS,
    ENTITY_ROTATION,
    ENTITY_WRAP_ENABLED,
)
from .helpers import update_runtime_settings
from .models import KnobSwipeNavigationConfigEntry

FRIENDLY_ENTITY_NAMES = {
    ENTITY_NAVIGATION_ENABLED: "Knob navigation",
    ENTITY_OVERLAY_ENABLED: "Tab overlay",
    ENTITY_WRAP_ENABLED: "Tab wraparound",
    ENTITY_OVERLAY_TIMEOUT_MS: "Overlay display time",
    ENTITY_COOLDOWN_MS: "Rotation cooldown",
    ENTITY_IDLE_RETURN_ENABLED: "Idle return to first tab",
    ENTITY_IDLE_RETURN_TIMEOUT_SECONDS: "Idle return delay",
    ENTITY_ROTATION: "Knob rotation",
    ENTITY_LAST_ROTATION: "Last knob rotation",
    ENTITY_LAST_NAVIGATION_RESULT: "Last navigation result",
}


class KnobSwipeNavigationEntity(Entity):
    """Base entity for Knob Swipe Navigation."""

    _attr_has_entity_name = True
    _attr_should_poll = False

    def __init__(
        self,
        entry: KnobSwipeNavigationConfigEntry,
        entity_key: str,
        *,
        entity_category: EntityCategory | None = None,
    ) -> None:
        """Initialize the entity."""
        self._entry = entry
        self._entity_key = entity_key
        self._attr_unique_id = f"{entry.entry_id}_{entity_key}"
        self._attr_name = FRIENDLY_ENTITY_NAMES.get(entity_key)
        self._attr_translation_key = entity_key
        self._attr_entity_category = entity_category

    @property
    def device_info(self) -> DeviceInfo:
        """Return the service device info."""
        return DeviceInfo(identifiers={(DOMAIN, self._entry.entry_id)})

    async def async_added_to_hass(self) -> None:
        """Register the frontend-visible entity ID."""
        if self.entity_id is not None:
            self._entry.runtime_data.entity_ids[self._entity_key] = self.entity_id

    async def async_will_remove_from_hass(self) -> None:
        """Remove the frontend-visible entity ID."""
        if (
            self._entry.runtime_data.entity_ids.get(self._entity_key)
            == self.entity_id
        ):
            self._entry.runtime_data.entity_ids.pop(self._entity_key, None)


def async_set_entry_option(
    hass: HomeAssistant,
    entry: KnobSwipeNavigationConfigEntry,
    key: str,
    value: Any,
) -> None:
    """Persist one config entry option and refresh runtime settings."""
    options = dict(entry.options)
    options[key] = value
    hass.config_entries.async_update_entry(entry, options=options)
    update_runtime_settings(entry)
