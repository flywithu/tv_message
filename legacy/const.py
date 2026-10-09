"""Constants for the Samsung TV integration."""

from typing import Final

DOMAIN: Final = "samsung_tv"
MANUFACTURER: Final = "Samsung"

# Device states
STATE_ON: Final = "on"
STATE_OFF: Final = "off"
STATE_UNKNOWN: Final = "unknown"

# Attributes
ATTR_POWER: Final = "power"
ATTR_VOLUME: Final = "volume"
ATTR_CHANNEL: Final = "channel"
ATTR_SOURCE: Final = "source"
ATTR_MODEL: Final = "model"
ATTR_MAC_ADDRESS: Final = "mac_address"
ATTR_APP_NAME: Final = "app_name"
ATTR_BRIGHTNESS: Final = "brightness"
ATTR_CONTRAST: Final = "contrast"
ATTR_COLOR: Final = "color"
ATTR_SLEEP_TIMER: Final = "sleep_timer"

# Config
DEFAULT_PORT: Final = 8002
DEFAULT_TIMEOUT: Final = 5
DEFAULT_POLLING_INTERVAL: Final = 30

# Message display
MESSAGE_MIN_DURATION: Final = 1
MESSAGE_MAX_DURATION: Final = 10
MESSAGE_DEFAULT_DURATION: Final = 5

# Channel settings
MIN_CHANNEL: Final = 0
MAX_CHANNEL: Final = 999

# Picture settings
MIN_BRIGHTNESS: Final = 0
MAX_BRIGHTNESS: Final = 100
MIN_CONTRAST: Final = 0
MAX_CONTRAST: Final = 100
MIN_COLOR: Final = 0
MAX_COLOR: Final = 100

# Sleep timer
MIN_SLEEP_TIMER: Final = 1
MAX_SLEEP_TIMER: Final = 180

# Input sources
INPUT_SOURCE_HDMI1: Final = "HDMI1"
INPUT_SOURCE_HDMI2: Final = "HDMI2"
INPUT_SOURCE_HDMI3: Final = "HDMI3"
INPUT_SOURCE_HDMI4: Final = "HDMI4"
INPUT_SOURCE_TV: Final = "TV"

SUPPORTED_INPUT_SOURCES: Final = [
    INPUT_SOURCE_HDMI1,
    INPUT_SOURCE_HDMI2,
    INPUT_SOURCE_HDMI3,
    INPUT_SOURCE_HDMI4,
    INPUT_SOURCE_TV,
]

# Remote control keys
REMOTE_KEYS: Final = {
    "POWER": "KEY_POWER",
    "HOME": "KEY_HOME",
    "MENU": "KEY_MENU",
    "BACK": "KEY_BACK",
    "UP": "KEY_UP",
    "DOWN": "KEY_DOWN",
    "LEFT": "KEY_LEFT",
    "RIGHT": "KEY_RIGHT",
    "ENTER": "KEY_ENTER",
    "PLAY": "KEY_PLAY",
    "PAUSE": "KEY_PAUSE",
    "NEXT": "KEY_NEXT",
    "PREV": "KEY_PREV",
    "CH_UP": "KEY_CHUP",
    "CH_DOWN": "KEY_CHDOWN",
    "VOL_UP": "KEY_VOLUP",
    "VOL_DOWN": "KEY_VOLDOWN",
}
