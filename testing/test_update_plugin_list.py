from __future__ import annotations

from pathlib import Path
import runpy
from unittest.mock import Mock

import pytest


@pytest.mark.parametrize("empty_releases", [{}, {"1.0": []}])
@pytest.mark.parametrize("with_previous_release", [False, True])
def test_missing_release_date(
    monkeypatch: pytest.MonkeyPatch,
    empty_releases: dict[str, list[dict[str, str]]],
    with_previous_release: bool,
) -> None:
    for module in ("platformdirs", "requests_cache", "tabulate", "tqdm", "wcwidth"):
        pytest.importorskip(module)

    script = Path(__file__).resolve().parents[1] / "scripts/update-plugin-list.py"
    iter_plugins = runpy.run_path(str(script))["iter_plugins"]

    releases_by_name = {}
    expected_dates = []

    if with_previous_release:
        releases_by_name["pytest-with-release"] = {
            "1.0": [{"upload_time_iso_8601": "2026-01-15T12:00:00Z"}],
        }
        expected_dates.append("Jan 15, 2026")

    releases_by_name["pytest-without-files"] = empty_releases
    expected_dates.append("N/A")

    def get_response(session: object, name: str, serial: int) -> Mock:
        response = Mock(status_code=200)
        response.json.return_value = {
            "info": {
                "name": name,
                "classifiers": [],
                "requires_dist": [],
                "summary": "",
            },
            "releases": releases_by_name[name],
        }
        return response

    namespace = iter_plugins.__globals__
    monkeypatch.setitem(namespace, "get_session", lambda: None)
    monkeypatch.setitem(
        namespace,
        "pytest_plugin_projects_from_pypi",
        lambda session: dict.fromkeys(releases_by_name, 1),
    )
    monkeypatch.setitem(namespace, "project_response_with_refresh", get_response)
    monkeypatch.setitem(namespace, "tqdm", lambda items, **kwargs: items)

    plugins = list(iter_plugins())

    assert [plugin["last_release"] for plugin in plugins] == expected_dates
