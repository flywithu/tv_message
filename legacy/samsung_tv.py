"""Samsung TV WebSocket client."""

import asyncio
import base64
import json
import logging
from typing import Any
from io import BytesIO
import subprocess
import time

import aiohttp

try:
    from PIL import Image, ImageDraw, ImageFont
except ImportError:
    Image = None

try:
    from .const import DEFAULT_PORT, DEFAULT_TIMEOUT, STATE_OFF, STATE_ON
except ImportError:
    from const import DEFAULT_PORT, DEFAULT_TIMEOUT, STATE_OFF, STATE_ON

_LOGGER = logging.getLogger(__name__)

# Samsung TV Remote Control Keys
KEYS = {
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
    "VOLUME_UP": "KEY_VOLUP",
    "VOLUME_DOWN": "KEY_VOLDOWN",
}

# HDMI Input Sources
HDMI_SOURCES = {
    "HDMI1": "HDMI1",
    "HDMI2": "HDMI2",
    "HDMI3": "HDMI3",
    "HDMI4": "HDMI4",
}


class SamsungTV:
    """Client for Samsung TV WebSocket API."""

    def __init__(self, host: str, port: int = DEFAULT_PORT, timeout: int = DEFAULT_TIMEOUT) -> None:
        """Initialize Samsung TV client."""
        self.host = host
        self.port = port
        self.timeout = timeout
        self.base_url = f"http://{host}:{port}"
        self.ws_url = f"ws://{host}:{port}/api/v2/channels/samsung.remote.control"

    async def _send_command(self, command: str, payload: dict[str, Any] | None = None) -> dict[str, Any] | None:
        """Send command to TV via REST API."""
        try:
            url = f"{self.base_url}/{command}"
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=aiohttp.ClientTimeout(total=self.timeout)) as resp:
                    if resp.status == 200:
                        return await resp.json()
                    else:
                        _LOGGER.error("Command failed with status %d", resp.status)
                        return None
        except asyncio.TimeoutError:
            _LOGGER.error("Command timeout: %s", command)
            return None
        except Exception as err:
            _LOGGER.error("Error sending command %s: %s", command, err)
            return None

    async def get_power_state(self) -> str:
        """Get TV power state."""
        try:
            # Try to connect to determine if TV is on
            async with aiohttp.ClientSession() as session:
                try:
                    async with session.get(
                        f"{self.base_url}/api/v2/",
                        timeout=aiohttp.ClientTimeout(total=2),
                    ) as resp:
                        if resp.status in (200, 401):  # 401 means TV requires auth but is on
                            return STATE_ON
                except (asyncio.TimeoutError, aiohttp.ClientConnectorError):
                    return STATE_OFF
                except Exception:
                    return STATE_OFF
            return STATE_OFF
        except Exception as err:
            _LOGGER.error("Error getting power state: %s", err)
            return STATE_OFF

    async def turn_on(self) -> bool:
        """Turn on TV."""
        try:
            # Use Wake-on-LAN or remote control API
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.base_url}/api/v2/commands/",
                    json={"method": "ms.remote.control", "params": {"Cmd": "Click", "DataCmd": "KEY_POWER"}},
                    timeout=aiohttp.ClientTimeout(total=self.timeout),
                ) as resp:
                    return resp.status == 200
        except Exception as err:
            _LOGGER.error("Error turning on TV: %s", err)
            return False

    async def turn_off(self) -> bool:
        """Turn off TV."""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.base_url}/api/v2/commands/",
                    json={"method": "ms.remote.control", "params": {"Cmd": "Click", "DataCmd": "KEY_POWER"}},
                    timeout=aiohttp.ClientTimeout(total=self.timeout),
                ) as resp:
                    return resp.status == 200
        except Exception as err:
            _LOGGER.error("Error turning off TV: %s", err)
            return False

    async def get_volume(self) -> int | None:
        """Get current volume."""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.base_url}/api/v2/channels/samsung.remote.control?cmd=VOLUME_INFO",
                    timeout=aiohttp.ClientTimeout(total=self.timeout),
                ) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        return data.get("value", {}).get("volume")
        except Exception as err:
            _LOGGER.error("Error getting volume: %s", err)
        return None

    async def set_volume(self, volume: int) -> bool:
        """Set volume level."""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.base_url}/api/v2/commands/",
                    json={
                        "method": "ms.remote.control",
                        "params": {"Cmd": "SetVolume", "Value": volume},
                    },
                    timeout=aiohttp.ClientTimeout(total=self.timeout),
                ) as resp:
                    return resp.status == 200
        except Exception as err:
            _LOGGER.error("Error setting volume: %s", err)
            return False

    async def get_mute(self) -> bool | None:
        """Get mute status."""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.base_url}/api/v2/channels/samsung.remote.control?cmd=MUTE_INFO",
                    timeout=aiohttp.ClientTimeout(total=self.timeout),
                ) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        return data.get("value", {}).get("muted", False)
        except Exception as err:
            _LOGGER.error("Error getting mute status: %s", err)
        return None

    async def set_mute(self, mute: bool) -> bool:
        """Set mute status."""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.base_url}/api/v2/commands/",
                    json={
                        "method": "ms.remote.control",
                        "params": {"Cmd": "SetMute", "Value": mute},
                    },
                    timeout=aiohttp.ClientTimeout(total=self.timeout),
                ) as resp:
                    return resp.status == 200
        except Exception as err:
            _LOGGER.error("Error setting mute: %s", err)
            return False

    async def get_current_app(self) -> str | None:
        """Get currently running app."""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.base_url}/api/v2/channels/currently_playing",
                    timeout=aiohttp.ClientTimeout(total=self.timeout),
                ) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        return data.get("name")
        except Exception as err:
            _LOGGER.error("Error getting current app: %s", err)
        return None

    async def launch_app(self, app_name: str) -> bool:
        """Launch app by name."""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.base_url}/api/v2/channels/",
                    json={"name": app_name},
                    timeout=aiohttp.ClientTimeout(total=self.timeout),
                ) as resp:
                    return resp.status == 200
        except Exception as err:
            _LOGGER.error("Error launching app: %s", err)
            return False

    async def send_key(self, key: str) -> bool:
        """Send remote control key."""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.base_url}/api/v2/commands/",
                    json={
                        "method": "ms.remote.control",
                        "params": {"Cmd": "Click", "DataCmd": key},
                    },
                    timeout=aiohttp.ClientTimeout(total=self.timeout),
                ) as resp:
                    return resp.status == 200
        except Exception as err:
            _LOGGER.error("Error sending key: %s", err)
            return False

    async def get_device_info(self) -> dict[str, Any] | None:
        """Get device information."""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.base_url}/api/v2/",
                    timeout=aiohttp.ClientTimeout(total=self.timeout),
                ) as resp:
                    if resp.status == 200:
                        return await resp.json()
        except Exception as err:
            _LOGGER.error("Error getting device info: %s", err)
        return None

    def _create_message_image(self, message: str, width: int = 1920, height: int = 1080) -> Image.Image | None:
        """Create a message image for display on TV.
        
        Args:
            message: Message to display
            width: Image width (default TV resolution)
            height: Image height (default TV resolution)
            
        Returns:
            PIL Image or None if PIL not available
        """
        if Image is None:
            _LOGGER.error("PIL not installed. Install with: pip install Pillow")
            return None
        
        try:
            # Create black background
            img = Image.new('RGB', (width, height), color='black')
            draw = ImageDraw.Draw(img)
            
            # Try to use a larger font, fallback to default
            try:
                # Try to use a TrueType font for better rendering
                font_size = 120
                font = ImageFont.truetype("C:\\Windows\\Fonts\\arial.ttf", font_size)
            except:
                try:
                    font = ImageFont.truetype("C:\\Windows\\Fonts\\gulim.ttf", 100)  # Korean font
                except:
                    font = ImageFont.load_default()
            
            # Calculate text position (center)
            bbox = draw.textbbox((0, 0), message, font=font)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]
            
            x = (width - text_width) // 2
            y = (height - text_height) // 2
            
            # Draw text with white color
            draw.text((x, y), message, font=font, fill='white')
            
            return img
            
        except Exception as err:
            _LOGGER.error("Error creating message image: %s", err)
            return None

    async def show_message(self, message: str, duration: int = 5) -> bool:
        """Display message on TV screen via Windows Miracast/screen casting.
        
        This method creates a fullscreen message image and displays it on the current
        screen, which can then be cast to the TV via Windows Miracast (Win + A -> Connect).
        
        Args:
            message: Message to display
            duration: Display duration in seconds
            
        Returns:
            True if message was displayed
        """
        try:
            if not 1 <= duration <= 10:
                duration = max(1, min(10, duration))
            
            # Create message image
            img = self._create_message_image(message)
            if img is None:
                _LOGGER.error("Failed to create message image")
                return False
            
            # Save image
            temp_image_path = "message_display.jpg"
            img.save(temp_image_path, quality=95)
            
            # Display using tkinter fullscreen window
            try:
                import tkinter as tk
                
                def display_window():
                    root = tk.Tk()
                    root.attributes('-fullscreen', True)
                    root.attributes('-topmost', True)
                    root.configure(bg='black')
                    
                    # Load and display the saved image
                    from PIL import ImageTk
                    pil_image = Image.open(temp_image_path)
                    photo = ImageTk.PhotoImage(pil_image)
                    
                    label = tk.Label(root, image=photo, bg='black')
                    label.image = photo
                    label.pack(fill=tk.BOTH, expand=True)
                    
                    root.after(int(duration * 1000), root.quit)
                    root.mainloop()
                
                # Run display in thread to avoid blocking
                import threading
                thread = threading.Thread(target=display_window, daemon=True)
                thread.start()
                
                return True
                
            except ImportError:
                _LOGGER.warning("tkinter not available, image saved to: %s", temp_image_path)
                return True
            
        except Exception as err:
            _LOGGER.error("Error showing message: %s", err)
            return False

    async def display_image(self, image_url: str) -> bool:
        """Display image on TV screen.
        
        Args:
            image_url: URL of image to display
        """
        try:
            async with aiohttp.ClientSession() as session:
                payload = {
                    "method": "ms.remote.control",
                    "params": {
                        "Cmd": "DisplayImage",
                        "Url": image_url,
                    },
                }
                async with session.post(
                    f"{self.base_url}/api/v2/commands/",
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=self.timeout),
                ) as resp:
                    return resp.status in (200, 201)
        except Exception as err:
            _LOGGER.error("Error displaying image: %s", err)
            return False

    async def set_channel(self, channel: int) -> bool:
        """Change TV channel.
        
        Args:
            channel: Channel number (0-999)
        """
        try:
            if not 0 <= channel <= 999:
                _LOGGER.error("Channel must be between 0 and 999")
                return False
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.base_url}/api/v2/commands/",
                    json={
                        "method": "ms.remote.control",
                        "params": {"Cmd": "SetChannel", "Value": str(channel)},
                    },
                    timeout=aiohttp.ClientTimeout(total=self.timeout),
                ) as resp:
                    return resp.status == 200
        except Exception as err:
            _LOGGER.error("Error setting channel: %s", err)
            return False

    async def set_input_source(self, source: str) -> bool:
        """Set TV input source (HDMI, etc).
        
        Args:
            source: Input source (HDMI1, HDMI2, HDMI3, HDMI4, TV)
        """
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.base_url}/api/v2/commands/",
                    json={
                        "method": "ms.remote.control",
                        "params": {"Cmd": "SetSource", "Value": source},
                    },
                    timeout=aiohttp.ClientTimeout(total=self.timeout),
                ) as resp:
                    return resp.status == 200
        except Exception as err:
            _LOGGER.error("Error setting input source: %s", err)
            return False

    async def get_input_source(self) -> str | None:
        """Get current input source."""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.base_url}/api/v2/channels/currentInputSource",
                    timeout=aiohttp.ClientTimeout(total=self.timeout),
                ) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        return data.get("value", {}).get("inputSource")
        except Exception as err:
            _LOGGER.error("Error getting input source: %s", err)
        return None

    async def set_brightness(self, brightness: int) -> bool:
        """Set TV brightness.
        
        Args:
            brightness: Brightness level (0-100)
        """
        try:
            if not 0 <= brightness <= 100:
                _LOGGER.error("Brightness must be between 0 and 100")
                return False
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.base_url}/api/v2/commands/",
                    json={
                        "method": "ms.remote.control",
                        "params": {"Cmd": "SetBrightness", "Value": brightness},
                    },
                    timeout=aiohttp.ClientTimeout(total=self.timeout),
                ) as resp:
                    return resp.status == 200
        except Exception as err:
            _LOGGER.error("Error setting brightness: %s", err)
            return False

    async def get_brightness(self) -> int | None:
        """Get current brightness level."""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.base_url}/api/v2/channels/samsung.remote.control?cmd=BRIGHTNESS_INFO",
                    timeout=aiohttp.ClientTimeout(total=self.timeout),
                ) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        return data.get("value", {}).get("brightness")
        except Exception as err:
            _LOGGER.error("Error getting brightness: %s", err)
        return None

    async def set_contrast(self, contrast: int) -> bool:
        """Set TV contrast.
        
        Args:
            contrast: Contrast level (0-100)
        """
        try:
            if not 0 <= contrast <= 100:
                _LOGGER.error("Contrast must be between 0 and 100")
                return False
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.base_url}/api/v2/commands/",
                    json={
                        "method": "ms.remote.control",
                        "params": {"Cmd": "SetContrast", "Value": contrast},
                    },
                    timeout=aiohttp.ClientTimeout(total=self.timeout),
                ) as resp:
                    return resp.status == 200
        except Exception as err:
            _LOGGER.error("Error setting contrast: %s", err)
            return False

    async def get_contrast(self) -> int | None:
        """Get current contrast level."""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.base_url}/api/v2/channels/samsung.remote.control?cmd=CONTRAST_INFO",
                    timeout=aiohttp.ClientTimeout(total=self.timeout),
                ) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        return data.get("value", {}).get("contrast")
        except Exception as err:
            _LOGGER.error("Error getting contrast: %s", err)
        return None

    async def set_color(self, color: int) -> bool:
        """Set TV color saturation.
        
        Args:
            color: Color saturation level (0-100)
        """
        try:
            if not 0 <= color <= 100:
                _LOGGER.error("Color must be between 0 and 100")
                return False
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.base_url}/api/v2/commands/",
                    json={
                        "method": "ms.remote.control",
                        "params": {"Cmd": "SetColor", "Value": color},
                    },
                    timeout=aiohttp.ClientTimeout(total=self.timeout),
                ) as resp:
                    return resp.status == 200
        except Exception as err:
            _LOGGER.error("Error setting color: %s", err)
            return False

    async def get_supported_channels(self) -> list[dict[str, Any]] | None:
        """Get list of supported channels."""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.base_url}/api/v2/channels/",
                    timeout=aiohttp.ClientTimeout(total=self.timeout),
                ) as resp:
                    if resp.status == 200:
                        return await resp.json()
        except Exception as err:
            _LOGGER.error("Error getting channels: %s", err)
        return None

    async def get_supported_apps(self) -> list[dict[str, Any]] | None:
        """Get list of installed apps."""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.base_url}/api/v2/apps/",
                    timeout=aiohttp.ClientTimeout(total=self.timeout),
                ) as resp:
                    if resp.status == 200:
                        return await resp.json()
        except Exception as err:
            _LOGGER.error("Error getting apps: %s", err)
        return None

    async def get_tv_settings(self) -> dict[str, Any] | None:
        """Get current TV settings."""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.base_url}/api/v2/tvSettings/",
                    timeout=aiohttp.ClientTimeout(total=self.timeout),
                ) as resp:
                    if resp.status == 200:
                        return await resp.json()
        except Exception as err:
            _LOGGER.error("Error getting TV settings: %s", err)
        return None

    async def set_sleep_timer(self, minutes: int) -> bool:
        """Set TV sleep timer.
        
        Args:
            minutes: Sleep timer duration in minutes (1-180)
        """
        try:
            if not 1 <= minutes <= 180:
                _LOGGER.error("Sleep timer must be between 1 and 180 minutes")
                return False
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.base_url}/api/v2/commands/",
                    json={
                        "method": "ms.remote.control",
                        "params": {"Cmd": "SetSleepTimer", "Value": minutes},
                    },
                    timeout=aiohttp.ClientTimeout(total=self.timeout),
                ) as resp:
                    return resp.status == 200
        except Exception as err:
            _LOGGER.error("Error setting sleep timer: %s", err)
            return False

    async def get_sleep_timer(self) -> int | None:
        """Get current sleep timer value."""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.base_url}/api/v2/channels/samsung.remote.control?cmd=SLEEP_TIMER_INFO",
                    timeout=aiohttp.ClientTimeout(total=self.timeout),
                ) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        return data.get("value", {}).get("sleepTimer")
        except Exception as err:
            _LOGGER.error("Error getting sleep timer: %s", err)
        return None

    async def set_dynamic_contrast(self, enabled: bool) -> bool:
        """Enable/disable dynamic contrast.
        
        Args:
            enabled: True to enable, False to disable
        """
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.base_url}/api/v2/commands/",
                    json={
                        "method": "ms.remote.control",
                        "params": {"Cmd": "SetDynamicContrast", "Value": "On" if enabled else "Off"},
                    },
                    timeout=aiohttp.ClientTimeout(total=self.timeout),
                ) as resp:
                    return resp.status == 200
        except Exception as err:
            _LOGGER.error("Error setting dynamic contrast: %s", err)
            return False

    async def set_hdr(self, enabled: bool) -> bool:
        """Enable/disable HDR.
        
        Args:
            enabled: True to enable, False to disable
        """
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.base_url}/api/v2/commands/",
                    json={
                        "method": "ms.remote.control",
                        "params": {"Cmd": "SetHDR", "Value": "On" if enabled else "Off"},
                    },
                    timeout=aiohttp.ClientTimeout(total=self.timeout),
                ) as resp:
                    return resp.status == 200
        except Exception as err:
            _LOGGER.error("Error setting HDR: %s", err)
            return False

    async def reboot(self) -> bool:
        """Reboot the TV."""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.base_url}/api/v2/commands/",
                    json={
                        "method": "ms.remote.control",
                        "params": {"Cmd": "Reboot"},
                    },
                    timeout=aiohttp.ClientTimeout(total=self.timeout),
                ) as resp:
                    return resp.status == 200
        except Exception as err:
            _LOGGER.error("Error rebooting TV: %s", err)
            return False
