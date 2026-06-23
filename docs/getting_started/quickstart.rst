==========
Quickstart
==========

DecayLanguage provides tools for describing, parsing, and visualizing particle decays.
The three main areas are:

Parsing ``.dec`` decay files
----------------------------

Use :class:`~decaylanguage.dec.dec.DecFileParser` to parse EvtGen-format ``.dec`` files:

.. code-block:: python

   from decaylanguage import DecFileParser

   parser = DecFileParser("my_decays.dec")
   parser.parse()

   # List all decay mother particles
   parser.list_decay_mother_names()

   # Get decay modes for a specific particle
   parser.list_decay_modes("D+")

See :doc:`/examples/decfile_parsing` for more details.

Validate ``.dec`` files from the command line:

.. code-block:: bash

   decaylanguage-validate my_decays.dec
   decaylanguage-validate path/to/decfiles-directory

Use ``decaylanguage-validate --list-diagnostics`` to list selectable
diagnostic codes. Downstream pre-commit hooks can disable experiment-specific
codes with options such as ``--ignore=DLW004``.

On failure, pre-commit shows output such as:

.. code-block:: text

   tests/data/example.dec: DLW004 missing-cdecay-source: missing Decay source for CDecay: anti-B0sig
   summary: DLW004=1

Building and visualizing decay chains
-------------------------------------

Use :class:`~decaylanguage.decay.decay.DecayMode` and
:class:`~decaylanguage.decay.decay.DecayChain` to construct and visualize decay chains:

.. code-block:: python

   from decaylanguage import DecayMode, DecayChain, DecayChainViewer

   dm1 = DecayMode(0.5, "K- pi+ pi+ pi0")
   dm2 = DecayMode(0.5, "K+ pi- pi- pi0")
   dm3 = DecayMode(1.0, "D+ D-")
   dc = DecayChain("B0", {"D+": dm1, "D-": dm2, "B0": dm3})

   # Visualize the chain
   dcv = DecayChainViewer(dc)
   dcv  # renders in Jupyter

See :doc:`/examples/decay_chains` for more details.

Amplitude models
----------------

The :mod:`~decaylanguage.modeling` module supports parsing AmpGen amplitude model files
and converting them to GooFit format:

.. code-block:: bash

   python -m decaylanguage.goofit models/DtoKpipipi_v2.txt

See :doc:`/examples/amplitude_models` for more details.
