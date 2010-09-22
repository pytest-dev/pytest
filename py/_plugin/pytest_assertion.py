import py
import sys

def pytest_addoption(parser):
    group = parser.getgroup("debugconfig")
    group._addoption('--no-assert', action="store_true", default=False,
        dest="noassert",
        help="disable python assert expression reinterpretation."),

def pytest_configure(config):
    # The _pytesthook attribute on the AssertionError is used by
    # py._code._assertionnew to detect this plugin was loaded and in
    # turn call the hooks defined here as part of the
    # DebugInterpreter.
    if not config.getvalue("noassert") and not config.getvalue("nomagic"):
        warn_about_missing_assertion()
        config._oldassertion = py.builtin.builtins.AssertionError
        py.builtin.builtins.AssertionError = py.code._AssertionError
        py.builtin.builtins.AssertionError._pytesthook = config.hook

def pytest_unconfigure(config):
    if hasattr(config, '_oldassertion'):
        py.builtin.builtins.AssertionError = config._oldassertion
        del config._oldassertion

def warn_about_missing_assertion():
    try:
        assert False
    except AssertionError:
        pass
    else:
        py.std.warnings.warn("Assertions are turned off!"
                             " (are you using python -O?)")


# Provide basestring in python3
try:
    basestring = basestring
except NameError:
    basestring = str


def pytest_assert_binrepr(op, left, right):
    """Make specialised explanations for some operators/operands"""
    left_repr = py.io.saferepr(left, maxsize=30)
    right_repr = py.io.saferepr(right, maxsize=30)
    summary = '%s %s %s' % (left_repr, op, right_repr)

    issequence = lambda x: isinstance(x, (list, tuple))
    istext = lambda x: isinstance(x, basestring)
    isdict = lambda x: isinstance(x, dict)
    isset = lambda x: isinstance(x, set)

    explanation = None
    if op == '==':
        if istext(left) and istext(right):
            explanation = [line.strip('\n') for line in
                           py.std.difflib.ndiff(left.splitlines(),
                                                right.splitlines())]
        elif issequence(left) and issequence(right):
            explanation = _compare_eq_sequence(left, right)
        elif isset(left) and isset(right):
            explanation = _compare_eq_set(left, right)
        elif isdict(left) and isdict(right):
            explanation = _pprint_diff(left, right)
    elif op == 'in':
        # XXX
        pass

    if not explanation:
        return None

    # Don't include pageloads of data, should be configurable
    if len(''.join(explanation)) > 80*8:
        explanation = ['Detailed information too verbose, truncated']

    return [summary] + explanation


def _compare_eq_sequence(left, right):
    explanation = []
    for i in range(min(len(left), len(right))):
        if left[i] != right[i]:
            explanation += ['First differing item %s: %s != %s' %
                            (i, left[i], right[i])]
            break
    if len(left) > len(right):
        explanation += ['Left contains more items, '
                        'first extra item: %s' % left[len(right)]]
    elif len(left) < len(right):
        explanation += ['Right contains more items, '
                        'first extra item: %s' % right[len(right)]]
    return explanation + _pprint_diff(left, right)


def _pprint_diff(left, right):
    """Make explanation using pprint and difflib"""
    return [line.strip('\n') for line in
            py.std.difflib.ndiff(py.std.pprint.pformat(left).splitlines(),
                                 py.std.pprint.pformat(right).splitlines())]


def _compare_eq_set(left, right):
    explanation = []
    diff_left = left - right
    diff_right = right - left
    if diff_left:
        explanation.append('Extra items in the left set:')
        for item in diff_left:
            explanation.append(py.io.saferepr(item))
    if diff_right:
        explanation.append('Extra items in the right set:')
        for item in diff_right:
            explanation.append(py.io.saferepr(item))
    return explanation
