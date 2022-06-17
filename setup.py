from setuptools import setup, find_packages

with open("./README.md", "r") as fh:
    long_description = fh.read()

setup(
    name="any_inference",
    version="0.0.6",
    author="Francesco Saverio Zuppichini",
    author_email="francesco.zuppichini@gmail.com",
    description="Run inference in any model using a message broker.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/FrancescoSaverioZuppichini/any-inference",
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    install_requires=[
        "kombu",
        "rich",
    ],
    python_requires=">=3.8",
     extras_require={
        "dev": ["markdown", "mkdocs-material", "pymdown-extensions", "mkdocstrings", "mkdocs-gen-files", "mkdocs-literate-nav", "mkdocstrings-python"]
    },
)