# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""braidpy's names are spelled in American English, as Python's and its
libraries' are (``color``, ``center``, ``neighbor``); its prose — comments,
docstrings, pages — is spelled as its writer likes, and is not checked.

Checked: in Python, every name braidpy defines (a module, function, class,
argument, variable or attribute set); in JavaScript, every name declared.
Not checked, being data rather than names: strings, the keys of the JSON
the page reads (a ``TypedDict``'s fields), and an old name kept working
after a rename (``braidpy._renamed``).  ``catalogue`` is braidpy's own word,
in its modules and their ``CATALOGUE``.
"""

from __future__ import annotations

import ast
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# British spelling in a name: the American one.
AMERICAN = {
    "behaviour": "behavior",
    "centre": "center",
    "colour": "color",
    "favour": "favor",
    "fibre": "fiber",
    "grey": "gray",
    "labelled": "labeled",
    "labelling": "labeling",
    "modelled": "modeled",
    "modelling": "modeling",
    "neighbour": "neighbor",
    "travelled": "traveled",
}
_BRITISH = re.compile("|".join(AMERICAN), re.IGNORECASE)

# The old module names kept working after a rename: data, not names.
KEPT = {
    f"src/braidpy/{name}_catalog.py"
    for name in ("braid", "machine", "mobidai", "solid_sinnets", "topology")
}


def _british(name: str) -> str | None:
    """The British spelling a name holds, if any."""
    match = _BRITISH.search(name)
    return match.group().lower() if match else None


def _kept(tree: ast.AST) -> set[int]:
    """The nodes that are data, not names: a TypedDict's fields, and an old
    name kept as an alias (``colour = renamed_attribute("color")``)."""
    kept: set[int] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef) and any(
            getattr(base, "id", getattr(base, "attr", None)) == "TypedDict"
            for base in node.bases
        ):
            kept |= {
                id(field.target)
                for field in node.body
                if isinstance(field, ast.AnnAssign)
            }
        if (
            isinstance(node, ast.Assign)
            and isinstance(node.value, ast.Call)
            and getattr(node.value.func, "id", None) == "renamed_attribute"
        ):
            kept |= {id(target) for target in node.targets}
    return kept


def _defined(path: str, source: str) -> list[str]:
    tree = ast.parse(source)
    kept = _kept(tree)
    found: list[str] = []
    for node in ast.walk(tree):
        if id(node) in kept:
            continue
        name = None
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            name = node.name
        elif isinstance(node, ast.arg):
            name = node.arg
        elif isinstance(node, ast.Name) and isinstance(node.ctx, ast.Store):
            name = node.id
        elif isinstance(node, ast.Attribute) and isinstance(node.ctx, ast.Store):
            name = node.attr
        if name and _british(name):
            found.append(f"{path}:{getattr(node, 'lineno', '?')}: {name}")
    if _british(Path(path).stem):
        found.append(f"{path}: the file's name")
    return found


def _declared(path: str, source: str) -> list[str]:
    found = []
    for match in re.finditer(
        r"\b(?:function|const|let|var|class)\s+([A-Za-z_$][\w$]*)", source
    ):
        if _british(match.group(1)):
            line = source.count("\n", 0, match.start()) + 1
            found.append(f"{path}:{line}: {match.group(1)}")
    return found


def _files() -> list[str]:
    listed = subprocess.run(
        ["git", "ls-files", "*.py", "web/*.js"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=True,
    ).stdout.split()
    return [f for f in listed if f not in KEPT and (ROOT / f).exists()]


def test_braidpy_s_names_are_spelled_in_american_english():
    found: list[str] = []
    for path in _files():
        source = (ROOT / path).read_text(encoding="utf-8")
        found += (_defined if path.endswith(".py") else _declared)(path, source)
    spelled = [f"{hit} (American: {AMERICAN[_british(hit) or '']})" for hit in found]
    assert not found, "British spelling in a name:\n" + "\n".join(spelled)


def test_a_british_name_is_found_and_data_is_not():
    """The check itself: names are checked; strings, a TypedDict's fields
    and an alias are not."""
    source = (
        "class Info(TypedDict):\n"
        "    colour: str\n"
        "def strand_colour(centres):\n"
        '    """The neighbour\'s colour, free prose."""\n'
        '    plot(key="colour")\n'
        '    colour = renamed_attribute("color")\n'
    )
    assert [hit.split()[-1] for hit in _defined("x.py", source)] == [
        "strand_colour",
        "centres",
    ]
    assert _declared("x.js", "const grey = getColour(); // a colour") == [
        "x.js:1: grey"
    ]
