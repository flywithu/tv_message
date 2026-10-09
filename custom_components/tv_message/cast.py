"""Show an image on a Google Cast / Chromecast-compatible receiver (blocking)."""

from __future__ import annotations

import uuid

CAST_PORT = 8009


def _connect(host: str):
    import pychromecast  # imported lazily: only needed for the cast protocol

    cast = pychromecast.get_chromecast_from_host(
        (host, CAST_PORT, uuid.uuid4(), None, host)
    )
    cast.wait(timeout=10)
    return cast


def show_image(host: str, image_url: str) -> None:
    cast = _connect(host)
    try:
        mc = cast.media_controller
        mc.play_media(image_url, "image/jpeg")
        mc.block_until_active(timeout=15)
    finally:
        cast.disconnect()


def stop(host: str) -> None:
    cast = _connect(host)
    try:
        cast.quit_app()
    finally:
        cast.disconnect()
