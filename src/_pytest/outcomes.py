"""
exception classes and constants handling test outcomes
as well as functions creating them
"""
import sys
from typing import Any
from typing import Optional

from packaging.version import Version

if False:  # TYPE_CHECKING
    from typing import NoReturn


class OutcomeException(BaseException):
    """ OutcomeException and its subclass instances indicate and
        contain info about test and collection outcomes.
    """

    def __init__(self, msg: Optional[str] = None, pytrace: bool = True) -> None:
        if msg is not None and not isinstance(msg, str):
            error_msg = (
                "{} expected string as 'msg' parameter, got '{}' instead.\n"
                "Perhaps you meant to use a mark?"
            )
            raise TypeError(error_msg.format(type(self).__name__, type(msg).__name__))
        BaseException.__init__(self, msg)
        self.msg = msg
        self.pytrace = pytrace

    def __repr__(self) -> str:
        if self.msg:
            return self.msg
        return "<{} instance>".format(self.__class__.__name__)

    __str__ = __repr__


TEST_OUTCOME = (OutcomeException, Exception)


class Skipped(OutcomeException):
    # XXX hackish: on 3k we fake to live in the builtins
    # in order to have Skipped exception printing shorter/nicer
    __module__ = "builtins"

    def __init__(
        self,
        msg: Optional[str] = None,
        pytrace: bool = True,
        allow_module_level: bool = False,
    ) -> None:
        OutcomeException.__init__(self, msg=msg, pytrace=pytrace)
        self.allow_module_level = allow_module_level


class Failed(OutcomeException):
    """ raised from an explicit call to pytest.fail() """

    __module__ = "builtins"


class Exit(Exception):
    """ raised for immediate program exits (no tracebacks/summaries)"""

    def __init__(
        self, msg: str = "unknown reason", returncode: Optional[int] = None
    ) -> None:
        self.msg = msg
        self.returncode = returncode
        super().__init__(msg)


# exposed helper methods


def exit(msg: str, returncode: Optional[int] = None) -> "NoReturn":
    """
    Exit testing process.

    :param str msg: message to display upon exit.
    :param int returncode: return code to be used when exiting pytest.
    """
    __tracebackhide__ = True
    raise Exit(msg, returncode)


# Ignore type because of https://github.com/python/mypy/issues/2087.
exit.Exception = Exit  # type: ignore


def skip(msg: str = "", *, allow_module_level: bool = False) -> "NoReturn":
    """
    Skip an executing test with the given message.

    This function should be called only during testing (setup, call or teardown) or
    during collection by using the ``allow_module_level`` flag.  This function can
    be called in doctests as well.

    :kwarg bool allow_module_level: allows this function to be called at
        module level, skipping the rest of the module. Default to False.

    .. note::
        It is better to use the :ref:`pytest.mark.skipif ref` marker when possible to declare a test to be
        skipped under certain conditions like mismatching platforms or
        dependencies.
        Similarly, use the ``# doctest: +SKIP`` directive (see `doctest.SKIP
        <https://docs.python.org/3/library/doctest.html#doctest.SKIP>`_)
        to skip a doctest statically.
    """
    __tracebackhide__ = True
    raise Skipped(msg=msg, allow_module_level=allow_module_level)


# Ignore type because of https://github.com/python/mypy/issues/2087.
skip.Exception = Skipped  # type: ignore


def fail(msg: str = "", pytrace: bool = True) -> "NoReturn":
    """
    Explicitly fail an executing test with the given message.

    :param str msg: the message to show the user as reason for the failure.
    :param bool pytrace: if false the msg represents the full failure information and no
        python traceback will be reported.
    """
    __tracebackhide__ = True
    raise Failed(msg=msg, pytrace=pytrace)


# Ignore type because of https://github.com/python/mypy/issues/2087.
fail.Exception = Failed  # type: ignore


class XFailed(Failed):
    """ raised from an explicit call to pytest.xfail() """


def xfail(reason: str = "") -> "NoReturn":
    """
    Imperatively xfail an executing test or setup functions with the given reason.

    This function should be called only during testing (setup, call or teardown).

    .. note::
        It is better to use the :ref:`pytest.mark.xfail ref` marker when possible to declare a test to be
        xfailed under certain conditions like known bugs or missing features.
    """
    __tracebackhide__ = True
    raise XFailed(reason)


# Ignore type because of https://github.com/python/mypy/issues/2087.
xfail.Exception = XFailed  # type: ignore


def importorskip(
    modname: str, minversion: Optional[str] = None, reason: Optional[str] = None
) -> Any:
    """Imports and returns the requested module ``modname``, or skip the
    current test if the module cannot be imported.

    :param str modname: the name of the module to import
    :param str minversion: if given, the imported module's ``__version__``
        attribute must be at least this minimal version, otherwise the test is
        still skipped.
    :param str reason: if given, this reason is shown as the message when the
        module cannot be imported.
    :returns: The imported module. This should be assigned to its canonical
        name.

    Example::

        docutils = pytest.importorskip("docutils")
    """
    import warnings

    __tracebackhide__ = True
    compile(modname, "", "eval")  # to catch syntaxerrors

    with warnings.catch_warnings():
        # make sure to ignore ImportWarnings that might happen because
        # of existing directories with the same name we're trying to
        # import but without a __init__.py file
        warnings.simplefilter("ignore")
        try:
            __import__(modname)
        except ImportError as exc:
            if reason is None:
                reason = "could not import {!r}: {}".format(modname, exc)
            raise Skipped(reason, allow_module_level=True) from None
    mod = sys.modules[modname]
    if minversion is None:
        return mod
    verattr = getattr(mod, "__version__", None)
    if minversion is not None:
        if verattr is None or Version(verattr) < Version(minversion):
            raise Skipped(
                "module %r has __version__ %r, required is: %r"
                % (modname, verattr, minversion),
                allow_module_level=True,
            )
    return mod
