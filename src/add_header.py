import subprocess
import sys
import os
import re
from datetime import datetime
from pathlib import Path

MPL_HEADER_TEMPLATE = """# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

\"\"\"
Filename: {filename}
Description: {description}
Authors: {authors}
Created: {created}
Repository: {repo_url}
License: Mozilla Public License 2.0
\"\"\"

"""

DEFAULT_DESCRIPTION = "[TODO: Add description here]"


def get_git_authors(filepath):
    raw = (
        subprocess.check_output(
            ["git", "log", "--follow", "--format=%aN", filepath],
            stderr=subprocess.DEVNULL,
        )
        .decode()
        .strip()
        .split("\n")
    )
    return ", ".join(sorted(set(filter(None, raw))))


def get_git_creation_date(filepath):
    date_str = (
        subprocess.check_output(
            ["git", "log", "--diff-filter=A", "--follow", "--format=%aI", filepath],
            stderr=subprocess.DEVNULL,
        )
        .decode()
        .strip()
        .split("\n")[0]
    )
    return date_str[:10] if date_str else datetime.today().strftime("%Y-%m-%d")


def extract_description(content):
    match = re.search(r"Description:\s*(.*?)\n", content)
    return match.group(1).strip() if match else DEFAULT_DESCRIPTION


def remove_existing_mpl_header(content):
    pattern = re.compile(
        r'# This Source Code Form is subject to the terms of the Mozilla Public.*?"""[\r\n]+',
        re.DOTALL,
    )
    return pattern.sub("", content, count=1)


def get_repo_url():
    url = (
        subprocess.check_output(
            ["git", "config", "--get", "remote.origin.url"],
            stderr=subprocess.DEVNULL,
        )
        .decode()
        .strip()
    )
    return url or "Unknown"


def insert_or_replace_header(filepath, repo_url):
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()

    description = extract_description(content)
    content = remove_existing_mpl_header(content)

    filename = os.path.basename(filepath)
    authors = get_git_authors(filepath)
    created = get_git_creation_date(filepath)

    header = MPL_HEADER_TEMPLATE.format(
        filename=filename,
        authors=authors,
        created=created,
        description=description,
        repo_url=repo_url,
    )

    new_content = header + "\n" + content.lstrip()

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(new_content)

    return True


def process_repository(root="."):
    repo_url = get_repo_url()
    updated = 0
    for path in Path(root).rglob("*.py"):
        if path.is_file():
            if insert_or_replace_header(str(path), repo_url):
                print(f"🔄 Header updated in: {path}")
                updated += 1
    print(f"\n✅ Done. Headers updated in {updated} file(s).")


if __name__ == "__main__":
    if len(sys.argv) == 1:
        process_repository("braidpy")
    elif len(sys.argv) == 2:
        process_repository(sys.argv[1])
    else:
        print("Usage: python add_header.py [optional_path_to_repo]")
