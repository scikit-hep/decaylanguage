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


Installation
============

Just run the following:

::

    pip install decaylanguage


You can use a virtual environment through `pipenv` or `--user` if you know what those are.

Usage
=====

This is a quick user guide; for full API docs, see https://decaylanguage.readthedocs.io/en/latest/

DecayLanguage is a set of tools for building and transforming particle decays. The parts are:

Particles
---------

You can use a variety of methods to get particles; if you know the PDG number you can get a particle directly, or you can use a search::

    Particle.from_pdg(211)
    Particle.from_search_list(name='pi')[0]

You can search for the properties, which are ``name``, ``mass``, ``width``, ``charge``, ``A``, ``rank``, ``I``, ``J``, ``G``, ``P``, ``quarks``, ``status``, ``latex``, ``mass_upper``, ``mass_lower``, ``width_upper``, and ``width_lower`` (some of those don't make sense). You can also use ``from_search`` to require only one match.

Once you have a particle, any of the properties can be accessed, along with several methods. Though they are not real properties, you can access ``bar``, ``radius``, and ``spintype``. You can also ``invert()`` a particle. There are lots of printing choices, ``describe()``, ``programatic_name()``, ``html_name()``, html printing outs in notebooks, and of course ``repr``
and ``str`` support.

Decays
------

The most common way to create a decay chain is to read in an AmpGen style syntax from a file or a string.

Converters
----------

You can output to a format (currently only GooFit supported, feel free to make a PR to add more). Use a subclass of `DecayChain`, in this case, `GooFitChain`.

Acknowledgements
================
Decay Language is free software released under a BSD 3-Clause License. It was originally developed by Henry Schreiner.

