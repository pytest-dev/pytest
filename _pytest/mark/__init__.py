""" generic mechanism for marking and selecting python functions. """
from .model import MarkInfo, MarkDecorator, MarkGenerator


class MarkerError(Exception):
    """Error in use of a pytest marker/attribute."""


def pytest_namespace():
    return {'mark': MarkGenerator()}


def pytest_addoption(parser):
    # yapf: disable
    group = parser.getgroup("general")
    group._addoption(
        '-k',
        action="store", dest="keyword", default='', metavar="EXPRESSION",
        help="only run tests which match the given substring expression. "
             "An expression is a python evaluatable expression "
             "where all names are substring-matched against test names "
             "and their parent classes. Example: -k 'test_method or test "
             "other' matches all test functions and classes whose name "
             "contains 'test_method' or 'test_other'. "
             "Additionally keywords are matched to classes and functions "
             "containing extra names in their 'extra_keyword_matches' set, "
             "as well as functions which have names assigned directly to them."
    )

    group._addoption(
        "-m",
        action="store", dest="markexpr", default="", metavar="MARKEXPR",
        help="only run tests matching given mark expression.  "
             "example: -m 'mark1 and not mark2'."
    )

    group.addoption(
        "--markers", action="store_true",
        help="show markers (builtin, plugin and per-project ones)."
    )

    parser.addini("markers", "markers for test functions", 'linelist')
    # yapf: enable

def pytest_cmdline_main(config):
    import _pytest.config
    if config.option.markers:
        config._do_configure()
        tw = _pytest.config.create_terminal_writer(config)
        for line in config.getini("markers"):
            name, rest = line.split(":", 1)
            tw.write("@pytest.mark.%s:" % name, bold=True)
            tw.line(rest)
            tw.line()
        config._ensure_unconfigure()
        return 0


pytest_cmdline_main.tryfirst = True


def pytest_collection_modifyitems(items, config):
    keywordexpr = config.option.keyword
    matchexpr = config.option.markexpr
    if not keywordexpr and not matchexpr:
        return
    # pytest used to allow "-" for negating
    # but today we just allow "-" at the beginning, use "not" instead
    # we probably remove "-" alltogether soon
    if keywordexpr.startswith("-"):
        keywordexpr = "not " + keywordexpr[1:]
    selectuntil = False
    if keywordexpr[-1:] == ":":
        selectuntil = True
        keywordexpr = keywordexpr[:-1]

    remaining = []
    deselected = []
    for colitem in items:
        if keywordexpr and not matchkeyword(colitem, keywordexpr):
            deselected.append(colitem)
        else:
            if selectuntil:
                keywordexpr = None
            if matchexpr:
                if not matchmark(colitem, matchexpr):
                    deselected.append(colitem)
                    continue
            remaining.append(colitem)

    if deselected:
        config.hook.pytest_deselected(items=deselected)
        items[:] = remaining


class MarkMapping:
    """Provides a local mapping for markers where item access
    resolves to True if the marker is present. """

    def __init__(self, keywords):
        mymarks = set()
        for key, value in keywords.items():
            if isinstance(value, MarkInfo) or isinstance(value, MarkDecorator):
                mymarks.add(key)
        self._mymarks = mymarks

    def __getitem__(self, name):
        return name in self._mymarks


class KeywordMapping:
    """Provides a local mapping for keywords.
    Given a list of names, map any substring of one of these names to True.
    """

    def __init__(self, names):
        self._names = names

    def __getitem__(self, subname):
        for name in self._names:
            if subname in name:
                return True
        return False


def matchmark(colitem, markexpr):
    """Tries to match on any marker names, attached to the given colitem."""
    return eval(markexpr, {}, MarkMapping(colitem.keywords))


def matchkeyword(colitem, keywordexpr):
    """Tries to match given keyword expression to given collector item.

    Will match on the name of colitem, including the names of its parents.
    Only matches names of items which are either a :class:`Class` or a
    :class:`Function`.
    Additionally, matches on names in the 'extra_keyword_matches' set of
    any item, as well as names directly assigned to test functions.
    """
    mapped_names = set()

    # Add the names of the current item and any parent items
    import pytest
    for item in colitem.listchain():
        if not isinstance(item, pytest.Instance):
            mapped_names.add(item.name)

    # Add the names added as extra keywords to current or parent items
    for name in colitem.listextrakeywords():
        mapped_names.add(name)

    # Add the names attached to the current function through direct assignment
    if hasattr(colitem, 'function'):
        for name in colitem.function.__dict__:
            mapped_names.add(name)

    mapping = KeywordMapping(mapped_names)
    if " " not in keywordexpr:
        # special case to allow for simple "-k pass" and "-k 1.3"
        return mapping[keywordexpr]
    elif keywordexpr.startswith("not ") and " " not in keywordexpr[4:]:
        return not mapping[keywordexpr[4:]]
    return eval(keywordexpr, {}, mapping)


def pytest_configure(config):
    import pytest
    if config.option.strict:
        pytest.mark._config = config


def _parsed_markers(config):
    for line in config.getini("markers"):
        beginning = line.split(":", 1)
        yield beginning[0].split("(", 1)[0]
