#!/usr/bin/env bash
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
#
# Tag main with the version pyproject.toml gives and push the tag; the
# release workflow (.github/workflows/release.yml) then publishes it on PyPI.
# Run as `make release`, after develop has been merged into main on GitHub.
#
# Every check comes before anything is changed, and the first that fails
# stops it, saying what to do: nothing is tagged on the wrong commit.

set -euo pipefail

fail() {
    echo "release: $*" >&2
    exit 1
}

cd "$(git rev-parse --show-toplevel)"

[ "$(git rev-parse --abbrev-ref HEAD)" = main ] ||
    fail "not on main: git checkout main"
git diff --quiet && git diff --cached --quiet ||
    fail "uncommitted changes: commit or stash them (git stash)"

git fetch --quiet --no-tags origin main
git merge --quiet --ff-only origin/main ||
    fail "main has diverged from origin/main. See what is yours with
  git log --oneline origin/main..main
then, if nothing there is needed: git reset --hard origin/main"

version=$(python3 -c "import tomllib; print(tomllib.load(open('pyproject.toml', 'rb'))['project']['version'])")

grep -q "\"version\": \"$version\"" server.json ||
    fail "server.json does not give version $version"
grep -q "^## $version" CHANGELOG.md ||
    fail "CHANGELOG.md has no section for $version"
if git rev-parse --quiet --verify "refs/tags/$version" >/dev/null; then
    fail "tag $version already exists here; if it is wrong: git tag -d $version"
fi
if [ -n "$(git ls-remote --tags origin "refs/tags/$version")" ]; then
    fail "tag $version is already on GitHub; if it is wrong:
  git push origin :refs/tags/$version"
fi

echo "Tagging $(git log --oneline -1) as $version"
git tag "$version"
git push origin "$version"
echo "Pushed. The release workflow publishes $version on PyPI:"
echo "  https://github.com/baptistelabat/braidpy/actions/workflows/release.yml"
echo "Then publish the documentation: make doc-deploy"
