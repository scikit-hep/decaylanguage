=====
Usage
=====


To use `decaylanguage.particle` in a project::

    from decaylanguage.particle import Particle
    pi = Particle.from_pdg(211)


You can search for particles easily using `Particle.from_search` or `Particle.from_search_list`, where the first one will return an error if more than one particle matches the search criteria, and the second returns a list of all candidates. Lower-case search terms ``name`` and ``latex`` can be partial matches, ``name_re`` and ``latex_re`` are regular expression, and the rest of the terms are exact matches only.

The primary way to use `decaylanguage.decay` is through the module provided to read in a language file and produce an output. For example, for GooFit, call:

.. code-block:: bash

    python -m decaylanguage.goofit models/DtoKpipipi_v2.txt

You can pipe the output to a file.

Examples of interaction with the API directly are provided in the ``/notebooks`` folder, including svg diagrams of lines.


