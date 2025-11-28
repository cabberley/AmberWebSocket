"""Config flow for the Amber WebSocket integration."""
from __future__ import annotations

from typing import Any

import voluptuous as vol
from homeassistant import config_entries

from .const import (
    CONF_AUTH_TOKEN,
    CONF_CHANNEL_CONTROLLED_LOAD,
    CONF_CHANNEL_FEED_IN,
    CONF_CHANNEL_GENERAL,
    CONF_DEBUG_LOGGING,
    CONF_SITE_ID,
    DEFAULT_CONTROLLED_LOAD_ENABLED,
    DEFAULT_FEED_IN_ENABLED,
    DEFAULT_GENERAL_ENABLED,
    DOMAIN,
)


class AmberConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):  # type: ignore[misc]
    """Handle a config flow for Amber WebSocket."""

    VERSION = 1

    async def async_step_user(self, user_input: dict[str, Any] | None = None):
        if user_input is not None:
            await self.async_set_unique_id(user_input[CONF_SITE_ID])
            self._abort_if_unique_id_configured()
            return self.async_create_entry(
                title=f"Amber {user_input[CONF_SITE_ID]}",
                data=user_input,
            )

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_AUTH_TOKEN): str,
                    vol.Required(CONF_SITE_ID): str,
                }
            ),
        )

    @staticmethod
    def async_get_options_flow(config_entry):
        return AmberOptionsFlow(config_entry)


class AmberOptionsFlow(config_entries.OptionsFlow):
    """Handle Amber WebSocket options."""

    def __init__(self, entry: config_entries.ConfigEntry) -> None:
        self.entry = entry

    async def async_step_init(self, user_input: dict[str, Any] | None = None):
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        current = self.entry.options.get(CONF_DEBUG_LOGGING, False)
        general_enabled = self.entry.options.get(CONF_CHANNEL_GENERAL, DEFAULT_GENERAL_ENABLED)
        feed_enabled = self.entry.options.get(CONF_CHANNEL_FEED_IN, DEFAULT_FEED_IN_ENABLED)
        controlled_enabled = self.entry.options.get(
            CONF_CHANNEL_CONTROLLED_LOAD, DEFAULT_CONTROLLED_LOAD_ENABLED
        )
        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Optional(CONF_DEBUG_LOGGING, default=current): bool,
                    vol.Optional(CONF_CHANNEL_GENERAL, default=general_enabled): bool,
                    vol.Optional(CONF_CHANNEL_FEED_IN, default=feed_enabled): bool,
                    vol.Optional(
                        CONF_CHANNEL_CONTROLLED_LOAD, default=controlled_enabled
                    ): bool,
                }
            ),
        )
