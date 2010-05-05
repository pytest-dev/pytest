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
Interpreters: Python versions 2.4 through to 3.2, Jython 2.5.1 and PyPy
For questions please check out http://pylib.org/contact.html

.. _`py.test`: http://pytest.org
.. _`py.path`: http://pylib.org/path.html
.. _`py.code`: http://pylib.org/code.html

(c) Holger Krekel and others, 2004-2010
"""
def main():
    setup(
        name='py',
        description='py.test and pylib: rapid testing and development utils.',
        long_description = long_description,
        version= '1.3.0',
        url='http://pylib.org',
        license='MIT license',
        platforms=['unix', 'linux', 'osx', 'cygwin', 'win32'],
        author='holger krekel, Guido Wesdorp, Carl Friedrich Bolz, Armin Rigo, Maciej Fijalkowski & others',
        author_email='holger at merlinux.eu',
        entry_points= make_entry_points(),
        classifiers=['Development Status :: 5 - Production/Stable',
                     'Intended Audience :: Developers',
                     'License :: OSI Approved :: MIT License',
                     'Operating System :: POSIX',
                     'Operating System :: Microsoft :: Windows',
                     'Operating System :: MacOS :: MacOS X',
                     'Topic :: Software Development :: Testing',
                     'Topic :: Software Development :: Libraries',
                     'Topic :: Utilities',
                     'Programming Language :: Python',
                     'Programming Language :: Python :: 3'],
        packages=['py',
                  'py._plugin',
                  'py._cmdline',
                  'py._code',
                  'py._compat',
                  'py._io',
                  'py._log',
                  'py._path',
                  'py._process',
                  'py._test',
        ],
        zip_safe=False,
    )

def cmdline_entrypoints(versioninfo, platform, basename):
    if platform.startswith('java'):
        points = {'py.test-jython': 'py.cmdline:pytest', 
                  'py.which-jython': 'py.cmdline:pywhich'}
    else:
        if basename.startswith("pypy"):
            points = {'py.test-%s' % basename: 'py.cmdline:pytest', 
                      'py.which-%s' % basename: 'py.cmdline:pywhich',}
        else: # cpython
            points = {
              'py.test-%s.%s' % versioninfo[:2] : 'py.cmdline:pytest',
              'py.which-%s.%s' % versioninfo[:2] : 'py.cmdline:pywhich'
            }
        for x in ['py.cleanup', 'py.convert_unittest', 'py.countloc', 
                  'py.lookup', 'py.svnwcrevert', 'py.which', 'py.test']:
            points[x] = "py.cmdline:%s" % x.replace('.','')
    return points

def make_entry_points():
    basename = os.path.basename(sys.executable)
    points = cmdline_entrypoints(sys.version_info, sys.platform, basename)
    keys = list(points.keys())
    keys.sort()
    l = ["%s = %s" % (x, points[x]) for x in keys]
    return {'console_scripts': l}

if __name__ == '__main__':
    main()

