# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""braidpy's front door, braidpy.tools, and the MCP server offering it."""

import asyncio
import json

import pytest

from braidpy import tools


def test_every_answer_is_plain_data():
    """Text, numbers, lists and dicts: JSON as it is."""
    for answer in (
        tools.describe_braid("1 -2"),
        tools.compare_braids("1 -2", "-2 1"),
        tools.list_braids("lace"),
        tools.ways_to_make("1 -2"),
        tools.make_braid({"source": "sinnet", "name": "abok_2965"}),
    ):
        assert json.loads(json.dumps(answer)) == answer


def test_a_braid_is_described_and_linked():
    info = tools.describe_braid("aB")  # letters, as braidpy reads words
    assert info["n_strands"] == 3 and info["permutation"] == [2, 3, 1]
    assert info["studio"].startswith(tools.STUDIO + "#source=word")


def test_the_same_braid_however_written():
    """Ashley's flat sinnet of 7 is the catalogue's word read backwards."""
    same = tools.compare_braids("1 2 3 -6 -5 -4", "3 2 1 -4 -5 -6", n_strands=7)
    assert same == {"same_braid": True, "distance": 0.0}
    assert not tools.compare_braids("1 -2", "1 2")["same_braid"]


def test_ways_to_make_a_braid_no_sinnet_makes():
    """The weave of 3: a disk's moves, a lace card, and Ashley's stand one
    strand a space, as no sinnet of the book's kind makes it."""
    made = tools.ways_to_make("1 -2 -2 1")
    assert set(made) == {"disk", "lace", "ashley"}
    assert made["ashley"]["a_sinnet"] is False
    assert made["ashley"]["spaces"] == "1 0 1 0 1 0"
    assert made["lace"]["bobbins"] == ["A-B", "B-C", "C-D"]


def test_a_braid_word_with_no_crossing_says_so():
    with pytest.raises(ValueError, match="No crossing"):
        tools.describe_braid("")


@pytest.mark.slow
def test_similar_braids_come_with_every_way_of_making_them():
    """The plait is in the catalogues: first, distance 0, made four ways."""
    found = tools.similar_braids("1 -2", count=3)
    assert found[0]["distance"] == 0.0
    assert {m["source"] for m in found[0]["made_as"]} >= {"word", "sinnet", "machine"}


def test_the_mcp_server_offers_every_tool():
    pytest.importorskip("mcp")
    from braidpy.mcp_server import TOOLS, server

    made = server()
    listed = asyncio.run(made.list_tools())
    assert [t.name for t in listed] == [f.__name__ for f in TOOLS]
    # What an assistant reads of a tool is its docstring.
    describe = next(t for t in listed if t.name == "describe_braid")
    assert "permutation" in describe.description
    answer = asyncio.run(made.call_tool("compare_braids", {"a": "1 -2", "b": "-2 1"}))
    assert "true" in json.dumps(answer, default=str).lower()
