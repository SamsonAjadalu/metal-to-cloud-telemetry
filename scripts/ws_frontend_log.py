#!/usr/bin/env python3
"""
Production backend host (same idea as telemetry_bridge):
  ws://159.203.4.11:8000/ws/frontend
  ws://159.203.4.11:8000/ws/robot/<robot_id>

  tap / listen — Extra client on /ws/frontend. Server almost only PUSHES telemetry here.
                 Goals/commands are sent by the BROWSER on its own socket — they will
                 NOT show up on tap. Use `frontend` MITM to log those.

  frontend — MITM: logs CLIENT→SERVER (goals, commands from UI). Hides telemetry
               on SERVER→CLIENT unless --show-telemetry.

  robot <id> — MITM for telemetry_bridge: logs SERVER→CLIENT (commands to robot).
               Hides bridge→server telemetry spam. Point bridge WS URL at this port.

  robots [id …] — Read backend /ws/robot/<id> directly for several bots at once
                  (default: tb3_001 tb3_002). Same caveats as tap: extra clients may
                  not receive copies of commands meant for the real bridge.

  pip install websockets
"""

from __future__ import annotations

# Same backend host as robot_bridge telemetry_bridge.py
DEFAULT_FRONTEND_WS = "ws://159.203.4.11:8000/ws/frontend"
DEFAULT_ROBOT_WS_BASE = "ws://159.203.4.11:8000"

import argparse
import asyncio
import json
import sys


def _is_telemetry_json(raw: str | bytes) -> bool:
    try:
        text = raw.decode() if isinstance(raw, bytes) else raw
        data = json.loads(text)
        return data.get("type") == "telemetry"
    except (json.JSONDecodeError, TypeError, UnicodeDecodeError):
        return False


def _print_frame(direction: str, raw: str | bytes) -> None:
    text = raw.decode() if isinstance(raw, bytes) else raw
    print(f"\n{'=' * 60}\n{direction}\n{'-' * 60}", flush=True)
    try:
        data = json.loads(text)
        t = data.get("type")
        print(f"type: {t!r}", flush=True)
        print(json.dumps(data, indent=2), flush=True)
    except json.JSONDecodeError:
        print(repr(text[:4000]), flush=True)


async def run_listen(url: str, *, show_telemetry: bool) -> None:
    import websockets

    hide = not show_telemetry
    print(
        f"Direct connect (no proxy): {url}\n"
        f"Logging SERVER → this client."
        + (" Hiding type=telemetry (use --show-telemetry to print it).\n" if hide else "\n")
        + "\n*** This socket will NOT show goals/commands from the website. ***\n"
        "Those go browser→server on the browser’s connection only.\n"
        "To log them:  python3 scripts/ws_frontend_log.py frontend --port 9876\n"
        "then set the app WebSocket to  ws://127.0.0.1:9876/ws/frontend\n\n"
        "To log commands sent TO the robot:  python3 scripts/ws_frontend_log.py robot tb3_001\n"
        "then point telemetry_bridge at  ws://127.0.0.1:9877/ws/robot/tb3_001\n",
        flush=True,
    )
    suppressed = 0
    async with websockets.connect(url) as ws:
        print("Connected.\n", flush=True)
        async for message in ws:
            if hide and _is_telemetry_json(message):
                suppressed += 1
                if suppressed % 200 == 0:
                    print(
                        f"[suppressed {suppressed} telemetry frames — tap cannot see UI goals/commands]\n",
                        flush=True,
                    )
                continue
            _print_frame("SERVER → THIS CLIENT", message)


async def run_proxy(
    host: str,
    port: int,
    upstream: str,
    *,
    connect_hint: str | None = None,
    hide_server_telemetry: bool = True,
    hide_client_telemetry: bool = False,
) -> None:
    import websockets

    async def handler(client_ws):  # websockets 10+ passes one arg
        print(f"Client connected from {client_ws.remote_address}", flush=True)
        try:
            async with websockets.connect(upstream) as upstream_ws:

                async def client_to_server():
                    async for message in client_ws:
                        if hide_client_telemetry and _is_telemetry_json(message):
                            await upstream_ws.send(message)
                            continue
                        _print_frame("CLIENT → SERVER (your UI / other tool)", message)
                        await upstream_ws.send(message)

                async def server_to_client():
                    async for message in upstream_ws:
                        if hide_server_telemetry and _is_telemetry_json(message):
                            await client_ws.send(message)
                            continue
                        _print_frame("SERVER → CLIENT", message)
                        await client_ws.send(message)

                done, pending = await asyncio.wait(
                    [
                        asyncio.create_task(client_to_server()),
                        asyncio.create_task(server_to_client()),
                    ],
                    return_when=asyncio.FIRST_EXCEPTION,
                )
                for t in pending:
                    t.cancel()
                for t in done:
                    if t.exception():
                        print(f"Task ended: {t.exception()!r}", flush=True)
        except Exception as e:
            print(f"Proxy session error: {e!r}", flush=True)
        finally:
            print("Client disconnected", flush=True)

    async with websockets.serve(handler, host, port):
        client_hint = (
            "127.0.0.1"
            if host in ("0.0.0.0", "::", "::0")
            else host
        )
        if connect_hint:
            banner = (
                f"Proxy listening (bind {host}:{port})\n"
                f"Forwarding to {upstream}\n\n"
                f"{connect_hint}\n"
                f"(Use this machine's LAN IP instead of 127.0.0.1 if the client runs elsewhere.)\n"
                f"Browsers cannot use 0.0.0.0 as hostname.\n"
            )
        else:
            banner = (
                f"Proxy listening (bind {host}:{port})\n"
                f"Forwarding to {upstream}\n\n"
                f"In your FRONTEND env / config, set WebSocket URL to:\n"
                f"  ws://{client_hint}:{port}/ws/frontend\n"
                f"(Use LAN IP instead of 127.0.0.1 if the browser is on another device.)\n"
                f"Browsers cannot use 0.0.0.0 as hostname.\n"
            )
        print(banner, flush=True)
        await asyncio.Future()


async def run_backend_robots(
    robot_ids: list[str],
    upstream_base: str,
    *,
    show_telemetry: bool,
) -> None:
    """Direct connect to backend /ws/robot/<id> for each robot (parallel)."""
    import websockets

    base = upstream_base.rstrip("/")
    hide = not show_telemetry

    print(
        "Direct read from backend (robot sockets, same path as telemetry_bridge):\n",
        flush=True,
    )
    for rid in robot_ids:
        print(f"  {rid}  →  {base}/ws/robot/{rid}", flush=True)
    print(
        "\nHiding type=telemetry by default (--show-telemetry to print).\n"
        "Note: if the server only delivers commands to the real bridge connection,\n"
        "this tap may only show telemetry or nothing — use `robot` MITM on the bridge then.\n",
        flush=True,
    )

    async def one(rid: str) -> None:
        url = f"{base}/ws/robot/{rid}"
        suppressed = 0
        try:
            async with websockets.connect(url) as ws:
                print(f"[{rid}] connected\n", flush=True)
                async for message in ws:
                    if hide and _is_telemetry_json(message):
                        suppressed += 1
                        if suppressed % 200 == 0:
                            print(
                                f"[{rid}] suppressed {suppressed} telemetry\n",
                                flush=True,
                            )
                        continue
                    _print_frame(
                        f"[{rid}] BACKEND → this tap (same URL as telemetry_bridge)",
                        message,
                    )
        except Exception as e:
            print(f"[{rid}] stopped: {e!r}\n", flush=True)

    await asyncio.gather(*[one(rid) for rid in robot_ids])


def main() -> None:
    p = argparse.ArgumentParser(
        description="Log WebSocket JSON from production (159.203.4.11:8000) — tap = direct connect"
    )
    sub = p.add_subparsers(dest="cmd", required=True)

    pt = sub.add_parser(
        "tap",
        help=f"Same as listen; default {DEFAULT_FRONTEND_WS} (direct, no proxy)",
    )
    pt.add_argument("url", nargs="?", default=DEFAULT_FRONTEND_WS)
    pt.add_argument(
        "--show-telemetry",
        action="store_true",
        help="Print type=telemetry (default: hidden)",
    )

    pl = sub.add_parser("listen", help="Direct connect; log only server→you (default: production)")
    pl.add_argument("url", nargs="?", default=DEFAULT_FRONTEND_WS)
    pl.add_argument(
        "--show-telemetry",
        action="store_true",
        help="Print type=telemetry (default: hidden)",
    )

    pf = sub.add_parser(
        "frontend",
        help="Proxy /ws/frontend: log UI→backend and backend→UI (set frontend WS URL to this port)",
    )
    pf.add_argument(
        "--upstream",
        default=DEFAULT_FRONTEND_WS,
        help="Real backend /ws/frontend URL",
    )
    pf.add_argument("--host", default="0.0.0.0", help="Bind address")
    pf.add_argument("--port", type=int, default=9876, help="Local port for browser to use")
    pf.add_argument(
        "--show-telemetry",
        action="store_true",
        help="Print SERVER→CLIENT telemetry (default: hidden)",
    )

    pr = sub.add_parser(
        "robot",
        help="Proxy /ws/robot/<id>: log bridge↔backend (point telemetry_bridge URL here)",
    )
    pr.add_argument("robot_id", help="e.g. tb3_001")
    pr.add_argument(
        "--upstream-base",
        default=DEFAULT_ROBOT_WS_BASE,
        help="Backend origin without path (…/ws/robot/<id> is appended)",
    )
    pr.add_argument("--host", default="0.0.0.0", help="Bind address")
    pr.add_argument("--port", type=int, default=9877, help="Local port")
    pr.add_argument(
        "--show-telemetry",
        action="store_true",
        help="Print telemetry both ways (default: hidden on bridge↔server)",
    )

    pbs = sub.add_parser(
        "robots",
        help="Backend /ws/robot/… for multiple bots (default: tb3_001 tb3_002)",
    )
    pbs.add_argument(
        "robot_ids",
        nargs="*",
        help="e.g. tb3_001 tb3_002 tb3_003 (omit for default 001 and 002)",
    )
    pbs.add_argument(
        "--upstream-base",
        default=DEFAULT_ROBOT_WS_BASE,
        help="Backend origin, e.g. ws://159.203.4.11:8000",
    )
    pbs.add_argument(
        "--show-telemetry",
        action="store_true",
        help="Print type=telemetry (default: hidden)",
    )

    pp = sub.add_parser("proxy", help="MITM: full upstream URL + --port")
    pp.add_argument(
        "upstream",
        nargs="?",
        default="ws://127.0.0.1:8000/ws/frontend",
        help="Full upstream WebSocket URL",
    )
    pp.add_argument("--host", default="0.0.0.0", help="Bind address for proxy")
    pp.add_argument("--port", type=int, default=9876, help="Bind port for proxy")
    pp.add_argument(
        "--show-telemetry",
        action="store_true",
        help="Print SERVER→CLIENT telemetry (default: hidden)",
    )

    args = p.parse_args()

    try:
        import websockets  # noqa: F401
    except ImportError:
        print("Install: pip install websockets", file=sys.stderr)
        sys.exit(1)

    if args.cmd in ("listen", "tap"):
        asyncio.run(
            run_listen(args.url, show_telemetry=args.show_telemetry)
        )
    elif args.cmd == "frontend":
        asyncio.run(
            run_proxy(
                args.host,
                args.port,
                args.upstream,
                hide_server_telemetry=not args.show_telemetry,
            )
        )
    elif args.cmd == "robots":
        rids = list(args.robot_ids) if args.robot_ids else ["tb3_001", "tb3_002"]
        asyncio.run(
            run_backend_robots(
                rids,
                args.upstream_base,
                show_telemetry=args.show_telemetry,
            )
        )
    elif args.cmd == "robot":
        base = args.upstream_base.rstrip("/")
        rid = args.robot_id
        upstream = f"{base}/ws/robot/{rid}"
        ch = (
            f"Point telemetry_bridge backend WebSocket to:\n"
            f"  ws://127.0.0.1:{args.port}/ws/robot/{rid}\n"
            f"(Change the URL in telemetry_bridge / env so the bridge connects through this proxy.)"
        )
        asyncio.run(
            run_proxy(
                args.host,
                args.port,
                upstream,
                connect_hint=ch,
                hide_server_telemetry=not args.show_telemetry,
                hide_client_telemetry=not args.show_telemetry,
            )
        )
    else:
        asyncio.run(
            run_proxy(
                args.host,
                args.port,
                args.upstream,
                hide_server_telemetry=not args.show_telemetry,
            )
        )


if __name__ == "__main__":
    main()
