

if __name__ == "__main__":
    import os
    import sys
    import glob
    from setuptools import setup, Extension

    cython_directives = {
        'embedsignature': True,  # needed to embed docstrings in ext module
        }

    try:
        sys.argv.remove("--use-cython")
        use_cython = True
    except ValueError:
        use_cython = False

    if use_cython:
        ext_files = glob.glob('src/*.pyx')
        ext_files.append('src/pure_py_module.py')
    else:
        ext_files = glob.glob('src/*.c')

    extensions = []
    for file_ in ext_files:
        filename, ext = os.path.splitext(file_)
        extensions.append(Extension(filename, [file_],
                                    include_dirs=[os.path.abspath('clib')]))

    if use_cython:
        from Cython.Build import cythonize
        from Cython.Distutils import build_ext
        extensions = cythonize(extensions, force=True,
                               compiler_directives=cython_directives)
    else:
        from distutils.command.build_ext import build_ext

    setup(
        name="cythontests",
        version="0.1",
        description="build cython extension modules for pytest tests",
        ext_modules=extensions,
        cmdclass = {
            'build_ext': build_ext,
            }
        )
