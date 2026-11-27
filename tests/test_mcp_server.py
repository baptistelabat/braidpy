# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""braidpy's MCP server, as a client meets it."""

import asyncio
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent


def test_a_client_is_told_the_tools_and_answered():
    """The server, spawned as a client spawns it, says its tools, and
    answers a question asked of it."""
    pytest.importorskip("mcp")
    from braidpy import mcp_server

    async def ask():
        from mcp import ClientSession, StdioServerParameters
        from mcp.client.stdio import stdio_client

        server = StdioServerParameters(
            command=sys.executable, args=["-m", "braidpy.mcp_server"], cwd=str(ROOT)
        )
        async with (
            stdio_client(server) as (read, write),
            ClientSession(read, write) as session,
        ):
            await asyncio.wait_for(session.initialize(), 60)
            tools = await asyncio.wait_for(session.list_tools(), 60)
            answer = await asyncio.wait_for(
                session.call_tool("compare_braids", {"a": "1 -2", "b": "-2 1"}), 60
            )
            return tools, answer

    tools, answer = asyncio.run(ask())
    assert [tool.name for tool in tools.tools] == [
        function.__name__ for function in mcp_server.TOOLS
    ]
    assert '"same_braid": true' in answer.content[0].text


def test_the_http_option_serves_streamable_http(monkeypatch):
    """With ``--http``, the server runs over streamable HTTP on the host and
    port given, 127.0.0.1 for a port alone; without it, over stdio as
    before."""
    from braidpy import mcp_server

    seen = []

    class PretendServer:
        def run(self, *args, **kwargs):
            seen.append((args, kwargs))

    monkeypatch.setattr(mcp_server, "server", PretendServer)
    mcp_server.main(["--http", "0.0.0.0:8123"])
    assert seen[-1] == (("streamable-http",), {"host": "0.0.0.0", "port": 8123})
    mcp_server.main(["--http", "8123"])
    assert seen[-1] == (("streamable-http",), {"host": "127.0.0.1", "port": 8123})
    mcp_server.main([])
    assert seen[-1] == ((), {})


def test_the_token_guards_the_http_server(monkeypatch):
    """With a token, given or in the environment, the HTTP server runs
    behind the check of it; without one, it is open as before."""
    from braidpy import mcp_server

    seen = []

    class PretendServer:
        def run(self, *args, **kwargs):
            seen.append(("open", args, kwargs))

    def pretend_guarded(made, host, port, token):
        seen.append(("guarded", host, port, token))

    monkeypatch.setattr(mcp_server, "server", PretendServer)
    monkeypatch.setattr(mcp_server, "_serve_guarded", pretend_guarded)

    mcp_server.main(["--http", "0.0.0.0:8123", "--token", "s3cret"])
    assert seen[-1] == ("guarded", "0.0.0.0", 8123, "s3cret")

    monkeypatch.setenv("BRAIDPY_MCP_TOKEN", "from-environment")
    mcp_server.main(["--http", "8123"])
    assert seen[-1] == ("guarded", "127.0.0.1", 8123, "from-environment")

    monkeypatch.delenv("BRAIDPY_MCP_TOKEN")
    mcp_server.main(["--http", "8123"])
    assert seen[-1] == (
        "open",
        ("streamable-http",),
        {"host": "127.0.0.1", "port": 8123},
    )
