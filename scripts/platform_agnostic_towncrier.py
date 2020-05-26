from subprocess import check_call


def main():
    """
    Platform agnostic towncrier to support tox -e docs on a windows based platform natively.
    Previously we used 'sh -c' which will not work on pycharm terminal in windows for example.
    """
    check_call("towncrier --draft > doc/en/_changelog_towncrier_draft.rst", shell=True)


if __name__ == "__main__":
    main()
