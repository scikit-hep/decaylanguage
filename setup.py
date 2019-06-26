#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# Copyright (c) 2018-2019, Eduardo Rodrigues and Henry Schreiner.
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
    ![[DecayLanguage](https://github.com/scikit-hep/decaylanguage)](https://github.com/scikit-hep/decaylanguage/raw/master/images/DecayLanguage.png)

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
    name='decaylanguage',
    author='Henry Fredrick Schreiner III',
    author_email='henry.schreiner@cern.ch',
    maintainer = 'The Scikit-HEP admins',
    maintainer_email = 'scikit-hep-admins@googlegroups.com',
    version = get_version(),
    license='BSD 3-Clause License',
    description='A language to describe particle decays, and tools to work with them.',
    long_description=proc_readme(read('README.md')) + '\n\n' + read('CHANGELOG.md'),
    long_description_content_type="text/markdown",
    url='https://github.com/scikit-hep/decaylanguage',
    packages=find_packages(),
    package_data={'': ['data/*.*']},
    classifiers=[
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
        'Topic :: Scientific/Engineering',
    ],
    keywords=[
        'particle', 'decay', 'HEP'
    ],
    install_requires=[
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
        'particle>=0.5.0'
    ],
    extras_require=extras,
    setup_requires=[] + pytest_runner,
    tests_require=extras['test'],
    platforms="Any",
)
