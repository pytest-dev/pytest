# mypy: disallow-untyped-defs
"""
Script used to publish GitHub release notes extracted from CHANGELOG.rst.

This script is meant to be executed after a successful deployment in GitHub actions.

Uses the following environment variables:

* GIT_TAG: the name of the tag of the current commit.
* GH_RELEASE_NOTES_TOKEN: a personal access token with 'repo' permissions.

  Create one at:

    https://github.com/settings/tokens

  This token should be set in a secret in the repository, which is exposed as an
  environment variable in the main.yml workflow file.

The script also requires ``pandoc`` to be previously installed in the system.

Requires Python3.6+.
"""
import re
import sys
from pathlib import Path
from typing import Sequence

import pypandoc


def parse_changelog(tag_name: str) -> str:
    p = Path(__file__).parent.parent / "doc/en/changelog.rst"
    changelog_lines = p.read_text(encoding="UTF-8").splitlines()

    title_regex = re.compile(r"pytest (\d\.\d+\.\d+\w*) \(\d{4}-\d{2}-\d{2}\)")
    consuming_version = False
    version_lines = []
    for line in changelog_lines:
        m = title_regex.match(line)
        if m:
            # found the version we want: start to consume lines until we find the next version title
            if m.group(1) == tag_name:
                consuming_version = True
            # found a new version title while parsing the version we want: break out
            elif consuming_version:
                break
        if consuming_version:
            version_lines.append(line)

    return "\n".join(version_lines)


def convert_rst_to_md(text: str) -> str:
    result = pypandoc.convert_text(
        text, "md", format="rst", extra_args=["--wrap=preserve"]
    )
    assert isinstance(result, str), repr(result)
    return result


def main(argv: Sequence[str]) -> int:
    if len(argv) != 3:
        print("Usage: generate-gh-release-notes VERSION FILE")
        return 2

    version, filename = argv[1:3]
    print(f"Generating GitHub release notes for version {version}")
    rst_body = parse_changelog(version)
    md_body = convert_rst_to_md(rst_body)
    Path(filename).write_text(md_body, encoding="UTF-8")
    print()
    print(f"Done: {filename}")
    print()
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
