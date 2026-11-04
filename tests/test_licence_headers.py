# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""Every source file says, at its top, that it is under the MPL 2.0: the
notice the licence's Exhibit A asks for."""

import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).parent.parent
SOURCES = ["src/*.py", "tests/*.py", "tests/js/*.js", "web/*.js", "web/*.py"]
SOURCES += ["scripts/*.py", "examples/*.py"]


def test_every_source_file_carries_the_licence_notice():
    try:
        listed = subprocess.run(
            ["git", "ls-files", *SOURCES],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=True,
        ).stdout.split()
    except (OSError, subprocess.CalledProcessError):
        pytest.skip("needs the git checkout")
    notice = "This Source Code Form is subject to the terms of the Mozilla Public"
    missing = [
        name
        for name in listed
        if notice not in (ROOT / name).read_text(encoding="utf-8").partition("\n")[0]
    ]
    assert missing == []
