"""Constants for Knob Swipe Navigation."""

from __future__ import annotations

DOMAIN = "knob_swipe_navigation"

FRONTEND_URL_PATH = "/knob_swipe_navigation"
FRONTEND_MODULE = "knob-swipe-navigation.js"
FRONTEND_MODULE_URL = f"{FRONTEND_URL_PATH}/{FRONTEND_MODULE}?v=0.1.1"

WS_TYPE_CONFIG = f"{DOMAIN}/config"

EVENT_ZHA = "zha_event"
COMMAND_ROTATE_TYPE = "rotate_type"

DEFAULT_NAME = "Knob Swipe Navigation"

REPAIR_ISSUE_DEVICE_NOT_ZHA = "device_not_zha"
