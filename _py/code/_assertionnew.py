"""
Like _assertion.py but using builtin AST.  It should replace _assertion.py
eventually.
"""

import sys
import ast

import py
from _py.code.assertion import _format_explanation, BuiltinAssertionError


if sys.platform.startswith("java") and sys.version_info < (2, 5, 2):
    # See http://bugs.jython.org/issue1497
    _exprs = ("BoolOp", "BinOp", "UnaryOp", "Lambda", "IfExp", "Dict",
              "ListComp", "GeneratorExp", "Yield", "Compare", "Call",
              "Repr", "Num", "Str", "Attribute", "Subscript", "Name",
              "List", "Tuple")
    _stmts = ("FunctionDef", "ClassDef", "Return", "Delete", "Assign",
              "AugAssign", "Print", "For", "While", "If", "With", "Raise",
              "TryExcept", "TryFinally", "Assert", "Import", "ImportFrom",
              "Exec", "Global", "Expr", "Pass", "Break", "Continue")
    _expr_nodes = set(getattr(ast, name) for name in _exprs)
    _stmt_nodes = set(getattr(ast, name) for name in _stmts)
    def _is_ast_expr(node):
        return node.__class__ in _expr_nodes
    def _is_ast_stmt(node):
        return node.__class__ in _stmt_nodes
else:
    def _is_ast_expr(node):
        return isinstance(node, ast.expr)
    def _is_ast_stmt(node):
        return isinstance(node, ast.stmt)


class Failure(Exception):
    """Error found while interpreting AST."""

    def __init__(self, explanation=""):
        self.cause = sys.exc_info()
        self.explanation = explanation


def interpret(source, frame, should_fail=False):
    mod = ast.parse(source)
    visitor = DebugInterpreter(frame)
    try:
        visitor.visit(mod)
    except Failure:
        failure = sys.exc_info()[1]
        return getfailure(failure)
    if should_fail:
        return ("(assertion failed, but when it was re-run for "
                "printing intermediate values, it did not fail.  Suggestions: "
                "compute assert expression before the assert or use --nomagic)")

def run(offending_line, frame=None):
    if frame is None:
        frame = py.code.Frame(sys._getframe(1))
    return interpret(offending_line, frame)

def getfailure(failure):
    explanation = _format_explanation(failure.explanation)
    value = failure.cause[1]
    if str(value):
        lines = explanation.splitlines()
        if not lines:
            lines.append("")
        lines[0] += " << {0}".format(value)
        explanation = "\n".join(lines)
    text = "{0}: {1}".format(failure.cause[0].__name__, explanation)
    if text.startswith("AssertionError: assert "):
        text = text[16:]
    return text


operator_map = {
    ast.BitOr : "|",
    ast.BitXor : "^",
    ast.BitAnd : "&",
    ast.LShift : "<<",
    ast.RShift : ">>",
    ast.Add : "+",
    ast.Sub : "-",
    ast.Mult : "*",
    ast.Div : "/",
    ast.FloorDiv : "//",
    ast.Mod : "%",
    ast.Eq : "==",
    ast.NotEq : "!=",
    ast.Lt : "<",
    ast.LtE : "<=",
    ast.Gt : ">",
    ast.GtE : ">=",
    ast.Is : "is",
    ast.IsNot : "is not",
    ast.In : "in",
    ast.NotIn : "not in"
}

unary_map = {
    ast.Not : "not {0}",
    ast.Invert : "~{0}",
    ast.USub : "-{0}",
    ast.UAdd : "+{0}"
}


class DebugInterpreter(ast.NodeVisitor):
    """Interpret AST nodes to gleam useful debugging information."""

    def __init__(self, frame):
        self.frame = frame

    def generic_visit(self, node):
        # Fallback when we don't have a special implementation.
        if _is_ast_expr(node):
            mod = ast.Expression(node)
            co = self._compile(mod)
            try:
                result = self.frame.eval(co)
            except Exception:
                raise Failure()
            explanation = self.frame.repr(result)
            return explanation, result
        elif _is_ast_stmt(node):
            mod = ast.Module([node])
            co = self._compile(mod, "exec")
            try:
                self.frame.exec_(co)
            except Exception:
                raise Failure()
            return None, None
        else:
            raise AssertionError("can't handle %s" %(node,))

    def _compile(self, source, mode="eval"):
        return compile(source, "<assertion interpretation>", mode)

    def visit_Expr(self, expr):
        return self.visit(expr.value)

    def visit_Module(self, mod):
        for stmt in mod.body:
            self.visit(stmt)

    def visit_Name(self, name):
        explanation, result = self.generic_visit(name)
        # See if the name is local.
        source = "{0!r} in locals() is not globals()".format(name.id)
        co = self._compile(source)
        try:
            local = self.frame.eval(co)
        except Exception:
            # have to assume it isn't
            local = False
        if not local:
            return name.id, result
        return explanation, result

    def visit_Compare(self, comp):
        left = comp.left
        left_explanation, left_result = self.visit(left)
        got_result = False
        for op, next_op in zip(comp.ops, comp.comparators):
            if got_result and not result:
                break
            next_explanation, next_result = self.visit(next_op)
            op_symbol = operator_map[op.__class__]
            explanation = "{0} {1} {2}".format(left_explanation, op_symbol,
                                               next_explanation)
            source = "__exprinfo_left {0} __exprinfo_right".format(op_symbol)
            co = self._compile(source)
            try:
                result = self.frame.eval(co, __exprinfo_left=left_result,
                                         __exprinfo_right=next_result)
            except Exception:
                raise Failure(explanation)
            else:
                got_result = True
            left_explanation, left_result = next_explanation, next_result
        return explanation, result

    def visit_BoolOp(self, boolop):
        is_or = isinstance(boolop.op, ast.Or)
        explanations = []
        for operand in boolop.values:
            explanation, result = self.visit(operand)
            explanations.append(explanation)
            if result == is_or:
                break
        name = is_or and " or " or " and "
        explanation = "(" + name.join(explanations) + ")"
        return explanation, result

    def visit_UnaryOp(self, unary):
        pattern = unary_map[unary.op.__class__]
        operand_explanation, operand_result = self.visit(unary.operand)
        explanation = pattern.format(operand_explanation)
        co = self._compile(pattern.format("__exprinfo_expr"))
        try:
            result = self.frame.eval(co, __exprinfo_expr=operand_result)
        except Exception:
            raise Failure(explanation)
        return explanation, result

    def visit_BinOp(self, binop):
        left_explanation, left_result = self.visit(binop.left)
        right_explanation, right_result = self.visit(binop.right)
        symbol = operator_map[binop.op.__class__]
        explanation = "({0} {1} {2})".format(left_explanation, symbol,
                                             right_explanation)
        source = "__exprinfo_left {0} __exprinfo_right".format(symbol)
        co = self._compile(source)
        try:
            result = self.frame.eval(co, __exprinfo_left=left_result,
                                     __exprinfo_right=right_result)
        except Exception:
            raise Failure(explanation)
        return explanation, result

    def visit_Call(self, call):
        func_explanation, func = self.visit(call.func)
        arg_explanations = []
        ns = {"__exprinfo_func" : func}
        arguments = []
        for arg in call.args:
            arg_explanation, arg_result = self.visit(arg)
            arg_name = "__exprinfo_{0}".format(len(ns))
            ns[arg_name] = arg_result
            arguments.append(arg_name)
            arg_explanations.append(arg_explanation)
        for keyword in call.keywords:
            arg_explanation, arg_result = self.visit(keyword.value)
            arg_name = "__exprinfo_{0}".format(len(ns))
            ns[arg_name] = arg_result
            keyword_source = "{0}={{0}}".format(keyword.id)
            arguments.append(keyword_source.format(arg_name))
            arg_explanations.append(keyword_source.format(arg_explanation))
        if call.starargs:
            arg_explanation, arg_result = self.visit(call.starargs)
            arg_name = "__exprinfo_star"
            ns[arg_name] = arg_result
            arguments.append("*{0}".format(arg_name))
            arg_explanations.append("*{0}".format(arg_explanation))
        if call.kwargs:
            arg_explanation, arg_result = self.visit(call.kwargs)
            arg_name = "__exprinfo_kwds"
            ns[arg_name] = arg_result
            arguments.append("**{0}".format(arg_name))
            arg_explanations.append("**{0}".format(arg_explanation))
        args_explained = ", ".join(arg_explanations)
        explanation = "{0}({1})".format(func_explanation, args_explained)
        args = ", ".join(arguments)
        source = "__exprinfo_func({0})".format(args)
        co = self._compile(source)
        try:
            result = self.frame.eval(co, **ns)
        except Exception:
            raise Failure(explanation)
        # Only show result explanation if it's not a builtin call or returns a
        # bool.
        if not isinstance(call.func, ast.Name) or \
                not self._is_builtin_name(call.func):
            source = "isinstance(__exprinfo_value, bool)"
            co = self._compile(source)
            try:
                is_bool = self.frame.eval(co, __exprinfo_value=result)
            except Exception:
                is_bool = False
            if not is_bool:
                pattern = "{0}\n{{{0} = {1}\n}}"
                rep = self.frame.repr(result)
                explanation = pattern.format(rep, explanation)
        return explanation, result

    def _is_builtin_name(self, name):
        pattern = "{0!r} not in globals() and {0!r} not in locals()"
        source = pattern.format(name.id)
        co = self._compile(source)
        try:
            return self.frame.eval(co)
        except Exception:
            return False

    def visit_Attribute(self, attr):
        if not isinstance(attr.ctx, ast.Load):
            return self.generic_visit(attr)
        source_explanation, source_result = self.visit(attr.value)
        explanation = "{0}.{1}".format(source_explanation, attr.attr)
        source = "__exprinfo_expr.{0}".format(attr.attr)
        co = self._compile(source)
        try:
            result = self.frame.eval(co, __exprinfo_expr=source_result)
        except Exception:
            raise Failure(explanation)
        # Check if the attr is from an instance.
        source = "{0!r} in getattr(__exprinfo_expr, '__dict__', {{}})"
        source = source.format(attr.attr)
        co = self._compile(source)
        try:
            from_instance = self.frame.eval(co, __exprinfo_expr=source_result)
        except Exception:
            from_instance = True
        if from_instance:
            rep = self.frame.repr(result)
            pattern = "{0}\n{{{0} = {1}\n}}"
            explanation = pattern.format(rep, explanation)
        return explanation, result

    def visit_Assert(self, assrt):
        test_explanation, test_result = self.visit(assrt.test)
        if test_explanation.startswith("False\n{False =") and \
                test_explanation.endswith("\n"):
            test_explanation = test_explanation[15:-2]
        explanation = "assert {0}".format(test_explanation)
        if not test_result:
            try:
                raise BuiltinAssertionError
            except Exception:
                raise Failure(explanation)
        return explanation, test_result

    def visit_Assign(self, assign):
        value_explanation, value_result = self.visit(assign.value)
        explanation = "... = {0}".format(value_explanation)
        name = ast.Name("__exprinfo_expr", ast.Load(), assign.value.lineno,
                        assign.value.col_offset)
        new_assign = ast.Assign(assign.targets, name, assign.lineno,
                                assign.col_offset)
        mod = ast.Module([new_assign])
        co = self._compile(mod, "exec")
        try:
            self.frame.exec_(co, __exprinfo_expr=value_result)
        except Exception:
            raise Failure(explanation)
        return explanation, value_result
