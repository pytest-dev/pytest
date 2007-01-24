import py

from py.__.initpkg import initpkg

initpkg(__name__,
        description="test package",
        exportdefs = {
         'pak.mod.one': ('./pak/mod.py', 'one'),
         'pak.mod.two': ('./pak/mod.py', 'nottwo'),
         'notpak.notmod.notclass': ('./pak/mod.py', 'cls'),
         'somenamespace': ('./pak/somenamespace.py', '*'),
        })

