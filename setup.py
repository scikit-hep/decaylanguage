#!/usr/bin/env python
# -*- encoding: utf-8 -*-
from __future__ import absolute_import
from __future__ import print_function

import io
from os.path import dirname
from os.path import join

from setuptools import find_packages
from setuptools import setup


def read(*names, **kwargs):
    return io.open(
        join(dirname(__file__), *names),
        encoding=kwargs.get('encoding', 'utf8')
    ).read()

def proc_readme(text):
    text = text.split('<!-- break -->')[-1]
    return '''
    ![[DecayLanguage](https://github.com/scikit-hep/decaylanguage)](https://github.com/scikit-hep/decaylanguage/raw/master/images/DecayLanguage.png)

    ''' + text



setup(
    name='decaylanguage',
    version='0.2.0',
    license='BSD 3-Clause License',
    description='A language to describe particle decays, and tools to work with them.',
    long_description=proc_readme(read('README.md')) + '\n\n' + read('CHANGELOG.md'),
    long_description_content_type="text/markdown",
    author='Henry Fredrick Schreiner III',
    author_email='henry.schreiner@cern.ch',
    url='https://github.com/scikit-hep/decaylanguage',
    packages=find_packages(),
    include_package_data=True,
    zip_safe=True,
    classifiers=[
        # complete classifier list: http://pypi.python.org/pypi?%3Aaction=list_classifiers
        "Development Status :: 3 - Alpha",
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Operating System :: Unix',
        'Operating System :: POSIX',
        'Operating System :: Microsoft :: Windows',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: Implementation :: CPython',
        'Programming Language :: Python :: Implementation :: PyPy',
        'Topic :: Utilities',
    ],
    keywords=[
        'particle', 'decay', 'HEP'
    ],
    install_requires=[
        'plumbum>=1.6.6',
        'attrs>=17.0',
        'numpy>=1.12',
        'pandas>=0.22',
        'six>=1.11',
        'lark-parser>=0.6.3',
        'pathlib2>=2.3; python_version<"3.5"',
        'enum34>=1.1; python_version<"3.4"',
        'importlib_resources>=1.0; python_version<"3.7"',
    ],
    extras_require={
        'notebook': ['graphviz'],
    },
    setup_requires=['pytest-runner'],
    tests_require=['pytest']
)
