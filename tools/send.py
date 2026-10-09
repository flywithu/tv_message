#!/usr/bin/env python3
"""Send a message to a TV from the command line (same code as the HA plugin).

    python tools/send.py 192.168.10.38 "지금은 취침시간입니다." --duration 10
    python tools/send.py 192.168.10.19 "안녕" --protocol cast
    python tools/send.py 192.168.10.38 --clear
"""

from __future__ import annotations

import argparse
import asyncio
import http.server
import secrets
import socket
import sys
import threading
from pathlib import Path

import aiohttp

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "custom_components" / "tv_message"))
import cast  # noqa: E402
import dlna  # noqa: E402
from renderer import render_message  # noqa: E402


def local_ip(target: str) -> str:
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect((target, 9))
        return s.getsockname()[0]
    finally:
        s.close()


def serve(jpeg: bytes, path: str, port: int) -> http.server.ThreadingHTTPServer:
    class Handler(http.server.BaseHTTPRequestHandler):
        def _send(self, body: bool) -> None:
            if self.path != path:
                self.send_response(404)
                self.end_headers()
                return
            self.send_response(200)
            self.send_header("Content-Type", "image/jpeg")
            self.send_header("Content-Length", str(len(jpeg)))
            self.end_headers()
            if body:
                self.wfile.write(jpeg)

        def do_GET(self):
            self._send(True)

        def do_HEAD(self):
            self._send(False)

        def log_message(self, *args):
            pass

    server = http.server.ThreadingHTTPServer(("0.0.0.0", port), Handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    return server


async def run(args: argparse.Namespace) -> int:
    protocols = ["dlna", "cast"] if args.protocol == "auto" else [args.protocol]

    async with aiohttp.ClientSession() as session:
        if args.clear:
            for proto in protocols:
                try:
                    if proto == "dlna":
                        await dlna.async_stop(session, args.host, args.dlna_port)
                    else:
                        await asyncio.to_thread(cast.stop, args.host)
                    print(f"cleared via {proto}")
                    return 0
                except Exception as err:  # noqa: BLE001
                    print(f"{proto}: {err}")
            return 1

        jpeg = render_message(args.message, (1920, 1080), args.bg, args.fg)
        path = f"/{secrets.token_urlsafe(8)}.jpg"
        server = serve(jpeg, path, args.http_port)
        url = f"http://{local_ip(args.host)}:{args.http_port}{path}"
        try:
            used = None
            for proto in protocols:
                try:
                    if proto == "dlna":
                        await dlna.async_show_image(session, args.host, args.dlna_port, url)
                    else:
                        await asyncio.to_thread(cast.show_image, args.host, url)
                    used = proto
                    break
                except Exception as err:  # noqa: BLE001
                    print(f"{proto} failed: {err}")
            if used is None:
                return 1
            print(f"shown via {used} ({url}); removing in {args.duration}s")
            await asyncio.sleep(args.duration)
            if used == "dlna":
                await dlna.async_stop(session, args.host, args.dlna_port)
            else:
                await asyncio.to_thread(cast.stop, args.host)
            return 0
        finally:
            server.shutdown()


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("host")
    p.add_argument("message", nargs="?", default="")
    p.add_argument("--protocol", choices=["auto", "dlna", "cast"], default="auto")
    p.add_argument("--duration", type=int, default=10)
    p.add_argument("--dlna-port", type=int, default=9197)
    p.add_argument("--http-port", type=int, default=8765)
    p.add_argument("--bg", default="#1a1a1a")
    p.add_argument("--fg", default="#ffffff")
    p.add_argument("--clear", action="store_true", help="stop the message that is showing")
    args = p.parse_args()
    if not args.clear and not args.message:
        p.error("message is required unless --clear")
    sys.exit(asyncio.run(run(args)))


if __name__ == "__main__":
    main()
