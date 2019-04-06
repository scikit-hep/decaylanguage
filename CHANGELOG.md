# Changelog

## Version 0.3.0

Under development

* Decays modelling:
  - Updates to Mint related particle data files.
* Particle decays:
  - Lark parser files added, for ``.dec`` decay files.
  - ``DecFileParser`` class introduced, with doc and test suite.
  - Various ``.dec`` test decay files added.
* Package dependencies:
  - Package made dependent on Scikit-HEP's ``Particle`` package
  - Redundant code removed.
* Continuous integration:
  - CI with Azure pipelines introduced.
  - Simplification of ``.travis.yml`` file.
* Miscellaneous:
  - Minor bug fixes.


## Version 0.2.0 (2018-08-02)
* First release as part of Scikit-HEP.
* Using new data package with ``importlib_resources`` (or ``importlib.resources`` on Python 3.7).
* Better docs and examples.
* Some method renaming.
* Generalized converter script.


## Version 0.1.0 (2018-03-13)

* First release on PyPI.
