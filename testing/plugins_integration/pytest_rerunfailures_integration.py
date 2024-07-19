from __future__ import annotations

import unittest


class MyTestCase(unittest.TestCase):
    first_time = True

    def test_fail_the_first_time(self) -> None:
        """Regression test for issue #12424."""
        if self.first_time:
            type(self).first_time = False
            self.fail()
