"""Show an image on a DLNA/UPnP MediaRenderer (e.g. Samsung Tizen TV)."""

from __future__ import annotations

import logging
from xml.sax.saxutils import escape

import aiohttp

_LOGGER = logging.getLogger(__name__)

AVT = "urn:schemas-upnp-org:service:AVTransport:1"
CONTROL_PATH = "/upnp/control/AVTransport1"


async def _soap(
    session: aiohttp.ClientSession, host: str, port: int, action: str, args: str
) -> None:
    body = (
        '<?xml version="1.0" encoding="utf-8"?>'
        '<s:Envelope xmlns:s="http://schemas.xmlsoap.org/soap/envelope/" '
        's:encodingStyle="http://schemas.xmlsoap.org/soap/encoding/"><s:Body>'
        f'<u:{action} xmlns:u="{AVT}">{args}</u:{action}></s:Body></s:Envelope>'
    )
    headers = {
        "Content-Type": 'text/xml; charset="utf-8"',
        "SOAPACTION": f'"{AVT}#{action}"',
    }
    async with session.post(
        f"http://{host}:{port}{CONTROL_PATH}",
        data=body.encode(),
        headers=headers,
        timeout=aiohttp.ClientTimeout(total=8),
    ) as resp:
        if resp.status != 200:
            raise RuntimeError(f"{action} -> HTTP {resp.status}")


async def async_show_image(
    session: aiohttp.ClientSession, host: str, port: int, image_url: str
) -> None:
    """Point the renderer at *image_url* and start playback."""
    didl = (
        '<DIDL-Lite xmlns="urn:schemas-upnp-org:metadata-1-0/DIDL-Lite/" '
        'xmlns:dc="http://purl.org/dc/elements/1.1/" '
        'xmlns:upnp="urn:schemas-upnp-org:metadata-1-0/upnp/">'
        '<item id="0" parentID="-1" restricted="1"><dc:title>message</dc:title>'
        "<upnp:class>object.item.imageItem.photo</upnp:class>"
        '<res protocolInfo="http-get:*:image/jpeg:DLNA.ORG_PN=JPEG_LRG;DLNA.ORG_OP=00">'
        f"{escape(image_url)}</res></item></DIDL-Lite>"
    )
    await _soap(
        session, host, port, "SetAVTransportURI",
        f"<InstanceID>0</InstanceID><CurrentURI>{escape(image_url)}</CurrentURI>"
        f"<CurrentURIMetaData>{escape(didl)}</CurrentURIMetaData>",
    )
    await _soap(session, host, port, "Play", "<InstanceID>0</InstanceID><Speed>1</Speed>")


async def async_stop(session: aiohttp.ClientSession, host: str, port: int) -> None:
    await _soap(session, host, port, "Stop", "<InstanceID>0</InstanceID>")
