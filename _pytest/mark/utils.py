from .model import apply_mark, MarkDecorator


def _marked(func, mark):
    """ Returns True if :func: is already marked with :mark:, False otherwise.
    This can happen if marker is applied to class and the test file is
    invoked more than once.
    """
    try:
        func_mark = getattr(func, mark.name)
    except AttributeError:
        return False
    return mark.args == func_mark.args and mark.kwargs == func_mark.kwargs


def get_marks(obj):
    try:
        maybe_mark = obj.pytestmark
    except AttributeError:
        return []
    else:
        if isinstance(maybe_mark, list):
            return maybe_mark
        elif isinstance(maybe_mark, MarkDecorator):
            return [maybe_mark.mark]
        else:
            raise TypeError('%r is not a mark' % (maybe_mark,))


def transfer_markers(funcobj, cls, mod):
    for holder in (cls, mod):
        for mark in get_marks(holder):
            if not _marked(funcobj, mark):
                apply_mark(mark=mark, obj=funcobj)
