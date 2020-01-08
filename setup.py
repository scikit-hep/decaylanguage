#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# Copyright (c) 2018-2020, Eduardo Rodrigues and Henry Schreiner.
#
# Distributed under the 3-clause BSD license, see accompanying file LICENSE
# or https://github.com/scikit-hep/decaylanguage for details.

from __future__ import absolute_import
from __future__ import print_function

import io
import sys
import os

from setuptools import find_packages
from setuptools import setup


PYTHON_REQUIRES = ">=2.7, !=3.0.*, !=3.1.*, !=3.2.*, !=3.3.*, !=3.4.*"

INSTALL_REQUIRES = [
    'attrs>=17.4',
    'plumbum>=1.6.6',
    'numpy>=1.12',
    'pandas>=0.22',
    'six>=1.11',
    'lark-parser>=0.6.3',
    'pathlib2>=2.3; python_version<"3.5"',
    'enum34>=1.1; python_version<"3.4"',
    'importlib_resources>=1.0; python_version<"3.7"',
    'cachetools; python_version<"3.3"',
    'particle==0.9.*'
]

needs_pytest = {'pytest', 'test', 'ptr'}.intersection(sys.argv)
pytest_runner = ['pytest-runner'] if needs_pytest else []

def read(*names, **kwargs):
    return io.open(
        os.path.join(os.path.dirname(__file__), *names),
        encoding=kwargs.get('encoding', 'utf8')
    ).read()

def proc_readme(text):
    text = text.split('<!-- break -->')[-1]
    return '''
    <a href="https://decaylanguage.readthedocs.io/en/latest/"><img align="left" src="https://raw.githubusercontent.com/scikit-hep/decaylanguage/master/images/DecayLanguage.png"></img></a><br>

    ''' + text

def get_version():
    g = {}
    exec(open(os.path.join("decaylanguage", "_version.py")).read(), g)
    return g["__version__"]

extras = {
    'test': ['pytest', 'pydot'],
    'notebook': ['graphviz', 'pydot'],
}

setup(
    name = 'DecayLanguage',
    author = 'Henry Fredrick Schreiner III, Eduardo Rodrigues',
    author_email = 'henry.schreiner@cern.ch, eduardo.rodrigues@cern.ch',
    maintainer = 'The Scikit-HEP admins',
    maintainer_email = 'scikit-hep-admins@googlegroups.com',
    version = get_version(),
    license = 'BSD 3-Clause License',
    description = 'A language to describe particle decays, and tools to work with them.',
    long_description = proc_readme(read('README.md')) + '\n\n' + read('CHANGELOG.md'),
    long_description_content_type = "text/markdown",
    url = 'https://github.com/scikit-hep/decaylanguage',
    packages = find_packages(),
    package_data = {'': ['data/*.*']},
    python_requires = PYTHON_REQUIRES,
    install_requires = INSTALL_REQUIRES,
    setup_requires = [] + pytest_runner,
    tests_require = extras['test'],
    extras_require = extras,
    keywords = [
        'HEP', 'particle', 'decay', 'representation'
    ],
    classifiers = [
        # complete classifier list: http://pypi.python.org/pypi?%3Aaction=list_classifiers
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'Intended Audience :: Science/Research',
        'License :: OSI Approved :: BSD License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Topic :: Scientific/Engineering',
    ],
    platforms = "Any",
)
