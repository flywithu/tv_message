"""TV Message: show a custom message on a TV via DLNA or Google Cast."""

from __future__ import annotations

import asyncio
import logging
import secrets
import socket

import voluptuous as vol
from aiohttp import web

from homeassistant.components.http import HomeAssistantView
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.event import async_call_later

from . import cast, dlna
from .const import (
    ATTR_BG_COLOR,
    ATTR_DURATION,
    ATTR_FG_COLOR,
    ATTR_HOST,
    ATTR_MESSAGE,
    ATTR_WAIT,
    CONF_BASE_URL,
    CONF_DLNA_PORT,
    CONF_PROTOCOL,
    DEFAULT_DLNA_PORT,
    DEFAULT_DURATION,
    DEFAULT_WAIT,
    DOMAIN,
    IMAGE_URL,
    PROTOCOL_AUTO,
    PROTOCOL_CAST,
    PROTOCOL_DLNA,
    RETRY_INTERVAL,
    SERVICE_CLEAR,
    SERVICE_SHOW,
)
from .renderer import render_message

_LOGGER = logging.getLogger(__name__)

COLOR = vol.All(cv.string, vol.Match(r"^#[0-9a-fA-F]{6}$"))

SHOW_SCHEMA = vol.Schema(
    {
        vol.Required(ATTR_MESSAGE): cv.string,
        vol.Optional(ATTR_DURATION, default=DEFAULT_DURATION): vol.All(
            vol.Coerce(int), vol.Range(min=1, max=3600)
        ),
        vol.Optional(ATTR_HOST): cv.string,
        vol.Optional(ATTR_BG_COLOR, default="#1a1a1a"): COLOR,
        vol.Optional(ATTR_FG_COLOR, default="#ffffff"): COLOR,
        vol.Optional(ATTR_WAIT, default=DEFAULT_WAIT): vol.All(
            vol.Coerce(int), vol.Range(min=0, max=300)
        ),
    }
)
CLEAR_SCHEMA = vol.Schema({vol.Optional(ATTR_HOST): cv.string})


class MessageImageView(HomeAssistantView):
    """Serve the rendered message to the TV (unauthenticated, random-token URL)."""

    url = IMAGE_URL.format(token="{token}")
    name = "api:tv_message:image"
    requires_auth = False

    def __init__(self, images: dict[str, bytes]) -> None:
        self._images = images

    async def get(self, request: web.Request, token: str) -> web.Response:
        data = self._images.get(token)
        if data is None:
            return web.Response(status=404)
        return web.Response(body=data, content_type="image/jpeg")

    head = get


def _local_ip(target: str) -> str:
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        sock.connect((target, 9))
        return sock.getsockname()[0]
    finally:
        sock.close()


class TvMessenger:
    """Sends rendered messages to one TV."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry, images: dict) -> None:
        self.hass = hass
        self.entry = entry
        self._images = images
        self._cancel_stop = None

    @property
    def host(self) -> str:
        return self.entry.data[CONF_HOST]

    @property
    def protocol(self) -> str:
        return self.entry.options.get(
            CONF_PROTOCOL, self.entry.data.get(CONF_PROTOCOL, PROTOCOL_AUTO)
        )

    @property
    def dlna_port(self) -> int:
        return int(self.entry.data.get(CONF_DLNA_PORT, DEFAULT_DLNA_PORT))

    def _protocols(self) -> list[str]:
        if self.protocol == PROTOCOL_AUTO:
            return [PROTOCOL_DLNA, PROTOCOL_CAST]
        return [self.protocol]

    async def _base_url(self) -> str:
        if base := self.entry.data.get(CONF_BASE_URL):
            return base.rstrip("/")
        ip = await self.hass.async_add_executor_job(_local_ip, self.host)
        return f"http://{ip}:{self.hass.http.server_port}"

    async def _show(self, protocol: str, url: str) -> None:
        if protocol == PROTOCOL_DLNA:
            await dlna.async_show_image(
                async_get_clientsession(self.hass), self.host, self.dlna_port, url
            )
        else:
            await self.hass.async_add_executor_job(cast.show_image, self.host, url)

    async def _stop(self, protocol: str) -> None:
        if protocol == PROTOCOL_DLNA:
            await dlna.async_stop(
                async_get_clientsession(self.hass), self.host, self.dlna_port
            )
        else:
            await self.hass.async_add_executor_job(cast.stop, self.host)

    async def async_show(
        self, message: str, duration: int, bg: str, fg: str, wait: int
    ) -> None:
        """Show *message*, retrying for *wait* seconds.

        A TV that has just powered on needs a few seconds before its renderer
        answers, so failures are retried until the deadline.
        """
        jpeg = await self.hass.async_add_executor_job(
            render_message, message, (1920, 1080), bg, fg
        )
        token = secrets.token_urlsafe(16)
        self._images[token] = jpeg
        url = await self._base_url() + IMAGE_URL.format(token=token)

        loop = asyncio.get_running_loop()
        deadline = loop.time() + wait
        last_err: Exception | None = None
        used: str | None = None
        while used is None:
            for proto in self._protocols():
                try:
                    await self._show(proto, url)
                    used = proto
                    break
                except Exception as err:  # noqa: BLE001 - try next protocol / retry
                    last_err = err
                    _LOGGER.debug("%s via %s failed: %s", self.host, proto, err)
            if used is None:
                if loop.time() >= deadline:
                    self._images.pop(token, None)
                    raise HomeAssistantError(
                        f"Could not show message on {self.host}: {last_err}"
                    )
                await asyncio.sleep(RETRY_INTERVAL)

        _LOGGER.debug("Message shown on %s via %s", self.host, used)
        self._schedule_stop(used, duration, token)

    def _schedule_stop(self, protocol: str, duration: int, token: str) -> None:
        self.shutdown()

        async def _later(_now) -> None:
            self._cancel_stop = None
            self._images.pop(token, None)
            try:
                await self._stop(protocol)
            except Exception as err:  # noqa: BLE001
                _LOGGER.warning("Stopping message on %s failed: %s", self.host, err)

        self._cancel_stop = async_call_later(self.hass, duration, _later)

    async def async_clear(self) -> None:
        self.shutdown()
        for proto in self._protocols():
            try:
                await self._stop(proto)
                return
            except Exception as err:  # noqa: BLE001
                _LOGGER.debug("clear on %s via %s failed: %s", self.host, proto, err)

    def shutdown(self) -> None:
        """Cancel a pending auto-stop."""
        if self._cancel_stop:
            self._cancel_stop()
            self._cancel_stop = None


def _targets(hass: HomeAssistant, host: str | None) -> list[TvMessenger]:
    messengers: dict[str, TvMessenger] = hass.data[DOMAIN]["messengers"]
    found = [m for m in messengers.values() if host in (None, m.host)]
    if not found:
        raise HomeAssistantError(f"No TV Message device configured for host {host}")
    return found


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    data = hass.data.setdefault(DOMAIN, {"messengers": {}, "images": {}})

    if not data.get("view_registered"):
        hass.http.register_view(MessageImageView(data["images"]))
        data["view_registered"] = True

    data["messengers"][entry.entry_id] = TvMessenger(hass, entry, data["images"])

    if not hass.services.has_service(DOMAIN, SERVICE_SHOW):

        async def handle_show(call: ServiceCall) -> None:
            d = call.data
            await asyncio.gather(
                *(
                    m.async_show(
                        d[ATTR_MESSAGE],
                        d[ATTR_DURATION],
                        d[ATTR_BG_COLOR],
                        d[ATTR_FG_COLOR],
                        d[ATTR_WAIT],
                    )
                    for m in _targets(hass, d.get(ATTR_HOST) or None)
                )
            )

        async def handle_clear(call: ServiceCall) -> None:
            await asyncio.gather(
                *(m.async_clear() for m in _targets(hass, call.data.get(ATTR_HOST) or None))
            )

        hass.services.async_register(DOMAIN, SERVICE_SHOW, handle_show, SHOW_SCHEMA)
        hass.services.async_register(DOMAIN, SERVICE_CLEAR, handle_clear, CLEAR_SCHEMA)

    entry.async_on_unload(entry.add_update_listener(_reload))
    return True


async def _reload(hass: HomeAssistant, entry: ConfigEntry) -> None:
    await hass.config_entries.async_reload(entry.entry_id)


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    data = hass.data[DOMAIN]
    if messenger := data["messengers"].pop(entry.entry_id, None):
        messenger.shutdown()
    if not data["messengers"]:
        hass.services.async_remove(DOMAIN, SERVICE_SHOW)
        hass.services.async_remove(DOMAIN, SERVICE_CLEAR)
    return True
