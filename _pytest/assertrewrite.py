"""Rewrite assertion AST to produce nice error messages"""

import ast
import collections
import itertools

import py


def rewrite_asserts(mod):
    """Rewrite the assert statements in mod."""
    AssertionRewriter().run(mod)


_saferepr = py.io.saferepr
_format_explanation = py.code._format_explanation

def _format_boolop(operands, explanations, is_or):
    show_explanations = []
    for operand, expl in zip(operands, explanations):
        show_explanations.append(expl)
        if operand == is_or:
            break
    return "(" + (is_or and " or " or " and ").join(show_explanations) + ")"

def _call_reprcompare(ops, results, expls, each_obj):
    for i, res, expl in zip(range(len(ops)), results, expls):
        if not res:
            break
    if py.code._reprcompare is not None:
        custom = py.code._reprcompare(ops[i], each_obj[i], each_obj[i + 1])
        if custom is not None:
            return custom
    return expl


unary_map = {
    ast.Not : "not %s",
    ast.Invert : "~%s",
    ast.USub : "-%s",
    ast.UAdd : "+%s"
}

binop_map = {
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
    ast.Pow : "**",
    ast.Is : "is",
    ast.IsNot : "is not",
    ast.In : "in",
    ast.NotIn : "not in"
}


class AssertionRewriter(ast.NodeVisitor):

    def run(self, mod):
        """Find all assert statements in *mod* and rewrite them."""
        if not mod.body:
            # Nothing to do.
            return
        # Insert some special imports at top but after any docstrings.
        aliases = [ast.alias(py.builtin.builtins.__name__, "@py_builtins"),
                   ast.alias("py", "@pylib"),
                   ast.alias("_pytest.assertrewrite", "@pytest_ar")]
        imports = [ast.Import([alias], lineno=0, col_offset=0)
                   for alias in aliases]
        pos = 0
        if isinstance(mod.body[0], ast.Str):
            pos = 1
        mod.body[pos:pos] = imports
        # Collect asserts.
        asserts = []
        nodes = collections.deque([mod])
        while nodes:
            node = nodes.popleft()
            for name, field in ast.iter_fields(node):
                if isinstance(field, list):
                    for i, child in enumerate(field):
                        if isinstance(child, ast.Assert):
                            asserts.append((field, i, child))
                        elif isinstance(child, ast.AST):
                            nodes.append(child)
                elif (isinstance(field, ast.AST) and
                      # Don't recurse into expressions as they can't contain
                      # asserts.
                      not isinstance(field, ast.expr)):
                    nodes.append(field)
        # Transform asserts.
        for parent, pos, assert_ in asserts:
            parent[pos:pos + 1] = self.visit(assert_)

    def assign(self, expr):
        """Give *expr* a name."""
        # Use a character invalid in python identifiers to avoid clashing.
        name = "@py_assert" + str(next(self.variable_counter))
        self.variables.add(name)
        self.statements.append(ast.Assign([ast.Name(name, ast.Store())], expr))
        return ast.Name(name, ast.Load())

    def display(self, expr):
        """Call py.io.saferepr on the expression."""
        return self.helper("saferepr", expr)

    def helper(self, name, *args):
        """Call a helper in this module."""
        py_name = ast.Name("@pytest_ar", ast.Load())
        attr = ast.Attribute(py_name, "_" + name, ast.Load())
        return ast.Call(attr, list(args), [], None, None)

    def builtin(self, name):
        """Return the builtin called *name*."""
        builtin_name = ast.Name("@py_builtins", ast.Load())
        return ast.Attribute(builtin_name, name, ast.Load())

    def explanation_param(self, expr):
        specifier = "py" + str(next(self.variable_counter))
        self.explanation_specifiers[specifier] = expr
        return "%(" + specifier + ")s"

    def push_format_context(self):
        self.explanation_specifiers = {}
        self.stack.append(self.explanation_specifiers)

    def pop_format_context(self, expl_expr):
        current = self.stack.pop()
        if self.stack:
            self.explanation_specifiers = self.stack[-1]
        keys = [ast.Str(key) for key in current.keys()]
        format_dict = ast.Dict(keys, current.values())
        form = ast.BinOp(expl_expr, ast.Mod(), format_dict)
        name = "@py_format" + str(next(self.variable_counter))
        self.on_failure.append(ast.Assign([ast.Name(name, ast.Store())], form))
        return ast.Name(name, ast.Load())

    def generic_visit(self, node):
        """Handle expressions we don't have custom code for."""
        assert isinstance(node, ast.expr)
        res = self.assign(node)
        return res, self.explanation_param(self.display(res))

    def visit_Assert(self, assert_):
        if assert_.msg:
            # There's already a message. Don't mess with it.
            return [assert_]
        self.statements = []
        self.variables = set()
        self.variable_counter = itertools.count()
        self.stack = []
        self.on_failure = []
        self.push_format_context()
        # Rewrite assert into a bunch of statements.
        top_condition, explanation = self.visit(assert_.test)
        # Create failure message.
        body = self.on_failure
        negation = ast.UnaryOp(ast.Not(), top_condition)
        self.statements.append(ast.If(negation, body, []))
        explanation = "assert " + explanation
        template = ast.Str(explanation)
        msg = self.pop_format_context(template)
        fmt = self.helper("format_explanation", msg)
        body.append(ast.Assert(top_condition, fmt))
        # Delete temporary variables.
        names = [ast.Name(name, ast.Del()) for name in self.variables]
        if names:
            delete = ast.Delete(names)
            self.statements.append(delete)
        # Fix line numbers.
        for stmt in self.statements:
            stmt.lineno = assert_.lineno
            stmt.col_offset = assert_.col_offset
            ast.fix_missing_locations(stmt)
        return self.statements

    def visit_Name(self, name):
        # Check if the name is local or not.
        locs = ast.Call(self.builtin("locals"), [], [], None, None)
        globs = ast.Call(self.builtin("globals"), [], [], None, None)
        ops = [ast.In(), ast.IsNot()]
        test = ast.Compare(ast.Str(name.id), ops, [locs, globs])
        expr = ast.IfExp(test, self.display(name), ast.Str(name.id))
        return name, self.explanation_param(expr)

    def visit_BoolOp(self, boolop):
        operands = []
        explanations = []
        self.push_format_context()
        for operand in boolop.values:
            res, explanation = self.visit(operand)
            operands.append(res)
            explanations.append(explanation)
        expls = ast.Tuple([ast.Str(expl) for expl in explanations], ast.Load())
        is_or = ast.Num(isinstance(boolop.op, ast.Or))
        expl_template = self.helper("format_boolop",
                                    ast.Tuple(operands, ast.Load()), expls,
                                    is_or)
        expl = self.pop_format_context(expl_template)
        res = self.assign(ast.BoolOp(boolop.op, operands))
        return res, self.explanation_param(expl)

    def visit_UnaryOp(self, unary):
        pattern = unary_map[unary.op.__class__]
        operand_res, operand_expl = self.visit(unary.operand)
        res = self.assign(ast.UnaryOp(unary.op, operand_res))
        return res, pattern % (operand_expl,)

    def visit_BinOp(self, binop):
        symbol = binop_map[binop.op.__class__]
        left_expr, left_expl = self.visit(binop.left)
        right_expr, right_expl = self.visit(binop.right)
        explanation = "(%s %s %s)" % (left_expl, symbol, right_expl)
        res = self.assign(ast.BinOp(left_expr, binop.op, right_expr))
        return res, explanation

    def visit_Call(self, call):
        new_func, func_expl = self.visit(call.func)
        arg_expls = []
        new_args = []
        new_kwargs = []
        new_star = new_kwarg = None
        for arg in call.args:
            res, expl = self.visit(arg)
            new_args.append(res)
            arg_expls.append(expl)
        for keyword in call.keywords:
            res, expl = self.visit(keyword.value)
            new_kwargs.append(ast.keyword(keyword.arg, res))
            arg_expls.append(keyword.arg + "=" + expl)
        if call.starargs:
            new_star, expl = self.visit(call.starargs)
            arg_expls.append("*" + expl)
        if call.kwargs:
            new_kwarg, expl = self.visit(call.kwarg)
            arg_expls.append("**" + expl)
        expl = "%s(%s)" % (func_expl, ', '.join(arg_expls))
        new_call = ast.Call(new_func, new_args, new_kwargs, new_star, new_kwarg)
        res = self.assign(new_call)
        res_expl = self.explanation_param(self.display(res))
        outer_expl = "%s\n{%s = %s\n}" % (res_expl, res_expl, expl)
        return res, outer_expl

    def visit_Attribute(self, attr):
        if not isinstance(attr.ctx, ast.Load):
            return self.generic_visit(attr)
        value, value_expl = self.visit(attr.value)
        res = self.assign(ast.Attribute(value, attr.attr, ast.Load()))
        res_expl = self.explanation_param(self.display(res))
        pat = "%s\n{%s = %s.%s\n}"
        expl = pat % (res_expl, res_expl, value_expl, attr.attr)
        return res, expl

    def visit_Compare(self, comp):
        self.push_format_context()
        left_res, left_expl = self.visit(comp.left)
        res_variables = ["@py_assert" + str(next(self.variable_counter))
                         for i in range(len(comp.ops))]
        load_names = [ast.Name(v, ast.Load()) for v in res_variables]
        store_names = [ast.Name(v, ast.Store()) for v in res_variables]
        it = zip(range(len(comp.ops)), comp.ops, comp.comparators)
        expls = []
        syms = []
        results = [left_res]
        for i, op, next_operand in it:
            next_res, next_expl = self.visit(next_operand)
            results.append(next_res)
            sym = binop_map[op.__class__]
            syms.append(ast.Str(sym))
            expl = "%s %s %s" % (left_expl, sym, next_expl)
            expls.append(ast.Str(expl))
            res_expr = ast.Compare(left_res, [op], [next_res])
            self.statements.append(ast.Assign([store_names[i]], res_expr))
            left_res, left_expl = next_res, next_expl
        # Use py.code._reprcompare if that's available.
        expl_call = self.helper("call_reprcompare", ast.Tuple(syms, ast.Load()),
                                ast.Tuple(load_names, ast.Load()),
                                ast.Tuple(expls, ast.Load()),
                                ast.Tuple(results, ast.Load()))
        args = [ast.List(load_names, ast.Load())]
        res = ast.Call(self.builtin("all"), args, [], None, None)
        return res, self.explanation_param(self.pop_format_context(expl_call))
