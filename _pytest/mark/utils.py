from .model import apply_mark


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


def transfer_markers(funcobj, cls, mod):
    # XXX this should rather be code in the mark plugin or the mark
    # plugin should merge with the python plugin.
    for holder in (cls, mod):
        try:
            pytestmark = holder.pytestmark
        except AttributeError:
            continue
        if isinstance(pytestmark, list):
            for mark in pytestmark:

                if not _marked(funcobj, mark):
                    apply_mark(mark=mark, obj=funcobj)
        else:
            if not _marked(funcobj, pytestmark):
                apply_mark(mark=pytestmark, obj=funcobj)
