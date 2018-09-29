
import os
import errno
import atexit
import operator
import six
from functools import reduce
import uuid
from six.moves import map
import itertools
import shutil

from .compat import PY36

if PY36:
    from pathlib import Path, PurePath
else:
    from pathlib2 import Path, PurePath

__all__ = ["Path", "PurePath"]


LOCK_TIMEOUT = 60 * 60 * 3

get_lock_path = operator.methodcaller("joinpath", ".lock")


def find_prefixed(root, prefix):
    l_prefix = prefix.lower()
    for x in root.iterdir():
        if x.name.lower().startswith(l_prefix):
            yield x


def extract_suffixes(iter, prefix):
    p_len = len(prefix)
    for p in iter:
        yield p.name[p_len:]


def find_suffixes(root, prefix):
    return extract_suffixes(find_prefixed(root, prefix), prefix)


def parse_num(maybe_num):
    try:
        return int(maybe_num)
    except ValueError:
        return -1


def _max(iterable, default):
    # needed due to python2.7 lacking the default argument for max
    return reduce(max, iterable, default)


def make_numbered_dir(root, prefix):
    for i in range(10):
        # try up to 10 times to create the folder
        max_existing = _max(map(parse_num, find_suffixes(root, prefix)), -1)
        new_number = max_existing + 1
        new_path = root.joinpath("{}{}".format(prefix, new_number))
        try:
            new_path.mkdir()
        except Exception:
            pass
        else:
            return new_path
    else:
        raise EnvironmentError(
            "could not create numbered dir with prefix {prefix} in {root})".format(
                prefix=prefix, root=root
            )
        )


def create_cleanup_lock(p):
    lock_path = get_lock_path(p)
    try:
        fd = os.open(str(lock_path), os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o644)
    except OSError as e:
        if e.errno == errno.EEXIST:
            six.raise_from(
                EnvironmentError("cannot create lockfile in {path}".format(path=p)), e
            )
        else:
            raise
    else:
        pid = os.getpid()
        spid = str(pid)
        if not isinstance(spid, six.binary_type):
            spid = spid.encode("ascii")
        os.write(fd, spid)
        os.close(fd)
        if not lock_path.is_file():
            raise EnvironmentError("lock path got renamed after sucessfull creation")
        return lock_path


def register_cleanup_lock_removal(lock_path, register=atexit.register):
    pid = os.getpid()

    def cleanup_on_exit(lock_path=lock_path, original_pid=pid):
        current_pid = os.getpid()
        if current_pid != original_pid:
            # fork
            return
        try:
            lock_path.unlink()
        except (OSError, IOError):
            pass

    return register(cleanup_on_exit)


def delete_a_numbered_dir(path):
    create_cleanup_lock(path)
    parent = path.parent

    garbage = parent.joinpath("garbage-{}".format(uuid.uuid4()))
    path.rename(garbage)
    shutil.rmtree(str(garbage), ignore_errors=True)


def ensure_deletable(path, consider_lock_dead_if_created_before):
    lock = get_lock_path(path)
    if not lock.exists():
        return True
    try:
        lock_time = lock.stat().st_mtime
    except Exception:
        return False
    else:
        if lock_time < consider_lock_dead_if_created_before:
            lock.unlink()
            return True
        else:
            return False


def try_cleanup(path, consider_lock_dead_if_created_before):
    if ensure_deletable(path, consider_lock_dead_if_created_before):
        delete_a_numbered_dir(path)


def cleanup_candidates(root, prefix, keep):
    max_existing = _max(map(parse_num, find_suffixes(root, prefix)), -1)
    max_delete = max_existing - keep
    paths = find_prefixed(root, prefix)
    paths, paths2 = itertools.tee(paths)
    numbers = map(parse_num, extract_suffixes(paths2, prefix))
    for path, number in zip(paths, numbers):
        if number <= max_delete:
            yield path


def cleanup_numbered_dir(root, prefix, keep, consider_lock_dead_if_created_before):
    for path in cleanup_candidates(root, prefix, keep):
        try_cleanup(path, consider_lock_dead_if_created_before)
    for path in root.glob("garbage-*"):
        try_cleanup(path, consider_lock_dead_if_created_before)


def make_numbered_dir_with_cleanup(root, prefix, keep, lock_timeout):
    e = None
    for i in range(10):
        try:
            p = make_numbered_dir(root, prefix)
            lock_path = create_cleanup_lock(p)
            register_cleanup_lock_removal(lock_path)
        except Exception as e:
            pass
        else:
            consider_lock_dead_if_created_before = p.stat().st_mtime - lock_timeout
            cleanup_numbered_dir(
                root=root,
                prefix=prefix,
                keep=keep,
                consider_lock_dead_if_created_before=consider_lock_dead_if_created_before,
            )
            return p
    assert e is not None
    raise e
