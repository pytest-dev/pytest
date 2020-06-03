from setuptools import setup

INSTALL_REQUIRES = [
    # keep this list sorted
    "atomicwrites>=1.0;sys_platform=='win32'",
    "attrs>=17.4.0",  # should match oldattrs tox env.
    "colorama;sys_platform=='win32'",
    "importlib-metadata>=0.12;python_version<'3.8'",
    "iniconfig",
    "more-itertools>=4.0.0",
    "packaging",
    "pathlib2>=2.2.0;python_version<'3.6'",
    "pluggy>=0.12,<1.0",
    "py>=1.5.0",  # remove _width_of_current_line in terminal.py when upgrading to py>=1.6
]


def main():
    setup(
        use_scm_version={"write_to": "src/_pytest/_version.py"},
        setup_requires=["setuptools-scm", "setuptools>=40.0"],
        package_dir={"": "src"},
        extras_require={
            "testing": [
                "argcomplete",
                "hypothesis>=3.56",
                "mock",
                "nose",
                "requests",
                "xmlschema",
            ],
            "checkqa-mypy": [
                "mypy==v0.770",  # keep this in sync with .pre-commit-config.yaml.
            ],
        },
        install_requires=INSTALL_REQUIRES,
    )


if __name__ == "__main__":
    main()
