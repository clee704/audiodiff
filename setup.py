import os
import re
import sys

import audiodiff

try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

packages = [
    'audiodiff',
]

requires = [
    "mutagenwrapper == 0.0.5",
    "termcolor == 1.1.0",
]

setup(
    name = "audiodiff",
    version = audiodiff.__version__,
    description = "compares audio files",
    long_description = open("README.rst").read(),
    author = "Choongmin Lee",
    author_email = "choongmin@me.com",
    url = "https://github.com/clee704/audiodiff",
    packages = packages,
    install_requires = requires,
    entry_points = {
      "console_scripts": [
        'audiodiff = audiodiff.commandlinetool:main_func',
      ],
    },
    license = open('LICENSE').read(),
    keywords = "lossless audio metadata comparison",
    classifiers = [
        # Full list is here: http://pypi.python.org/pypi?%3Aaction=list_classifiers
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Intended Audience :: End Users/Desktop",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python",
        "Topic :: Multimedia :: Sound/Audio :: Analysis",
        "Topic :: Utilities",
    ],
)
