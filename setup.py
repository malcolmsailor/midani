import setuptools

README = "README.md"

with open(README, "r", encoding="utf-8") as fh:
    long_description = fh.read()

long_description = long_description.replace(
    "docs/resources/demo_frame",
    "https://github.com/malcolmsailor/midani/raw/master/docs/resources/demo_frame",
)

setuptools.setup(
    name="midani",
    version="0.0.3",
    author="Malcolm Sailor",
    author_email="malcolm.sailor@gmail.com",
    description="Make piano-roll animations from midi files",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/malcolmsailor/midani",
    project_urls={
        "Bug Tracker": "https://github.com/malcolmsailor/midani/issues",
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    package_dir={"": "."},
    packages=setuptools.find_packages(where="."),
    python_requires=">=3.8",
    install_requires=["opencv_python", "mido"],
    entry_points={"console_scripts": ["midani = midani.__main__:main"]},
)
