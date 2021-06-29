from setuptools import find_packages, setup

setup(
    name="midani",
    version="0.0.0",
    packages=find_packages(),
    entry_points={"console_scripts": ["midani = midani.__main__:main"]},
)
