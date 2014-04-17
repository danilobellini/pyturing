#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Created on Sun Apr  6 02:11:30 2014
# MIT Licensed. See COPYING.TXT for more information.
""" Turing machine setup module """

from setuptools import setup
from setuptools.command.test import test as TestClass
from pyturing import __version__

class Tox(TestClass):
    def finalize_options(self):
        TestClass.finalize_options(self)
        self.test_args = ["-v"] if self.verbose else []
        self.test_suite = True
    def run_tests(self):
        import sys, tox
        sys.exit(tox.cmdline(self.test_args))

metadata = {
  "name": "pyturing",
  "version": __version__,
  "author": "Danilo J. S. Bellini and Nicolas França",
  "author_email": "danilo [dot] bellini [at] gmail [dot] com",
  "url": "http://github.com/danilobellini/pyturing",
  "description": "A simple Turing machine simulator using Python.",
  "license": "MIT",
  "py_modules": ["pyturing"],
  "tests_require": ["tox"],
  "cmdclass": {"test": Tox},
}

metadata["long_description"] = """
There's three Turing Machine interfaces in this project:

- Python API, for Turing a-machines and c-machines;
- CLI (Command Line Interface), for a-machines;
- Web UI in Flask, also for a-machines.

See the GitHub project page for more information.
"""

metadata["classifiers"] = [
  "Development Status :: 2 - Pre-Alpha",
  "Environment :: Console",
  "Environment :: Web Environment",
  "Framework :: Flask",
  "Intended Audience :: Developers",
  "Intended Audience :: Education",
  "Intended Audience :: Science/Research",
  "Intended Audience :: Other Audience",
  "License :: OSI Approved :: MIT License",
  "Operating System :: POSIX :: Linux",
  "Operating System :: OS Independent",
  "Programming Language :: Python",
  "Programming Language :: Python :: 2",
  "Programming Language :: Python :: 2.7",
  "Programming Language :: Python :: 3",
  "Programming Language :: Python :: 3.2",
  "Programming Language :: Python :: 3.3",
  "Programming Language :: Python :: 3.4",
  "Programming Language :: Other",
  "Topic :: Software Development",
  "Topic :: Software Development :: Interpreters",
  "Topic :: Software Development :: Libraries",
  "Topic :: Software Development :: Libraries :: Python Modules",
  "Topic :: Software Development :: Testing",
  "Topic :: System :: Emulators",
]

setup(**metadata)
