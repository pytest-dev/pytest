# mypy: allow-untyped-defs
from __future__ import annotations

import sqlite3

import pytest


class GreetingPlugin:
    def __init__(self):
        self.connection = sqlite3.connect(":memory:")

    def pytest_generate_tests(self, metafunc):
        if "greeting" in metafunc.fixturenames:
            languages = [
                row[0]
                for row in self.connection.execute(
                    "SELECT language FROM greetings ORDER BY language"
                )
            ]
            metafunc.parametrize("greeting", languages, indirect=True)

    @pytest.fixture
    def greeting(self, request):
        (message,) = self.connection.execute(
            "SELECT message FROM greetings WHERE language = ?", (request.param,)
        ).fetchone()
        return message

    def pytest_unconfigure(self):
        self.connection.close()


def pytest_configure(config):
    plugin = GreetingPlugin()
    config.pluginmanager.register(plugin, "greetings")
    plugin.connection.executescript(
        """
        CREATE TABLE greetings (language TEXT, message TEXT);
        INSERT INTO greetings VALUES ('english', 'Hello'), ('french', 'Bonjour');
        """
    )
