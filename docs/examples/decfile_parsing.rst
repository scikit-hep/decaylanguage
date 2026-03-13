======================
Parsing ``.dec`` files
======================

The :class:`~decaylanguage.dec.dec.DecFileParser` class provides a full parser
for EvtGen-format ``.dec`` decay files used by LHCb, Belle II, and other experiments.

Basic usage
-----------

.. jupyter-execute::

   from decaylanguage import DecFileParser
   from decaylanguage.data import basepath

   # Parse the bundled LHCb decay file
   parser = DecFileParser(basepath / "DECAY_LHCB.DEC")
   parser.parse()

   # List all mother particles with defined decays
   parser.list_decay_mother_names()[:10]

.. jupyter-execute::

   # Get decay modes for a specific particle
   parser.list_decay_modes("D*+")

.. jupyter-execute::

   # Get branching fractions
   parser.print_decay_modes("D*+")

Building decay chains
---------------------

.. jupyter-execute::

   # Access the decay model information
   parser.list_decay_mode_details("D*+")

Charge conjugation
------------------

By default, charge-conjugated decays are automatically included. This behavior
can be controlled at parse time.

For more detailed examples, see the :doc:`/examples/notebooks/index` section.
