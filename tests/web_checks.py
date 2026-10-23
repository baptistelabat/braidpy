# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""Checks the web tests share."""

import json
import math


def check(result, n_strands):
    """Plain data, every yarn drawn, every number finite."""
    json.dumps(result)
    assert result["title"]
    assert len(result["strands"]) == n_strands
    for strand in result["strands"]:
        assert strand["colour"].startswith("#")
        assert len(strand["points"]) >= 2
        assert all(len(p) == 3 and all(map(math.isfinite, p)) for p in strand["points"])
    assert result["info"]["n_strands"] == n_strands
    assert result["yarn_diameter"] > 0
