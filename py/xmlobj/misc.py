import re
class _escape:
    def __init__(self):
        self.escape = {
            u'"' : u'&quot;', u'<' : u'&lt;', u'>' : u'&gt;', 
            u'&' : u'&amp;', u"'" : u'&apos;',
            }
        self.charef_rex = re.compile(u"|".join(self.escape.keys()))

    def _replacer(self, match):
        return self.escape[match.group(0)]

    def __call__(self, ustring):
        """ xml-escape the given unicode string. """
        return self.charef_rex.sub(self._replacer, ustring)

escape = _escape()
