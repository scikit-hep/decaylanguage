[![DecayLanguage](images/DecayLanguage.png)](http://decaylanguage.readthedocs.io/en/latest/)

[![Documentation Status](https://readthedocs.org/projects/decaylanguage/badge/?style=flat)](https://readthedocs.org/projects/decaylanguage)
[![Azure Build Status](https://dev.azure.com/scikit-hep/decaylanguage/_apis/build/status/scikit-hep.decaylanguage?branchName=master)](https://dev.azure.com/scikit-hep/decaylanguage/_build/latest?definitionId=3?branchName=master)
[![Coverage Status](https://img.shields.io/azure-devops/coverage/scikit-hep/decaylanguage/3.svg)](https://dev.azure.com/scikit-hep/decaylanguage/_build/latest?definitionId=3?branchName=master)
[![Tests Status](https://img.shields.io/azure-devops/tests/scikit-hep/decaylanguage/3.svg)](https://dev.azure.com/scikit-hep/decaylanguage/_build/latest?definitionId=3?branchName=master)
[![PyPI Package latest release](https://img.shields.io/pypi/v/decaylanguage.svg)](https://pypi.python.org/pypi/decaylanguage)
[![Supported versions](https://img.shields.io/pypi/pyversions/decaylanguage.svg)](https://pypi.python.org/pypi/decaylanguage)
[![Commits since latest release](https://img.shields.io/github/commits-since/scikit-hep/decaylanguage/v0.2.0.svg)](https://github.com/scikit-hep/decaylanguage/compare/v0.2.0...master)
[![Binder demo](https://mybinder.org/badge_logo.svg)](https://mybinder.org/v2/gh/scikit-hep/decaylanguage/master?urlpath=lab/tree/notebooks/DecayLanguageDemo.ipynb)


<!-- break -->

A language to describe particle decays, and tools to work with them.

# Installation

Just run the following:

```bash
pip install decaylanguage
```

You can use a virtual environment through pipenv or with `--user` if you know
what those are. [Python 2.7 and 3.4+](http://docs.python-guide.org/en/latest/starting/installation) are supported.

<details><summary>Dependencies: (click to expand)</summary><p>

Required and compatibility dependencies will be automatically installed by pip.

### Required dependencies:

-   [particle](https://github.com/scikit-hep/particle): PDG particle data and identification codes
-   [Numpy](https://scipy.org/install.html): The numerical library for Python
-   [pandas](https://pandas.pydata.org/): Tabular data in Python
-   [attrs](https://github.com/python-attrs/attrs): DataClasses for Python
-   [plumbum](https://github.com/tomerfiliba/plumbum): Command line tools
-   [lark-parser](https://github.com/lark-parser/lark): A modern parsing library for Python

### Python compatibility:
-   [six](https://github.com/benjaminp/six): Compatibility library
-   [pathlib2](https://github.com/mcmtroffaes/pathlib2) backport if using Python 2.7
-   [enum34](https://bitbucket.org/stoneleaf/enum34) backport if using Python /< 3.5
-   [importlib_resources](http://importlib-resources.readthedocs.io/en/latest/) backport if using Python /< 3.7


### Recommended dependencies:
-   [graphviz](https://gitlab.com/graphviz/graphviz/) to render (DOT
    language) graph descriptions of decay chains.
</p></details>


# Usage

This is a quick user guide; for full API docs, go [here](https://decaylanguage.readthedocs.io/en/latest/).

``DecayLanguage`` is a set of tools for building and transforming particle
decays. The parts are:

## Particles

Particles are a key component when dealing with decays.
Refer to the [particle package](https://github.com/scikit-hep/particle)
for how to deal with particles and PDG identification codes.

## Decays

The most common way to create a decay chain is to read in an [AmpGen]
style syntax from a file or a string. You can use:

```python
from decaylanguage.modeling import AmplitudeChain
lines, parameters, constants, states = AmplitudeChain.read_ampgen(text='''
EventType D0 K- pi+ pi+ pi-

D0[D]{K*(892)bar0{K-,pi+},rho(770)0{pi+,pi-}}                            0 1 0.1 0 1 0.1

K(1460)bar-_mass  0 1460 1
K(1460)bar-_width 0  250 1

a(1)(1260)+::Spline::Min 0.18412
a(1)(1260)+::Spline::Max 1.86869
a(1)(1260)+::Spline::N 34
''')
```

Here, `lines` will be a list of AmplitudeChain lines (pretty print supported in Jupyter notebooks),
`parameters` will be a table of parameters (ranged parameters not yet supported),
`constants` will be a table of constants,
and `states` will be the list of known states (EventType).

## Converters

You can output to a format (currently only [GooFit] supported, feel free
to make a PR to add more). Use a subclass of DecayChain, in this case,
GooFitChain. To use the [GooFit] output, type from the shell:

```bash
python -m decaylanguage -G goofit myinput.opts
```

# Acknowledgements

DecayLanguage is free software released under a BSD 3-Clause License.
It was originally developed by Henry Schreiner.

[AmpGen]: https://gitlab.cern.ch/lhcb/Gauss/tree/LHCBGAUSS-1058.AmpGenDev/Gen/AmpGen
[GooFit]: https://GooFit.github.io
