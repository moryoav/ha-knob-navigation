"""Capability profiles for supported rotary knob event payloads."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

from .const import (
    CAPABILITY_PROFILE_ZHA_ROTATE_TYPE,
    COMMAND_ROTATE_TYPE,
    DEFAULT_CAPABILITY_PROFILE,
    EVENT_ZHA,
    ROTATION_NEXT,
    ROTATION_PREVIOUS,
)


@dataclass(frozen=True, slots=True)
class RotationCapabilityProfile:
    """Describe how a device profile exposes rotation events."""

    profile_id: str
    event_type: str
    command: str
    value_parameter: str
    value_attribute: str
    args_index: int
    rotation_map: Mapping[int, str]


ZHA_ROTATE_TYPE_PROFILE = RotationCapabilityProfile(
    profile_id=CAPABILITY_PROFILE_ZHA_ROTATE_TYPE,
    event_type=EVENT_ZHA,
    command=COMMAND_ROTATE_TYPE,
    value_parameter="rotate_type",
    value_attribute="rotate_type",
    args_index=0,
    rotation_map={
        0: ROTATION_NEXT,
        1: ROTATION_PREVIOUS,
    },
)

CAPABILITY_PROFILES: Mapping[str, RotationCapabilityProfile] = {
    ZHA_ROTATE_TYPE_PROFILE.profile_id: ZHA_ROTATE_TYPE_PROFILE,
}


def capability_profile_from_id(
    profile_id: str | None,
) -> RotationCapabilityProfile:
    """Return a supported capability profile by id."""
    return CAPABILITY_PROFILES.get(
        profile_id or DEFAULT_CAPABILITY_PROFILE, ZHA_ROTATE_TYPE_PROFILE
    )


def rotation_value(
    profile: RotationCapabilityProfile, event_data: dict[str, Any]
) -> int | None:
    """Return the profile-specific rotation value from an event."""
    params = event_data.get("params")
    if isinstance(params, dict) and profile.value_parameter in params:
        try:
            return int(params[profile.value_parameter])
        except (TypeError, ValueError):
            return None

    args = event_data.get("args")
    if isinstance(args, list) and len(args) > profile.args_index:
        try:
            return int(args[profile.args_index])
        except (TypeError, ValueError):
            return None

    return None


def rotation_direction(
    profile: RotationCapabilityProfile, value: int | None
) -> str | None:
    """Return the navigation direction for a profile-specific rotation value."""
    if value is None:
        return None
    return profile.rotation_map.get(value)


def profile_to_frontend(profile: RotationCapabilityProfile) -> dict[str, Any]:
    """Return a JSON-serializable frontend profile payload."""
    return {
        "id": profile.profile_id,
        "event_type": profile.event_type,
        "command": profile.command,
        "value_parameter": profile.value_parameter,
        "value_attribute": profile.value_attribute,
        "args_index": profile.args_index,
        "rotate": {
            str(value): direction
            for value, direction in profile.rotation_map.items()
        },
    }
