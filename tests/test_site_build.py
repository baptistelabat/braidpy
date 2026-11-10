# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""Braid Studio's site, as web/build.py assembles it."""

import gzip
import importlib.util
import json
from pathlib import Path

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
