DecayLanguage data folder contents
==================================

You can ``import decaylanguage.data``, then use ``decaylanguage.data.joinpath(<A_FILE>).open()``
to access data reliably regardless of how you have installed or are running the package (even from a zip file!).


``DECAY_LHCB.DEC``
------------------

Copy of the LHCb experiment master decay file for EvtGen, which describes
all generic particle decays.


``decfile.lark``
----------------
Lark parser grammar definition file for parsing .dec decay files.


``MintDalitzSpecialParticles.fwf``
----------------------------------

An extended PDG data file, prepared by this package's maintainers,
for the definitions of special particles used by the Mint program.
It is similar to the extended PDG data file ``mass_width_2008.fwf``, see
https://github.com/scikit-hep/particle/blob/master/particle/data/README.rst.


``MintDalitzSpecialParticlesLatex.csv``
---------------------------------------

A list of PDG IDs and LaTeX names for the special Mint program particles
defined in the file above.


``MintDalitzSpecialParticles.csv``
----------------------------------

The combined data file of special particles used by the Mint program,
in a format that is easy for the ``Particle`` class
to read and easy for physicists to extend or edit.

To regenerate the file from the fixed width file
``MintDalitzSpecialParticles.fwf`` run

.. code-block:: bash

    $ python -m particle.particle.convert extended \
        decaylanguage/data/MintDalitzSpecialParticles.fwf \
        decaylanguage/data/MintDalitzSpecialParticlesLatex.csv \
        decaylanguage/data/MintDalitzSpecialParticles.csv
