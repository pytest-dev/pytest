from __future__ import annotations

import textwrap
from typing import Any

from _pytest.fixtures import FixtureRequest
from _pytest.main import Session
from _pytest.pytester import Pytester
from _pytest.pytester import RecordedHookCall
from _pytest.pytester import RunResult
import pytest


# Start of tests for classes

# def run_import_class_test(pytester: Pytester, passed: int = 0, errors: int = 0) -> None:
#     src_dir = pytester.mkdir("src")
#     tests_dir = pytester.mkdir("tests")
#     src_file = src_dir / "foo.py"

#     src_file.write_text(
#         textwrap.dedent("""\
#     class Testament(object):
#         def __init__(self):
#             super().__init__()
#             self.collections = ["stamp", "coin"]

#         def personal_property(self):
#             return [f"my {x} collection" for x in self.collections]
#     """),
#         encoding="utf-8",
#     )

#     test_file = tests_dir / "foo_test.py"
#     test_file.write_text(
#         textwrap.dedent("""\
#     import sys
#     import os

#     current_file = os.path.abspath(__file__)
#     current_dir = os.path.dirname(current_file)
#     parent_dir = os.path.abspath(os.path.join(current_dir, '..'))
#     sys.path.append(parent_dir)

#     from src.foo import Testament

#     class TestDomain:
#         def test_testament(self):
#             testament = Testament()
#             assert testament.personal_property()
#     """),
#         encoding="utf-8",
#     )

#     result = pytester.runpytest()
#     result.assert_outcomes(passed=passed, errors=errors)

# def test_collect_imports_disabled(pytester: Pytester) -> None:
#     pytester.makeini("""
#         [pytest]
#         testpaths = "tests"
#         collect_imported_tests = false
#     """)

#     run_import_class_test(pytester, passed=1)

#     # Verify that the state of hooks
#     reprec = pytester.inline_run()
#     items_collected = reprec.getcalls("pytest_itemcollected")
#     assert len(items_collected) == 1
#     for x in items_collected:
#         assert x.item._getobj().__name__ == "test_testament"

# def test_collect_imports_default(pytester: Pytester) -> None:
#     run_import_class_test(pytester, errors=1)

#     # TODO, hooks


# def test_collect_imports_enabled(pytester: Pytester) -> None:
#     pytester.makeini("""
#         [pytest]
#         collect_imported_tests = true
#     """)

#     run_import_class_test(pytester, errors=1)
#     # TODO, hooks


# End of tests for classes
#################################
# Start of tests for functions


def run_import_functions_test(
    pytester: Pytester, passed: int, errors: int, failed: int
) -> RunResult:
    # Note that these "tests" should _not_ be treated as tests if `collect_imported_tests = false`
    # They are normal functions in that case, that happens to have test_* or *_test in the name.
    # Thus should _not_ be collected!
    pytester.makepyfile(
        **{
            "src/foo.py": textwrap.dedent(
                """\
                def test_function():
                    some_random_computation = 5
                    return some_random_computation

                def test_bar():
                    pass
                """
            )
        }
    )

    # Inferred from the comment above, this means that there is _only_ one actual test
    # which should result in only 1 passing test being ran.
    pytester.makepyfile(
        **{
            "tests/foo_test.py": textwrap.dedent(
                """\
                import sys
                import os

                current_file = os.path.abspath(__file__)
                current_dir = os.path.dirname(current_file)
                parent_dir = os.path.abspath(os.path.join(current_dir, '..'))
                sys.path.append(parent_dir)

                from src.foo import *

                class TestDomain:
                    def test_important(self):
                        res = test_function()
                        if res == 5:
                            pass
                """
            )
        }
    )

    result = pytester.runpytest()
    result.assert_outcomes(passed=passed, errors=errors, failed=failed)
    return result


# def test_collect_function_imports_enabled(pytester: Pytester) -> None:
#     pytester.makeini("""
#         [pytest]
#         testpaths = "tests"
#         collect_imported_tests = true
#     """)

#     run_import_functions_test(pytester, passed=2, errors=0, failed=1)
#     reprec = pytester.inline_run()
#     items_collected = reprec.getcalls("pytest_itemcollected")
#     # Recall that the default is `collect_imported_tests = true`.
#     # Which means that the normal functions are now interpreted as
#     # valid tests and `test_function()` will fail.
#     assert len(items_collected) == 3
#     for x in items_collected:
#         assert x.item._getobj().__name__ in [
#             "test_important",
#             "test_bar",
#             "test_function",
#         ]


# def test_behaviour_without_testpaths_set_and_false(pytester: Pytester) -> None:
#     # Make sure `collect_imported_tests` has no dependence on `testpaths`
#     pytester.makeini("""
#         [pytest]
#         collect_imported_tests = false
#     """)

#     run_import_functions_test(pytester, passed=1, errors=0, failed=0)
#     reprec = pytester.inline_run()
#     items_collected = reprec.getcalls("pytest_itemcollected")
#     assert len(items_collected) == 1
#     for x in items_collected:
#         assert x.item._getobj().__name__ == "test_important"


# def test_behaviour_without_testpaths_set_and_true(pytester: Pytester) -> None:
#     # Make sure `collect_imported_tests` has no dependence on `testpaths`
#     pytester.makeini("""
#         [pytest]
#         collect_imported_tests = true
#     """)

#     run_import_functions_test(pytester, passed=2, errors=0, failed=1)
#     reprec = pytester.inline_run()
#     items_collected = reprec.getcalls("pytest_itemcollected")
#     assert len(items_collected) == 3


class TestHookBehaviour:
    collect_outcomes: dict[str, Any] = {}

    @pytest.mark.parametrize("step", [1, 2, 3])
    def test_hook_behaviour(self, pytester: Pytester, step: int) -> None:
        if step == 1:
            self._test_hook_default_behaviour(pytester)
        elif step == 2:
            self._test_hook_behaviour_when_collect_off(pytester)
        elif step == 3:
            self._test_hook_behaviour()

    @pytest.fixture(scope="class", autouse=True)
    def setup_collect_outcomes(self, request: FixtureRequest) -> None:
        request.cls.collect_outcomes = {}

    def _test_hook_default_behaviour(self, pytester: Pytester) -> None:
        pytester.makepyfile(
            **{
                "tests/foo_test.py": textwrap.dedent(
                    """\
                    class TestDomain:
                        def test_important(self):
                            pass
                    """
                )
            }
        )

        result = pytester.runpytest()
        result.assert_outcomes(passed=1)
        reprec = pytester.inline_run()
        reports = reprec.getreports("pytest_collectreport")
        modified = reprec.getcalls("pytest_collection_modifyitems")
        items_collected = reprec.getcalls("pytest_itemcollected")

        self.collect_outcomes["default"] = {
            "result": result.parseoutcomes(),
            "modified": modified,
            "items_collected": items_collected,
            "reports": reports,
        }

    def _test_hook_behaviour_when_collect_off(self, pytester: Pytester) -> None:
        pytester.makeini("""
            [pytest]
            collect_imported_tests = false
        """)
        res = run_import_functions_test(pytester, passed=1, errors=0, failed=0)
        reprec = pytester.inline_run()
        reports = reprec.getreports("pytest_collectreport")
        modified = reprec.getcalls("pytest_collection_modifyitems")
        items_collected = reprec.getcalls("pytest_itemcollected")

        self.collect_outcomes["collect_off"] = {
            "result": res.parseoutcomes(),
            "modified": modified,
            "items_collected": items_collected,
            "reports": reports,
        }

    # Now check that the two tests above did indeed result in the same outcome.
    def _test_hook_behaviour(self) -> None:
        print("ABCD", self.collect_outcomes)
        default = self.collect_outcomes["default"]
        collect_off = self.collect_outcomes["collect_off"]
        assert default["result"] == collect_off["result"]

        assert len(default["modified"]) == len(collect_off["modified"]) == 1

        def_modified_record: RecordedHookCall = default["modified"][0]
        off_modified_record: RecordedHookCall = collect_off["modified"][0]
        def_sess: Session = def_modified_record.__dict__["session"]
        off_sess: Session = off_modified_record.__dict__["session"]

        assert def_sess.exitstatus == off_sess.exitstatus
        assert def_sess.testsfailed == off_sess.testsfailed
        assert def_sess.testscollected == off_sess.testscollected

        def_items = def_modified_record.__dict__["items"]
        off_items = off_modified_record.__dict__["items"]
        assert len(def_items) == len(off_items) == 1
        assert def_items[0].name == off_items[0].name

        assert (
            len(default["items_collected"]) == len(collect_off["items_collected"]) == 1
        )

        def_items_record: RecordedHookCall = default["items_collected"][0]
        off_items_record: RecordedHookCall = collect_off["items_collected"][0]
        def_items = def_items_record.__dict__["item"]
        off_items = off_items_record.__dict__["item"]
        assert def_items.name == off_items.name

        # TODO: fix diff:
        # [
        #   <CollectReport '' lenresult=1 outcome='passed'>,
        # - <CollectReport 'src' lenresult=0 outcome='passed'>,
        #   <CollectReport 'tests/foo_test.py::TestDomain' lenresult=1 outcome='passed'>,
        #   <CollectReport 'tests/foo_test.py' lenresult=1 outcome='passed'>,
        #   <CollectReport 'tests' lenresult=1 outcome='passed'>,
        # - <CollectReport '.' lenresult=2 outcome='passed'>,
        # ?                                  ^
        # + <CollectReport '.' lenresult=1 outcome='passed'>,
        # ?                                  ^
        # ]

        # assert len(default['reports']) == len(collect_off['reports'])
        # for i in range(len(default['reports'])):
        #     print("def",default['reports'][i].__dict__)
        #     print("off",collect_off['reports'][i].__dict__)

        # from pprint import pprint
        # pprint(default['reports'])
        # pprint(collect_off['reports'])
        # assert default['reports'] == collect_off['reports']
