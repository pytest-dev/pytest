from struct import pack, unpack, calcsize


def message(tp, *values):
    strtype = type('')
    typecodes = ['']
    for v in values:
        if type(v) is strtype:
            typecodes.append('%ds' % len(v))
        elif 0 <= v < 256:
            typecodes.append('B')
        else:
            typecodes.append('l')
    typecodes = ''.join(typecodes)
    assert len(typecodes) < 256
    return pack(("!B%dsc" % len(typecodes)) + typecodes,
                len(typecodes), typecodes, tp, *values)

def decodemessage(data):
    if data:
        limit = ord(data[0]) + 1
        if len(data) >= limit:
            typecodes = "!c" + data[1:limit]
            end = limit + calcsize(typecodes)
            if len(data) >= end:
                return unpack(typecodes, data[limit:end]), data[end:]
            #elif end > 1000000:
            #    raise OverflowError
    return None, data
