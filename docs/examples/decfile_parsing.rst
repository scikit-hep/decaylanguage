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

Command-line validation
-----------------------

EvtGen ``.dec`` files can be validated without writing Python code:

.. code-block:: bash

   decaylanguage-validate my-decay-file.dec
   decaylanguage-validate path/to/decfiles-directory

The validator reports stable diagnostic codes. Exact codes or code families can
be disabled, which lets experiments choose their own pre-commit policy:

.. code-block:: bash

   decaylanguage-validate --ignore=DLW004 my-decay-file.dec

Use ``decaylanguage-validate --list-diagnostics`` to inspect the currently
available diagnostics.

Available diagnostics:

.. list-table::
   :header-rows: 1

   * - Code
     - Name
     - Meaning
   * - ``DLP001``
     - ``parse-error``
     - The file could not be parsed by ``DecFileParser``.
   * - ``DLW001``
     - ``duplicate-decay``
     - A particle has multiple ``Decay`` blocks; only the first is retained.
   * - ``DLW002``
     - ``missing-copydecay-source``
     - A ``CopyDecay`` statement references a missing ``Decay`` source.
   * - ``DLW003``
     - ``duplicate-cdecay``
     - A particle is defined with both ``Decay`` and ``CDecay``; ``CDecay`` is ignored.
   * - ``DLW004``
     - ``missing-cdecay-source``
     - A ``CDecay`` statement has no corresponding ``Decay`` source.
   * - ``DLW005``
     - ``self-conjugate-cdecay``
     - A ``CDecay`` statement targets a self-conjugate particle.
   * - ``DLW999``
     - ``parser-warning``
     - An otherwise unclassified warning was emitted by ``DecFileParser``.

When run through pre-commit, failures include the validator output. Parser
errors include the source location and a pointer:

.. code-block:: text

   Validate EvtGen decay files..............................................Failed
   - hook id: decaylanguage-validate
   - exit code: 1

   DecayLanguage: 1 diagnostic(s) in 1 file(s)
   tests/data/broken.dec:13:68: DLP001 parse-error: UnexpectedToken: Unexpected token Token('SIGNED_NUMBER', '2') at line 13, column 68.
          13: 0.000044342 Upsilon pi0     pi0                             VVPIPI;2 #[Reconstructed PDG2011]
                                                                                ^
   summary: DLP001=1

Parser warnings are reported more compactly:

.. code-block:: text

   tests/data/example.dec: DLW004 missing-cdecay-source: missing Decay source for CDecay: anti-B0sig
   summary: DLW004=1

By default, at most 100 diagnostics are printed before the remaining diagnostics
are summarized. Pass ``--max-diagnostics=0`` to print every diagnostic.

Downstream projects can use the packaged pre-commit hook:

.. code-block:: yaml

   - repo: https://github.com/scikit-hep/decaylanguage
     rev: <version>
     hooks:
     - id: decaylanguage-validate
       args: ["--ignore=DLW004"]

For more detailed examples, see the :doc:`/examples/notebooks/index` section.
