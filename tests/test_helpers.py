"""Tests for Knob Swipe Navigation helpers."""

from __future__ import annotations

from custom_components.knob_swipe_navigation.const import (
    CONF_COOLDOWN_MS,
    CONF_DASHBOARD_PATH,
    CONF_NAVIGATION_ENABLED,
    CONF_OVERLAY_TIMEOUT_MS,
    DEFAULT_DASHBOARD_PATH,
    MAX_COOLDOWN_MS,
)
from custom_components.knob_swipe_navigation.helpers import (
    normalize_dashboard_path,
    settings_from_mapping,
    settings_to_options,
)


def test_normalize_dashboard_path() -> None:
    """Test dashboard path normalization."""
    assert normalize_dashboard_path("lovelace") == "lovelace"
    assert normalize_dashboard_path("/dashboard-home/default_view?kiosk") == (
        "dashboard-home"
    )
    assert normalize_dashboard_path("http://ha.local:8123/kitchen/0") == "kitchen"
    assert normalize_dashboard_path("") == DEFAULT_DASHBOARD_PATH
    assert normalize_dashboard_path(None) == DEFAULT_DASHBOARD_PATH


def test_settings_from_mapping_clamps_and_defaults() -> None:
    """Test settings are normalized from options."""
    settings = settings_from_mapping(
        {
            CONF_DASHBOARD_PATH: "/tablet/home",
            CONF_NAVIGATION_ENABLED: False,
            CONF_OVERLAY_TIMEOUT_MS: 999999,
            CONF_COOLDOWN_MS: -1,
        }
    )

    assert settings.dashboard_path == "tablet"
    assert settings.navigation_enabled is False
    assert settings.overlay_timeout_ms == 10000
    assert settings.cooldown_ms == 0


def test_settings_to_options_round_trip() -> None:
    """Test settings serialize to config entry options."""
    settings = settings_from_mapping({CONF_COOLDOWN_MS: MAX_COOLDOWN_MS})
    options = settings_to_options(settings)

    assert options[CONF_DASHBOARD_PATH] == DEFAULT_DASHBOARD_PATH
    assert options[CONF_COOLDOWN_MS] == MAX_COOLDOWN_MS
