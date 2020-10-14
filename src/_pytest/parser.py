"""
Find a test class and/or test method in given source code line.

Original code by Pavel Savchenko
"""
import ast

class PytestParser(ast.NodeVisitor):
    """
    Given <source>, extract the top level class/function which contains given
    line number.

    Optional arguments:
        * <ignore_bases> list of class base names to be skipped

    """
    nested_class = None

    def __init__(self, source, ignore_bases=None):
        self.source = source
        self.ignore_bases = ignore_bases or []

    def find(self, line):
        self.nearest_class = None
        self.nearest_func = None
        self.nearest_ignored = None
        self.lineno = line
        tree = ast.parse(self.source)
        self.visit(tree)
        return [part.name for part in (self.nearest_class, self.nearest_func) if part]

    def should_stop(self, node):
        assert self.lineno, 'line number required'
        return node.lineno > self.lineno

    def ignore_class(self, node):
        if not hasattr(node, 'bases'):
            return False

        def should_ignore(base):
            if hasattr(base, 'id'):
                return base.id in self.ignore_bases
            elif hasattr(base, 'attr'):
                return base.attr in self.ignore_bases
            raise Exception('Unknown base node %s' % base)

        return any(should_ignore(base) for base in node.bases)

    def inside_class(self, node):
        """
        Test whether node is inside a class definition.
        Test ignores classes whose base is in self.ignore_bases.
        """
        return (
            # verify none of the bases are in ignored bases
            not self.ignore_class(node) and
            # check if currently already inside a class
            self.nearest_class and
            # compare col offset to check if we unindented
            node.col_offset > self.nearest_class.col_offset and
            # also make sure we're not currently in an ignored class
            not self.nearest_ignored
        )

    def first_argument_is_self(self, node):
        if not node.args.args:
            return False
        first_arg = node.args.args[0]
        arg_name = getattr(first_arg, 'arg', getattr(first_arg, 'id', None))
        return arg_name == 'self'

    def is_method(self, node):
        if not self.inside_class(node):
            return False
        if self.nested_class and node.col_offset > self.nested_class.col_offset:
            return False
        return self.first_argument_is_self(node)

    def visit_ClassDef(self, node):
        if self.should_stop(node):
            return
        elif self.inside_class(node):
            self.nested_class = node
            # ignore nested classes
            return self.generic_visit(node)

        self.nested_class = None

        if self.ignore_class(node):
            self.nearest_ignored = node
            self.nearest_class = None
        else:
            self.nearest_class = node   # set new class node
            self.nearest_ignored = None
        self.nearest_func = None        # reset method node
        return self.generic_visit(node)

    def visit_FunctionDef(self, node):
        if self.should_stop(node):
            return
        elif self.is_method(node):
            self.nearest_func = node  # set method
            self.nearest_ignored = None
        elif not self.inside_class(node) and not self.nearest_ignored:
            self.nearest_class = None
            self.nearest_func = node
        return self.generic_visit(node)