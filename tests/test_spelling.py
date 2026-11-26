# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""braidpy spells its own words in British English: the names it defines,
its docstrings and comments, its pages.  A library's names are its own
(Plotly's ``color=``, CSS's ``text-align: center``, three.js's
``getCenter``) and are not braidpy's to spell: they are not checked.

Checked: in Python, every name braidpy defines (a module, function, class,
argument, variable or attribute set) and the words of its comments and
docstrings; in JavaScript, every name declared and the words of its
comments; in Markdown, its prose.  Words in backticks are code, not prose.
``-ize`` is British too (the Oxford spelling) and is left as it is.
"""

from __future__ import annotations

import ast
import io
import re
import subprocess
import tokenize
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# American spelling: the British one.
BRITISH = {
    "analyze": "analyse",
    "analyzed": "analysed",
    "behavior": "behaviour",
    "behaviors": "behaviours",
    "canceled": "cancelled",
    "catalog": "catalogue",
    "catalogs": "catalogues",
    "center": "centre",
    "centered": "centred",
    "centering": "centring",
    "centers": "centres",
    "centimeter": "centimetre",
    "centimeters": "centimetres",
    "color": "colour",
    "colored": "coloured",
    "colorful": "colourful",
    "coloring": "colouring",
    "colorize": "colourise",
    "colorized": "coloured",
    "colors": "colours",
    "favor": "favour",
    "favorite": "favourite",
    "fiber": "fibre",
    "fibers": "fibres",
    "gray": "grey",
    "labeled": "labelled",
    "labeling": "labelling",
    "meter": "metre",
    "meters": "metres",
    "millimeter": "millimetre",
    "millimeters": "millimetres",
    "modeled": "modelled",
    "modeling": "modelling",
    "neighbor": "neighbour",
    "neighborhood": "neighbourhood",
    "neighboring": "neighbouring",
    "neighbors": "neighbours",
    "traveled": "travelled",
}

# Titles of what braidpy cites, spelled as their authors spelled them.
TITLES = (
    "Modeling, and Visualization",  # Vision, Modeling, and Visualization
    "modeling of supercoiled",  # Klenin and Langowski, Biopolymers, 2000
)

# Files keeping the old names working after a rename, spelled as they were.
KEPT = {
    "CHANGELOG.md",
    "src/braidpy/braid_catalog.py",
    "src/braidpy/machine_catalog.py",
    "src/braidpy/mobidai_catalog.py",
    "src/braidpy/solid_sinnets_catalog.py",
    "src/braidpy/topology_catalog.py",
}


def _words(name: str) -> list[str]:
    """A name's words: split at underscores and where lower case meets
    upper (``strandColor``)."""
    return [w.lower() for w in re.split(r"_|(?<=[a-z0-9])(?=[A-Z])", name) if w]


def _american(text: str) -> list[str]:
    return [w for w in _words(text) if w in BRITISH]


def _prose(text: str) -> list[str]:
    """The American words of prose: code (in backticks), links and the
    titles of what is cited left out."""
    for code in (r"```.*?```", r"``.*?``", r"`[^`\n]*`", r"https?://\S+"):
        text = re.sub(code, " ", text, flags=re.DOTALL)
    for title in TITLES:
        text = text.replace(title, " ")
    return [w for w in re.findall(r"[A-Za-z]+", text) if w.lower() in BRITISH]


def _defined(tree: ast.AST) -> list[tuple[int, str]]:
    """The names a Python module defines, with their lines."""
    found: list[tuple[int, str]] = []
    # An old name kept as an alias, ``color = renamed_attribute("colour")``.
    kept = {
        id(target)
        for node in ast.walk(tree)
        if isinstance(node, ast.Assign)
        and isinstance(node.value, ast.Call)
        and getattr(node.value.func, "id", None) == "renamed_attribute"
        for target in node.targets
    }
    for node in ast.walk(tree):
        if id(node) in kept:
            continue
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            found.append((node.lineno, node.name))
        elif isinstance(node, ast.arg):
            found.append((node.lineno, node.arg))
        elif isinstance(node, ast.alias) and node.asname:
            found.append((node.lineno, node.asname))
        elif isinstance(node, (ast.Name, ast.Attribute)) and isinstance(
            node.ctx, ast.Store
        ):
            found.append(
                (node.lineno, node.id if isinstance(node, ast.Name) else node.attr)
            )
    return found


def _python(path: str, source: str) -> list[str]:
    found = [
        f"{path}:{line}: {name}"
        for line, name in _defined(ast.parse(source))
        if _american(name)
    ]
    found += [f"{path}: the file's name" for _ in _american(Path(path).stem)]
    for token in tokenize.generate_tokens(io.StringIO(source).readline):
        docstring = token.type == tokenize.STRING and re.match(
            r"[rbuRBU]*('''|\"\"\")", token.string
        )
        if token.type == tokenize.COMMENT or docstring:
            found += [f"{path}:{token.start[0]}: {w}" for w in _prose(token.string)]
    return found


def _javascript(path: str, source: str) -> list[str]:
    found = []
    for match in re.finditer(
        r"\b(?:function|const|let|var|class)\s+([A-Za-z_$][\w$]*)", source
    ):
        if _american(match.group(1)):
            line = source.count("\n", 0, match.start()) + 1
            found.append(f"{path}:{line}: {match.group(1)}")
    for match in re.finditer(r"//[^\n]*|/\*.*?\*/", source, flags=re.DOTALL):
        line = source.count("\n", 0, match.start()) + 1
        found += [f"{path}:{line}: {w}" for w in _prose(match.group())]
    return found


def _files() -> list[str]:
    listed = subprocess.run(
        ["git", "ls-files", "*.py", "*.js", "*.md"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=True,
    ).stdout.split()
    return [f for f in listed if f not in KEPT and (ROOT / f).exists()]


def test_braidpy_spells_its_own_words_in_british_english():
    found: list[str] = []
    for path in _files():
        source = (ROOT / path).read_text(encoding="utf-8")
        if path.endswith(".py"):
            found += _python(path, source)
        elif path.endswith(".js"):
            found += _javascript(path, source)
        else:
            found += [f"{path}: {w}" for w in _prose(source)]
    spelled = [f"{hit} (British: {BRITISH[hit.split()[-1].lower()]})" for hit in found]
    assert not found, "American spelling:\n" + "\n".join(spelled)


def test_an_american_word_is_found_and_a_library_s_name_is_not():
    """The check itself: a name braidpy defines, and its prose, are
    checked; a keyword passed to a library is not."""
    source = (
        "def strand_color(colors):\n"
        '    """The neighbor\'s `color`."""\n'
        "    plot(color=colors)  # centered\n"
    )
    found = _python("x.py", source)
    assert [hit.split()[-1] for hit in found] == [
        "strand_color",
        "colors",
        "neighbor",
        "centered",
    ]
    assert _javascript("x.js", "const gray = getCenter(); // a color") == [
        "x.js:1: gray",
        "x.js:1: color",
    ]
