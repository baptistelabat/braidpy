# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""web/i18n.js: Braid Studio in another language, from web/locales/."""

import json
import re
import shutil
import subprocess
from pathlib import Path

import pytest
import tomllib
from test_site_build import PRIVATE, WEB, _build

build = _build()
pytestmark = pytest.mark.skipif(shutil.which("node") is None, reason="needs Node.js")

CASES = Path(__file__).parent / "js" / "i18n_cases.mjs"
FRENCH = tomllib.loads((WEB / "locales" / "fr.toml").read_text())
# A site in French naming nothing of braidpy, as braid-designer is.
DESIGNER = tomllib.loads(PRIVATE)


def shown(texts, language="fr", tmp_path=None, chosen=None):
    """Each text as the page shows it on a site in ``language``, another
    ``chosen`` from its menu if given, and those it lacks."""
    (tmp_path / "i18n.js").write_text((WEB / "i18n.js").read_text())
    (tmp_path / "locale.js").write_text(build.locale(language))
    run = subprocess.run(
        ["node", str(CASES), str(tmp_path), *([chosen] if chosen else [])],
        input=json.dumps(texts),
        capture_output=True,
        text=True,
        check=True,
    )
    out = json.loads(run.stdout)
    return out["shown"], set(out["untranslated"])


def test_a_text_is_found_whole_its_spaces_run_together_and_kept(tmp_path):
    out, missing = shown(
        ["Strands", "  Top\n   view ", " 12 moves a repeat "], tmp_path=tmp_path
    )
    assert out == ["Brins", "  Vue de dessus ", " 12 mouvements par motif "]
    assert not missing


def test_a_pattern_s_words_are_looked_up_and_put_in_their_own_order(tmp_path):
    out, missing = shown(
        [
            "Kongo gumi, 8 strands, 2 cycles",
            "ABOK #3042, 8-strand round, 3 cycles",
            "Flat braid, 3 carriers",
        ],
        tmp_path=tmp_path,
    )
    assert out == [
        "Kongo gumi, 8 brins, 2 cycles",
        "ABOK n° 3042, tresse ronde à 8 brins, 3 cycles",
        "Tresse plate, 3 fuseaux",
    ]
    assert not missing


def test_a_note_keeps_the_lines_of_its_card(tmp_path):
    card = "     A B C D\n0 ↺  ○ ○ ○ ○\n  ↻   ○ ○ ○ ●"
    note = (
        "Words are read over one pass of the card. The card, a column a gear, "
        "two lines a step — the gears turning anticlockwise ↺, then clockwise ↻ "
        "— ● punched:\n" + card
    )
    (out,), missing = shown([note], tmp_path=tmp_path)
    assert out.endswith("● perforé :\n" + card)
    assert not missing


def test_what_the_catalogue_lacks_stays_in_english_and_is_listed(tmp_path):
    out, missing = shown(["No such words here", "3 · 4", "Brins"], tmp_path=tmp_path)
    assert out == ["No such words here", "3 · 4", "Brins"]
    assert missing == {"No such words here"}


def test_in_english_every_text_is_shown_as_written(tmp_path):
    out, missing = shown(["Strands", "Nothing"], language="en", tmp_path=tmp_path)
    assert out == ["Strands", "Nothing"]
    assert not missing


def test_a_site_in_english_is_shown_in_french_once_chosen_and_back(tmp_path):
    out, missing = shown(
        ["Strands", "Top view"], language="en", tmp_path=tmp_path, chosen="fr"
    )
    assert out == ["Brins", "Vue de dessus"]
    assert not missing
    out, _ = shown(["Strands"], language="fr", tmp_path=tmp_path, chosen="en")
    assert out == ["Strands"]


def test_each_language_is_offered_by_its_own_name():
    assert FRENCH["English"] == "Français"


def test_every_translation_takes_the_words_its_english_leaves_open():
    for english, french in FRENCH.items():
        places = len(re.findall(r"\{#?\}", english))
        taken = re.findall(r"\{(\d*)\}", french)
        assert all(not at or 1 <= int(at) <= places for at in taken), english
        numbered = sorted(int(at) for at in taken if at)
        if numbered:
            assert numbered == list(range(1, places + 1)), english
        else:
            assert len(taken) == places, english


def _page_texts(text):
    """The words a page shows: its text, its titles and its description."""
    words = re.findall(r'(?:title|placeholder|aria-label|alt|content)="([^"]*)"', text)
    body = re.sub(r"<(script|style)\b.*?</\1>", "", text, flags=re.DOTALL)
    words += re.split(r"<[^>]+>", body)
    return [w for w in words if re.search(r"[A-Za-z]{2}", w)]


@pytest.mark.parametrize("page", ["index.html", "make.html"])
def test_the_pages_are_all_in_french(page, tmp_path):
    text = build._rendered((WEB / page).read_text(), DESIGNER)
    _, missing = shown(_page_texts(text), tmp_path=tmp_path)
    # The site's own name, and what the page is made with, by their names.
    assert missing <= {
        "Braid Designer",
        "Pyodide",
        "three.js",
        "width=device-width, initial-scale=1",
        "noindex, nofollow",
    }


def test_every_braid_the_studio_offers_is_named_in_french(tmp_path):
    from braidpy import web

    texts = []

    def titles(x, key=None):
        if isinstance(x, dict):
            for k, v in x.items():
                titles(v, k)
        elif isinstance(x, list):
            for v in x:
                titles(v, key)
        elif isinstance(x, str) and key in (
            "title",
            "shape",
            "grids",
            "shapes",
            "orders",
        ):
            texts.append(x)

    catalogue = web.catalogue()
    titles(catalogue)
    for about in catalogue.values():
        for key in ("grids", "orders"):
            texts += list(about.get(key, {}).values())
        for shapes in about.get("shapes", {}).values():
            texts += list(shapes.values())
    _, missing = shown(texts, tmp_path=tmp_path)
    assert not missing
