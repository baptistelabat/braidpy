# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""The geometry pages explain why there is no formula for a braid's shape, and
point at the code that does what can be done instead.

Prose rots when code moves, and these pages already had four references to
files that a refactor had dissolved.  These tests make the pointers fail
loudly instead.
"""

import ast
import importlib
import pathlib
import re

import pytest

ROOT = pathlib.Path(__file__).parent.parent
DOCS = ROOT / "docs" / "source"
ANALYTIC = ROOT / "src" / "braidpy" / "analytic"
PACKAGE = ROOT / "src" / "braidpy"

PAGES = ("why_no_closed_form.md", "solving_numerically.md")


def note_text() -> str:
    """Both pages together: a name may be introduced on either."""
    return "\n".join((DOCS / page).read_text() for page in PAGES)


def defined_names() -> set:
    """Every name braidpy defines, plus the names of the modules themselves.

    The pages refer to both — `annulus_braid` the module and `lay_radius` the
    function within one — so both have to be resolvable.
    """
    names = {source.stem for source in PACKAGE.glob("*.py")}
    for source in PACKAGE.glob("*.py"):
        try:
            tree = ast.parse(source.read_text())
        except SyntaxError:  # pragma: no cover - a module mid-edit
            continue
        for node in tree.body:
            if isinstance(node, (ast.FunctionDef, ast.ClassDef)):
                names.add(node.name)
            elif isinstance(node, ast.Assign):
                names.update(
                    target.id for target in node.targets if isinstance(target, ast.Name)
                )
            elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
                names.add(node.target.id)
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                names.update(
                    item.name for item in node.body if isinstance(item, ast.FunctionDef)
                )
    return names


@pytest.mark.parametrize("page", PAGES)
def test_the_pages_are_in_the_docs_and_in_the_toctree(page):
    """A page outside the toctree is a page nobody reaches."""
    assert (DOCS / page).is_file()
    assert page in (DOCS / "index.md").read_text()


def test_the_analytic_directory_holds_only_a_pointer():
    """It is named for a thing that does not exist; it must hold no code."""
    assert [path.name for path in ANALYTIC.iterdir() if path.is_file()] == ["README.md"]
    pointer = (ANALYTIC / "README.md").read_text()
    for page in PAGES:
        assert page in pointer, f"the pointer does not name {page}"


def test_the_pointer_and_the_code_agree_on_where_the_pages_live():
    """Every docs path named anywhere in the package must resolve."""
    named = set()
    for source in list(PACKAGE.rglob("*.py")) + [ANALYTIC / "README.md"]:
        named |= set(re.findall(r"docs/source/([\w.]+\.md)", source.read_text()))
    missing = [page for page in sorted(named) if not (DOCS / page).is_file()]
    assert not missing, f"the code points at pages that are gone: {missing}"


def test_every_module_the_pages_name_exists():
    paths = set(re.findall(r"`([\w/]+\.py)`", note_text()))
    missing = [
        path for path in paths if not (PACKAGE / pathlib.Path(path).name).is_file()
    ]
    assert not missing, f"the pages point at files that are gone: {missing}"


def test_every_name_the_pages_name_exists():
    """Both dotted paths and bare names, since the pages use each."""
    known = defined_names()
    unresolved = []

    for ref in sorted(set(re.findall(r"`([A-Za-z_][\w.]*)`", note_text()))):
        if ref.endswith(".py"):
            continue
        parts = ref.split(".")
        if parts[0] == "braidpy":
            continue  # the package itself, or a directory within it
        if len(parts) == 1:
            if parts[0] not in known:
                unresolved.append(ref)
            continue
        # A dotted path: either module.name or Class.method.
        if parts[-1] in known and parts[-2] in known:
            continue
        try:
            module = importlib.import_module(f"braidpy.{parts[0]}")
        except ModuleNotFoundError:
            unresolved.append(ref)
            continue
        target = module
        for attribute in parts[1:]:
            target = getattr(target, attribute, None)
            if target is None:
                unresolved.append(ref)
                break

    assert not unresolved, f"the pages point at names that are gone: {unresolved}"


@pytest.mark.parametrize(
    "claim",
    [
        "lay_radius",  # the rope limit, corrected from the packing formula
        "packing_radius",
        "closest_approach",
        "minimum_lay",
        "tightest_figure_eight",
    ],
)
def test_the_pages_still_name_the_results_they_rest_on(claim):
    """If one of these is renamed away, the argument loses its anchor."""
    assert f"`{claim}`" in note_text()
