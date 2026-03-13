================
Amplitude models
================

The :mod:`decaylanguage.modeling` module provides tools for working with amplitude
model descriptions, specifically for converting between AmpGen and GooFit formats.

Command-line conversion
-----------------------

Convert an AmpGen model file to GooFit format:

.. code-block:: bash

   python -m decaylanguage.goofit models/DtoKpipipi_v2.txt

You can pipe the output to a file:

.. code-block:: bash

   python -m decaylanguage.goofit models/DtoKpipipi_v2.txt > output.cu

API usage
---------

.. code-block:: python

   from decaylanguage.modeling.amplitudechain import AmplitudeChain

   lines = AmplitudeChain.read_ampgen("models/DtoKpipipi_v2.txt")

For a detailed walkthrough, see the :doc:`/examples/notebooks/index` section.
