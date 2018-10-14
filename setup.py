import os
from setuptools import setup


def main():
    install_requires = [
        "py>=1.5.0",  # if py gets upgrade to >=1.6, remove _width_of_current_line in terminal.py
        "six>=1.10.0",
        "setuptools",
        "attrs>=17.4.0",
        "more-itertools>=4.0.0",
        "atomicwrites>=1.0",
        'funcsigs;python_version<"3.0"',
        'pathlib2>=2.2.0;python_version<"3.6"',
        'colorama;sys_platform=="win32"',
    ]
    # if _PYTEST_SETUP_SKIP_PLUGGY_DEP is set, skip installing pluggy;
    # used by tox.ini to test with pluggy master
    if "_PYTEST_SETUP_SKIP_PLUGGY_DEP" not in os.environ:
        install_requires.append("pluggy>=0.7")

    setup(
        use_scm_version={"write_to": "src/_pytest/_version.py"},
        url="https://docs.pytest.org/en/latest/",
        project_urls={
            "Source": "https://github.com/pytest-dev/pytest",
            "Tracker": "https://github.com/pytest-dev/pytest/issues",
        },
        license="MIT license",
        platforms=["unix", "linux", "osx", "cygwin", "win32"],
        author=(
            "Holger Krekel, Bruno Oliveira, Ronny Pfannschmidt, "
            "Floris Bruynooghe, Brianna Laugher, Florian Bruhin and others"
        ),
        entry_points={"console_scripts": ["pytest=pytest:main", "py.test=pytest:main"]},
        keywords="test unittest",
        # the following should be enabled for release
        setup_requires=["setuptools-scm", "setuptools>30.3"],
        package_dir={"": "src"},
        python_requires=">=2.7, !=3.0.*, !=3.1.*, !=3.2.*, !=3.3.*",
        install_requires=install_requires,
        packages=[
            "_pytest",
            "_pytest.assertion",
            "_pytest._code",
            "_pytest.mark",
            "_pytest.config",
        ],
        py_modules=["pytest"],
        zip_safe=False,
    )


if __name__ == "__main__":
    main()
