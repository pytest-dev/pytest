
def pytest_addoption(parser):
    group = parser.getgroup("general")
    group._addoption('-k',
        action="store", dest="keyword", default='',
        help="only run test items matching the given "
             "space separated keywords.  precede a keyword with '-' to negate. "
             "Terminate the expression with ':' to treat a match as a signal "
             "to run all subsequent tests. ")

def pytest_collection_modifyitems(items, config):
    keywordexpr = config.option.keyword
    if not keywordexpr:
        return
    selectuntil = False
    if keywordexpr[-1] == ":":
        selectuntil = True
        keywordexpr = keywordexpr[:-1]

    remaining = []
    deselected = []
    for colitem in items:
        if keywordexpr and skipbykeyword(colitem, keywordexpr):
            deselected.append(colitem)
        else:
            remaining.append(colitem)
            if selectuntil:
                keywordexpr = None

    if deselected:
        config.hook.pytest_deselected(items=deselected)
        items[:] = remaining

def skipbykeyword(colitem, keywordexpr):
    """ return True if they given keyword expression means to
        skip this collector/item.
    """
    if not keywordexpr:
        return
    chain = colitem.listchain()
    for key in filter(None, keywordexpr.split()):
        eor = key[:1] == '-'
        if eor:
            key = key[1:]
        if not (eor ^ matchonekeyword(key, chain)):
            return True

def matchonekeyword(key, chain):
    elems = key.split(".")
    # XXX O(n^2), anyone cares?
    chain = [item.keywords for item in chain if item.keywords]
    for start, _ in enumerate(chain):
        if start + len(elems) > len(chain):
            return False
        for num, elem in enumerate(elems):
            for keyword in chain[num + start]:
                ok = False
                if elem in keyword:
                    ok = True
                    break
            if not ok:
                break
        if num == len(elems) - 1 and ok:
            return True
    return False
