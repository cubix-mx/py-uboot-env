#!/usr/bin/env python3
"""
Setup file for py_uboot_env package.
"""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="py_uboot_env",
    version="0.1.0",
    author="Edel Macias",
    description="A package for reading, modifying, and writing U-Boot environment files",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/cubix-mx/py-uboot-env",
    project_urls={
        "Bug Tracker": "https://github.com/cubix-mx/py-uboot-env/issues",
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    packages=find_packages(),
    python_requires=">=3.6",
    entry_points={
        "console_scripts": [
            "uboot-env=py_uboot_env.cli:main",
        ],
    },
)
