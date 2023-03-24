<img alt="DecayLanguage logo" src="https://raw.githubusercontent.com/scikit-hep/decaylanguage/master/images/DecayLanguage.png"/>

# DecayLanguage: describe, manipulate and convert particle decays

[![Scikit-HEP](https://scikit-hep.org/assets/images/Scikit--HEP-Project-blue.svg)](https://scikit-hep.org/)
[![PyPI Package latest release](https://img.shields.io/pypi/v/decaylanguage.svg)](https://pypi.python.org/pypi/decaylanguage)
[![Conda latest release](https://img.shields.io/conda/vn/conda-forge/decaylanguage.svg)](https://github.com/conda-forge/decaylanguage-feedstock)
[![Supported versions](https://img.shields.io/pypi/pyversions/decaylanguage.svg)](https://pypi.python.org/pypi/decaylanguage)
[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.3257423.svg)](https://doi.org/10.5281/zenodo.3257423)

[![GitHub Actions Status: CI](https://github.com/scikit-hep/decaylanguage/workflows/CI/badge.svg)](https://github.com/scikit-hep/decaylanguage/actions)
[![Code Coverage](https://codecov.io/gh/scikit-hep/decaylanguage/graph/badge.svg?branch=master)](https://codecov.io/gh/scikit-hep/decaylanguage?branch=master)
[![Documentation Status](https://readthedocs.org/projects/decaylanguage/badge/?style=flat)](https://decaylanguage.readthedocs.io)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

[![Binder demo](https://mybinder.org/badge_logo.svg)](https://mybinder.org/v2/gh/scikit-hep/decaylanguage/master?urlpath=lab/tree/notebooks/DecayLanguageDemo.ipynb)


DecayLanguage implements a language to describe and convert particle decays
between digital representations, effectively making it possible to interoperate
several fitting programs. Particular interest is given to programs dedicated
to amplitude analyses.

DecayLanguage provides tools to parse so-called .dec decay files,
and describe, manipulate and visualize decay chains.


## Installation

Just run the following:

```bash
pip install decaylanguage
```

You can use a virtual environment through pipenv or with `--user` if you know
what those are. [Python
3.7+](http://docs.python-guide.org/en/latest/starting/installation) supported
(see version 0.12 for Python 2 & 3.5 support, 0.14 for Python 3.6 support).

<details><summary>Dependencies: (click to expand)</summary><p>

Required and compatibility dependencies will be automatically installed by pip.

### Required dependencies:

-   [particle](https://github.com/scikit-hep/particle): PDG particle data and identification codes
-   [NumPy](https://scipy.org/install.html): The numerical library for Python
-   [pandas](https://pandas.pydata.org/): Tabular data in Python
-   [attrs](https://github.com/python-attrs/attrs): DataClasses for Python
-   [plumbum](https://github.com/tomerfiliba/plumbum): Command line tools
-   [lark](https://github.com/lark-parser/lark): A modern parsing library for Python
-   [graphviz](https://gitlab.com/graphviz/graphviz/) to render (DOT language) graph
    descriptions and visualizations of decay chains.

### Python compatibility:
-   [importlib_resources](http://importlib-resources.readthedocs.io/en/latest/) backport if using Python /< 3.7
</p></details>


## Getting started

The [Binder demo](https://mybinder.org/v2/gh/scikit-hep/decaylanguage/master?urlpath=lab/tree/notebooks/DecayLanguageDemo.ipynb)
is an excellent way to get started with `DecayLanguage`.

This is a quick user guide. For a full API docs, go [here](https://decaylanguage.readthedocs.io)
(note that it is presently work-in-progress).

### What is DecayLanguage?

`DecayLanguage` is a set of tools for building and transforming particle
decays:

1. It provides tools to parse so-called `.dec` decay files,
and describe, manipulate and visualize the resulting decay chains.

2. It implements a language to describe and convert particle decays
between digital representations, effectively making it possible to interoperate
several fitting programs. Particular interest is given to programs dedicated
to amplitude analyses.

### Particles

Particles are a key component when dealing with decays.
Refer to the [particle package](https://github.com/scikit-hep/particle)
for how to deal with particles and Monte Carlo particle identification codes.

### Parse decay files

Decay `.dec` files can be parsed simply with

```python
from decaylanguage import DecFileParser

parser = DecFileParser('my-decay-file.dec')
parser.parse()

# Inspect what decays are defined
parser.list_decay_mother_names()

# Print decay modes, etc. ...
```

A copy of the master DECAY.DEC file used by the LHCb experiment is provided
[here](https://github.com/scikit-hep/decaylanguage/tree/master/src/decaylanguage/data)
for convenience.

The `DecFileParser` class implements a series of methods giving access to all
information stored in decay files: the decays themselves, particle name aliases,
definitions of charge-conjugate particles, variable and Pythia-specific
definitions, etc.

It can be handy to parse from a multi-line string rather than a file:

```python
s = """Decay pi0
0.988228297   gamma   gamma                   PHSP;
0.011738247   e+      e-      gamma           PI0_DALITZ;
0.000033392   e+      e+      e-      e-      PHSP;
0.000000065   e+      e-                      PHSP;
Enddecay
"""

dfp = DecFileParser.from_string(s)
dfp.parse()
```

#### Advanced usage

The list of `.dec` file decay models known to the package can be inspected via

```python
from decaylanguage.dec import known_decay_models
```

Say you have to deal with a decay file containing a new model not yet on the list above.
Running the parser as usual will result in a `UnexpectedToken` exception.
It is nevertheless easy to deal with this issue; no need to wait for a new release.
It is just a matter of adding the model name to the list in `decaylanguage/data/decfile.lark`
(or your private copy), see the line
`MODEL_NAME.2 : "BaryonPCR"|"BTO3PI_CP"|"BTOSLLALI"|...`,
and then proceed as usual apart from adding an extra line to call to `load_grammar`
to specify the Lark grammar to use:

```python
dfp = DecFileParser('my_decfile.dec')
dfp.load_grammar('path/to/my_updated_decfile.lark')
dfp.parse()
...
```

This being said, please do submit a pull request to add new models,
if you spot missing ones ...

### Visualize decay files

The class `DecayChainViewer` allows the visualization of parsed decay chains:

```python
from decaylanguage import DecayChainViewer

# Build the (dictionary-like) D*+ decay chain representation setting the
# D+ and D0 mesons to stable, to avoid too cluttered an image
d = dfp.build_decay_chains('D*+', stable_particles=('D+', 'D0'))
DecayChainViewer(d)  # works in a notebook
```

![DecayChain D*](https://raw.githubusercontent.com/scikit-hep/decaylanguage/master/images/DecayChain_Dst_stable-D0-and-D+.png)

The actual graph is available as

```python
# ...
dcv = DecayChainViewer(d)
dcv.graph
```

making all `graphviz.Digraph` class properties and methods available, such as

```python
dcv.graph.render(filename='mygraph', format='pdf', view=True, cleanup=True)
```

In the same way, all `graphviz.Digraph` class attributes are settable
upon instantiation of `DecayChainViewer`:

```python
dcv = DecayChainViewer(chain, name='TEST', format='pdf')
```

### Universal representation of decay chains

A series of classes and methods have been designed to provide universal representations
of particle decay chains of any complexity, and to provide the ability
to convert between these representations.
Specifically, class- and dictionary-based representations have been implemented.

An example of a class-based representation of a decay chain is the following:

```python
>>> from decaylanguage import DaughtersDict, DecayMode, DecayChain
>>>
>>> dm1 = DecayMode(0.0124, 'K_S0 pi0', model='PHSP')
>>> dm2 = DecayMode(0.692, 'pi+ pi-')
>>> dm3 = DecayMode(0.98823, 'gamma gamma')
>>> dc = DecayChain('D0', {'D0':dm1, 'K_S0':dm2, 'pi0':dm3})
>>> dc
<DecayChain: D0 -> K_S0 pi0 (2 sub-decays), BF=0.0124>
```

Decay chains can be visualised with the `DecayChainViewer` class making use
of the dictionary representation `dc.to_dict()`, which is the simple
representation understood by `DecayChainViewer`, as see above:

```python
DecayChainViewer(dc.to_dict())
```

The fact that 2 representations of particle decay chains are provided ensures
the following:

1. Human-readable (class) and computer-efficient (dictionary) alternatives.
2. Flexibility for parsing, manipulation and storage of decay chain information.

### Decay modeling

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

#### Converters

You can output to a format (currently only [GooFit] supported, feel free
to make a PR to add more). Use a subclass of DecayChain, in this case,
GooFitChain. To use the [GooFit] output, type from the shell:

```bash
python -m decaylanguage -G goofit myinput.opts
```

## Contributors

We hereby acknowledge the contributors that made this project possible ([emoji key](https://allcontributors.org/docs/en/emoji-key)):
<!-- ALL-CONTRIBUTORS-LIST:START - Do not remove or modify this section -->
<!-- prettier-ignore-start -->
<!-- markdownlint-disable -->
<table>
  <tbody>
    <tr>
      <td align="center" valign="top" width="14.28%"><a href="http://cern.ch/eduardo.rodrigues"><img src="https://avatars.githubusercontent.com/u/5013581?v=4?s=100" width="100px;" alt="Eduardo Rodrigues"/><br /><sub><b>Eduardo Rodrigues</b></sub></a><br /><a href="#maintenance-eduardo-rodrigues" title="Maintenance">🚧</a> <a href="https://github.com/scikit-hep/decaylanguage/commits?author=eduardo-rodrigues" title="Code">💻</a> <a href="https://github.com/scikit-hep/decaylanguage/commits?author=eduardo-rodrigues" title="Documentation">📖</a></td>
      <td align="center" valign="top" width="14.28%"><a href="http://iscinumpy.dev"><img src="https://avatars.githubusercontent.com/u/4616906?v=4?s=100" width="100px;" alt="Henry Schreiner"/><br /><sub><b>Henry Schreiner</b></sub></a><br /><a href="#maintenance-henryiii" title="Maintenance">🚧</a> <a href="https://github.com/scikit-hep/decaylanguage/commits?author=henryiii" title="Code">💻</a> <a href="https://github.com/scikit-hep/decaylanguage/commits?author=henryiii" title="Documentation">📖</a></td>
      <td align="center" valign="top" width="14.28%"><a href="https://github.com/yipengsun"><img src="https://avatars.githubusercontent.com/u/33738176?v=4?s=100" width="100px;" alt="Yipeng Sun"/><br /><sub><b>Yipeng Sun</b></sub></a><br /><a href="https://github.com/scikit-hep/decaylanguage/commits?author=yipengsun" title="Code">💻</a></td>
      <td align="center" valign="top" width="14.28%"><a href="https://github.com/chrisburr"><img src="https://avatars.githubusercontent.com/u/5220533?v=4?s=100" width="100px;" alt="Chris Burr"/><br /><sub><b>Chris Burr</b></sub></a><br /><a href="https://github.com/scikit-hep/decaylanguage/commits?author=chrisburr" title="Documentation">📖</a></td>
      <td align="center" valign="top" width="14.28%"><a href="https://www.lieret.net"><img src="https://avatars.githubusercontent.com/u/13602468?v=4?s=100" width="100px;" alt="Kilian Lieret"/><br /><sub><b>Kilian Lieret</b></sub></a><br /><a href="https://github.com/scikit-hep/decaylanguage/commits?author=klieret" title="Documentation">📖</a></td>
      <td align="center" valign="top" width="14.28%"><a href="https://github.com/sognetic"><img src="https://avatars.githubusercontent.com/u/10749132?v=4?s=100" width="100px;" alt="Moritz Bauer"/><br /><sub><b>Moritz Bauer</b></sub></a><br /><a href="https://github.com/scikit-hep/decaylanguage/commits?author=sognetic" title="Code">💻</a></td>
      <td align="center" valign="top" width="14.28%"><a href="https://github.com/FlorianReiss"><img src="https://avatars.githubusercontent.com/u/44642966?v=4?s=100" width="100px;" alt="FlorianReiss"/><br /><sub><b>FlorianReiss</b></sub></a><br /><a href="https://github.com/scikit-hep/decaylanguage/commits?author=FlorianReiss" title="Code">💻</a> <a href="https://github.com/scikit-hep/decaylanguage/commits?author=FlorianReiss" title="Documentation">📖</a></td>
    </tr>
  </tbody>
</table>

<!-- markdownlint-restore -->
<!-- prettier-ignore-end -->

<!-- ALL-CONTRIBUTORS-LIST:END -->

This project follows the [all-contributors](https://github.com/all-contributors/all-contributors) specification.

## Acknowledgements

The UK Science and Technology Facilities Council (STFC) and the University of Liverpool
provide funding for Eduardo Rodrigues (2020-) to work on this project part-time.

Support for this work was provided by the National Science Foundation
cooperative agreement OAC-1450377 (DIANA/HEP) in 2016-2019
and has been provided by OAC-1836650 (IRIS-HEP) since 2019.
Any opinions, findings, conclusions or recommendations expressed in this material
are those of the authors and do not necessarily reflect the views of the National Science Foundation.


[AmpGen]: https://gitlab.cern.ch/lhcb/Gauss/tree/LHCBGAUSS-1058.AmpGenDev/Gen/AmpGen
[GooFit]: https://GooFit.github.io
