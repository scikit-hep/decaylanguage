=====
Usage
=====

Particles are a key component when dealing with decays.
Refer to the [particle package](https://github.com/scikit-hep/particle) for how to deal with particles and PDG identification codes.

The primary way to use `decaylanguage.decay` is through the module provided to read in a language file and produce an output. For example, for GooFit, call:

.. code-block:: bash

    python -m decaylanguage.goofit models/DtoKpipipi_v2.txt

You can pipe the output to a file.

Examples of interaction with the API directly are provided in the ``/notebooks`` folder, including svg diagrams of lines.
