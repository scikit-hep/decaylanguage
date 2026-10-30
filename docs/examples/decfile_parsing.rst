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

Unknown decay model names and undefined ``ModelAlias`` names produce a
``DLP001`` diagnostic with the name, source location, and instructions for
registering a custom model. When using Python, these errors inherit from
:class:`~decaylanguage.dec.dec.DecayModelError`, a ``ValueError`` subclass.
:class:`~decaylanguage.dec.dec.UnknownDecayModelError` identifies a model name
that cannot be resolved. Register a custom model before parsing:

.. code-block:: python

   parser = DecFileParser("my-decay-file.dec")
   parser.load_additional_decay_models("MYMODEL")
   parser.parse()

An unregistered model with parameters can be indistinguishable from daughter
particle names in the decfile grammar. These lines raise
:class:`~decaylanguage.dec.dec.AmbiguousDecayModelError` with registration
guidance, without suggesting that a parameter should be registered as a model.
A line missing its model can also produce this diagnostic. Registering the
intended model before parsing establishes its boundary. The parser accepts
experiment-specific daughter names and string-valued parameters for registered
models; it does not validate every daughter name against the particle table.

All ``ModelAlias`` definitions are checked, including unused definitions.
References between aliases are resolved, while cyclic references and additional
parameters on an alias reference raise
:class:`~decaylanguage.dec.dec.InvalidModelAliasError`. Define such aliases
directly using the registered model and its parameters.

Model errors expose ``model_name`` (``None`` for ambiguous input), ``line``,
``column``, and ``path`` (``None`` for string input). File locations refer to the
original input, including when intermediate ``End`` lines are ignored or several
files are parsed together. These exceptions can be serialized with ``pickle``.

To contribute a standard model, add its name to ``known_decay_models`` in
`src/decaylanguage/dec/enums.py <https://github.com/scikit-hep/decaylanguage/blob/main/src/decaylanguage/dec/enums.py>`_
and add a parsing test following the existing model tests.

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
     - ``duplicate-cdecay``
     - A particle has multiple ``CDecay`` statements; only the first is retained.
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
     - ``missing-copydecay-source``
     - A ``CopyDecay`` statement references a missing ``Decay`` source.
   * - ``DLW010``
     - ``misconfigured-alias``
     - An `Alias` statement is misleading/misconfigured.
   * - ``DLW011``
     - ``misconfigured-chargeconj``
     - A `ChargeConj` statement is misleading/misconfigured.
   * - ``DLW012``
     - ``self-conjugate-chargeconj``
     - A ``ChargeConj`` statement targets a non-alias self-conjugate particle.
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

For example, suppose ``decays/pi0.dec`` uses an unregistered model:

.. code-block:: text

   Decay pi0
   1.0 gamma gamma MYMODEL;
   Enddecay
   End

The hook fails and includes the following validator output. The long diagnostic
is wrapped here for readability:

.. code-block:: text

   DecayLanguage: 1 diagnostic(s) in 1 file(s)
   decays/pi0.dec:2:17: DLP001 parse-error: UnknownDecayModelError: Unknown decay model or undefined
     ModelAlias 'MYMODEL'. Check the spelling or define a ModelAlias in the decay file. For a custom
     model, call load_additional_decay_models('MYMODEL') before parse(), or pass
     --additional-decay-model=MYMODEL to decaylanguage-validate. To add a standard model to
     DecayLanguage's model registry, update known_decay_models in src/decaylanguage/dec/enums.py
     (https://github.com/scikit-hep/decaylanguage/blob/main/src/decaylanguage/dec/enums.py).
          2: 1.0 gamma gamma MYMODEL;
                             ^
   summary: DLP001=1

After checking the spelling and any ``ModelAlias`` definition, enable an
experiment-specific model by adding the registration option to the hook:

.. code-block:: yaml

   - id: decaylanguage-validate
     args: ["--additional-decay-model=MYMODEL"]

This example then passes validation. For a standard model missing from the
default registry, follow the contribution guidance above.

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
