""" support for skip/xfail functions and markers. """
import os
import platform
import sys
import traceback
from typing import Any
from typing import Dict
from typing import List
from typing import Optional
from typing import Tuple

from _pytest.config import Config
from _pytest.config import hookimpl
from _pytest.config.argparsing import Parser
from _pytest.mark.structures import Mark
from _pytest.nodes import Item
from _pytest.outcomes import fail
from _pytest.outcomes import skip
from _pytest.outcomes import TEST_OUTCOME
from _pytest.outcomes import xfail
from _pytest.reports import BaseReport
from _pytest.runner import CallInfo
from _pytest.store import StoreKey


def pytest_addoption(parser: Parser) -> None:
    group = parser.getgroup("general")
    group.addoption(
        "--runxfail",
        action="store_true",
        dest="runxfail",
        default=False,
        help="report the results of xfail tests as if they were not marked",
    )

    parser.addini(
        "xfail_strict",
        "default for the strict parameter of xfail "
        "markers when not given explicitly (default: False)",
        default=False,
        type="bool",
    )


def pytest_configure(config: Config) -> None:
    if config.option.runxfail:
        # yay a hack
        import pytest

        old = pytest.xfail
        config._cleanup.append(lambda: setattr(pytest, "xfail", old))

        def nop(*args, **kwargs):
            pass

        nop.Exception = xfail.Exception  # type: ignore[attr-defined] # noqa: F821
        setattr(pytest, "xfail", nop)

    config.addinivalue_line(
        "markers",
        "skip(reason=None): skip the given test function with an optional reason. "
        'Example: skip(reason="no way of currently testing this") skips the '
        "test.",
    )
    config.addinivalue_line(
        "markers",
        "skipif(condition): skip the given test function if eval(condition) "
        "results in a True value.  Evaluation happens within the "
        "module global context. Example: skipif('sys.platform == \"win32\"') "
        "skips the test if we are on the win32 platform. see "
        "https://docs.pytest.org/en/latest/skipping.html",
    )
    config.addinivalue_line(
        "markers",
        "xfail(condition, reason=None, run=True, raises=None, strict=False): "
        "mark the test function as an expected failure if eval(condition) "
        "has a True value. Optionally specify a reason for better reporting "
        "and run=False if you don't even want to execute the test function. "
        "If only specific exception(s) are expected, you can list them in "
        "raises, and if the test fails in other ways, it will be reported as "
        "a true failure. See https://docs.pytest.org/en/latest/skipping.html",
    )


def compiled_eval(expr: str, d: Dict[str, object]) -> Any:
    import _pytest._code

    exprcode = _pytest._code.compile(expr, mode="eval")
    return eval(exprcode, d)


class MarkEvaluator:
    def __init__(self, item: Item, name: str) -> None:
        self.item = item
        self._marks = None  # type: Optional[List[Mark]]
        self._mark = None  # type: Optional[Mark]
        self._mark_name = name

    def __bool__(self) -> bool:
        # don't cache here to prevent staleness
        return bool(self._get_marks())

    def wasvalid(self) -> bool:
        return not hasattr(self, "exc")

    def _get_marks(self) -> List[Mark]:
        return list(self.item.iter_markers(name=self._mark_name))

    def invalidraise(self, exc) -> Optional[bool]:
        raises = self.get("raises")
        if not raises:
            return None
        return not isinstance(exc, raises)

    def istrue(self) -> bool:
        try:
            return self._istrue()
        except TEST_OUTCOME:
            self.exc = sys.exc_info()
            if isinstance(self.exc[1], SyntaxError):
                # TODO: Investigate why SyntaxError.offset is Optional, and if it can be None here.
                assert self.exc[1].offset is not None
                msg = [" " * (self.exc[1].offset + 4) + "^"]
                msg.append("SyntaxError: invalid syntax")
            else:
                msg = traceback.format_exception_only(*self.exc[:2])
            fail(
                "Error evaluating %r expression\n"
                "    %s\n"
                "%s" % (self._mark_name, self.expr, "\n".join(msg)),
                pytrace=False,
            )

    def _getglobals(self) -> Dict[str, object]:
        d = {"os": os, "sys": sys, "platform": platform, "config": self.item.config}
        if hasattr(self.item, "obj"):
            d.update(self.item.obj.__globals__)  # type: ignore[attr-defined] # noqa: F821
        return d

    def _istrue(self) -> bool:
        if hasattr(self, "result"):
            result = getattr(self, "result")  # type: bool
            return result
        self._marks = self._get_marks()

        if self._marks:
            self.result = False
            for mark in self._marks:
                self._mark = mark
                if "condition" not in mark.kwargs:
                    args = mark.args
                else:
                    args = (mark.kwargs["condition"],)

                for expr in args:
                    self.expr = expr
                    if isinstance(expr, str):
                        d = self._getglobals()
                        result = compiled_eval(expr, d)
                    else:
                        if "reason" not in mark.kwargs:
                            # XXX better be checked at collection time
                            msg = (
                                "you need to specify reason=STRING "
                                "when using booleans as conditions."
                            )
                            fail(msg)
                        result = bool(expr)
                    if result:
                        self.result = True
                        self.reason = mark.kwargs.get("reason", None)
                        self.expr = expr
                        return self.result

                if not args:
                    self.result = True
                    self.reason = mark.kwargs.get("reason", None)
                    return self.result
        return False

    def get(self, attr, default=None):
        if self._mark is None:
            return default
        return self._mark.kwargs.get(attr, default)

    def getexplanation(self):
        expl = getattr(self, "reason", None) or self.get("reason", None)
        if not expl:
            if not hasattr(self, "expr"):
                return ""
            else:
                return "condition: " + str(self.expr)
        return expl


skipped_by_mark_key = StoreKey[bool]()
evalxfail_key = StoreKey[MarkEvaluator]()
unexpectedsuccess_key = StoreKey[str]()


@hookimpl(tryfirst=True)
def pytest_runtest_setup(item: Item) -> None:
    # Check if skip or skipif are specified as pytest marks
    item._store[skipped_by_mark_key] = False
    eval_skipif = MarkEvaluator(item, "skipif")
    if eval_skipif.istrue():
        item._store[skipped_by_mark_key] = True
        skip(eval_skipif.getexplanation())

    for skip_info in item.iter_markers(name="skip"):
        item._store[skipped_by_mark_key] = True
        if "reason" in skip_info.kwargs:
            skip(skip_info.kwargs["reason"])
        elif skip_info.args:
            skip(skip_info.args[0])
        else:
            skip("unconditional skip")

    item._store[evalxfail_key] = MarkEvaluator(item, "xfail")
    check_xfail_no_run(item)


@hookimpl(hookwrapper=True)
def pytest_runtest_call(item: Item):
    check_xfail_no_run(item)
    outcome = yield
    passed = outcome.excinfo is None
    if passed:
        check_strict_xfail(item)


def check_xfail_no_run(item: Item) -> None:
    """check xfail(run=False)"""
    if not item.config.option.runxfail:
        evalxfail = item._store[evalxfail_key]
        if evalxfail.istrue():
            if not evalxfail.get("run", True):
                xfail("[NOTRUN] " + evalxfail.getexplanation())


def check_strict_xfail(item: Item) -> None:
    """check xfail(strict=True) for the given PASSING test"""
    evalxfail = item._store[evalxfail_key]
    if evalxfail.istrue():
        strict_default = item.config.getini("xfail_strict")
        is_strict_xfail = evalxfail.get("strict", strict_default)
        if is_strict_xfail:
            del item._store[evalxfail_key]
            explanation = evalxfail.getexplanation()
            fail("[XPASS(strict)] " + explanation, pytrace=False)


@hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item: Item, call: CallInfo[None]):
    outcome = yield
    rep = outcome.get_result()
    evalxfail = item._store.get(evalxfail_key, None)
    # unittest special case, see setting of unexpectedsuccess_key
    if unexpectedsuccess_key in item._store and rep.when == "call":
        reason = item._store[unexpectedsuccess_key]
        if reason:
            rep.longrepr = "Unexpected success: {}".format(reason)
        else:
            rep.longrepr = "Unexpected success"
        rep.outcome = "failed"

    elif item.config.option.runxfail:
        pass  # don't interfere
    elif call.excinfo and isinstance(call.excinfo.value, xfail.Exception):
        assert call.excinfo.value.msg is not None
        rep.wasxfail = "reason: " + call.excinfo.value.msg
        rep.outcome = "skipped"
    elif evalxfail and not rep.skipped and evalxfail.wasvalid() and evalxfail.istrue():
        if call.excinfo:
            if evalxfail.invalidraise(call.excinfo.value):
                rep.outcome = "failed"
            else:
                rep.outcome = "skipped"
                rep.wasxfail = evalxfail.getexplanation()
        elif call.when == "call":
            strict_default = item.config.getini("xfail_strict")
            is_strict_xfail = evalxfail.get("strict", strict_default)
            explanation = evalxfail.getexplanation()
            if is_strict_xfail:
                rep.outcome = "failed"
                rep.longrepr = "[XPASS(strict)] {}".format(explanation)
            else:
                rep.outcome = "passed"
                rep.wasxfail = explanation
    elif (
        item._store.get(skipped_by_mark_key, True)
        and rep.skipped
        and type(rep.longrepr) is tuple
    ):
        # skipped by mark.skipif; change the location of the failure
        # to point to the item definition, otherwise it will display
        # the location of where the skip exception was raised within pytest
        _, _, reason = rep.longrepr
        filename, line = item.reportinfo()[:2]
        assert line is not None
        rep.longrepr = str(filename), line + 1, reason


# called by terminalreporter progress reporting


def pytest_report_teststatus(report: BaseReport) -> Optional[Tuple[str, str, str]]:
    if hasattr(report, "wasxfail"):
        if report.skipped:
            return "xfailed", "x", "XFAIL"
        elif report.passed:
            return "xpassed", "X", "XPASS"
    return None
