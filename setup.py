import setuptools
from setuptools import find_packages

with open("README.md", "r") as fh:
    long_description = fh.read()

print(find_packages())

setuptools.setup(
    name="imgvid_utils",
    version="0.2.0",
    author="Philippe Solodov",
    author_email="solop1906@gmail.com",
    description="A package that provides helpful utilities to interact with videos and images through OpenCV.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/philippeitis/imgvid_utils",
    packages=find_packages(exclude=["tests", "tests.*"]),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.6',
    install_requires=[
        "opencv-python==4.6.0.66",
    ],

)
