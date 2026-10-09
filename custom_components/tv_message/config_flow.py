"""Config flow for TV Message."""

from __future__ import annotations

from typing import Any

import voluptuous as vol

from homeassistant.config_entries import ConfigFlow, ConfigFlowResult, OptionsFlow
from homeassistant.const import CONF_HOST, CONF_NAME

from .const import (
    CONF_BASE_URL,
    CONF_DLNA_PORT,
    CONF_PROTOCOL,
    DEFAULT_DLNA_PORT,
    DOMAIN,
    PROTOCOL_AUTO,
    PROTOCOLS,
)


class TvMessageConfigFlow(ConfigFlow, domain=DOMAIN):
    """Register a TV. The TV may be off, so no connection test is done."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        errors: dict[str, str] = {}
        if user_input is not None:
            host = user_input[CONF_HOST].strip()
            if not host:
                errors[CONF_HOST] = "invalid_host"
            else:
                await self.async_set_unique_id(host)
                self._abort_if_unique_id_configured()
                data = {**user_input, CONF_HOST: host}
                if not data.get(CONF_BASE_URL):
                    data.pop(CONF_BASE_URL, None)
                return self.async_create_entry(title=user_input[CONF_NAME], data=data)

        schema = vol.Schema(
            {
                vol.Required(CONF_NAME, default="TV Message"): str,
                vol.Required(CONF_HOST): str,
                vol.Required(CONF_PROTOCOL, default=PROTOCOL_AUTO): vol.In(PROTOCOLS),
                vol.Optional(CONF_DLNA_PORT, default=DEFAULT_DLNA_PORT): int,
                vol.Optional(CONF_BASE_URL): str,
            }
        )
        return self.async_show_form(step_id="user", data_schema=schema, errors=errors)

    @staticmethod
    def async_get_options_flow(config_entry):
        return TvMessageOptionsFlow()


class TvMessageOptionsFlow(OptionsFlow):
    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        if user_input is not None:
            return self.async_create_entry(data=user_input)
        current = self.config_entry.options.get(
            CONF_PROTOCOL, self.config_entry.data.get(CONF_PROTOCOL, PROTOCOL_AUTO)
        )
        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {vol.Required(CONF_PROTOCOL, default=current): vol.In(PROTOCOLS)}
            ),
        )
