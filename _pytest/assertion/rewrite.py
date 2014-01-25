"""Rewrite assertion AST to produce nice error messages"""

import ast
import errno
import itertools
import imp
import marshal
import os
import re
import struct
import sys
import types

import py
from _pytest.assertion import util


# pytest caches rewritten pycs in __pycache__.
if hasattr(imp, "get_tag"):
    PYTEST_TAG = imp.get_tag() + "-PYTEST"
else:
    if hasattr(sys, "pypy_version_info"):
        impl = "pypy"
    elif sys.platform == "java":
        impl = "jython"
    else:
        impl = "cpython"
    ver = sys.version_info
    PYTEST_TAG = "%s-%s%s-PYTEST" % (impl, ver[0], ver[1])
    del ver, impl

PYC_EXT = ".py" + (__debug__ and "c" or "o")
PYC_TAIL = "." + PYTEST_TAG + PYC_EXT

REWRITE_NEWLINES = sys.version_info[:2] != (2, 7) and sys.version_info < (3, 2)
ASCII_IS_DEFAULT_ENCODING = sys.version_info[0] < 3

class AssertionRewritingHook(object):
    """PEP302 Import hook which rewrites asserts."""

    def __init__(self):
        self.session = None
        self.modules = {}
        self._register_with_pkg_resources()

    def set_session(self, session):
        self.fnpats = session.config.getini("python_files")
        self.session = session

    def find_module(self, name, path=None):
        if self.session is None:
            return None
        sess = self.session
        state = sess.config._assertstate
        state.trace("find_module called for: %s" % name)
        names = name.rsplit(".", 1)
        lastname = names[-1]
        pth = None
        if path is not None:
            # Starting with Python 3.3, path is a _NamespacePath(), which
            # causes problems if not converted to list.
            path = list(path)
            if len(path) == 1:
                pth = path[0]
        if pth is None:
            try:
                fd, fn, desc = imp.find_module(lastname, path)
            except ImportError:
                return None
            if fd is not None:
                fd.close()
            tp = desc[2]
            if tp == imp.PY_COMPILED:
                if hasattr(imp, "source_from_cache"):
                    fn = imp.source_from_cache(fn)
                else:
                    fn = fn[:-1]
            elif tp != imp.PY_SOURCE:
                # Don't know what this is.
                return None
        else:
            fn = os.path.join(pth, name.rpartition(".")[2] + ".py")
        fn_pypath = py.path.local(fn)
        # Is this a test file?
        if not sess.isinitpath(fn):
            # We have to be very careful here because imports in this code can
            # trigger a cycle.
            self.session = None
            try:
                for pat in self.fnpats:
                    if fn_pypath.fnmatch(pat):
                        state.trace("matched test file %r" % (fn,))
                        break
                else:
                    return None
            finally:
                self.session = sess
        else:
            state.trace("matched test file (was specified on cmdline): %r" %
                        (fn,))
        # The requested module looks like a test file, so rewrite it. This is
        # the most magical part of the process: load the source, rewrite the
        # asserts, and load the rewritten source. We also cache the rewritten
        # module code in a special pyc. We must be aware of the possibility of
        # concurrent pytest processes rewriting and loading pycs. To avoid
        # tricky race conditions, we maintain the following invariant: The
        # cached pyc is always a complete, valid pyc. Operations on it must be
        # atomic. POSIX's atomic rename comes in handy.
        write = not sys.dont_write_bytecode
        cache_dir = os.path.join(fn_pypath.dirname, "__pycache__")
        if write:
            try:
                os.mkdir(cache_dir)
            except OSError:
                e = sys.exc_info()[1].errno
                if e == errno.EEXIST:
                    # Either the __pycache__ directory already exists (the
                    # common case) or it's blocked by a non-dir node. In the
                    # latter case, we'll ignore it in _write_pyc.
                    pass
                elif e in [errno.ENOENT, errno.ENOTDIR]:
                    # One of the path components was not a directory, likely
                    # because we're in a zip file.
                    write = False
                elif e == errno.EACCES:
                    state.trace("read only directory: %r" % fn_pypath.dirname)
                    write = False
                else:
                    raise
        cache_name = fn_pypath.basename[:-3] + PYC_TAIL
        pyc = os.path.join(cache_dir, cache_name)
        # Notice that even if we're in a read-only directory, I'm going
        # to check for a cached pyc. This may not be optimal...
        co = _read_pyc(fn_pypath, pyc)
        if co is None:
            state.trace("rewriting %r" % (fn,))
            co = _rewrite_test(state, fn_pypath)
            if co is None:
                # Probably a SyntaxError in the test.
                return None
            if write:
                _make_rewritten_pyc(state, fn_pypath, pyc, co)
        else:
            state.trace("found cached rewritten pyc for %r" % (fn,))
        self.modules[name] = co, pyc
        return self

    def load_module(self, name):
        co, pyc = self.modules.pop(name)
        # I wish I could just call imp.load_compiled here, but __file__ has to
        # be set properly. In Python 3.2+, this all would be handled correctly
        # by load_compiled.
        mod = sys.modules[name] = imp.new_module(name)
        try:
            mod.__file__ = co.co_filename
            # Normally, this attribute is 3.2+.
            mod.__cached__ = pyc
            mod.__loader__ = self
            py.builtin.exec_(co, mod.__dict__)
        except:
            del sys.modules[name]
            raise
        return sys.modules[name]



    def is_package(self, name):
        try:
            fd, fn, desc = imp.find_module(name)
        except ImportError:
            return False
        if fd is not None:
            fd.close()
        tp = desc[2]
        return tp == imp.PKG_DIRECTORY

    @classmethod
    def _register_with_pkg_resources(cls):
        """
        Ensure package resources can be loaded from this loader. May be called
        multiple times, as the operation is idempotent.
        """
        try:
            import pkg_resources
            # access an attribute in case a deferred importer is present
            pkg_resources.__name__
        except ImportError:
            return

        # Since pytest tests are always located in the file system, the
        #  DefaultProvider is appropriate.
        pkg_resources.register_loader_type(cls, pkg_resources.DefaultProvider)


def _write_pyc(state, co, source_path, pyc):
    # Technically, we don't have to have the same pyc format as
    # (C)Python, since these "pycs" should never be seen by builtin
    # import. However, there's little reason deviate, and I hope
    # sometime to be able to use imp.load_compiled to load them. (See
    # the comment in load_module above.)
    mtime = int(source_path.mtime())
    try:
        fp = open(pyc, "wb")
    except IOError:
        err = sys.exc_info()[1].errno
        state.trace("error writing pyc file at %s: errno=%s" %(pyc, err))
        # we ignore any failure to write the cache file
        # there are many reasons, permission-denied, __pycache__ being a
        # file etc.
        return False
    try:
        fp.write(imp.get_magic())
        fp.write(struct.pack("<l", mtime))
        marshal.dump(co, fp)
    finally:
        fp.close()
    return True

RN = "\r\n".encode("utf-8")
N = "\n".encode("utf-8")

cookie_re = re.compile(r"^[ \t\f]*#.*coding[:=][ \t]*[-\w.]+")
BOM_UTF8 = '\xef\xbb\xbf'

def _rewrite_test(state, fn):
    """Try to read and rewrite *fn* and return the code object."""
    try:
        source = fn.read("rb")
    except EnvironmentError:
        return None
    if ASCII_IS_DEFAULT_ENCODING:
        # ASCII is the default encoding in Python 2. Without a coding
        # declaration, Python 2 will complain about any bytes in the file
        # outside the ASCII range. Sadly, this behavior does not extend to
        # compile() or ast.parse(), which prefer to interpret the bytes as
        # latin-1. (At least they properly handle explicit coding cookies.) To
        # preserve this error behavior, we could force ast.parse() to use ASCII
        # as the encoding by inserting a coding cookie. Unfortunately, that
        # messes up line numbers. Thus, we have to check ourselves if anything
        # is outside the ASCII range in the case no encoding is explicitly
        # declared. For more context, see issue #269. Yay for Python 3 which
        # gets this right.
        end1 = source.find("\n")
        end2 = source.find("\n", end1 + 1)
        if (not source.startswith(BOM_UTF8) and
            cookie_re.match(source[0:end1]) is None and
            cookie_re.match(source[end1 + 1:end2]) is None):
            if hasattr(state, "_indecode"):
                return None  # encodings imported us again, we don't rewrite
            state._indecode = True
            try:
                try:
                    source.decode("ascii")
                except UnicodeDecodeError:
                    # Let it fail in real import.
                    return None
            finally:
                del state._indecode
    # On Python versions which are not 2.7 and less than or equal to 3.1, the
    # parser expects *nix newlines.
    if REWRITE_NEWLINES:
        source = source.replace(RN, N) + N
    try:
        tree = ast.parse(source)
    except SyntaxError:
        # Let this pop up again in the real import.
        state.trace("failed to parse: %r" % (fn,))
        return None
    rewrite_asserts(tree)
    try:
        co = compile(tree, fn.strpath, "exec")
    except SyntaxError:
        # It's possible that this error is from some bug in the
        # assertion rewriting, but I don't know of a fast way to tell.
        state.trace("failed to compile: %r" % (fn,))
        return None
    return co

def _make_rewritten_pyc(state, fn, pyc, co):
    """Try to dump rewritten code to *pyc*."""
    if sys.platform.startswith("win"):
        # Windows grants exclusive access to open files and doesn't have atomic
        # rename, so just write into the final file.
        _write_pyc(state, co, fn, pyc)
    else:
        # When not on windows, assume rename is atomic. Dump the code object
        # into a file specific to this process and atomically replace it.
        proc_pyc = pyc + "." + str(os.getpid())
        if _write_pyc(state, co, fn, proc_pyc):
            os.rename(proc_pyc, pyc)

def _read_pyc(source, pyc):
    """Possibly read a pytest pyc containing rewritten code.

    Return rewritten code if successful or None if not.
    """
    try:
        fp = open(pyc, "rb")
    except IOError:
        return None
    try:
        try:
            mtime = int(source.mtime())
            data = fp.read(8)
        except EnvironmentError:
            return None
        # Check for invalid or out of date pyc file.
        if (len(data) != 8 or data[:4] != imp.get_magic() or
                struct.unpack("<l", data[4:])[0] != mtime):
            return None
        co = marshal.load(fp)
        if not isinstance(co, types.CodeType):
            # That's interesting....
            return None
        return co
    finally:
        fp.close()


def rewrite_asserts(mod):
    """Rewrite the assert statements in mod."""
    AssertionRewriter().run(mod)


_saferepr = py.io.saferepr
from _pytest.assertion.util import format_explanation as _format_explanation # noqa

def _should_repr_global_name(obj):
    return not hasattr(obj, "__name__") and not py.builtin.callable(obj)

def _format_boolop(explanations, is_or):
    return "(" + (is_or and " or " or " and ").join(explanations) + ")"

def _call_reprcompare(ops, results, expls, each_obj):
    for i, res, expl in zip(range(len(ops)), results, expls):
        try:
            done = not res
        except Exception:
            done = True
        if done:
            break
    if util._reprcompare is not None:
        custom = util._reprcompare(ops[i], each_obj[i], each_obj[i + 1])
        if custom is not None:
            return custom
    return expl


unary_map = {
    ast.Not: "not %s",
    ast.Invert: "~%s",
    ast.USub: "-%s",
    ast.UAdd: "+%s"
}

binop_map = {
    ast.BitOr: "|",
    ast.BitXor: "^",
    ast.BitAnd: "&",
    ast.LShift: "<<",
    ast.RShift: ">>",
    ast.Add: "+",
    ast.Sub: "-",
    ast.Mult: "*",
    ast.Div: "/",
    ast.FloorDiv: "//",
    ast.Mod: "%%", # escaped for string formatting
    ast.Eq: "==",
    ast.NotEq: "!=",
    ast.Lt: "<",
    ast.LtE: "<=",
    ast.Gt: ">",
    ast.GtE: ">=",
    ast.Pow: "**",
    ast.Is: "is",
    ast.IsNot: "is not",
    ast.In: "in",
    ast.NotIn: "not in"
}


def set_location(node, lineno, col_offset):
    """Set node location information recursively."""
    def _fix(node, lineno, col_offset):
        if "lineno" in node._attributes:
            node.lineno = lineno
        if "col_offset" in node._attributes:
            node.col_offset = col_offset
        for child in ast.iter_child_nodes(node):
            _fix(child, lineno, col_offset)
    _fix(node, lineno, col_offset)
    return node


class AssertionRewriter(ast.NodeVisitor):

    def run(self, mod):
        """Find all assert statements in *mod* and rewrite them."""
        if not mod.body:
            # Nothing to do.
            return
        # Insert some special imports at the top of the module but after any
        # docstrings and __future__ imports.
        aliases = [ast.alias(py.builtin.builtins.__name__, "@py_builtins"),
                   ast.alias("_pytest.assertion.rewrite", "@pytest_ar")]
        expect_docstring = True
        pos = 0
        lineno = 0
        for item in mod.body:
            if (expect_docstring and isinstance(item, ast.Expr) and
                    isinstance(item.value, ast.Str)):
                doc = item.value.s
                if "PYTEST_DONT_REWRITE" in doc:
                    # The module has disabled assertion rewriting.
                    return
                lineno += len(doc) - 1
                expect_docstring = False
            elif (not isinstance(item, ast.ImportFrom) or item.level > 0 or
                  item.module != "__future__"):
                lineno = item.lineno
                break
            pos += 1
        imports = [ast.Import([alias], lineno=lineno, col_offset=0)
                   for alias in aliases]
        mod.body[pos:pos] = imports
        # Collect asserts.
        nodes = [mod]
        while nodes:
            node = nodes.pop()
            for name, field in ast.iter_fields(node):
                if isinstance(field, list):
                    new = []
                    for i, child in enumerate(field):
                        if isinstance(child, ast.Assert):
                            # Transform assert.
                            new.extend(self.visit(child))
                        else:
                            new.append(child)
                            if isinstance(child, ast.AST):
                                nodes.append(child)
                    setattr(node, name, new)
                elif (isinstance(field, ast.AST) and
                      # Don't recurse into expressions as they can't contain
                      # asserts.
                      not isinstance(field, ast.expr)):
                    nodes.append(field)

    def variable(self):
        """Get a new variable."""
        # Use a character invalid in python identifiers to avoid clashing.
        name = "@py_assert" + str(next(self.variable_counter))
        self.variables.append(name)
        return name

    def assign(self, expr):
        """Give *expr* a name."""
        name = self.variable()
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
        format_dict = ast.Dict(keys, list(current.values()))
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
        self.cond_chain = ()
        self.variables = []
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
        err_name = ast.Name("AssertionError", ast.Load())
        exc = ast.Call(err_name, [fmt], [], None, None)
        if sys.version_info[0] >= 3:
            raise_ = ast.Raise(exc, None)
        else:
            raise_ = ast.Raise(exc, None, None)
        body.append(raise_)
        # Clear temporary variables by setting them to None.
        if self.variables:
            variables = [ast.Name(name, ast.Store())
                         for name in self.variables]
            clear = ast.Assign(variables, ast.Name("None", ast.Load()))
            self.statements.append(clear)
        # Fix line numbers.
        for stmt in self.statements:
            set_location(stmt, assert_.lineno, assert_.col_offset)
        return self.statements

    def visit_Name(self, name):
        # Display the repr of the name if it's a local variable or
        # _should_repr_global_name() thinks it's acceptable.
        locs = ast.Call(self.builtin("locals"), [], [], None, None)
        inlocs = ast.Compare(ast.Str(name.id), [ast.In()], [locs])
        dorepr = self.helper("should_repr_global_name", name)
        test = ast.BoolOp(ast.Or(), [inlocs, dorepr])
        expr = ast.IfExp(test, self.display(name), ast.Str(name.id))
        return name, self.explanation_param(expr)

    def visit_BoolOp(self, boolop):
        res_var = self.variable()
        expl_list = self.assign(ast.List([], ast.Load()))
        app = ast.Attribute(expl_list, "append", ast.Load())
        is_or = int(isinstance(boolop.op, ast.Or))
        body = save = self.statements
        fail_save = self.on_failure
        levels = len(boolop.values) - 1
        self.push_format_context()
        # Process each operand, short-circuting if needed.
        for i, v in enumerate(boolop.values):
            if i:
                fail_inner = []
                # cond is set in a prior loop iteration below
                self.on_failure.append(ast.If(cond, fail_inner, [])) # noqa
                self.on_failure = fail_inner
            self.push_format_context()
            res, expl = self.visit(v)
            body.append(ast.Assign([ast.Name(res_var, ast.Store())], res))
            expl_format = self.pop_format_context(ast.Str(expl))
            call = ast.Call(app, [expl_format], [], None, None)
            self.on_failure.append(ast.Expr(call))
            if i < levels:
                cond = res
                if is_or:
                    cond = ast.UnaryOp(ast.Not(), cond)
                inner = []
                self.statements.append(ast.If(cond, inner, []))
                self.statements = body = inner
        self.statements = save
        self.on_failure = fail_save
        expl_template = self.helper("format_boolop", expl_list, ast.Num(is_or))
        expl = self.pop_format_context(expl_template)
        return ast.Name(res_var, ast.Load()), self.explanation_param(expl)

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
            new_kwarg, expl = self.visit(call.kwargs)
            arg_expls.append("**" + expl)
        expl = "%s(%s)" % (func_expl, ', '.join(arg_expls))
        new_call = ast.Call(new_func, new_args, new_kwargs,
                            new_star, new_kwarg)
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
        res_variables = [self.variable() for i in range(len(comp.ops))]
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
        # Use pytest.assertion.util._reprcompare if that's available.
        expl_call = self.helper("call_reprcompare",
                                ast.Tuple(syms, ast.Load()),
                                ast.Tuple(load_names, ast.Load()),
                                ast.Tuple(expls, ast.Load()),
                                ast.Tuple(results, ast.Load()))
        if len(comp.ops) > 1:
            res = ast.BoolOp(ast.And(), load_names)
        else:
            res = load_names[0]
        return res, self.explanation_param(self.pop_format_context(expl_call))
