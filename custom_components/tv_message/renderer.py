"""Render a message into a JPEG (no Home Assistant dependency)."""

from __future__ import annotations

import io
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

FONT_PATH = Path(__file__).parent / "fonts" / "NanumGothic-Bold.ttf"


def _load_font(size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    try:
        return ImageFont.truetype(str(FONT_PATH), size)
    except OSError:
        return ImageFont.load_default()


def render_message(
    text: str,
    size: tuple[int, int] = (1920, 1080),
    background: str = "#1a1a1a",
    foreground: str = "#ffffff",
) -> bytes:
    """Return a JPEG with *text* centred; long text shrinks and wraps on newlines."""
    img = Image.new("RGB", size, background)
    draw = ImageDraw.Draw(img)

    fsize = 160
    while True:
        font = _load_font(fsize)
        box = draw.multiline_textbbox((0, 0), text, font=font, align="center")
        if fsize <= 40 or (
            box[2] - box[0] <= size[0] * 0.9 and box[3] - box[1] <= size[1] * 0.8
        ):
            break
        fsize -= 10

    x = (size[0] - (box[2] - box[0])) // 2 - box[0]
    y = (size[1] - (box[3] - box[1])) // 2 - box[1]
    draw.multiline_text((x, y), text, fill=foreground, font=font, align="center")

    buf = io.BytesIO()
    img.save(buf, "JPEG", quality=92)
    return buf.getvalue()
