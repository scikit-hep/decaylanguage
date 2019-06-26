# Changelog

## Version 0.3.0 (2019-06-26)

* Decays modelling:
  - Updates to Mint related particle data files.
* Parsing of decay files (aka .dec files):
  - Lark parser files added, for ``.dec`` decay files.
  - ``DecFileParser`` class introduced, with documentation and test suite.
  - Various ``.dec`` test decay files added.
* Visualisation of decay chains:
  - ``DecayChainViewer`` class introduced, with documentation and test suite.
* Universal representation of decay chains:
  - First "building block" classes ``DaughtersDict`` and ``DecayMode`` introduced,
    with documentation and test suite.
* Package dependencies:
  - Package made dependent on Scikit-HEP's ``Particle`` package.
  - Redundant code removed.
* Continuous integration:
  - CI with Azure pipelines introduced.
  - CI with Travis and AppVeyor removed.
* Miscellaneous:
  - Demo notebook added, with a launcher for Binder.
  -Copyright statements added to repository files.
  - General clean-up and minor bug fixes.


## Version 0.2.0 (2018-08-02)

* First release as part of Scikit-HEP.
* Using new data package with ``importlib_resources`` (or ``importlib.resources`` on Python 3.7).
* Better docs and examples.
* Some method renaming.
* Generalized converter script.


## Version 0.1.0 (2018-03-13)

* First release on PyPI.
