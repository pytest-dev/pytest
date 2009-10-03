"""py lib / py.test setup.py file"""
import os, sys
from setuptools import setup
long_description = """

py.test and pylib: rapid testing and development utils

- `py.test`_: cross-project testing tool with many advanced features
- `py.path`_: path abstractions over local and subversion files
- `py.code`_: dynamic code compile and traceback printing support

Compatibility: Linux, Win32, OSX, Python versions 2.4 through to 3.1.
For questions please check out http://pylib.org/contact.html

.. _`py.test`: http://pylib.org/test.html
.. _`py.path`: http://pylib.org/path.html
.. _`py.code`: http://pylib.org/code.html

(c) Holger Krekel and others, 2009

"""
trunk = None
def main():
    setup(
        name='py',
        description='py.test and pylib: rapid testing and development utils.',
        long_description = long_description,
        version= trunk or '1.1.0b1',
        url='http://pylib.org',
        license='MIT license',
        platforms=['unix', 'linux', 'osx', 'cygwin', 'win32'],
        author='holger krekel, Guido Wesdorp, Carl Friedrich Bolz, Armin Rigo, Maciej Fijalkowski & others',
        author_email='holger at merlinux.eu',
        entry_points={'console_scripts': ['py.cleanup = py.cmdline:pycleanup',
                                          'py.convert_unittest = py.cmdline:pyconvert_unittest',
                                          'py.countloc = py.cmdline:pycountloc',
                                          'py.lookup = py.cmdline:pylookup',
                                          'py.rest = py.cmdline:pyrest',
                                          'py.svnwcrevert = py.cmdline:pysvnwcrevert',
                                          'py.test = py.cmdline:pytest',
                                          'py.which = py.cmdline:pywhich']},
        classifiers=['Development Status :: 4 - Beta',
                     'Intended Audience :: Developers',
                     'License :: OSI Approved :: MIT License',
                     'Operating System :: POSIX',
                     'Operating System :: Microsoft :: Windows',
                     'Operating System :: MacOS :: MacOS X',
                     'Topic :: Software Development :: Testing',
                     'Topic :: Software Development :: Libraries',
                     'Topic :: System :: Distributed Computing',
                     'Topic :: Utilities',
                     'Programming Language :: Python'],
        packages=['py',
                  '_py',
                  '_py.builtin',
                  '_py.cmdline',
                  '_py.code',
                  '_py.compat',
                  '_py.io',
                  '_py.log',
                  '_py.path',
                  '_py.path.gateway',
                  '_py.process',
                  '_py.rest',
                  '_py.test',
                  '_py.test.dist',
                  '_py.test.looponfail',
                  '_py.test.plugin',],
        package_data={'py': ['bin/_findpy.py',
                             'bin/env.cmd',
                             'bin/env.py',
                             'bin/py.cleanup',
                             'bin/py.convert_unittest',
                             'bin/py.countloc',
                             'bin/py.lookup',
                             'bin/py.rest',
                             'bin/py.svnwcrevert',
                             'bin/py.test',
                             'bin/py.which',
                             'bin/win32/py.cleanup.cmd',
                             'bin/win32/py.convert_unittest.cmd',
                             'bin/win32/py.countloc.cmd',
                             'bin/win32/py.lookup.cmd',
                             'bin/win32/py.rest.cmd',
                             'bin/win32/py.svnwcrevert.cmd',
                             'bin/win32/py.test.cmd',
                             'bin/win32/py.which.cmd',],
                        '_py': ['rest/rest.sty.template']},
        zip_safe=True,
    )

if __name__ == '__main__':
    main()

