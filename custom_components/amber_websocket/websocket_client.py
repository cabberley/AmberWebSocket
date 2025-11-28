"""WebSocket client wrapper for Amber live price updates."""
from __future__ import annotations

import asyncio
import json
import logging
from collections.abc import Callable
from typing import Any

from aiohttp import ClientError, ClientWebSocketResponse, WSMsgType
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import (
    EVENT_PRICE_UPDATE,
    MAX_RECONNECT_DELAY,
    MIN_RECONNECT_DELAY,
    ORIGIN_HEADER,
    SUBSCRIBE_SERVICE,
    WS_URL,
)

_LOGGER = logging.getLogger(__name__)


class AmberWebsocketClient:
    """Manage the Amber WebSocket lifecycle and message fan-out."""

    def __init__(self, hass: HomeAssistant, auth_token: str, site_id: str) -> None:
        self._hass = hass
        self._auth_token = auth_token
        self._site_id = site_id
        self._session = async_get_clientsession(hass)
        self._listeners: list[Callable[[dict[str, Any]], None]] = []
        self._task: asyncio.Task | None = None
        self._ws: ClientWebSocketResponse | None = None
        self._stop_event = asyncio.Event()

    def add_listener(self, callback: Callable[[dict[str, Any]], None]) -> Callable[[], None]:
        """Register a callback that fires for each inbound payload."""
        self._listeners.append(callback)

        def _remove() -> None:
            if callback in self._listeners:
                self._listeners.remove(callback)

        return _remove

    async def async_start(self) -> None:
        """Begin the background task if it is not already running."""
        if self._task and not self._task.done():
            return
        self._stop_event.clear()
        self._task = self._hass.async_create_task(self._run(), name="Amber websocket listener")

    async def async_stop(self) -> None:
        """Stop the background task and close the socket."""
        self._stop_event.set()
        if self._ws and not self._ws.closed:
            await self._ws.close()
        if self._task:
            await self._task

    async def _run(self) -> None:
        backoff = MIN_RECONNECT_DELAY
        while not self._stop_event.is_set():
            try:
                await self._connect_and_listen()
                backoff = MIN_RECONNECT_DELAY
            except asyncio.CancelledError:
                raise
            except Exception as err:  # pylint: disable=broad-except
                _LOGGER.warning("Amber websocket error: %s", err)
                await asyncio.sleep(backoff)
                backoff = min(backoff * 2, MAX_RECONNECT_DELAY)

    async def _connect_and_listen(self) -> None:
        headers = {
            "authorization": f"Bearer {self._auth_token}",
            "Origin": ORIGIN_HEADER,
        }
        subscribe_payload = {
            "service": SUBSCRIBE_SERVICE,
            "action": "subscribe",
            "data": {"siteId": self._site_id},
        }
        async with self._session.ws_connect(WS_URL, headers=headers, heartbeat=30) as ws:
            self._ws = ws
            _LOGGER.info("Connected to Amber websocket for site %s", self._site_id)
            await ws.send_str(json.dumps(subscribe_payload))
            async for msg in ws:
                if msg.type == WSMsgType.TEXT:
                    self._handle_message(msg.data)
                elif msg.type == WSMsgType.ERROR:
                    raise ClientError("Amber websocket closed with error")
                elif msg.type in (WSMsgType.CLOSED, WSMsgType.CLOSING):
                    break
        self._ws = None

    def _handle_message(self, payload: str) -> None:
        try:
            data = json.loads(payload)
        except json.JSONDecodeError:
            _LOGGER.debug("Received non-JSON payload: %s", payload)
            return
        self._hass.bus.async_fire(
            EVENT_PRICE_UPDATE,
            {"site_id": self._site_id, "payload": data},
        )
        for callback in list(self._listeners):
            callback(data)
