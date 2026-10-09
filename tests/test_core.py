"""Tests for the HA-independent core (renderer, DLNA). Run: python -m unittest discover tests"""

import io
import sys
import unittest
from pathlib import Path

import aiohttp
from aiohttp import web
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "custom_components" / "tv_message"))
import dlna  # noqa: E402
from renderer import FONT_PATH, render_message  # noqa: E402


class RendererTest(unittest.TestCase):
    def test_font_bundled(self):
        self.assertTrue(FONT_PATH.exists())

    def test_korean_renders_jpeg_with_text(self):
        img = Image.open(io.BytesIO(render_message("지금은 취침시간입니다.")))
        self.assertEqual(img.size, (1920, 1080))
        self.assertEqual(img.format, "JPEG")
        # text pixels must differ from the plain background
        self.assertGreater(len({img.getpixel((x, 540)) for x in range(0, 1920, 7)}), 5)

    def test_long_text_still_fits(self):
        img = Image.open(io.BytesIO(render_message("아주 긴 문장입니다. " * 10)))
        self.assertEqual(img.size, (1920, 1080))


class DlnaTest(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.calls = []

        async def handler(request):
            self.calls.append((request.headers["SOAPACTION"], await request.text()))
            return web.Response(text="<ok/>")

        app = web.Application()
        app.router.add_post(dlna.CONTROL_PATH, handler)
        self.runner = web.AppRunner(app)
        await self.runner.setup()
        site = web.TCPSite(self.runner, "127.0.0.1", 0)
        await site.start()
        self.port = site._server.sockets[0].getsockname()[1]
        self.session = aiohttp.ClientSession()

    async def asyncTearDown(self):
        await self.session.close()
        await self.runner.cleanup()

    async def test_show_sends_seturi_then_play(self):
        await dlna.async_show_image(self.session, "127.0.0.1", self.port, "http://h/a.jpg?x=1&y=2")
        actions = [c[0].split("#")[1].strip('"') for c in self.calls]
        self.assertEqual(actions, ["SetAVTransportURI", "Play"])
        self.assertIn("a.jpg?x=1&amp;y=2", self.calls[0][1])  # URL is XML-escaped

    async def test_stop(self):
        await dlna.async_stop(self.session, "127.0.0.1", self.port)
        self.assertTrue(self.calls[0][0].endswith('#Stop"'))

    async def test_http_error_raises(self):
        with self.assertRaises(Exception):
            await dlna.async_stop(self.session, "127.0.0.1", 1)  # nothing listens


if __name__ == "__main__":
    unittest.main()
