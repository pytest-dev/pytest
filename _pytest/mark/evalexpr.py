import sys
import traceback
import pytest
import os
import py


def cached_eval(config, expr, d):
    if not hasattr(config, '_evalcache'):
        config._evalcache = {}
    try:
        return config._evalcache[expr]
    except KeyError:
        import _pytest._code
        exprcode = _pytest._code.compile(expr, mode="eval")
        config._evalcache[expr] = x = eval(exprcode, d)
        return x


class MarkEvaluator:
    def __init__(self, item, name):
        self.item = item
        self.name = name

    @property
    def holder(self):
        return self.item.keywords.get(self.name)

    def __bool__(self):
        return bool(self.holder)

    __nonzero__ = __bool__

    def wasvalid(self):
        return not hasattr(self, 'exc')

    def invalidraise(self, exc):
        raises = self.get('raises')
        if not raises:
            return
        return not isinstance(exc, raises)

    def istrue(self):
        try:
            return self._istrue()
        except Exception:
            self.exc = sys.exc_info()
            if isinstance(self.exc[1], SyntaxError):
                msg = [" " * (self.exc[1].offset + 4) + "^", ]
                msg.append("SyntaxError: invalid syntax")
            else:
                msg = traceback.format_exception_only(*self.exc[:2])
            pytest.fail("Error evaluating %r expression\n"
                        "    %s\n"
                        "%s" % (self.name, self.expr, "\n".join(msg)),
                        pytrace=False)

    def _getglobals(self):
        d = {'os': os, 'sys': sys, 'config': self.item.config}
        d.update(self.item.obj.__globals__)
        return d

    def _istrue(self):
        if hasattr(self, 'result'):
            return self.result
        if self.holder:
            d = self._getglobals()
            if self.holder.args:
                self.result = False
                # "holder" might be a MarkInfo or a MarkDecorator; only
                # MarkInfo keeps track of all parameters it received
                try:
                    marklist = list(self.holder)
                except:
                    marklist = [self.holder.mark]
                for mark in marklist:
                    for expr in mark.args:
                        self.expr = expr
                        if isinstance(expr, py.builtin._basestring):
                            result = cached_eval(self.item.config, expr, d)
                        else:
                            if "reason" not in mark.kwargs:
                                # XXX better be checked at collection time
                                msg = "you need to specify reason=STRING " \
                                      "when using booleans as conditions."
                                pytest.fail(msg)
                            result = bool(expr)
                        if result:
                            self.result = True
                            self.reason = mark.kwargs.get('reason', None)
                            self.expr = expr
                            return self.result
            else:
                self.result = True
        return getattr(self, 'result', False)

    def get(self, attr, default=None):
        return self.holder.kwargs.get(attr, default)

    def getexplanation(self):
        expl = getattr(self, 'reason', None) or self.get('reason', None)
        if not expl:
            if not hasattr(self, 'expr'):
                return ""
            else:
                return "condition: " + str(self.expr)
        return expl
