"""Number entities for Knob Swipe Navigation."""

from __future__ import annotations

from homeassistant.components.number import NumberEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .const import (
    CONF_COOLDOWN_MS,
    CONF_OVERLAY_TIMEOUT_MS,
    ENTITY_COOLDOWN_MS,
    ENTITY_OVERLAY_TIMEOUT_MS,
    MAX_COOLDOWN_MS,
    MAX_OVERLAY_TIMEOUT_MS,
    MIN_COOLDOWN_MS,
    MIN_OVERLAY_TIMEOUT_MS,
)
from .entity import KnobSwipeNavigationEntity, async_set_entry_option
from .models import KnobSwipeNavigationConfigEntry

MILLISECONDS = "ms"

NUMBERS: tuple[tuple[str, str, int, int, int], ...] = (
    (
        ENTITY_OVERLAY_TIMEOUT_MS,
        CONF_OVERLAY_TIMEOUT_MS,
        MIN_OVERLAY_TIMEOUT_MS,
        MAX_OVERLAY_TIMEOUT_MS,
        100,
    ),
    (
        ENTITY_COOLDOWN_MS,
        CONF_COOLDOWN_MS,
        MIN_COOLDOWN_MS,
        MAX_COOLDOWN_MS,
        100,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: KnobSwipeNavigationConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up number entities."""
    async_add_entities(
        KnobSwipeNavigationNumber(entry, entity_key, option_key, minimum, maximum, step)
        for entity_key, option_key, minimum, maximum, step in NUMBERS
    )


class KnobSwipeNavigationNumber(KnobSwipeNavigationEntity, NumberEntity):
    """A number-backed navigation setting."""

    _attr_entity_category = EntityCategory.CONFIG
    _attr_native_unit_of_measurement = MILLISECONDS

    def __init__(
        self,
        entry: KnobSwipeNavigationConfigEntry,
        entity_key: str,
        option_key: str,
        minimum: int,
        maximum: int,
        step: int,
    ) -> None:
        """Initialize the number."""
        super().__init__(entry, entity_key, entity_category=EntityCategory.CONFIG)
        self._option_key = option_key
        self._attr_native_min_value = minimum
        self._attr_native_max_value = maximum
        self._attr_native_step = step

    @property
    def native_value(self) -> int:
        """Return the current value."""
        return int(getattr(self._entry.runtime_data.settings, self._option_key))

    async def async_set_native_value(self, value: float) -> None:
        """Set the number value."""
        next_value = max(
            int(self.native_min_value),
            min(int(self.native_max_value), int(value)),
        )
        async_set_entry_option(self.hass, self._entry, self._option_key, next_value)
        self.async_write_ha_state()
