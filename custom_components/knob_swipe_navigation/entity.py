"""Shared entity helpers for Knob Swipe Navigation."""

from __future__ import annotations

from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo, Entity, EntityCategory

from .const import DOMAIN
from .helpers import update_runtime_settings
from .models import KnobSwipeNavigationConfigEntry


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
