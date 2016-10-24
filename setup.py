from setuptools import setup


setup(
    name="pytest-warnings",
    description='pytest plugin to list Python warnings in pytest report',
    long_description=open("README.rst").read(),
    license="MIT license",
    version='0.2.0',
    author='Florian Schulze',
    author_email='florian.schulze@gmx.net',
    url='https://github.com/fschulze/pytest-warnings',
    packages=['pytest_warnings'],
    entry_points={'pytest11': ['pytest_warnings = pytest_warnings']},
    install_requires=['pytest'],
    classifiers=[
        "Framework :: Pytest"])
