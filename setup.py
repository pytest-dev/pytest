from setuptools import setup


def main():
    setup(use_scm_version={"write_to": "src/_pytest/_version.py"})


if __name__ == "__main__":
    main()
