# Changelog

## Version 0.15.3 (2023-04-06)

* CI and tests:
  - Updates to pre-commit hooks and CI YAML files.

## Version 0.15.2 (2023-03-28)

* Universal representation of decay chains:
  - Better test coverage for dec and decay submodules.
* Modeling for GooFit/AmpGen:
  - Major update to AmpGen2GooFit parsing.
* Miscellaneous:
  - Moved over to using Ruff.
* CI and tests:
  - Updates to pre-commit hooks and CI YAML files.

## Version 0.15.1 (2023-02-02)

* Universal representation of decay chains:
  - Test suite extended for a significantly better test coverage.
* CI and tests:
  - Run doctests via pytest.
  - Updates to pre-commit hooks and CI YAML files.

## Version 0.15.0 (2022-11-08)

* Dependencies:
  - Package dependent on ``Particle`` version 0.21.x.
  - Adapted to Python 3 only Lark 1.x series.
  - Support for Python 3.11 added and support for Python 3.6 removed.
* Parsing of decay files (aka .dec files):
  - Updated to the latest Belle II master file DECAY.DEC.
  - Added support for ModelAlias keyword used in Belle II decay files.
* Miscellaneous:
  - Added a CITATION.cff file.
  - Moved over to using hatchling.
  - Started using AllContributors to acknowledge contributions explicitly.
* CI and tests:
  - Updates to pre-commit hooks and CI YAML files.
  - Various improvements to the CI.

## Version 0.14.2 (2022-07-11)

* Parsing of decay files (aka .dec files):
  - Minor improvements such as in type checking.
  - Documentation updates.
  - More tests.
* CI and tests:
  - Several improvements to GHAs.
  - Various hooks version updates.
  - Added a `dependabot.yml`.

## Version 0.14.1 (2022-02-03)

* Universal representation of decay chains:
  - Extra documentation and examples of usage.
  - Test suite extended.
* Miscellaneous:
  - Type checking introduced.
* Tests:
  - CI now tests the notebooks as well.
  - Various hooks version updates.

## Version 0.14.0 (2022-01-17)

Package dependent on Python 3 only ``Particle`` version 0.20.
Otherwise identical to series 0.13.

## Version 0.13.1 (2022-01-15)

* Universal representation of decay chains:
  - Adapt DOT representations to work with graphviz >= 0.19, which broke the API removing `_repr_svg_()`.
* Tests:
  - Various hooks version updates.

## Version 0.13.0 (2021-11-10)

* Dependencies:
  - Dropped Python 2 (2.7) support.
  - Added support for Python 3.10 and dropped 3.5.
  - Dependency on `lark-parser` upgraded to recent versions.
* Tests:
  - Dependency on Pytest upgraded.
  - Added new pre-commit hooks and updated various versions of existing hooks.
* Miscellaneous:
  - Added Nox support.

## Version 0.12.0 (2021-09-02)

* Dependencies:
  - Package dependent on ``Particle`` version 0.16.
  - Support for Python 3.5 removed.
* Universal representation of decay chains:
  - Documentation updates.
* Tests:
  - CI enhanced adding isort checks to pre-commit hooks.
  - Various hooks version updates.

## Version 0.11.4 (2021-08-23)

* CI and tests:
  - Run the CI on Linux, MacOS and Windows.
  - Re-added coverage tests replacing Coveralls with Codecov.
  - Removed Azure pipelines since superseded by GitHub Actions.

## Version 0.11.3 (2021-07-28)

* Parsing of decay files (aka .dec files):
  - Fix to parsing of a couple of decay models (subtletly of Lark parsing priorities).
* Miscellaneous:
  - CI updates.

## Version 0.11.2 (2021-06-24)

* Universal representation of decay chains:
  - ``DecFileParser.print_decay_modes()`` enhanced.
  - Fix to visualisation of ``DecayChainViewer`` instances in notebooks.
* Miscellaneous:
  - CI improvements and updates.

## Version 0.11.1 (2021-06-07)

* Notebook clean-ups and improvement to ``environment.yml``.

## Version 0.11.0 (2021-05-28)

* Universal representation of decay chains:
  - More documentation and testing.
  - Allow default class method `DecayMode.from_pdgids()` mimicking the default constructor `DecayMode()`.
  - Fix in logic of ``DecayChain.flatten()``.
  - `DecayChainViewer` class adapted to make use of ``graphviz``.
* Dependencies:
  - Got rid of dependency on ``pydot``, as the package is no longer maintained.
  - Replaced with dependency on ``graphviz``, made a requirement.
* Tests:
  - Check for some expected warnings, to get rid of obvious warnings.
* Miscellaneous:
  - Follow Scikit-HEP org guidelines for code development and packaging.

## Version 0.10.3 (2021-03-23)

* Miscellaneous:
  - Code refactored in the CI by Sourcery.ai.
  - Updates to versions of pre-commit hooks.

## Version 0.10.2 (2021-01-19)

* Parsing of decay files (aka .dec files):
  - New decay models as taken from most-recent EvtGen documentation.

## Version 0.10.1 (2020-12-10)

* Environment YAML file updated to ``Particle`` version 0.14.

## Version 0.10.0 (2020-12-10)

* Dependencies:
  - Package dependent on ``Particle`` version 0.14.
* Miscellaneous:
  - Pre-commit hooks added - Black formatting, check-manifest, etc.

## Version 0.9.1 (2020-11-04)

* Parsing of decay files (aka .dec files):
  - ``DecFileParser`` class enhanced to understand EvtGen's CopyDecay statement in decay files.
* Tests:
  - Added tests for Python 3.8 and 3.9 on Windows.
* Miscellaneous:
  - Conda badge added to the README, since package now available in Conda.

## Version 0.9.0 (2020-10-31)

* Dependencies and Python version support:
  - Package dependent on ``Particle`` version 0.13.
  - Support for Python 3.9 added.

## Version 0.8.0 (2020-09-29)

* Dependencies:
  - Package dependent on ``Particle`` version 0.12.

## Version 0.7.0 (2020-08-13)

* Dependencies:
  - Package dependent on ``Particle`` version 0.11.
  - Dependencies on `lark-parser` and others upgraded.


## Version 0.6.2 (2020-06-05)

* Dependencies:
  - Package dependency on ``pydot`` made a requirement.


## Version 0.6.1 (2020-01-15)

* Parsing of decay files (aka .dec files):
  - Simplifications in various methods of class ``DecFileParser``.
  - A couple more tests added.
* Minor fixes.


## Version 0.6.0 (2020-01-10)

* Parsing of decay files (aka .dec files):
  - Master Belle II DECAY.DEC file added to the package.
  - Certain ``DecFileParser`` class methods made more versatile.
  - ``Lark`` parsing grammar file improved.
* Universal representation of decay chains:
  - Classes ``DecayChain``, ``DecayMode``, ``DaughtersDict`` and ``DecayChainViewer`` enhanced.
* Dependencies and Python version support:
  - Package dependent on ``Particle`` versions 0.9.
  - Support for Python 3.8 added.


## Version 0.5.3 (2019-10-28)

* Dict-like representation of particle decay chains improved.
* Documentation added to README.


## Version 0.5.2 (2019-10-23)

* Parsing of decay files (aka .dec files):
  - New Belle II decay models added.
* README updated to provide basic coverage of recent new features.
* Clean-up of obsolete files.


## Version 0.5.1 (2019-10-14)

* Universal representation of decay chains:
  - Classes ``DecayChain`` and ``DecayMode`` enhanced.
  - Tests for class ``DecayChain`` added.
* Parsing of decay files (aka .dec files):
  - ``DecFileParser`` class extended.


## Version 0.5.0 (2019-10-11)

* Universal representation of decay chains:
  - Class ``DecayChain`` introduced.
  - Classes ``DaughtersDict`` and ``DecayMode`` enhanced.
* Changes in API:
  - ``DecFileParser.build_decay_chain()`` renamed to ``DecFileParser.build_decay_chains()``.
* Package dependent on ``Particle`` package version 0.6.


## Version 0.4.0 (2019-09-02)

* Package dependent on ``Particle`` version 0.6.0.
  Otherwise identical to version 0.3.2.


## Version 0.3.2 (2019-08-29)

* Parsing of decay files (aka .dec files):
  - ``DecFileParser`` class extended to understand JETSET definitions.
* Visualisation of decay chains:
  - ``DecayChainViewer`` class simplified and improved.
  - Decay chain DOT graphs now display HTML particle names.
  - More tests.


## Version 0.3.1 (2019-07-18)

* Parsing of decay files (aka .dec files):
  - Update to latest LHCb DECAY.DEC file.
* Visualisation of decay chains:
  - ``DecayChainViewer`` class made more robust.
  - Better tests.
* Miscellaneous:
  - Demo notebook updated.
  - README updated with latest package functionality.
  - Python wheels generation added.
  - Zenodo DOI badge added to README.


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
  - Copyright statements added to repository files.
  - General clean-up and minor bug fixes.


## Version 0.2.0 (2018-08-02)

* First release as part of Scikit-HEP.
* Using new data package with ``importlib_resources`` (or ``importlib.resources`` on Python 3.7).
* Better docs and examples.
* Some method renaming.
* Generalized converter script.


## Version 0.1.0 (2018-03-13)

* First release on PyPI.
