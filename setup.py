import os, sys
import setuptools
import pkg_resources
from setuptools import setup, Command

classifiers = ['Development Status :: 6 - Mature',
               'Intended Audience :: Developers',
               'License :: OSI Approved :: MIT License',
               'Operating System :: POSIX',
               'Operating System :: Microsoft :: Windows',
               'Operating System :: MacOS :: MacOS X',
               'Topic :: Software Development :: Testing',
               'Topic :: Software Development :: Libraries',
               'Topic :: Utilities'] + [
              ('Programming Language :: Python :: %s' % x) for x in
                  '2 2.6 2.7 3 3.3 3.4 3.5 3.6'.split()]

with open('README.rst') as fd:
    long_description = fd.read()

def get_version():
    p = os.path.join(os.path.dirname(
                     os.path.abspath(__file__)), "_pytest", "__init__.py")
    with open(p) as f:
        for line in f.readlines():
            if "__version__" in line:
                return line.strip().split("=")[-1].strip(" '")
    raise ValueError("could not read version")


def has_environment_marker_support():
    """
    Tests that setuptools has support for PEP-426 environment marker support.

    The first known release to support it is 0.7 (and the earliest on PyPI seems to be 0.7.2
    so we're using that), see: http://pythonhosted.org/setuptools/history.html#id142

    References:

    * https://wheel.readthedocs.io/en/latest/index.html#defining-conditional-dependencies
    * https://www.python.org/dev/peps/pep-0426/#environment-markers
    """
    try:
        return pkg_resources.parse_version(setuptools.__version__) >= pkg_resources.parse_version('0.7.2')
    except Exception as exc:
        sys.stderr.write("Could not test setuptool's version: %s\n" % exc)
        return False


def main():
    install_requires = ['py>=1.4.29', 'setuptools']  # pluggy is vendored in _pytest.vendored_packages
    extras_require = {}
    if has_environment_marker_support():
        extras_require[':python_version=="2.6"'] = ['argparse']
        extras_require[':sys_platform=="win32"'] = ['colorama']
    else:
        if sys.version_info < (2, 7):
            install_requires.append('argparse')
        if sys.platform == 'win32':
            install_requires.append('colorama')

    setup(
        name='pytest',
        description='pytest: simple powerful testing with Python',
        long_description=long_description,
        version=get_version(),
        url='http://pytest.org',
        license='MIT license',
        platforms=['unix', 'linux', 'osx', 'cygwin', 'win32'],
        author='Holger Krekel, Bruno Oliveira, Ronny Pfannschmidt, Floris Bruynooghe, Brianna Laugher, Florian Bruhin and others',
        entry_points={'console_scripts':
                          ['pytest=pytest:main', 'py.test=pytest:main']},
        classifiers=classifiers,
        keywords="test unittest",
        cmdclass={'test': PyTest},
        # the following should be enabled for release
        install_requires=install_requires,
        extras_require=extras_require,
        packages=['_pytest', '_pytest.assertion', '_pytest._code', '_pytest.vendored_packages'],
        py_modules=['pytest'],
        zip_safe=False,
    )


class PyTest(Command):
    user_options = []
    def initialize_options(self):
        pass
    def finalize_options(self):
        pass
    def run(self):
        import subprocess
        PPATH = [x for x in os.environ.get('PYTHONPATH', '').split(':') if x]
        PPATH.insert(0, os.getcwd())
        os.environ['PYTHONPATH'] = ':'.join(PPATH)
        errno = subprocess.call([sys.executable, 'pytest.py', '--ignore=doc'])
        raise SystemExit(errno)


if __name__ == '__main__':
    main()
