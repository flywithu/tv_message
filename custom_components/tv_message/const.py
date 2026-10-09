"""Constants for the TV Message integration."""

from typing import Final

DOMAIN: Final = "tv_message"

CONF_PROTOCOL: Final = "protocol"
CONF_DLNA_PORT: Final = "dlna_port"
CONF_BASE_URL: Final = "base_url"

PROTOCOL_AUTO: Final = "auto"
PROTOCOL_DLNA: Final = "dlna"
PROTOCOL_CAST: Final = "cast"
PROTOCOLS: Final = [PROTOCOL_AUTO, PROTOCOL_DLNA, PROTOCOL_CAST]

DEFAULT_DLNA_PORT: Final = 9197
CAST_PORT: Final = 8009

ATTR_MESSAGE: Final = "message"
ATTR_DURATION: Final = "duration"
ATTR_HOST: Final = "host"
ATTR_BG_COLOR: Final = "background_color"
ATTR_FG_COLOR: Final = "text_color"
ATTR_WAIT: Final = "wait_for_tv"

DEFAULT_DURATION: Final = 10
DEFAULT_WAIT: Final = 30
RETRY_INTERVAL: Final = 3

SERVICE_SHOW: Final = "show"
SERVICE_CLEAR: Final = "clear"

IMAGE_URL: Final = "/api/tv_message/{token}.jpg"
