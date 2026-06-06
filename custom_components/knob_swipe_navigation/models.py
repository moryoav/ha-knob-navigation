"""Data models for Knob Swipe Navigation."""

from __future__ import annotations

from dataclasses import dataclass

from homeassistant.config_entries import ConfigEntry


@dataclass(slots=True)
class KnobSwipeNavigationRuntimeData:
    """Runtime data for a loaded config entry."""

    device_id: str
    service_device_id: str | None = None


KnobSwipeNavigationConfigEntry = ConfigEntry[KnobSwipeNavigationRuntimeData]
