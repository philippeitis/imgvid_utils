import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="imgvid_utils",
    version="0.0.2",
    author="Philippe Solodov",
    author_email="solop1906@gmail.com",
    description="A package that provides helpful utilities to interact with videos and images through OpenCV.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/philippeitis/imgvid_utils",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.6',
)
