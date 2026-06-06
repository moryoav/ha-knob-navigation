"""Test configuration for Knob Swipe Navigation."""

from __future__ import annotations

import os

import pytest
import pytest_socket

if os.name == "nt":
    def _disable_socket_allowing_asyncio_socketpair(
        *args: object, **kwargs: object
    ) -> None:
        """Allow Windows asyncio event loops to create their local socketpair."""
        pytest_socket.enable_socket()

    pytest_socket.disable_socket = _disable_socket_allowing_asyncio_socketpair

pytest_plugins = "pytest_homeassistant_custom_component"


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations):
    """Enable custom integrations in Home Assistant tests."""
    yield
