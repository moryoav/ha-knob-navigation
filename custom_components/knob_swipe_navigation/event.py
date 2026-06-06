"""Event entities for Knob Swipe Navigation."""

from __future__ import annotations

from homeassistant.components.event import EventEntity
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .const import ENTITY_ROTATION, ROTATION_NEXT, ROTATION_PREVIOUS
from .entity import KnobSwipeNavigationEntity
from .helpers import rotation_signal
from .models import KnobSwipeNavigationConfigEntry, RotationEventData


async def async_setup_entry(
    hass: HomeAssistant,
    entry: KnobSwipeNavigationConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up event entities."""
    async_add_entities([KnobSwipeNavigationRotationEvent(entry)])


class KnobSwipeNavigationRotationEvent(KnobSwipeNavigationEntity, EventEntity):
    """Rotation event from the selected knob."""

    _attr_event_types = [ROTATION_NEXT, ROTATION_PREVIOUS]

    def __init__(self, entry: KnobSwipeNavigationConfigEntry) -> None:
        """Initialize the event entity."""
        super().__init__(entry, ENTITY_ROTATION)

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

    @callback
    def _handle_rotation(self, data: RotationEventData) -> None:
        """Handle a rotation event."""
        self._trigger_event(
            data.direction,
            {
                data.value_attribute: data.value,
                "capability_profile": data.capability_profile,
            },
        )
        self.async_write_ha_state()
