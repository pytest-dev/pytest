"""
Simple marshal format (based on pickle) designed to work across Python versions.
"""

import sys
import struct

import py

_INPY3 = _REALLY_PY3 = sys.version_info > (3, 0)

class SerializeError(Exception):
    pass

class SerializationError(SerializeError):
    """Error while serializing an object."""

class UnserializableType(SerializationError):
    """Can't serialize a type."""

class UnserializationError(SerializeError):
    """Error while unserializing an object."""

class VersionMismatch(UnserializationError):
    """Data from a previous or later format."""

class Corruption(UnserializationError):
    """The pickle format appears to have been corrupted."""

if _INPY3:
    def b(s):
        return s.encode("ascii")
    _b = b
    class _unicode(str):
        pass
    bytes = bytes
else:
    b = str
    _b = bytes
    _unicode = unicode

FOUR_BYTE_INT_MAX = 2147483647

_int4_format = struct.Struct("!i")

# Protocol constants
VERSION_NUMBER = 1
VERSION = b(chr(VERSION_NUMBER))
PY2STRING = b('s')
PY3STRING = b('t')
UNICODE = b('u')
BYTES = b('b')
NEWLIST = b('l')
BUILDTUPLE = b('T')
SETITEM = b('m')
NEWDICT = b('d')
INT = b('i')
STOP = b('S')

class CrossVersionOptions(object):
    pass

class Serializer(object):

    def __init__(self, stream):
        self.stream = stream

    def save(self, obj):
        self.stream.write(VERSION)
        self._save(obj)
        self.stream.write(STOP)

    def _save(self, obj):
        tp = type(obj)
        try:
            dispatch = self.dispatch[tp]
        except KeyError:
            raise UnserializableType("can't serialize %s" % (tp,))
        dispatch(self, obj)

    dispatch = {}

    def save_bytes(self, bytes_):
        self.stream.write(BYTES)
        self._write_byte_sequence(bytes_)
    dispatch[bytes] = save_bytes

    if _INPY3:
        def save_string(self, s):
            self.stream.write(PY3STRING)
            self._write_unicode_string(s)
    else:
        def save_string(self, s):
            self.stream.write(PY2STRING)
            self._write_byte_sequence(s)

        def save_unicode(self, s):
            self.stream.write(UNICODE)
            self._write_unicode_string(s)
        dispatch[unicode] = save_unicode
    dispatch[str] = save_string

    def _write_unicode_string(self, s):
        try:
            as_bytes = s.encode("utf-8")
        except UnicodeEncodeError:
            raise SerializationError("strings must be utf-8 encodable")
        self._write_byte_sequence(as_bytes)

    def _write_byte_sequence(self, bytes_):
        self._write_int4(len(bytes_), "string is too long")
        self.stream.write(bytes_)

    def save_int(self, i):
        self.stream.write(INT)
        self._write_int4(i)
    dispatch[int] = save_int

    def _write_int4(self, i, error="int must be less than %i" %
                    (FOUR_BYTE_INT_MAX,)):
        if i > FOUR_BYTE_INT_MAX:
            raise SerializationError(error)
        self.stream.write(_int4_format.pack(i))

    def save_list(self, L):
        self.stream.write(NEWLIST)
        self._write_int4(len(L), "list is too long")
        for i, item in enumerate(L):
            self._write_setitem(i, item)
    dispatch[list] = save_list

    def _write_setitem(self, key, value):
        self._save(key)
        self._save(value)
        self.stream.write(SETITEM)

    def save_dict(self, d):
        self.stream.write(NEWDICT)
        for key, value in d.items():
            self._write_setitem(key, value)
    dispatch[dict] = save_dict

    def save_tuple(self, tup):
        for item in tup:
            self._save(item)
        self.stream.write(BUILDTUPLE)
        self._write_int4(len(tup), "tuple is too long")
    dispatch[tuple] = save_tuple


class _UnserializationOptions(object):
    pass

class _Py2UnserializationOptions(_UnserializationOptions):

    def __init__(self, py3_strings_as_str=False):
        self.py3_strings_as_str = py3_strings_as_str

class _Py3UnserializationOptions(_UnserializationOptions):

    def __init__(self, py2_strings_as_str=False):
        self.py2_strings_as_str = py2_strings_as_str

if _INPY3:
    UnserializationOptions = _Py3UnserializationOptions
else:
    UnserializationOptions = _Py2UnserializationOptions

class _Stop(Exception):
    pass

class Unserializer(object):

    def __init__(self, stream, options=None):
        self.stream = stream
        if options is None:
            options = UnserializationOptions()
        self.options = options

    def load(self):
        self.stack = []
        version = ord(self.stream.read(1))
        if version != VERSION_NUMBER:
            raise VersionMismatch("%i != %i" % (version, VERSION_NUMBER))
        try:
            while True:
                opcode = self.stream.read(1)
                if not opcode:
                    raise EOFError
                try:
                    loader = self.opcodes[opcode]
                except KeyError:
                    raise Corruption("unkown opcode %s" % (opcode,))
                loader(self)
        except _Stop:
            if len(self.stack) != 1:
                raise UnserializationError("internal unserialization error")
            return self.stack[0]
        else:
            raise Corruption("didn't get STOP")

    opcodes = {}

    def load_int(self):
        i = self._read_int4()
        self.stack.append(i)
    opcodes[INT] = load_int

    def _read_int4(self):
        return _int4_format.unpack(self.stream.read(4))[0]

    def _read_byte_string(self):
        length = self._read_int4()
        as_bytes = self.stream.read(length)
        return as_bytes

    def load_py3string(self):
        as_bytes = self._read_byte_string()
        if not _INPY3 and self.options.py3_strings_as_str:
            # XXX Should we try to decode into latin-1?
            self.stack.append(as_bytes)
        else:
            self.stack.append(as_bytes.decode("utf-8"))
    opcodes[PY3STRING] = load_py3string

    def load_py2string(self):
        as_bytes = self._read_byte_string()
        if _INPY3 and self.options.py2_strings_as_str:
            s = as_bytes.decode("latin-1")
        else:
            s = as_bytes
        self.stack.append(s)
    opcodes[PY2STRING] = load_py2string

    def load_bytes(self):
        s = self._read_byte_string()
        self.stack.append(s)
    opcodes[BYTES] = load_bytes

    def load_unicode(self):
        self.stack.append(self._read_byte_string().decode("utf-8"))
    opcodes[UNICODE] = load_unicode

    def load_newlist(self):
        length = self._read_int4()
        self.stack.append([None] * length)
    opcodes[NEWLIST] = load_newlist

    def load_setitem(self):
        if len(self.stack) < 3:
            raise Corruption("not enough items for setitem")
        value = self.stack.pop()
        key = self.stack.pop()
        self.stack[-1][key] = value
    opcodes[SETITEM] = load_setitem

    def load_newdict(self):
        self.stack.append({})
    opcodes[NEWDICT] = load_newdict

    def load_buildtuple(self):
        length = self._read_int4()
        tup = tuple(self.stack[-length:])
        del self.stack[-length:]
        self.stack.append(tup)
    opcodes[BUILDTUPLE] = load_buildtuple

    def load_stop(self):
        raise _Stop
    opcodes[STOP] = load_stop
