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

The tools are :mod:`braidpy.tools`'s functions as they are, their
docstrings what the assistant reads of them: nothing here but the wiring,
so what a person reads in the library and what an assistant is told are
the same words.
"""

from __future__ import annotations

import threading
from collections.abc import Callable
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
        from braidpy.topology_catalog import catalogue

        catalogue()

    threading.Thread(target=warm, daemon=True).start()
    return made


def main() -> None:
    """Run the server over stdio: ``braidpy-mcp``."""
    try:
        made = server()
    except ModuleNotFoundError as missing:
        if (missing.name or "").split(".")[0] != "mcp":
            raise
        raise SystemExit(
            "braidpy-mcp needs the mcp extra: pip install 'braidpy[mcp]'"
        ) from None
    made.run()


if __name__ == "__main__":
    main()
