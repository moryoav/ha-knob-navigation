"""Switch entities for Knob Swipe Navigation."""

from __future__ import annotations

from homeassistant.components.switch import SwitchEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .const import (
    CONF_NAVIGATION_ENABLED,
    CONF_OVERLAY_ENABLED,
    CONF_WRAP_ENABLED,
    ENTITY_NAVIGATION_ENABLED,
    ENTITY_OVERLAY_ENABLED,
    ENTITY_WRAP_ENABLED,
)
from .entity import KnobSwipeNavigationEntity, async_set_entry_option
from .models import KnobSwipeNavigationConfigEntry

SWITCHES: tuple[tuple[str, str, EntityCategory | None], ...] = (
    (ENTITY_NAVIGATION_ENABLED, CONF_NAVIGATION_ENABLED, None),
    (ENTITY_OVERLAY_ENABLED, CONF_OVERLAY_ENABLED, EntityCategory.CONFIG),
    (ENTITY_WRAP_ENABLED, CONF_WRAP_ENABLED, EntityCategory.CONFIG),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: KnobSwipeNavigationConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up switch entities."""
    async_add_entities(
        KnobSwipeNavigationSwitch(entry, entity_key, option_key, category)
        for entity_key, option_key, category in SWITCHES
    )


class KnobSwipeNavigationSwitch(KnobSwipeNavigationEntity, SwitchEntity):
    """A switch-backed navigation setting."""

    def __init__(
        self,
        entry: KnobSwipeNavigationConfigEntry,
        entity_key: str,
        option_key: str,
        entity_category: EntityCategory | None,
    ) -> None:
        """Initialize the switch."""
        super().__init__(entry, entity_key, entity_category=entity_category)
        self._option_key = option_key

    @property
    def is_on(self) -> bool:
        """Return true if the switch is on."""
        return bool(getattr(self._entry.runtime_data.settings, self._option_key))

    async def async_turn_on(self, **kwargs: object) -> None:
        """Turn the switch on."""
        async_set_entry_option(self.hass, self._entry, self._option_key, True)
        self.async_write_ha_state()

    async def async_turn_off(self, **kwargs: object) -> None:
        """Turn the switch off."""
        async_set_entry_option(self.hass, self._entry, self._option_key, False)
        self.async_write_ha_state()
