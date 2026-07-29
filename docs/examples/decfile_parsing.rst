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

   # Build the full decay chain for a particle
   chain = parser.build_decay_chains("D*+")

Charge conjugation
------------------

By default, charge-conjugated decays are automatically included. This behavior
can be controlled at parse time.

For more detailed examples, see the :doc:`/examples/notebooks/index` section.

.. _decfile-command-line-validation:

Command-line validation
-----------------------

EvtGen ``.dec`` files can be validated without writing Python code
with a provided script:

.. code-block:: bash

   decaylanguage-validate my-decay-file.dec
   decaylanguage-validate path/to/decfiles-directory

Experiment-specific and decay models not yet available in the package can be enabled by repeating
``--additional-decay-model`` as needed:

.. code-block:: bash

   decaylanguage-validate --additional-decay-model=MYMODEL my-decay-file.dec

The validator reports stable diagnostic codes. Exact codes such as ``DLW004``
or code families such as ``DLW`` can be disabled, which lets experiments choose
their own validation policy:

.. code-block:: bash

   decaylanguage-validate --ignore=DLW004 my-decay-file.dec
   decaylanguage-validate --ignore=DLW my-decay-file.dec

Use ``decaylanguage-validate --list-diagnostics`` to inspect the currently
available diagnostics, which are the following:

.. list-table::
   :header-rows: 1

   * - Code
     - Name
     - Meaning
   * - ``DLP001``
     - ``parse-error``
     - The file could not be read or parsed by ``DecFileParser``.
   * - ``DLW001``
     - ``duplicate-decay``
     - A particle has multiple ``Decay`` blocks; only the first is retained.
   * - ``DLW002``
     - ``missing-copydecay-source``
     - A ``CopyDecay`` statement references a missing ``Decay`` source.
   * - ``DLW003``
     - ``decay-cdecay-conflict``
     - A particle is defined with both ``Decay`` and ``CDecay``; ``CDecay`` is ignored.
   * - ``DLW004``
     - ``missing-cdecay-source``
     - A ``CDecay`` statement has no corresponding ``Decay`` source.
   * - ``DLW005``
     - ``self-conjugate-cdecay``
     - A ``CDecay`` statement targets a self-conjugate particle.
   * - ``DLW006``
     - ``duplicate-cdecay``
     - A particle has multiple ``CDecay`` statements; only the first is retained.
   * - ``DLW999``
     - ``parser-warning``
     - An otherwise unclassified warning was emitted by ``DecFileParser``.

Parser errors include the source location and a pointer:

.. code-block:: text

   DecayLanguage: 1 diagnostic(s) in 1 file(s)
   tests/data/test_issue90.dec:13:68: DLP001 parse-error: UnexpectedToken: Unexpected token Token('SIGNED_NUMBER', '2') at line 13, column 68.
          13: 0.000044342 Upsilon pi0     pi0                             VVPIPI;2 #[Reconstructed PDG2011]
                                                                                 ^
   summary: DLP001=1

Parser warnings are reported more compactly:

.. code-block:: text

   DecayLanguage: 2 diagnostic(s) in 1 file(s)
   tests/data/duplicate-decays.dec: DLW001 duplicate-decay: duplicate Decay block(s): Sigma(1775)0; later definitions ignored
   tests/data/duplicate-decays.dec: DLW003 decay-cdecay-conflict: both Decay and CDecay defined: anti-Sigma(1775)0; CDecay ignored
   summary: DLW001=1, DLW003=1

By default, at most 100 diagnostics are printed before the remaining diagnostics
are summarized. Pass ``--max-diagnostics=0`` to print every diagnostic.

Pre-commit hook
^^^^^^^^^^^^^^^

Downstream projects can run the same validator automatically with the packaged
pre-commit hook:

.. code-block:: yaml

   - repo: https://github.com/scikit-hep/decaylanguage
     rev: <version>
     hooks:
       - id: decaylanguage-validate

The hook accepts the same options as the command-line validator. For example,
experiments can ignore exact diagnostic codes or whole code families:

.. code-block:: yaml

   - id: decaylanguage-validate
     args: ["--ignore=DLW004"]

To ignore a whole diagnostic family, use the family prefix:

.. code-block:: yaml

   - id: decaylanguage-validate
     args: ["--ignore=DLW"]

Use ``decaylanguage-validate --list-diagnostics`` to list the available
diagnostics.
