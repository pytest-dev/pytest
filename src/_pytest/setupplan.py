from __future__ import annotations

from _pytest.config import Config
from _pytest.config.argparsing import Parser
from _pytest.fixtures import FixtureDef
from _pytest.fixtures import SubRequest
import pytest


#: This plugin defines no fixtures, so the fixture manager need not read
#: every attribute it has looking for them.
__pytest_no_fixtures__ = True


def pytest_addoption(parser: Parser) -> None:
    group = parser.getgroup("debugconfig")
    group.addoption(
        "--setupplan",
        "--setup-plan",
        action="store_true",
        help="Show what fixtures and tests would be executed but "
        "don't execute anything",
    )


@pytest.hookimpl(tryfirst=True)
def pytest_fixture_setup(
    fixturedef: FixtureDef[object], request: SubRequest
) -> object | None:
    # Will return a dummy fixture if the setuponly option is provided.
    if request.config.option.setupplan:
        my_cache_key = fixturedef.cache_key(request)
        fixturedef.cached_result = (None, my_cache_key, None)
        return fixturedef.cached_result
    return None


@pytest.hookimpl(tryfirst=True)
def pytest_configure(config: Config) -> None:
    # Normalizing at configure time rather than in pytest_cmdline_main means
    # it also applies to programmatically constructed configs, which are
    # configured but never go through the command line entry point.
    if config.option.setupplan:
        config.option.setuponly = True
        config.option.setupshow = True
