# mypy: allow-untyped-defs
from __future__ import annotations

import io
import re
import sys

from _pytest.outcomes import Failed
from _pytest.pytester import Pytester
from _pytest.warning_types import PytestWarning
import pytest


def wrap_escape(s: str) -> str:
    return "^" + re.escape(s) + "$"


class TestRaises:
    def test_check_callable(self) -> None:
        with pytest.raises(TypeError, match=r".* must be callable"):
            pytest.raises(RuntimeError, "int('qwe')")  # type: ignore[call-overload]

    def test_raises(self):
        excinfo = pytest.raises(ValueError, int, "qwe")
        assert "invalid literal" in str(excinfo.value)

    def test_raises_function(self):
        excinfo = pytest.raises(ValueError, int, "hello")
        assert "invalid literal" in str(excinfo.value)

    def test_raises_does_not_allow_none(self):
        with pytest.raises(
            ValueError,
            match=wrap_escape("You must specify at least one parameter to match on."),
        ):
            # We're testing that this invalid usage gives a helpful error,
            # so we can ignore Mypy telling us that None is invalid.
            pytest.raises(expected_exception=None)  # type: ignore

    # it's unclear if this message is helpful, and if it is, should it trigger more
    # liberally? Usually you'd get a TypeError here
    def test_raises_false_and_arg(self):
        with pytest.raises(
            ValueError,
            match=wrap_escape(
                "Expected an exception type or a tuple of exception types, but got `False`. "
                "Raising exceptions is already understood as failing the test, so you don't need "
                "any special code to say 'this should never raise an exception'."
            ),
        ):
            pytest.raises(False, int)  # type: ignore[call-overload]

    def test_raises_does_not_allow_empty_tuple(self):
        with pytest.raises(
            ValueError,
            match=wrap_escape("You must specify at least one parameter to match on."),
        ):
            pytest.raises(expected_exception=())

    def test_raises_callable_no_exception(self) -> None:
        class A:
            def __call__(self):
                pass

        try:
            pytest.raises(ValueError, A())
        except pytest.fail.Exception:
            pass

    def test_raises_falsey_type_error(self) -> None:
        with pytest.raises(TypeError):
            with pytest.raises(AssertionError, match=0):  # type: ignore[call-overload]
                raise AssertionError("ohai")

    def test_raises_repr_inflight(self):
        """Ensure repr() on an exception info inside a pytest.raises with block works (#4386)"""

        class E(Exception):
            pass

        with pytest.raises(E) as excinfo:
            # this test prints the inflight uninitialized object
            # using repr and str as well as pprint to demonstrate
            # it works
            print(str(excinfo))
            print(repr(excinfo))
            import pprint

            pprint.pprint(excinfo)
            raise E()

    def test_raises_as_contextmanager(self, pytester: Pytester) -> None:
        pytester.makepyfile(
            """
            import pytest
            import _pytest._code

            def test_simple():
                with pytest.raises(ZeroDivisionError) as excinfo:
                    assert isinstance(excinfo, _pytest._code.ExceptionInfo)
                    1/0
                print(excinfo)
                assert excinfo.type == ZeroDivisionError
                assert isinstance(excinfo.value, ZeroDivisionError)

            def test_noraise():
                with pytest.raises(pytest.raises.Exception):
                    with pytest.raises(ValueError):
                           int()

            def test_raise_wrong_exception_passes_by():
                with pytest.raises(ZeroDivisionError):
                    with pytest.raises(ValueError):
                           1/0
        """
        )
        result = pytester.runpytest()
        result.stdout.fnmatch_lines(["*3 passed*"])

    def test_does_not_raise(self, pytester: Pytester) -> None:
        pytester.makepyfile(
            """
            from contextlib import nullcontext as does_not_raise
            import pytest

            @pytest.mark.parametrize('example_input,expectation', [
                (3, does_not_raise()),
                (2, does_not_raise()),
                (1, does_not_raise()),
                (0, pytest.raises(ZeroDivisionError)),
            ])
            def test_division(example_input, expectation):
                '''Test how much I know division.'''
                with expectation:
                    assert (6 / example_input) is not None
        """
        )
        result = pytester.runpytest()
        result.stdout.fnmatch_lines(["*4 passed*"])

    def test_does_not_raise_does_raise(self, pytester: Pytester) -> None:
        pytester.makepyfile(
            """
            from contextlib import nullcontext as does_not_raise
            import pytest

            @pytest.mark.parametrize('example_input,expectation', [
                (0, does_not_raise()),
                (1, pytest.raises(ZeroDivisionError)),
            ])
            def test_division(example_input, expectation):
                '''Test how much I know division.'''
                with expectation:
                    assert (6 / example_input) is not None
        """
        )
        result = pytester.runpytest()
        result.stdout.fnmatch_lines(["*2 failed*"])

    def test_raises_with_invalid_regex(self, pytester: Pytester) -> None:
        pytester.makepyfile(
            """
            import pytest

            def test_invalid_regex():
                with pytest.raises(ValueError, match="invalid regex character ["):
                    raise ValueError()
            """
        )
        result = pytester.runpytest()
        result.stdout.fnmatch_lines(
            [
                "*Invalid regex pattern provided to 'match': unterminated character set at position 24*",
            ]
        )
        result.stdout.no_fnmatch_line("*Traceback*")
        result.stdout.no_fnmatch_line("*File*")
        result.stdout.no_fnmatch_line("*line*")

    def test_noclass(self) -> None:
        with pytest.raises(TypeError):
            pytest.raises("wrong", lambda: None)  # type: ignore[call-overload]

    def test_invalid_arguments_to_raises(self) -> None:
        with pytest.raises(TypeError, match="unknown"):
            with pytest.raises(TypeError, unknown="bogus"):  # type: ignore[call-overload]
                raise ValueError()

    def test_tuple(self):
        with pytest.raises((KeyError, ValueError)):
            raise KeyError("oops")

    def test_no_raise_message(self) -> None:
        try:
            pytest.raises(ValueError, int, "0")
        except pytest.fail.Exception as e:
            assert e.msg == f"DID NOT RAISE {ValueError!r}"
        else:
            assert False, "Expected pytest.raises.Exception"

        try:
            with pytest.raises(ValueError):
                pass
        except pytest.fail.Exception as e:
            assert e.msg == f"DID NOT RAISE {ValueError!r}"
        else:
            assert False, "Expected pytest.raises.Exception"

    @pytest.mark.parametrize(
        "method", ["function", "function_match", "with", "with_raisesexc", "with_group"]
    )
    def test_raises_cyclic_reference(self, method):
        """Ensure pytest.raises does not leave a reference cycle (#1965)."""
        import gc

        class T:
            def __call__(self):
                raise ValueError

        t = T()
        refcount = len(gc.get_referrers(t))

        if method == "function":
            pytest.raises(ValueError, t)
        elif method == "function_match":
            pytest.raises(ValueError, t).match("^$")
        elif method == "with":
            with pytest.raises(ValueError):
                t()
        elif method == "with_raisesexc":
            with pytest.RaisesExc(ValueError):
                t()
        elif method == "with_group":
            with pytest.RaisesGroup(ValueError, allow_unwrapped=True):
                t()
        else:  # pragma: no cover
            raise AssertionError("bad parametrization")

        # ensure both forms of pytest.raises don't leave exceptions in sys.exc_info()
        assert sys.exc_info() == (None, None, None)

        assert refcount == len(gc.get_referrers(t))

    def test_raises_match(self) -> None:
        msg = r"with base \d+"
        with pytest.raises(ValueError, match=msg):
            int("asdf")

        msg = "with base 10"
        with pytest.raises(ValueError, match=msg):
            int("asdf")

        msg = "with base 16"
        expr = (
            "Regex pattern did not match.\n"
            f" Regex: {msg!r}\n"
            " Input: \"invalid literal for int() with base 10: 'asdf'\""
        )
        with pytest.raises(AssertionError, match="^" + re.escape(expr) + "$"):
            with pytest.raises(ValueError, match=msg):
                int("asdf", base=10)

        # "match" without context manager.
        pytest.raises(ValueError, int, "asdf").match("invalid literal")
        with pytest.raises(AssertionError) as excinfo:
            pytest.raises(ValueError, int, "asdf").match(msg)
        assert str(excinfo.value) == expr

        pytest.raises(TypeError, int, match="invalid")

        def tfunc(match):
            raise ValueError(f"match={match}")

        pytest.raises(ValueError, tfunc, match="asdf").match("match=asdf")
        pytest.raises(ValueError, tfunc, match="").match("match=")

        # empty string matches everything, which is probably not what the user wants
        with pytest.warns(
            PytestWarning,
            match=wrap_escape(
                "matching against an empty string will *always* pass. If you want to check for an empty message you "
                "need to pass '^$'. If you don't want to match you should pass `None` or leave out the parameter."
            ),
        ):
            pytest.raises(match="")

    def test_match_failure_string_quoting(self):
        with pytest.raises(AssertionError) as excinfo:
            with pytest.raises(AssertionError, match="'foo"):
                raise AssertionError("'bar")
        (msg,) = excinfo.value.args
        assert msg == '''Regex pattern did not match.\n Regex: "'foo"\n Input: "'bar"'''

    def test_match_failure_exact_string_message(self):
        message = "Oh here is a message with (42) numbers in parameters"
        with pytest.raises(AssertionError) as excinfo:
            with pytest.raises(AssertionError, match=message):
                raise AssertionError(message)
        (msg,) = excinfo.value.args
        assert msg == (
            "Regex pattern did not match.\n"
            " Regex: 'Oh here is a message with (42) numbers in parameters'\n"
            " Input: 'Oh here is a message with (42) numbers in parameters'\n"
            " Did you mean to `re.escape()` the regex?"
        )

    def test_raises_match_wrong_type(self):
        """Raising an exception with the wrong type and match= given.

        pytest should throw the unexpected exception - the pattern match is not
        really relevant if we got a different exception.
        """
        with pytest.raises(
            ValueError,
            match=wrap_escape("invalid literal for int() with base 10: 'asdf'"),
        ):
            with pytest.raises(IndexError, match="nomatch"):
                int("asdf")

    def test_raises_exception_looks_iterable(self):
        class Meta(type):
            def __getitem__(self, item):
                return 1 / 0

            def __len__(self):
                return 1

        class ClassLooksIterableException(Exception, metaclass=Meta):
            pass

        with pytest.raises(
            Failed,
            match=r"DID NOT RAISE <class 'raises(\..*)*ClassLooksIterableException'>",
        ):
            pytest.raises(ClassLooksIterableException, lambda: None)

    def test_raises_with_raising_dunder_class(self) -> None:
        """Test current behavior with regard to exceptions via __class__ (#4284)."""

        class CrappyClass(Exception):
            # Type ignored because it's bypassed intentionally.
            @property  # type: ignore
            def __class__(self):
                assert False, "via __class__"

        with pytest.raises(AssertionError) as excinfo:
            with pytest.raises(CrappyClass()):  # type: ignore[call-overload]
                pass
        assert "via __class__" in excinfo.value.args[0]

    def test_raises_context_manager_with_kwargs(self):
        with pytest.raises(expected_exception=ValueError):
            raise ValueError
        with pytest.raises(
            TypeError,
            match=wrap_escape(
                "Unexpected keyword arguments passed to pytest.raises: foo\n"
                "Use context-manager form instead?"
            ),
        ):
            with pytest.raises(OSError, foo="bar"):  # type: ignore[call-overload]
                pass

    def test_expected_exception_is_not_a_baseexception(self) -> None:
        with pytest.raises(
            TypeError,
            match=wrap_escape(
                "expected exception must be a BaseException type, not 'str'"
            ),
        ):
            with pytest.raises("hello"):  # type: ignore[call-overload]
                pass  # pragma: no cover

        class NotAnException:
            pass

        with pytest.raises(
            ValueError,
            match=wrap_escape(
                "expected exception must be a BaseException type, not 'NotAnException'"
            ),
        ):
            with pytest.raises(NotAnException):  # type: ignore[type-var]
                pass  # pragma: no cover

        with pytest.raises(
            TypeError,
            match=wrap_escape(
                "expected exception must be a BaseException type, not 'str'"
            ),
        ):
            with pytest.raises(("hello", NotAnException)):  # type: ignore[arg-type]
                pass  # pragma: no cover

    def test_issue_11872(self) -> None:
        """Regression test for #11872.

        urllib.error.HTTPError on Python<=3.9 raises KeyError instead of
        AttributeError on invalid attribute access.

        https://github.com/python/cpython/issues/98778
        """
        from email.message import Message
        from urllib.error import HTTPError

        with pytest.raises(HTTPError, match="Not Found") as exc_info:
            raise HTTPError(
                code=404, msg="Not Found", fp=io.BytesIO(), hdrs=Message(), url=""
            )
        exc_info.value.close()  # avoid a resource warning
