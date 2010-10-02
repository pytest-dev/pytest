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
        config._oldbinrepr = py.code._reprcompare
        py.builtin.builtins.AssertionError = py.code._AssertionError
        def callbinrepr(op, left, right):
            hook_result = config.hook.pytest_assertrepr_compare(
                config=config, op=op, left=left, right=right)
            for new_expl in hook_result:
                if new_expl:
                    return '\n~'.join(new_expl)
        py.code._reprcompare = callbinrepr

def pytest_unconfigure(config):
    if hasattr(config, '_oldassertion'):
        py.builtin.builtins.AssertionError = config._oldassertion
        py.code._reprcompare = config._oldbinrepr
        del config._oldassertion
        del config._oldbinrepr

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


def pytest_assertrepr_compare(op, left, right):
    """return specialised explanations for some operators/operands"""
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
            explanation = _diff_text(left, right)
        elif issequence(left) and issequence(right):
            explanation = _compare_eq_sequence(left, right)
        elif isset(left) and isset(right):
            explanation = _compare_eq_set(left, right)
        elif isdict(left) and isdict(right):
            explanation = _diff_text(py.std.pprint.pformat(left),
                                     py.std.pprint.pformat(right))
    elif op == 'in':
        pass                    # XXX

    if not explanation:
        return None

    # Don't include pageloads of data, should be configurable
    if len(''.join(explanation)) > 80*8:
        explanation = ['Detailed information too verbose, truncated']

    return [summary] + explanation


def _diff_text(left, right):
    """Return the explanation for the diff between text

    This will skip leading and trailing characters which are
    identical to keep the diff minimal.
    """
    explanation = []
    for i in range(min(len(left), len(right))):
        if left[i] != right[i]:
            break
    if i > 42:
        i -= 10                 # Provide some context
        explanation = ['Skipping %s identical '
                       'leading characters in diff' % i]
        left = left[i:]
        right = right[i:]
    if len(left) == len(right):
        for i in range(len(left)):
            if left[-i] != right[-i]:
                break
        if i > 42:
            i -= 10     # Provide some context
            explanation += ['Skipping %s identical '
                            'trailing characters in diff' % i]
            left = left[:-i]
            right = right[:-i]
    explanation += [line.strip('\n')
                    for line in py.std.difflib.ndiff(left.splitlines(),
                                                     right.splitlines())]
    return explanation


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
                        'first extra item: %s' % right[len(left)]]
    return explanation + _diff_text(py.std.pprint.pformat(left),
                                    py.std.pprint.pformat(right))


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
