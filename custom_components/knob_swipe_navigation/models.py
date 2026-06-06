"""Data models for Knob Swipe Navigation."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from homeassistant.config_entries import ConfigEntry

from .const import (
    DEFAULT_COOLDOWN_MS,
    DEFAULT_DASHBOARD_PATH,
    DEFAULT_NAVIGATION_ENABLED,
    DEFAULT_OVERLAY_ENABLED,
    DEFAULT_OVERLAY_TIMEOUT_MS,
    DEFAULT_REQUIRE_QUERY_PARAM,
    DEFAULT_WRAP_ENABLED,
)
from .profiles import RotationCapabilityProfile, ZHA_ROTATE_TYPE_PROFILE


@dataclass(slots=True)
class KnobSwipeNavigationSettings:
    """Stored navigation settings."""

    dashboard_path: str = DEFAULT_DASHBOARD_PATH
    navigation_enabled: bool = DEFAULT_NAVIGATION_ENABLED
    overlay_enabled: bool = DEFAULT_OVERLAY_ENABLED
    overlay_timeout_ms: int = DEFAULT_OVERLAY_TIMEOUT_MS
    cooldown_ms: int = DEFAULT_COOLDOWN_MS
    wrap_enabled: bool = DEFAULT_WRAP_ENABLED
    require_query_param: str = DEFAULT_REQUIRE_QUERY_PARAM


@dataclass(slots=True)
class RotationEventData:
    """Rotation event data from the selected knob."""

    direction: str
    value: int
    value_attribute: str
    capability_profile: str
    event_data: dict[str, Any]


@dataclass(slots=True)
class NavigationResultData:
    """Frontend navigation result data."""

    result: str
    details: dict[str, Any]


@dataclass(slots=True)
class KnobSwipeNavigationRuntimeData:
    """Runtime data for a loaded config entry."""

    device_id: str
    settings: KnobSwipeNavigationSettings
    capability_profile: RotationCapabilityProfile = ZHA_ROTATE_TYPE_PROFILE
    service_device_id: str | None = None
    entity_ids: dict[str, str] = field(default_factory=dict)
    last_rotation: str | None = None
    last_rotation_at: datetime | None = None
    last_rotation_value: int | None = None
    last_rotation_value_attribute: str | None = None
    last_rotation_capability_profile: str | None = None
    last_navigation_result: str | None = None
    last_navigation_result_at: datetime | None = None
    last_navigation_details: dict[str, Any] | None = None


KnobSwipeNavigationConfigEntry = ConfigEntry[KnobSwipeNavigationRuntimeData]
