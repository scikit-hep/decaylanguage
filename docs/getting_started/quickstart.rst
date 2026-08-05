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

On failure, the validator prints output such as:

.. code-block:: text

   DecayLanguage: 2 diagnostic(s) in 1 file(s)
   tests/data/duplicate-decays.dec: DLW001 duplicate-decay: duplicate Decay block(s): Sigma(1775)0; later definitions ignored
   tests/data/duplicate-decays.dec: DLW003 decay-cdecay-conflict: both Decay and CDecay defined: anti-Sigma(1775)0; CDecay ignored
   summary: DLW001=1, DLW003=1

Use ``decaylanguage-validate --list-diagnostics`` to list the available
diagnostics. For diagnostic options and the packaged pre-commit hook, see
:ref:`the detailed validation guide <decfile-command-line-validation>`.

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
