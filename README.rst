.. image:: images/DecayLanguage.png
   :alt: DecayLanguage
   :target: http://decaylanaguage.readthedocs.io/en/latest/

.. start-badges

|docs| |travis| |appveyor| |coveralls| |version| |supported-versions| |commits-since|


.. |docs| image:: https://readthedocs.org/projects/decaylanguage/badge/?style=flat
    :target: https://readthedocs.org/projects/decaylanguage
    :alt: Documentation Status

.. |travis| image:: https://travis-ci.org/henryiii/decaylanguage.svg?branch=master
    :alt: Travis-CI Build Status
    :target: https://travis-ci.org/henryiii/decaylanguage

.. |appveyor| image:: https://ci.appveyor.com/api/projects/status/github/henryiii/decaylanguage?branch=master&svg=true
    :alt: AppVeyor Build Status
    :target: https://ci.appveyor.com/project/HenrySchreiner/decaylanguage

.. |requires| image:: https://requires.io/github/henryiii/decaylanguage/requirements.svg?branch=master
    :alt: Requirements Status
    :target: https://requires.io/github/henryiii/decaylanguage/requirements/?branch=master

.. |coveralls| image:: https://coveralls.io/repos/henryiii/decaylanguage/badge.svg?branch=master&service=github
    :alt: Coverage Status
    :target: https://coveralls.io/github/henryiii/decaylanguage

.. |version| image:: https://img.shields.io/pypi/v/decaylanguage.svg
    :alt: PyPI Package latest release
    :target: https://pypi.python.org/pypi/decaylanguage

.. |commits-since| image:: https://img.shields.io/github/commits-since/henryiii/decaylanguage/v0.1.0.svg
    :alt: Commits since latest release
    :target: https://github.com/henryiii/decaylanguage/compare/v0.1.0...master

.. |wheel| image:: https://img.shields.io/pypi/wheel/decaylanguage.svg
    :alt: PyPI Wheel
    :target: https://pypi.python.org/pypi/decaylanguage

.. |supported-versions| image:: https://img.shields.io/pypi/pyversions/decaylanguage.svg
    :alt: Supported versions
    :target: https://pypi.python.org/pypi/decaylanguage

.. |supported-implementations| image:: https://img.shields.io/pypi/implementation/decaylanguage.svg
    :alt: Supported implementations
    :target: https://pypi.python.org/pypi/decaylanguage


.. end-badges

A language to describe particle decays, and tools to work with them.

* Free software: BSD 3-Clause License

Installation
============

::

    pip install decaylanguage

Documentation
=============

https://decaylanguage.readthedocs.io/en/latest/

Development
===========

To run the all tests run::

    tox

Note, to combine the coverage data from all the tox environments run:

.. list-table::
    :widths: 10 90
    :stub-columns: 1

    - - Windows
      - ::

            set PYTEST_ADDOPTS=--cov-append
            tox

    - - Other
      - ::

            PYTEST_ADDOPTS=--cov-append tox
