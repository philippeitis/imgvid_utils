import setuptools
from setuptools import find_namespace_packages

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="imgvid_utils",
    version="0.0.4",
    author="Philippe Solodov",
    author_email="solop1906@gmail.com",
    description="A package that provides helpful utilities to interact with videos and images through OpenCV.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/philippeitis/imgvid_utils",
    package_dir={"": "imgvid_utils"},
    packages=find_namespace_packages(where="imgvid_utils"),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.6',
)
