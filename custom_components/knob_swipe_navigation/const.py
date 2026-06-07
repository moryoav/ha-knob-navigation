"""Constants for Knob Swipe Navigation."""

from __future__ import annotations

DOMAIN = "knob_swipe_navigation"

FRONTEND_URL_PATH = "/knob_swipe_navigation"
FRONTEND_MODULE = "knob-swipe-navigation.js"
FRONTEND_MODULE_URL = f"{FRONTEND_URL_PATH}/{FRONTEND_MODULE}?v=0.3.6"

WS_TYPE_CONFIG = f"{DOMAIN}/config"
WS_TYPE_SUBSCRIBE_ROTATIONS = f"{DOMAIN}/subscribe_rotations"
WS_TYPE_NAVIGATION_RESULT = f"{DOMAIN}/navigation_result"

EVENT_ZHA = "zha_event"
COMMAND_ROTATE_TYPE = "rotate_type"
ROTATION_NEXT = "next"
ROTATION_PREVIOUS = "previous"

CAPABILITY_PROFILE_ZHA_ROTATE_TYPE = "zha_rotate_type"
DEFAULT_CAPABILITY_PROFILE = CAPABILITY_PROFILE_ZHA_ROTATE_TYPE

CONF_DASHBOARD_PATH = "dashboard_path"
CONF_CAPABILITY_PROFILE = "capability_profile"
CONF_NAVIGATION_ENABLED = "navigation_enabled"
CONF_OVERLAY_ENABLED = "overlay_enabled"
CONF_OVERLAY_TIMEOUT_MS = "overlay_timeout_ms"
CONF_COOLDOWN_MS = "cooldown_ms"
CONF_WRAP_ENABLED = "wrap_enabled"
CONF_REQUIRE_QUERY_PARAM = "require_query_param"

DEFAULT_DASHBOARD_PATH = "lovelace"
DEFAULT_NAVIGATION_ENABLED = True
DEFAULT_OVERLAY_ENABLED = True
DEFAULT_OVERLAY_TIMEOUT_MS = 2800
DEFAULT_COOLDOWN_MS = 2000
DEFAULT_WRAP_ENABLED = True
DEFAULT_REQUIRE_QUERY_PARAM = ""

MIN_OVERLAY_TIMEOUT_MS = 500
MAX_OVERLAY_TIMEOUT_MS = 10000
MIN_COOLDOWN_MS = 0
MAX_COOLDOWN_MS = 10000

ENTITY_NAVIGATION_ENABLED = "navigation_enabled"
ENTITY_OVERLAY_ENABLED = "overlay_enabled"
ENTITY_WRAP_ENABLED = "wrap_enabled"
ENTITY_OVERLAY_TIMEOUT_MS = "overlay_timeout_ms"
ENTITY_COOLDOWN_MS = "cooldown_ms"
ENTITY_ROTATION = "rotation"
ENTITY_LAST_ROTATION = "last_rotation"
ENTITY_LAST_NAVIGATION_RESULT = "last_navigation_result"

SIGNAL_ROTATION = f"{DOMAIN}_rotation"
SIGNAL_NAVIGATION_RESULT = f"{DOMAIN}_navigation_result"

DEFAULT_NAME = "Knob Swipe Navigation"

REPAIR_ISSUE_DEVICE_NOT_ZHA = "device_not_zha"
