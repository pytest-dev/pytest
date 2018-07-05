from .compat import Path
from os.path import expanduser, expandvars, isabs


def resolve_from_str(input, root):
    assert not isinstance(input, Path), "would break on py2"
    root = Path(root)
    input = expanduser(input)
    input = expandvars(input)
    if isabs(input):
        return Path(input)
    else:
        return root.joinpath(input)
