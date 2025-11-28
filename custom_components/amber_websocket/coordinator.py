"""State coordinator for Amber websocket payloads."""
from __future__ import annotations

import logging
from collections.abc import Callable
from datetime import datetime
from typing import Any

from homeassistant.util import dt as dt_util

_LOGGER = logging.getLogger(__name__)


class AmberCoordinator:
    """Keep track of the latest payload and notify listeners."""

    def __init__(self, websocket_client, site_id: str) -> None:
        self._listeners: list[Callable[[], None]] = []
        self._channel_cache: dict[str, dict[str, Any]] = {}
        self.data: dict[str, Any] | None = None
        self._last_update: datetime | None = None
        self.site_id = site_id
        websocket_client.add_listener(self._handle_payload)
        _LOGGER.debug("Coordinator initialised for site %s", site_id)

    def _handle_payload(self, payload: dict[str, Any]) -> None:
        self.data = payload
        self._last_update = dt_util.utcnow()
        prices = payload.get("data", {}).get("prices", [])
        self._channel_cache = {
            price.get("channelType"): price for price in prices if price.get("channelType")
        }
        _LOGGER.debug(
            "Site %s received %s channel price entries", self.site_id, len(self._channel_cache)
        )
        for channel, data in self._channel_cache.items():
            _LOGGER.debug("Channel %s data: %s", channel, data)
        for listener in list(self._listeners):
            listener()

    def async_add_listener(self, callback: Callable[[], None]) -> Callable[[], None]:
        """Register a callback for state updates."""
        self._listeners.append(callback)
        _LOGGER.debug("Added listener to coordinator for site %s", self.site_id)

        def _remove() -> None:
            if callback in self._listeners:
                self._listeners.remove(callback)
            _LOGGER.debug("Removed listener from coordinator for site %s", self.site_id)

        return _remove

    def channel_value(self, channel: str, key: str) -> Any:
        """Return the requested field for a given channel."""
        channel_data = self._channel_cache.get(channel)
        #_LOGGER.debug("Channel %s missing for site %s", channel, self.site_id)
        if not channel_data:
            _LOGGER.debug("Channel %s missing for site %s", channel, self.site_id)
            return None
        return channel_data.get(key)

    def last_price_payload(self) -> dict[str, Any] | None:
        """Expose the raw data for other consumers if needed."""
        return self.data

    def last_update_at(self) -> datetime | None:
        """Return when the most recent payload was received."""
        return self._last_update

    def tariff_value(self, channel: str, key: str) -> Any:
        """Return tariffInformation.* fields when present."""
        channel_data = self._channel_cache.get(channel)
        if not channel_data:
            return None
        tariff = channel_data.get("tariffInformation") or {}
        return tariff.get(key)
