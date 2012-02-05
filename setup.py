import os, sys
try:
    from setuptools import setup
except ImportError:
    from distribute_setup import use_setuptools
    use_setuptools()
    from setuptools import setup

long_description = """
cross-project testing tool for Python.

Platforms: Linux, Win32, OSX

Interpreters: Python versions 2.4 through to 3.2, Jython 2.5.1 and PyPy-1.6/1.7

Bugs and issues: http://bitbucket.org/hpk42/pytest/issues/

Web page: http://pytest.org

(c) Holger Krekel and others, 2004-2012
"""
def main():
    setup(
        name='pytest',
        description='py.test: simple powerful testing with Python',
        long_description = long_description,
        version='2.2.2',
        url='http://pytest.org',
        license='MIT license',
        platforms=['unix', 'linux', 'osx', 'cygwin', 'win32'],
        author='Holger Krekel, Benjamin Peterson, Ronny Pfannschmidt, Floris Bruynooghe and others',
        author_email='holger at merlinux.eu',
        entry_points= make_entry_points(),
        # the following should be enabled for release
        install_requires=['py>=1.4.7.dev2'],
        classifiers=['Development Status :: 6 - Mature',
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
        packages=['_pytest', '_pytest.assertion'],
        py_modules=['pytest'],
        zip_safe=False,
    )

def cmdline_entrypoints(versioninfo, platform, basename):
    target = 'pytest:main'
    if platform.startswith('java'):
        points = {'py.test-jython': target}
    else:
        if basename.startswith("pypy"):
            points = {'py.test-%s' % basename: target}
        else: # cpython
            points = {'py.test-%s.%s' % versioninfo[:2] : target,}
        points['py.test'] = target
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