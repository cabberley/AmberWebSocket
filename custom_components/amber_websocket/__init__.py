"""Amber WebSocket custom integration."""
from __future__ import annotations

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.typing import ConfigType

from .const import (
    CONF_AUTH_TOKEN,
    CONF_DEBUG_LOGGING,
    CONF_SITE_ID,
    DOMAIN,
    PLATFORMS,
)
from .coordinator import AmberCoordinator
from .websocket_client import AmberWebsocketClient

_LOGGER = logging.getLogger(__package__)


async def async_setup(hass: HomeAssistant, _: ConfigType) -> bool:
    """Set up the integration via YAML (unused but required)."""
    hass.data.setdefault(DOMAIN, {})
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Amber WebSocket from a config entry."""
    hass.data.setdefault(DOMAIN, {})

    _configure_logging(entry)
    entry.async_on_unload(entry.add_update_listener(_async_options_updated))

    client = AmberWebsocketClient(
        hass,
        entry.data[CONF_AUTH_TOKEN],
        entry.data[CONF_SITE_ID],
    )
    coordinator = AmberCoordinator(client, entry.data[CONF_SITE_ID])

    hass.data[DOMAIN][entry.entry_id] = {
        "client": client,
        "coordinator": coordinator,
    }

    await client.async_start()
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    stored = hass.data[DOMAIN].get(entry.entry_id)
    if stored:
        await stored["client"].async_stop()

    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)

    hass.data[DOMAIN].pop(entry.entry_id, None)
    return unload_ok


def _configure_logging(entry: ConfigEntry) -> None:
    is_debug = entry.options.get(CONF_DEBUG_LOGGING, False)
    level = logging.DEBUG if is_debug else logging.INFO
    _LOGGER.setLevel(level)
    if is_debug:
        _LOGGER.debug("Amber WebSocket debug logging enabled")


async def _async_options_updated(hass: HomeAssistant, entry: ConfigEntry) -> None:
    _configure_logging(entry)
    await hass.config_entries.async_reload(entry.entry_id)
