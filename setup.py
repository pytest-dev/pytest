import os
from setuptools import setup


# TODO: if py gets upgrade to >=1.6,
#       remove _width_of_current_line in terminal.py
INSTALL_REQUIRES = [
    "py>=1.5.0",
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
    INSTALL_REQUIRES.append("pluggy>=0.7")


def main():
    setup(
        use_scm_version={"write_to": "src/_pytest/_version.py"},
        setup_requires=["setuptools-scm", "setuptools>=30.3"],
        package_dir={"": "src"},
        install_requires=INSTALL_REQUIRES,
    )


if __name__ == "__main__":
    main()
