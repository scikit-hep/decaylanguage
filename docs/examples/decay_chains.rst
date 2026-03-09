============
Decay chains
============

The :mod:`decaylanguage.decay` module provides classes for building and visualizing
decay chains programmatically.

Building a decay chain
----------------------

.. code-block:: python

   from decaylanguage import DecayMode, DecayChain, DecayChainViewer

   # Define individual decay modes with branching fractions
   dm1 = DecayMode(0.0263, "D0 pi+")
   dm2 = DecayMode(0.0391, "K- pi+")

   # Build the full chain
   dc = DecayChain("D*+", {"D*+": dm1, "D0": dm2})

Visualization
-------------

Decay chains can be visualized using Graphviz:

.. code-block:: python

   dcv = DecayChainViewer(dc)

   # In Jupyter, simply display the object
   dcv

   # Or export to a file
   dcv.graph.render("my_decay", format="png")

The :class:`~decaylanguage.decay.decay.DaughtersDict` class (a specialized
:class:`~collections.Counter`) represents final-state particle multiplicities.

For more detailed examples, see the :doc:`/examples/notebooks/index` section.
