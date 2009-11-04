"""py lib / py.test setup.py file"""
import os, sys
if sys.version_info >= (3,0):
    from distribute_setup import use_setuptools
    use_setuptools()
from setuptools import setup

long_description = """
py.test and pylib: rapid testing and development utils

- `py.test`_: cross-project testing tool with many advanced features
- `py.path`_: path abstractions over local and subversion files
- `py.code`_: dynamic code compile and traceback printing support

Platforms: Linux, Win32, OSX
Interpreters: Python versions 2.4 through to 3.1, Jython 2.5.1. 
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
        entry_points={'console_scripts': [
            'py.cleanup = py.cmdline:pycleanup',
            'py.convert_unittest = py.cmdline:pyconvert_unittest',
            'py.countloc = py.cmdline:pycountloc',
            'py.lookup = py.cmdline:pylookup',
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
                  'py.plugin',
                  'py.impl',
                  'py.impl.cmdline',
                  'py.impl.code',
                  'py.impl.compat',
                  'py.impl.io',
                  'py.impl.log',
                  'py.impl.path',
                  'py.impl.process',
                  'py.impl.test',
                  'py.impl.test.dist',
                  'py.impl.test.looponfail',
        ],
        zip_safe=False,
    )

if __name__ == '__main__':
    main()

