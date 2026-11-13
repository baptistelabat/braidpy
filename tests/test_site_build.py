# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""Braid Studio's site, as web/build.py assembles it."""

import gzip
import importlib.util
import json
import re
from pathlib import Path

import pytest

WEB = Path(__file__).resolve().parent.parent / "web"


def _build():
    spec = importlib.util.spec_from_file_location("site_build", WEB / "build.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_the_braids_made_with_the_site_are_kept_gzipped(tmp_path):
    """Gzipped, each braid made with the site unpacks to the very bytes it
    was made as, the index names the gzipped files, and the same braids
    gzip to the same bytes every time."""
    made = tmp_path / "made"
    made.mkdir()
    laid = json.dumps({"strands": [[0.5, 1.25, 2.0]] * 200}).encode()
    settled = json.dumps({"strands": [[0.25, 1.0, 2.5]] * 200}).encode()
    (made / "0.json").write_bytes(laid)
    (made / "0.settled.json").write_bytes(settled)
    (made / "1.json").write_bytes(laid)
    index = [
        {"spec": {"source": "word"}, "file": "0.json", "settled": "0.settled.json"},
        {"spec": {"source": "lace"}, "file": "1.json"},
    ]
    (made / "index.json").write_text(json.dumps(index))

    _build()._compressed(tmp_path)

    after = json.loads((made / "index.json").read_text())
    assert after == [
        {
            "spec": {"source": "word"},
            "file": "0.json.gz",
            "settled": "0.settled.json.gz",
        },
        {"spec": {"source": "lace"}, "file": "1.json.gz"},
    ]
    assert sorted(p.name for p in made.iterdir()) == [
        "0.json.gz",
        "0.settled.json.gz",
        "1.json.gz",
        "index.json",
    ]
    assert gzip.decompress((made / "0.json.gz").read_bytes()) == laid
    assert gzip.decompress((made / "0.settled.json.gz").read_bytes()) == settled
    assert (made / "0.json.gz").read_bytes() == (made / "1.json.gz").read_bytes()
    assert len((made / "0.json.gz").read_bytes()) < len(laid) / 10


# A site of its own, built from braidpy: named otherwise, crediting and
# linking nothing, kept from search engines (docs/source/private_sites.md).
PRIVATE = """
name = "Braid Designer"
by = ""
by_url = ""
documentation = ""
documentation_title = ""
sponsor = ""
indexed = false
"""


def _pages(build, about):
    return {
        name: build._rendered((WEB / name).read_text(), about)
        for name in build.PAGE
        if name.endswith(".html")
    }


def test_this_repositorys_profile_fills_every_page():
    """With this repository's profile, nothing of the profile's own markup
    is left on a page, and the site is open to search engines."""
    build = _build()
    for name, page in _pages(build, build.profile()).items():
        assert (
            "{{" not in page and "<!-- if" not in page and "<!-- end if" not in page
        ), name
        assert "Braid Studio" in page and "noindex" not in page, name


def test_a_site_of_its_own_names_neither_braidpy_nor_its_links(tmp_path):
    """A profile crediting nothing leaves braidpy, its repository and its
    sponsoring off every page's visible text, names the site its own way,
    and asks search engines to leave it out."""
    build = _build()
    given = tmp_path / "private.toml"
    given.write_text(PRIVATE)
    for name, page in _pages(build, build.profile(given)).items():
        # What a visitor reads: the page less its scripts and comments.
        shown = re.sub(r"<script.*?</script>|<!--.*?-->", "", page, flags=re.DOTALL)
        for told in ("braidpy", "github", "sponsor", "Braid Studio"):
            assert told.lower() not in shown.lower(), (name, told)
        assert "<title>Braid Designer</title>" in page, name
        assert '<meta name="robots" content="noindex, nofollow" />' in page, name


def test_a_profile_decides_every_key(tmp_path):
    """A profile leaving a key out is refused: a key added to this
    repository's profile is one every site built from braidpy decides."""
    build = _build()
    given = tmp_path / "short.toml"
    given.write_text(PRIVATE.replace('sponsor = ""\n', ""))
    with pytest.raises(SystemExit, match="sponsor"):
        build.profile(given)
