# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""braidpy as an MCP server: :mod:`braidpy.tools`, each function a tool an
AI assistant can call — Claude, or any client of the Model Context
Protocol (https://modelcontextprotocol.io).

Installed with the ``mcp`` extra, it runs over stdio::

    pip install "braidpy[mcp]"
    braidpy-mcp

and is added to a client as a command, for example to Claude Code::

    claude mcp add braidpy -- braidpy-mcp

A client that reaches the server across the network, as a hosted one does,
is served over streamable HTTP instead::

    braidpy-mcp --http 0.0.0.0:8000    # 127.0.0.1 if no host is given

An HTTP server open to the network asks who is calling: with ``--token``,
or the ``BRAIDPY_MCP_TOKEN`` environment variable, it answers only the
clients that give the token as their ``Authorization: Bearer`` header.

The tools are :mod:`braidpy.tools`'s functions as they are, their
docstrings what the assistant reads of them: nothing here but the wiring,
so what a person reads in the library and what an assistant is told are
the same words.
"""

from __future__ import annotations

import os
import threading
from argparse import ArgumentParser
from collections.abc import Callable, Sequence
from typing import Any

from braidpy import tools

__all__ = ["TOOLS", "main", "server"]

#: What the server offers, in the order it lists them.
TOOLS: list[Callable[..., Any]] = [
    tools.list_braids,
    tools.describe_braid,
    tools.compare_braids,
    tools.similar_braids,
    tools.ways_to_make,
    tools.make_braid,
    tools.studio_link,
]

INSTRUCTIONS = """\
braidpy answers questions about braids — braid words, kumihimo disks,
Ashley's sinnets, braiding and lace machines.  A braid is given as a braid
word: signed generators, "1 -2" for σ₁σ₂⁻¹.  Two braids are the same braid
when their topology is, however written.  Every answer that names a braid
gives a Braid Studio link: give it to the person, to see the braid in 3D.
"""


def server() -> Any:
    """The MCP server, its tools registered.  The catalogue of braids by
    topology, a minute or so to make, is made at once in the background, so
    that the first question needing it is not kept waiting long.

    Returns:
        An :class:`mcp.server.mcpserver.MCPServer`.

    Raises:
        ImportError: Without the ``mcp`` extra.
    """
    from mcp.server.mcpserver import MCPServer

    made = MCPServer(name="braidpy", instructions=INSTRUCTIONS)
    for function in TOOLS:
        made.add_tool(function)

    def warm() -> None:
        from braidpy.topology_catalog import catalog

        catalog()

    threading.Thread(target=warm, daemon=True).start()
    return made


def _serve_guarded(made: Any, host: str, port: int, token: str) -> None:
    """The server behind a check of the token: a client that gives it as
    its ``Authorization: Bearer`` header is answered; the rest are refused
    at the door, before braidpy spends anything."""
    import uvicorn

    expected = f"Bearer {token}".encode()
    app = made.streamable_http_app()

    async def guarded(scope: Any, receive: Any, send: Any) -> None:
        if scope["type"] == "http":
            headers = dict(scope.get("headers") or [])
            if headers.get(b"authorization") != expected:
                body = b'{"error": "unauthorized"}'
                await send(
                    {
                        "type": "http.response.start",
                        "status": 401,
                        "headers": [
                            (b"content-type", b"application/json"),
                            (b"content-length", str(len(body)).encode()),
                        ],
                    }
                )
                await send({"type": "http.response.body", "body": body})
                return
        await app(scope, receive, send)

    uvicorn.run(guarded, host=host, port=port)


def main(argv: Sequence[str] | None = None) -> None:
    """Run the server: over stdio, as ``braidpy-mcp``, or, with ``--http``,
    over streamable HTTP, for the client that reaches a server across the
    network."""
    parser = ArgumentParser(
        prog="braidpy-mcp", description="braidpy's tools, as an MCP server"
    )
    parser.add_argument(
        "--http",
        metavar="[HOST:]PORT",
        help="serve streamable HTTP there (127.0.0.1 if no host is given), rather than stdio",
    )
    parser.add_argument(
        "--token",
        metavar="TOKEN",
        help="answer only the clients giving this token as their Authorization: "
        "Bearer header ($BRAIDPY_MCP_TOKEN does as much)",
    )
    given = parser.parse_args(argv)
    try:
        made = server()
    except ModuleNotFoundError as missing:
        if (missing.name or "").split(".")[0] != "mcp":
            raise
        raise SystemExit(
            "braidpy-mcp needs the mcp extra: pip install 'braidpy[mcp]'"
        ) from None
    if given.http is None:
        made.run()
        return
    host, _, port = given.http.rpartition(":")
    host, port = host or "127.0.0.1", int(port)
    token = given.token or os.environ.get("BRAIDPY_MCP_TOKEN")
    if token:
        _serve_guarded(made, host, port, token)
        return
    made.run("streamable-http", host=host, port=port)


if __name__ == "__main__":
    main()
