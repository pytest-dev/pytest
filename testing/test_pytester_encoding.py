from __future__ import annotations

from encodings.aliases import aliases
from pathlib import Path
from textwrap import dedent
from typing import Generator

import pytest


def all_encodings() -> Generator[str, None, None]:
    """Yields string representation of encodings."""
    for encoding in set(aliases.values()):
        try:
            "abc123".encode(encoding)
            yield encoding
        except LookupError:
            continue


@pytest.fixture(scope="session", params=all_encodings())
def encoding(request):
    return request.param


@pytest.fixture(
    params=[
        ("3", "A"),
        ("✅", "💥"),
        ("é", "ü"),
        ("Я", "ж"),  # Cyrillic characters
        ("電腦", "电脑"),  # Chinese: traditional vs simplified for "computer"
        ("学校", "がっこう"),  # Japanese: Kanji vs Hiragana for "school"
    ],
    ids=[
        "latin",
        "check-explosion",
        "accented_letters",
        "cyrillic_basic",
        "chinese_computer",
        "japanese_school",
    ],
)
def any_charset(request):
    return request.param


@pytest.mark.parametrize("fix", ["testdir", "pytester"])
def test_compare_write_bytes(fix, request, encoding, any_charset):
    """
    `makeypfile` ignores keyword arguments `encoding` if content is not bytes.

    1. create test data and convert to bytes, if encoding fails the test is skipped.
    2. use both functions to create python file

    - if both functions raise the same error, everything is as expected
    - if Path.write_bytes succeeds so should `makepyfile` and error should be None
    - both files should exist after the test
    """
    _fixture = request.getfixturevalue(fix)

    a, b = any_charset

    try:
        bytes_content = dedent(
            f"""
                def f():
                    '''
                    >>> print('{a}')
                    {b}
                    '''
                    pass
                """
        ).encode(encoding)
    except UnicodeEncodeError:
        # skip test do testdata could not prepared
        pytest.xfail(f"{any_charset!r} cannot be encoded with encoding={encoding!r}")

    try:
        make_file = _fixture.makepyfile(
            bytes_content,
            encoding=encoding,
        )
    except Exception as e:
        error = e  # if both function fail the same, everything is as expected
    else:
        error = None

    try:
        temp_dir = _fixture.path  # pytester fixture
    except AttributeError:
        temp_dir = _fixture.tmpdir  # legacy testdir fixture

    basic_file = Path(temp_dir).joinpath("test_basic.py")
    try:
        basic_file.write_bytes(bytes_content)
    except Exception as e:
        assert type(error) is type(
            e
        ), f"basically never should happen, but {e=} was raised."
    else:
        assert error is None, f"makepyfile screwed up {encoding=} and raised {error=}"

    assert (
        Path(make_file).is_file() and Path(basic_file).is_file()
    ), "files are missing."
