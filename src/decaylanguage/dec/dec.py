# Copyright (c) 2018-2023, Eduardo Rodrigues and Henry Schreiner.
#
# Distributed under the 3-clause BSD license, see accompanying file LICENSE
# or https://github.com/scikit-hep/decaylanguage for details.

"""
Submodule with classes and utilities to deal with and parse .dec decay files.

Basic assumptions
-----------------

1) For standard particle names *not defined* via aliases:
    - Decay modes defined via a 'Decay' statement.
    - Related antiparticle decay modes either defined via a 'CDecay' statement
      or via a 'Decay' statement. The latter option is often used if CP matters.

2) For particle names defined via aliases:
    - Particle decay modes defined as above.
    - Related antiparticle decay modes defined with either options above,
      *but* there needs to be a 'ChargeConj' statement specifying the
      particle-antiparticle match. Typically::

        Alias MyP+ P+
        Alias MyP- P-
        ChargeConj MyP+ MyP-
        Decay MyP+
        ...
        Enddecay
        CDecay MyP-

3) As a consequence, particles that are self-conjugate should not be used
   in 'CDecay' statements, obviously.

4) Decays defined via a 'CopyDecay' statement are simply (deep) copied
   and no copy of the corresponding antiparticle is performed unless explicitly requested
   with another 'CopyDecay' statement.
"""


from __future__ import annotations

import copy
import operator
import os
import re
import warnings
from io import StringIO
from itertools import chain, zip_longest
from pathlib import Path
from typing import Any, Callable, Iterable

from lark import Lark, Token, Transformer, Tree, Visitor
from lark.lexer import TerminalDef
from particle import Particle
from particle.converters import PDG2EvtGenNameMap

from .. import data
from .._compat.typing import Self
from ..decay.decay import DecayModeDict, _expand_decay_modes
from ..utils import charge_conjugate_name
from .enums import PhotosEnum, known_decay_models


class DecFileNotParsed(RuntimeError):
    pass


class DecayNotFound(RuntimeError):
    pass


class DecFileParser:
    """
    The class to parse a .dec decay file.

    Example
    -------
    >>> dfp = DecFileParser('my-decay-file.dec')    # doctest: +SKIP
    >>> dfp.parse()    # doctest: +SKIP
    """

    __slots__ = (
        "_grammar",
        "_grammar_info",
        "_dec_file_names",
        "_dec_file",
        "_parsed_dec_file",
        "_parsed_decays",
        "_include_ccdecays",
        "_additional_decay_models",
    )

    def __init__(self, *filenames: str | os.PathLike[str]) -> None:
        """
        Default constructor. Parse one or more .dec decay files.

        Parameters
        ----------
        filenames: non-keyworded variable length argument
            Input .dec decay file name(s).
        """
        self._grammar: str | None = None  # Loaded Lark grammar definition file
        self._grammar_info: None | (
            dict[str, Any]
        ) = None  # Name of Lark grammar definition file

        # Name(s) of the input decay file(s)
        if filenames:
            self._dec_file_names = list(filenames)

            stream = StringIO()
            for filename in map(Path, self._dec_file_names):
                # Check input file
                if not filename.is_file():
                    raise FileNotFoundError(f"{str(filename)!r}!")

                with filename.open(encoding="utf_8") as file:
                    for line in file:
                        # We need to strip the unicode byte ordering if present before checking for *
                        beg = line.lstrip("\ufeff").lstrip()
                        # Make sure one discards all lines "End"
                        # in intermediate files, to avoid a parsing error
                        if not (
                            beg.startswith("End") and not beg.startswith("Enddecay")
                        ):
                            stream.write(line)
                    stream.write("\n")

            stream.seek(0)
            # Content of input file(s)
            self._dec_file = stream.read()
        else:
            self._dec_file_names = []
            self._dec_file = None  # type: ignore[assignment]

        self._parsed_dec_file: Tree | None = None  # Parsed decay file
        self._parsed_decays: None | (
            Any
        ) = None  # Particle decays found in the decay file

        self._additional_decay_models: None | Iterable[
            str
        ] = None  # Additional decay models not (yet) known to DecayLanguage

        # By default, consider charge-conjugate decays when parsing
        self._include_ccdecays = True

    @classmethod
    def from_string(cls, filecontent: str) -> Self:
        """
        Constructor from a .dec decay file provided as a multi-line string.

        Parameters
        ----------
        filecontent: str
            Input .dec decay file content.
        """
        stream = StringIO(filecontent)
        stream.seek(0)

        _cls = cls()
        _cls._dec_file_names = ["<dec file input as a string>"]
        _cls._dec_file = stream.read()

        return _cls

    def parse(self, include_ccdecays: bool = True) -> None:
        """
        Parse the given .dec decay file(s) according to the default Lark parser
        and specified options.

        Use the method `load_additional_decay_models` before `parse` to load decay models
        that might not yet be available in DecayLanguage.

        Parameters
        ----------
        include_ccdecays: boolean, optional, default=True
            Choose whether or not to consider charge-conjugate decays,
            which are specified via "CDecay <MOTHER>".
            Make sure you understand the consequences of ignoring
            charge conjugate decays - you won't have a complete picture otherwise!
        """
        # Has a file been parsed already?
        if self._parsed_decays is not None:
            warnings.warn("Input file being re-parsed ...", stacklevel=2)

        # Override the parsing settings for charge conjugate decays
        self._include_ccdecays = include_ccdecays or False

        # Retrieve all info on the default Lark grammar and its default options,
        # effectively loading it
        opts = self.grammar_info()
        extraopts = {
            k: v
            for k, v in opts.items()
            if k not in ("lark_file", "parser", "lexer", "edit_terminals")
        }

        # Instantiate the Lark parser according to chosen settings
        parser = Lark(
            self.grammar(),
            parser=opts["parser"],
            lexer=opts["lexer"],
            edit_terminals=opts["edit_terminals"],
            **extraopts,
        )
        self._parsed_dec_file = parser.parse(self._dec_file)

        # At last, find all particle decays defined in the .dec decay file ...
        self._find_parsed_decays()
        # Replace model aliases with the actual models and model parameters. Deepcopy to avoid modification of dict by
        # DecayModelParamValueReplacement Visitor.
        dict_model_aliases = copy.deepcopy(self._dict_raw_model_aliases())
        self._parsed_decays = [
            DecayModelAliasReplacement(model_alias_defs=dict_model_aliases).transform(
                tree
            )
            for tree in self._parsed_decays
        ]

        # Check whether certain decay model parameters are defined via
        # variable names with actual values provided via 'Define' statements,
        # and perform the replacements name -> value where relevant.
        # Do also a replacement of 'a_float' with a_float.
        dict_define_defs = self.dict_definitions()
        for tree in self._parsed_decays:
            DecayModelParamValueReplacement(define_defs=dict_define_defs).visit(tree)
        # Create on the fly the decays to be copied, if requested
        if self.dict_decays2copy():
            self._add_decays_to_be_copied()

        # Create on the fly the charge conjugate decays, if requested
        if self._include_ccdecays:
            self._add_charge_conjugate_decays()

    def grammar(self) -> str:
        """
        Access the internal Lark grammar definition file,
        effectively loading the default grammar with default parsing options
        if no grammar has been loaded before.

        Returns
        -------
        out: str
            The Lark grammar definition file.
        """
        if not self.grammar_loaded:
            self._load_grammar()

        return self._grammar  # type: ignore[return-value]

    def grammar_info(self) -> dict[str, Any]:
        """
        Access the internal Lark grammar definition file name and
        parser options, effectively loading the default grammar
        with default parsing options if no grammar has been loaded before.

        Returns
        -------
        out: dict
            The Lark grammar definition file name and parser options.
        """
        if not self.grammar_loaded:
            self._load_grammar()
        assert self._grammar_info is not None

        return self._grammar_info

    def load_grammar(
        self,
        filename: str | None = None,
        parser: str = "lalr",
        lexer: str = "auto",
        **options: Any,
    ) -> None:
        """
        DEPRECATED, please use "`load_additional_decay_models`" instead.

        Load a Lark grammar definition file, either the default one,
        or a user-specified one, optionally setting Lark parsing options.

        Parameters
        ----------
        filename: str, optional, default=None
            Input .dec decay file name. By default 'data/decfile.lark' is loaded.
        parser: str, optional, default='lalr'
            The Lark parser engine name.
        lexer: str, optional, default='auto'
            The Lark parser lexer mode to use.
        options: keyword arguments, optional
            Extra options to pass on to the parsing algorithm.

        See Lark's Lark class for a description of available options
        for parser, lexer and options.
        """

        warnings.warn(
            "This method is deprecated, please add unknown decay models by passing them to "
            "`load_additional_decay_models` instead before parsing the decayfile.",
            DeprecationWarning,
            stacklevel=2,
        )

        if filename is None:
            filename = "decfile.lark"

        self._load_grammar(filename, parser, lexer, **options)

    def load_additional_decay_models(self, *models: str) -> None:
        """
        Add one or more EvtGen decay models in addition to the ones already provided via
        `decaylanguage.dec.enums.known_decay_models`.

        Parameters
        ----------
        models: str
            names of the additional decay models to be considered.
        """

        if self._additional_decay_models is None:
            self._additional_decay_models = models
        else:
            self._additional_decay_models = chain.from_iterable(
                (self._additional_decay_models, models)
            )

    def _load_grammar(
        self,
        filename: str = "decfile.lark",
        parser: str = "lalr",
        lexer: str = "auto",
        **options: Any,
    ) -> None:
        """
        Load the default Lark grammar definition file with default parser and lexer.

        Parameters
        ----------
        filename: str, optional, default='decfile.lark'
            The Lark grammar file name.
        parser: str, optional, default='lalr'
            The Lark parser engine name.
        lexer: str, optional, default='auto'
            The Lark parser lexer mode to use.
        options: keyword arguments, optional
            Extra options to pass on to the parsing algorithm.
        """

        with data.basepath.joinpath(filename).open() as f1:
            self._grammar = f1.read()

        self._grammar_info = dict(
            lark_file=filename,
            parser=parser,
            lexer=lexer,
            edit_terminals=self._generate_edit_terminals_callback(),
            **options,
        )

    def _generate_edit_terminals_callback(self) -> Callable[[TerminalDef], None]:
        """
        This closure creates the callback used by Lark to modify the grammar terminals
        and inject the names of the EvtGen models.
        """

        if self._additional_decay_models is None:
            decay_models = known_decay_models  # type: tuple[str, ...]
        else:
            decay_models = tuple(
                chain.from_iterable([known_decay_models, self._additional_decay_models])
            )

        def edit_model_name_terminals(t: TerminalDef) -> None:
            """
            Edits the terminals of the grammar to replace the model name placeholder with the actual names of the models,
            see `Model_NAME_PLACEHOLDER` in the default grammar file `decaylanguage/data/decfile.lark`.
            The decay models are sorted by length and escaped to match the default Lark behavior.
            """

            modelstr = rf"(?:{'|'.join(re.escape(dm) for dm in sorted(decay_models, key=len, reverse=True))})"
            if t.name == "MODEL_NAME":
                t.pattern.value = t.pattern.value.replace(
                    "MODEL_NAME_PLACEHOLDER", modelstr
                )

        return edit_model_name_terminals

    @property
    def grammar_loaded(self) -> bool:
        """
        Check to see if the Lark grammar definition file is loaded.
        """
        return self._grammar is not None

    def dict_decays2copy(self) -> dict[str, str]:
        """
        Return a dictionary of all statements in the input parsed file
        defining a decay to be copied, of the form
        "CopyDecay <NAME> <DECAY_TO_COPY>",
        as {'NAME1': DECAY_TO_COPY1, 'NAME2': DECAY_TO_COPY2, ...}.
        """
        self._check_parsing()
        return get_decays2copy_statements(self._parsed_dec_file)

    def dict_definitions(self) -> dict[str, float]:
        """
        Return a dictionary of all definitions in the input parsed file,
        of the form "Define <NAME> <VALUE>",
        as {'NAME1': VALUE1, 'NAME2': VALUE2, ...}.
        """
        self._check_parsing()
        return get_definitions(self._parsed_dec_file)

    def dict_model_aliases(self) -> dict[str, list[str]]:
        """
        Return a dictionary of all model alias definitions in the input parsed file,
        of the form "ModelAlias <NAME> <MODEL>",
        as as {'NAME1': [MODEL_NAME, MODEL_OPTION1, MODEL_OPTION2,...],}.
        """
        self._check_parsing()
        return get_model_aliases(self._parsed_dec_file)

    def _dict_raw_model_aliases(self) -> dict[str, list[Token | Tree]]:
        """
        Return a dictionary of all model alias definitions in the input parsed file,
        of the form "ModelAlias <NAME> <MODEL>",
        as {'NAME1': MODELTREE1, 'NAME2': MODELTREE2, ...}.
        """
        self._check_parsing()
        assert self._parsed_dec_file is not None
        return {
            tree.children[0].children[0].value: copy.deepcopy(tree.children[1].children)
            for tree in self._parsed_dec_file.find_data("model_alias")
        }

    def dict_aliases(self) -> dict[str, str]:
        """
        Return a dictionary of all alias definitions in the input parsed file,
        of the form "Alias <NAME> <ALIAS>",
        as {'NAME1': ALIAS1, 'NAME2': ALIAS2, ...}.
        """
        self._check_parsing()
        return get_aliases(self._parsed_dec_file)

    def dict_charge_conjugates(self) -> dict[str, str]:
        """
        Return a dictionary of all charge conjugate definitions
        in the input parsed file, of the form
        "ChargeConj <PARTICLE> <CC_PARTICLE>", as
        {'PARTICLE1': CC_PARTICLE1, 'PARTICLE2': CC_PARTICLE2, ...}.
        """
        self._check_parsing()
        return get_charge_conjugate_defs(self._parsed_dec_file)

    def get_particle_property_definitions(self) -> dict[str, dict[str, float]]:
        """
        Return a dictionary of all particle property definitions
        in the input parsed file, of the form "Particle <PARTICLE> <MASS> <WIDTH>",
        as {'PARTICLE1': {'mass': MASS1, 'width': WIDTH1},
            'PARTICLE2': {'mass': MASS2, 'width': WIDTH2}, ...}.

        Note
        ----
        Particles are often defined via aliases and post-processing may be needed
        to match the mass and width to the actual particle.
        """
        self._check_parsing()
        return get_particle_property_definitions(self._parsed_dec_file)

    def dict_pythia_definitions(self) -> dict[str, dict[str, str | float]]:
        """
        Return a dictionary of all Pythia 8 commands
        "PythiaGenericParam" and/or "PythiaAliasParam" and/or "PythiaBothParam",
        with keys corresponding to the 3 types specifying whether the command is for
        generic decays, alias decays, or both.
        The commands are set in the input parsed file with statements of the form
        "Pythia<TYPE>Param <MODULE>:<PARAM>=<LABEL_OR_VALUE>.
        The dictionary takes the form
        {"PythiaAliasParam": {'<MODULE1>:<PARAM1>': 'LABEL1', '<MODULE1>:<PARAM2>': VALUE2, ...},
         "PythiaBothParam": {'<MODULE2>:<PARAM3>': 'LABEL3', '<MODULE3>:<PARAM4>': VALUE4, ...},
         "PythiaGenericParam": {'<MODULE4>:<PARAM5>': 'LABEL5', '<MODULE5>:<PARAM6>': VALUE6, ...}}.
        """
        self._check_parsing()
        return get_pythia_definitions(self._parsed_dec_file)

    def dict_jetset_definitions(self) -> dict[str, dict[int, int | float | str]]:
        """
        Return a dictionary of all JETSET definitions in the input parsed file,
        of the form
        "JetSetPar <MODULE>(<PARAMETER>)=<VALUE>"
        as
        {'MODULE1': {PARAMETER1: VALUE1, PARAMETER2: VALUE2, ...},
         'MODULE2': {...},
         ...}.
        """
        self._check_parsing()
        return get_jetset_definitions(self._parsed_dec_file)

    def expand_decay_modes(self, particle: str) -> list[str]:
        """
        Return a list of expanded decay descriptors for the given (mother) particle.
        The set of decay final states is effectively split and returned as a list.
        NB: this implicitly reverts aliases back to the original (EvtGen) names.
        """
        self._check_parsing()
        decay_chains = self.build_decay_chains(particle)
        aliases = self.dict_aliases()
        return _expand_decay_modes(decay_chains, aliases=aliases)

    def dict_lineshape_settings(self) -> dict[str, dict[str, str | float]]:
        """
        Return a dictionary of all lineshape settings,
        with keys corresponding to particle names or aliases, as
        {PARTICLE1: {'lineshape': 'NAME1',  # E.g. "LSFLAT" or "LSNONRELBW"
          'BlattWeisskopf': VALUE1,
          'ChangeMassMin': VALUE12,
          'ChangeMassMax': VALUE13},
         PARTICLE2: {'lineshape': 'NAME2',
          'BlattWeisskopf': VALUE2,
          'ChangeMassMin': VALUE22,
          'ChangeMassMax': VALUE23,
          'IncludeBirthFactor': TRUE_OR_FALSE,
          'IncludeDecayFactor': TRUE_OR_FALSE},
         ...
        }
        where not all "sub-dictionaries" may contain all and/or the same keys.
        """
        self._check_parsing()
        return get_lineshape_settings(self._parsed_dec_file)

    def list_lineshapePW_definitions(self) -> list[tuple[list[str], int]]:
        """
        Return a list of all SetLineshapePW definitions in the input parsed file,
        of the form
        "SetLineshapePW <MOTHER> <DAUGHTER1> <DAUGHTER2> <VALUE>",
        as
        [(['MOTHER1', 'DAUGHTER1-1', 'DAUGHTER1-2'], VALUE1),
        (['MOTHER2', 'DAUGHTER2-1', 'DAUGHTER2-2'], VALUE2),
        ...]
        """
        self._check_parsing()
        return get_lineshapePW_definitions(self._parsed_dec_file)

    def global_photos_flag(self) -> int:
        """
        Return a boolean-like PhotosEnum enum specifying whether or not PHOTOS
        has been enabled.

        Note: PHOTOS is turned on(off) for all decays with the global flag
        yesPhotos(noPhotos).

        Returns
        -------
        out: PhotosEnum, default=PhotosEnum.no
            PhotosEnum.yes / PhotosEnum.no if PHOTOS enabled / disabled
        """
        self._check_parsing()
        return get_global_photos_flag(self._parsed_dec_file)

    def list_charge_conjugate_decays(self) -> list[str]:
        """
        Return a (sorted) list of all charge conjugate decay definitions
        in the input parsed file, of the form "CDecay <MOTHER>", as
        ['MOTHER1', 'MOTHER2', ...].
        """
        self._check_parsing()
        return get_charge_conjugate_decays(self._parsed_dec_file)

    def _find_parsed_decays(self) -> None:
        """
        Find all decay definitions in the input parsed file,
        which are of the form "Decay <MOTHER>", and save them internally
        as a list of Lark Tree instances with Tree.data=='decay', i.e.,
        [Tree(decay, [Tree(particle, [Token(LABEL, <MOTHER1>]), ...),
        Tree(decay, [Tree(particle, [Token(LABEL, <MOTHER2>]), ...)].

        Duplicate definitions (a bug, of course) are removed, issuing a warning.

        Note
        ----
        1) Method not meant to be used directly!
        2) Charge conjugates need to be dealt with differently,
        see 'self._add_charge_conjugate_decays()'.
        """
        self._parsed_decays = get_decays(self._parsed_dec_file)

        # Check for duplicates - should be considered a bug in the .dec file!
        self._check_parsed_decays()

    def _add_decays_to_be_copied(self) -> None:
        """
        Create the copies of the Lark Tree instances of decays specified
        in the input parsed file via the statements of the form
        "CopyDecay <NAME> <DECAY_TO_COPY>".
        These are added to the internal list of decays stored in the class
        in variable 'self._parsed_decays'.

        Note
        ----
        1) There is no check that for a requested copy of non self-conjugate decay
           the copy of the corresponding antiparticle is also requested in the file!
           In other terms, only explicit copies are performed.
        2) Method not meant to be used directly!
        """
        decays2copy = self.dict_decays2copy()

        # match name -> position in list self._parsed_decays
        name2treepos = {
            t.children[0].children[0].value: i
            for i, t in enumerate(self._parsed_decays)  # type: ignore[arg-type]
        }

        # Make the copies taking care to change the name of the mother particle
        copied_decays = []
        misses = []
        for decay2copy, decay2becopied in decays2copy.items():
            try:
                match = self._parsed_decays[name2treepos[decay2becopied]]  # type: ignore[index]
                copied_decay = copy.deepcopy(match)
                copied_decay.children[0].children[0].value = decay2copy
                copied_decays.append(copied_decay)
            except Exception:
                misses.append(decay2copy)
        if misses:
            msg = """\nCorresponding 'Decay' statement for 'CopyDecay' statement(s) of following particle(s) not found:\n{}.
Skipping creation of these copied decay trees.""".format(
                "\n".join(misses)
            )

            warnings.warn(msg, stacklevel=2)

        # Actually add all these copied decays to the list of decays!
        self._parsed_decays.extend(copied_decays)  # type: ignore[union-attr]

    def _add_charge_conjugate_decays(self) -> None:
        """
        If requested (see the 'self._include_ccdecays' class attribute),
        create the Lark Tree instances describing the charge conjugate decays
        specified in the input parsed file via the statements of the form
        "CDecay <MOTHER>".
        These are added to the internal list of decays stored in the class
        in variable 'self._parsed_decays', performing a charge conjugate (CC)
        transformation on each CC-related decay, which is cloned.

        Note
        ----
        1) If a decay file only defines 'Decay' decays and no 'CDecay',
        then no charge conjugate decays will be created!
        This seems correct given the "instructions" in the decay file:
        - There is no 'CDecay' statement related to a 'Decay' statement
          for a self-conjugate decaying particle such as the pi0.
        - Else the decay file should be considered incomplete, hence buggy.
        2) Method not meant to be used directly!
        """

        # Do not add any charge conjugate decays if the input parsed file
        # does not define any!
        mother_names_ccdecays = self.list_charge_conjugate_decays()
        if len(mother_names_ccdecays) == 0:
            return

        # Cross-check - make sure charge conjugate decays are not defined
        # with both 'Decay' and 'CDecay' statements!
        mother_names_decays = [
            get_decay_mother_name(tree) for tree in self._parsed_decays  # type: ignore[union-attr]
        ]

        duplicates = [n for n in mother_names_ccdecays if n in mother_names_decays]
        if len(duplicates) > 0:
            str_duplicates = ", ".join(d for d in duplicates)
            msg = f"""The following particles are defined in the input .dec file with both 'Decay' and 'CDecay': {str_duplicates}!
The 'CDecay' definition(s) will be ignored ..."""
            warnings.warn(msg, stacklevel=2)

        # If that's the case, proceed using the decay definitions specified
        # via the 'Decay' statement, hence discard/remove the definition
        # via the 'CDecay' statement.
        for d in duplicates:
            mother_names_ccdecays.remove(d)

        # We're done if there are no more 'CDecay' decays to treat!
        if len(mother_names_ccdecays) == 0:
            return

        # At last, create the charge conjugate decays:
        # First, make a (deep) copy of the list of relevant Tree instances.
        # Example:
        # if mother_names_ccdecays = ['anti-M10', 'anti-M2+'],
        # the relevant Trees are the ones describing the decays of ['M10', 'M2-'].
        dict_cc_names = self.dict_charge_conjugates()

        # match name -> position in list self._parsed_decays
        name2treepos = {
            t.children[0].children[0].value: i
            for i, t in enumerate(self._parsed_decays)  # type: ignore[arg-type]
        }

        trees_to_conjugate = []
        misses = []
        for ccname in mother_names_ccdecays:
            name = find_charge_conjugate_match(ccname, dict_cc_names)
            try:
                match = self._parsed_decays[name2treepos[name]]  # type: ignore[index]
                trees_to_conjugate.append(match)
            except Exception:
                misses.append(ccname)
        if len(misses) > 0:
            msg = """\nCorresponding 'Decay' statement for 'CDecay' statement(s) of following particle(s) not found:\n{}.
Skipping creation of these charge-conjugate decay trees.""".format(
                "\n".join(m for m in misses)
            )
            warnings.warn(msg, stacklevel=2)

        cdecays = [copy.deepcopy(tree) for tree in trees_to_conjugate]

        # Finally, perform all particle -> anti(particle) replacements,
        # taking care of charge conjugate decays defined via aliases,
        # passing them as charge conjugates to be processed manually.
        def _is_not_self_conj(t: Tree) -> bool:
            try:
                mname = t.children[0].children[0].value
                if Particle.from_evtgen_name(mname).is_self_conjugate:
                    msg = """Found 'CDecay' statement for self-conjugate particle {}. This is a bug!
Skipping creation of charge-conjugate decay Tree.""".format(
                        mname
                    )
                    warnings.warn(msg, stacklevel=2)
                    return False
                return True
            except Exception:
                return True

        for t in cdecays:
            if _is_not_self_conj(t):
                ChargeConjugateReplacement(charge_conj_defs=dict_cc_names).visit(t)

        # ... and add all these charge-conjugate decays to the list of decays!
        self._parsed_decays.extend(cdecays)  # type: ignore[union-attr]

    def _check_parsing(self) -> None:
        """Has the .parse() method been called already?"""
        if self._parsed_dec_file is None:
            raise DecFileNotParsed("Hint: call 'parse()'!")

    def _check_parsed_decays(self) -> None:
        """
        Is the number of decays parsed consistent with the number of
        decay mother names? An inconsistency can arise if decays are redefined.

        Duplicates are removed, starting from the second occurrence.
        """
        # Issue a helpful warning if duplicates are found
        lmn = self.list_decay_mother_names()
        duplicates = set()
        if self.number_of_decays != len(set(lmn)):
            duplicates = {n for n in lmn if lmn.count(n) > 1}
            msg = """The following particle(s) is(are) redefined in the input .dec file with 'Decay': {}!
All but the first occurrence will be discarded/removed ...""".format(
                ", ".join(duplicates)
            )

            warnings.warn(msg, stacklevel=2)

        # Create a list with all occurrences to remove
        # (duplications means multiple instances to remove)
        duplicates_to_remove = []
        for item in duplicates:
            c = lmn.count(item)
            if c > 1:
                duplicates_to_remove.extend([item] * (c - 1))

        # Actually remove all but the first occurrence of duplicate decays
        for tree in reversed(self._parsed_decays):  # type: ignore[arg-type]
            val = tree.children[0].children[0].value
            if val in duplicates_to_remove:
                duplicates_to_remove.remove(val)
                self._parsed_decays.remove(tree)  # type: ignore[union-attr]

    @property
    def number_of_decays(self) -> int:
        """Return the number of particle decays defined in the parsed .dec file."""
        self._check_parsing()

        return len(self._parsed_decays)  # type: ignore[arg-type]

    def list_decay_mother_names(self) -> list[str | Any]:
        """
        Return a list of all decay mother names found in the parsed decay file.
        """
        self._check_parsing()

        return [get_decay_mother_name(d) for d in self._parsed_decays]  # type: ignore[union-attr]

    def _find_decay_modes(self, mother: str) -> tuple[Any, ...]:
        """
        Return a tuple of Lark Tree instances describing all the decay modes
        of the input mother particle as defined in the parsed .dec file.

        Parameters
        ----------
        mother: str
            Input mother particle name.
        """
        self._check_parsing()

        for decay_Tree in self._parsed_decays:  # type: ignore[union-attr]
            if get_decay_mother_name(decay_Tree) == mother:
                return tuple(decay_Tree.find_data("decayline"))

        raise DecayNotFound("Decays of particle '%s' not found in .dec file!" % mother)

    def list_decay_modes(self, mother: str, pdg_name: bool = False) -> list[list[str]]:
        """
        Return a list of decay modes for the given mother particle.

        Parameters
        ----------
        mother: str
            Input mother particle name.
        pdg_name: bool, optional, default=False
            Input mother particle name is the PDG name,
            not the (default) EvtGen name.

        Example
        -------
        >>> parser = DecFileParser('my-decay-file.dec')    # doctest: +SKIP
        >>> parser.parse()    # doctest: +SKIP
        >>> # Inspect what decays are defined
        >>> parser.list_decay_mother_names()    # doctest: +SKIP
        >>> parser.list_decay_modes('pi0')    # doctest: +SKIP
        """
        if pdg_name:
            mother = PDG2EvtGenNameMap[mother]

        return [
            get_final_state_particle_names(mode)
            for mode in self._find_decay_modes(mother)
        ]

    def _decay_mode_details(
        self, decay_mode: Tree, display_photos_keyword: bool = True
    ) -> DecayModeDict:
        """
        Parse a decay mode (Tree instance)
        and return the relevant bits of information in it.

        Parameters
        ----------
        decay_mode: Tree
            Input decay mode to list its details.
        display_photos_keyword: boolean
            Omit or not the "PHOTOS" keyword in decay models.
        """

        bf = get_branching_fraction(decay_mode)
        fsp_names = get_final_state_particle_names(decay_mode)
        model = get_model_name(decay_mode)
        model_params = get_model_parameters(decay_mode)

        if display_photos_keyword and list(decay_mode.find_data("photos")):
            model = "PHOTOS " + model

        return DecayModeDict(
            bf=bf, fs=fsp_names, model=model, model_params=model_params
        )

    def print_decay_modes(
        self,
        mother: str,
        pdg_name: bool = False,
        print_model: bool = True,
        display_photos_keyword: bool = True,
        ascending: bool = False,
        normalize: bool = False,
        scale: float | None = None,
    ) -> None:
        """
        Pretty print of the decay modes of a given particle,
        optionally with decay model information and/or normalisation or scaling
        of the branching fractions.

        Parameters
        ----------
        mother: str
            Input mother particle name.
        pdg_name: bool, optional, default=False
            Input mother particle name is the PDG name,
            not the (default) EvtGen name.
        print_model: bool, optional, default=True
            Specify whether to print the decay model and model parameters,
            if available.
        display_photos_keyword: bool, optional, default=True
            Display the "PHOTOS" keyword in decay models.
        ascending: bool, optional, default=False
            Print the list of decay modes ordered in ascending/descending order
            of branching fraction.
        normalize: bool, optional, default=False
            Print the branching fractions normalized to unity.
            The printing does not affect the values parsed and actually stored in memory.
        scale: float | None, optional, default=None
            If not None, the branching fractions (BFs) are normalized to the given value,
            which is taken to be the BF of the highest-BF mode of the list.
            Must be a number in the range ]0, 1].

        Examples
        --------
        >>> s = '''Decay MyD_0*+
        ...  0.533   MyD0   pi+        PHSP;
        ...  0.08    MyD*0  pi+  pi0   PHSP;
        ...  0.0271  MyD*+  pi0  pi0   PHSP;
        ...  0.0542  MyD*+  pi+  pi-   PHSP;
        ... Enddecay
        ... '''
        >>> p = DecFileParser.from_string(s)
        >>> p.parse()
        >>>
        >>> # Simply print what has been parsed
        >>> p.print_decay_modes("MyD_0*+")
          0.533             MyD0  pi+         PHSP;
          0.08              MyD*0 pi+ pi0     PHSP;
          0.0542            MyD*+ pi+ pi-     PHSP;
          0.0271            MyD*+ pi0 pi0     PHSP;
        >>>
        >>> # Print normalizing the sum of all mode BFs to unity
        >>> p.print_decay_modes("MyD_0*+", normalize=True)
          0.7676796774      MyD0  pi+         PHSP;
          0.1152239666      MyD*0 pi+ pi0     PHSP;
          0.07806423736     MyD*+ pi+ pi-     PHSP;
          0.03903211868     MyD*+ pi0 pi0     PHSP;
        >>>
        >>> # Print scaling all BFs relative to the BF of the highest-BF mode in the list,
        >>> # the latter being set to the value of "scale".
        >>> # In this example the decay file as printed would effectively signal, for inspection,
        >>> # that about 35% of the total decay width is not accounted for in the list of modes,
        >>> # since the sum of probabilities, interpreted as BFs, sum to about 65%.
        >>> p.print_decay_modes("MyD_0*+", scale=0.5)
          0.5               MyD0  pi+         PHSP;
          0.07504690432     MyD*0 pi+ pi0     PHSP;
          0.05084427767     MyD*+ pi+ pi-     PHSP;
          0.02542213884     MyD*+ pi0 pi0     PHSP;
        """

        if scale is not None:
            # One cannot normalize and scale at the same time, clearly
            if normalize:
                raise RuntimeError(
                    "Be consistent - use either 'normalize' and 'scale'!"
                )
            if not 0.0 < scale <= 1.0:
                raise RuntimeError(
                    "A branching fraction must be in the range ]0, 1]! You set scale = {scale}."
                )

        if pdg_name:
            mother = PDG2EvtGenNameMap[mother]

        dms = self._find_decay_modes(mother)

        ls_dict = {}
        for dm in dms:
            dmdict = self._decay_mode_details(dm, display_photos_keyword)
            model_params = [str(i) for i in dmdict["model_params"]]
            ls_dict[dmdict["bf"]] = (
                dmdict["fs"],
                dmdict["model"],
                model_params,
            )

        dec_details = list(ls_dict.values())
        ls_attrs_aligned = list(
            zip_longest(
                *[self._align_items(i) for i in zip(*dec_details)], fillvalue=""
            )
        )

        ls = [(bf, ls_attrs_aligned[idx]) for idx, bf in enumerate(ls_dict)]
        ls.sort(key=operator.itemgetter(0), reverse=(not ascending))

        norm = 1.0
        if normalize:
            norm = sum(bf for bf, _ in ls)
        elif scale is not None:
            # Get the largest branching fraction
            i = -1 if ascending else 0
            norm = ls[i][0] / scale

        for bf, info in ls:
            if print_model:
                line = "  {:<15.10g}   {}     {}  {}".format(bf / norm, *info)
            else:
                line = f"  {bf / norm:<15.10g}   {info[0]}"
            print(line.rstrip() + ";")  # noqa: T201

    @staticmethod
    def _align_items(
        to_align: str, align_mode: str = "left", sep: str = " "
    ) -> list[str]:
        """
        Left or right align all strings in a list to the same length.
        By default the string is space-broke into sub-strings and each sub-string aligned individually.

        Parameters
        ----------
        align_mode: {"left", "right"}, optional, default="left"
            Specify whether each sub-string set should be left or right aligned.
        sep: str, optional, default=" "
            Specify the separation between sub-strings.
        """
        if not isinstance(to_align[0], (list, tuple)):
            max_len = max(len(s) for s in to_align)
            if align_mode == "left":
                return [s.ljust(max_len) for s in to_align]
            if align_mode == "right":
                return [s.rjust(max_len) for s in to_align]
            raise ValueError(f"Unknown align mode: {align_mode}")

        aligned = []
        for cat in zip_longest(*to_align, fillvalue=""):
            max_len = max(len(s) for s in cat)

            if align_mode == "left":
                row = [s.ljust(max_len) for s in cat]
            elif align_mode == "right":
                row = [s.rjust(max_len) for s in cat]
            else:
                raise ValueError(f"Unknown align mode: {align_mode}")

            aligned.append(row)

        return [sep.join(row) for row in zip(*aligned)]

    def build_decay_chains(
        self,
        mother: str,
        stable_particles: list[str] | set[str] | tuple[str] | tuple[()] = (),
    ) -> dict[str, list[DecayModeDict]]:
        """
        Iteratively build the entire decay chains of a given mother particle,
        optionally considering, on the fly, certain particles as stable.
        This way, for example, only the B -> D E F part in a decay chain
        A -> B (-> D E F (-> G H)) C
        can be trivially selected for inspection.

        Parameters
        ----------
        mother: str
            Input mother particle name.
        stable_particles: iterable, optional, default=()
            If provided, stops the decay-chain parsing,
            taking the "list" as particles to be considered stable.

        Returns
        -------
        out: dict
            Decay chain as a dictionary of the form
            {mother: [{'bf': float, 'fs': list, 'model': str, 'model_params': str}]}
            where
            'bf' stands for the decay mode branching fraction,
            'fs' is a list of final-state particle names (strings)
            and/or dictionaries of the same form as the decay chain above,
            'model' is the model name, if found, else '',
            'model_params' are the model parameters, if specified, else ''

        Examples
        --------
        >>> parser = DecFileParser('a-Dplus-decay-file.dec')    # doctest: +SKIP
        >>> parser.parse()    # doctest: +SKIP
        >>> parser.build_decay_chains('D+')    # doctest: +SKIP
        {'D+': [{'bf': 1.0,
           'fs': ['K-',
            'pi+',
            'pi+',
            {'pi0': [{'bf': 0.988228297,
               'fs': ['gamma', 'gamma'],
               'model': 'PHSP',
               'model_params': ''},
              {'bf': 0.011738247,
               'fs': ['e+', 'e-', 'gamma'],
               'model': 'PI0_DALITZ',
               'model_params': ''},
              {'bf': 3.3392e-05,
              'fs': ['e+', 'e+', 'e-', 'e-'],
              'model': 'PHSP',
              'model_params': ''},
              {'bf': 6.5e-08, 'fs': ['e+', 'e-'], 'model': 'PHSP', 'model_params': ''}]}],
           'model': 'PHSP',
           'model_params': ''}]}
        >>> p.build_decay_chains('D+', stable_particles=['pi0'])    # doctest: +SKIP
        {'D+': [{'bf': 1.0, 'fs': ['K-', 'pi+', 'pi+', 'pi0'], 'model': 'PHSP', 'model_params': ''}]}
        """

        info = []
        for dm in self._find_decay_modes(mother):
            d = self._decay_mode_details(dm, display_photos_keyword=False)

            for i, fs in enumerate(d["fs"]):
                if fs in stable_particles:
                    continue

                try:
                    # This throws a DecayNotFound exception
                    # if fs does not have decays defined in the parsed file
                    # _n_dms = len(self._find_decay_modes(fs))

                    assert isinstance(fs, str)
                    _info = self.build_decay_chains(fs, stable_particles)
                    d["fs"][i] = _info  # type: ignore[index]
                except DecayNotFound:
                    pass

            info.append(d)

        return {mother: info}

    def __repr__(self) -> str:
        if self._parsed_dec_file is not None:
            return "<{self.__class__.__name__}: decfile(s)={decfile}, n_decays={n_decays}>".format(
                self=self, decfile=self._dec_file_names, n_decays=self.number_of_decays
            )
        return f"<{self.__class__.__name__}: decfile(s)={self._dec_file_names}>"

    def __str__(self) -> str:
        return repr(self)


class DecayModelAliasReplacement(Transformer):  # type: ignore[misc]
    """
    Lark Transformer implementing the replacement of decay model aliases
    with the model provided in 'ModelAlias' statements.
    This replaces the model_label with a subtree containing both the model name
    and its options.
    The replacement is only relevant for Lark Tree instances of name
    'model' (Tree.data == 'model').

    Parameters
    ----------
    model_alias_defs: dict, optional, default={}
        Dictionary with the 'ModelAlias' definitions in the parsed file.
        Argument to be passed to the class constructor.

    """

    def __init__(self, model_alias_defs: dict[str, Any] | None = None) -> None:
        super().__init__()
        self.define_defs = model_alias_defs or {}

    def _replacement(self, t: Token) -> Token:
        if t.value not in self.define_defs:
            raise ValueError(
                f"Decay model or ModelAlias {t.value} is not defined. Please load the decay model with "
                "`load_additional_decay_models` or define a ModelAlias in the decayfile."
            )
        return self.define_defs[t.value]

    def model(self, treelist: list[Tree]) -> Tree:
        """
        Method for the rule (here, a replacement) we wish to implement.
        Must happen on model level to replace a Lark Token with a Lark Tree.
        Doesn't do anything if no model_label is found.
        """
        if isinstance(treelist[0], Tree):
            assert (
                treelist[0].data == "model_label"
            ), f"Instead of a subtree of type 'model_label' one of type {treelist[0].data} has been passed."
            return Tree("model", self._replacement(treelist[0].children[0]))

        return Tree("model", treelist)


class DecayModelParamValueReplacement(Visitor):  # type: ignore[misc]
    """
    Lark Visitor implementing the replacement of decay model parameter names
    with the actual parameter values provided in 'Define' statements,
    and replacement of floats stored as strings to the actual floating values.
    The replacement is only relevant for Lark Tree instances of name
    'model_options' (Tree.data == 'model_options').

    Parameters
    ----------
    define_defs: dict, optional, default={}
        Dictionary with the 'Define' definitions in the parsed file.
        Argument to be passed to the class constructor.

    Examples
    --------
    >>> from lark import Tree, Token
    >>> ...  # doctest: +SKIP
    >>> t = Tree('decay', [Tree('particle', [Token('LABEL', 'Upsilon(4S)')]),
    ...         Tree('decayline', [Tree('value', [Token('SIGNED_NUMBER', '1.0')]),
    ...         Tree('particle', [Token('LABEL', 'B0')]),
    ...         Tree('particle', [Token('LABEL', 'anti-B0')]),
    ...         Tree('model', [Token('MODEL_NAME', 'VSS_BMIX'),
    ...         Tree('model_options', [Token('LABEL', 'dm')])])])])
    >>> dict_define_defs = {'dm': 0.507e12}
    >>> DecayModelParamValueReplacement(define_defs=dict_define_defs).visit(t)    # doctest: +NORMALIZE_WHITESPACE
    Tree('decay', [Tree('particle', [Token('LABEL', 'Upsilon(4S)')]),
    Tree('decayline', [Tree('value', [Token('SIGNED_NUMBER', '1.0')]),
    Tree('particle', [Token('LABEL', 'B0')]),
    Tree('particle', [Token('LABEL', 'anti-B0')]),
    Tree('model', [Token('MODEL_NAME', 'VSS_BMIX'),
    Tree('model_options', [Token('LABEL', 507000000000.0)])])])])
    """

    def __init__(self, define_defs: dict[str, Any] | None = None) -> None:
        self.define_defs = define_defs or {}

    def _replacement(self, t: Tree) -> None:
        try:
            t.children[0].value = float(t.children[0].value)
        except AttributeError:
            negative_param = (
                t.value[0] == "-"
            )  # account for uncommon cases such as "MODEL_NAME ... -DEFINE_NAME"
            value = t.value if not negative_param else t.value[1:]
            if value in self.define_defs:
                t.value = (
                    self.define_defs[value]
                    if not negative_param
                    else -self.define_defs[value]
                )

    def model_options(self, tree: Tree) -> None:
        """
        Method for the rule (here, a replacement) we wish to implement.
        """
        assert tree.data == "model_options"

        for child in tree.children:
            self._replacement(child)


class ChargeConjugateReplacement(Visitor):  # type: ignore[misc]
    """
    Lark Visitor implementing the replacement of all particle names
    with their charge conjugate particle names
    in a Lark Tree of name 'particle' (Tree.data == 'particle').

    Note
    ----
    1) There is no check of whether the mother particle is self-conjugate or not.
    It is the responsibility of the caller to make sure the operation
    is not trivial, meaning returning the same (self-conjugate) decay!
    2) If a particle name (say, 'UNKOWN') is not found or known,
    (search done via the Particle class in the particle package),
    its charge conjugate name is denoted as 'ChargeConj(UNKOWN)'.

    Parameters
    ----------
    charge_conj_defs: dict, optional, default={}
        Dictionary with the charge conjugate particle definitions
        in the parsed file. Argument to be passed to the class constructor.

    Examples
    --------
    >>> from lark import Tree, Token
    >>> ...    # doctest: +SKIP
    >>> t = Tree('decay', [Tree('particle', [Token('LABEL', 'D0')]), Tree('decayline', [Tree
    ... ('value', [Token('SIGNED_NUMBER', '1.0')]), Tree('particle', [Token('LABEL', 'K-')]),
    ... Tree('particle', [Token('LABEL', 'pi+')]), Tree('model', [Token('MODEL_NAME', 'PHSP')])])])
    >>> ChargeConjugateReplacement().visit(t)    # doctest: +NORMALIZE_WHITESPACE
    Tree('decay', [Tree('particle', [Token('LABEL', 'anti-D0')]),
    Tree('decayline', [Tree('value', [Token('SIGNED_NUMBER', '1.0')]),
    Tree('particle', [Token('LABEL', 'K+')]),
    Tree('particle', [Token('LABEL', 'pi-')]),
    Tree('model', [Token('MODEL_NAME', 'PHSP')])])])
    """

    def __init__(self, charge_conj_defs: dict[str, str] | None = None) -> None:
        self.charge_conj_defs = charge_conj_defs or {}

    def particle(self, tree: Tree) -> None:
        """
        Method for the rule (here, a replacement) we wish to implement.
        """
        assert tree.data == "particle"
        pname = tree.children[0].value
        ccpname = find_charge_conjugate_match(pname, self.charge_conj_defs)
        self.charge_conj_defs[pname] = ccpname
        tree.children[0].value = ccpname


def find_charge_conjugate_match(
    pname: str, dict_cc_names: dict[str, str] | None = None
) -> str:
    """
    Find the charge-conjugate particle name making use of user information
    from "ChargeConj" statements in a decay file.

    The name `ChargeConj(pname)` is returned if all matching "routes" fail,
    see `charge_conjugate_name(...) function.`
    """
    # Check the list of particle-antiparticle matches provided ;-)
    if dict_cc_names:
        match = dict_cc_names.get(pname)
        if match is not None:
            return match
        # Yes, both 'ChargeConj P CCP' and 'ChargeConj CCP P' are relevant
        for p, ccp in dict_cc_names.items():
            if ccp == pname:
                return p

    return charge_conjugate_name(pname)


def get_decay_mother_name(decay_tree: Tree) -> str | Any:
    """
    Return the mother particle name for the decay mode defined
    in the input Tree of name 'decay'.

    Parameters
    ----------
    decay_tree: Lark Tree instance
        Input Tree satisfying Tree.data=='decay'.
    """
    if decay_tree.data != "decay":
        raise RuntimeError("Input not an instance of a 'decay' Tree!")

    # For a 'decay' Tree, tree.children[0] is the mother particle Tree
    # and tree.children[0].children[0].value is the mother particle name
    return decay_tree.children[0].children[0].value


def get_branching_fraction(decay_mode: Tree) -> float:
    """
    Return the branching fraction (float) for the decay mode defined
    in the input Tree of name 'decayline'.

    Parameters
    ----------
    decay_mode: Lark Tree instance
        Input Tree satisfying Tree.data=='decayline'.
    """
    if decay_mode.data != "decayline":
        raise RuntimeError("Check your input, not an instance of a 'decayline' Tree!")

    # For a 'decayline' Tree, Tree.children[0] is the branching fraction Tree
    # and tree.children[0].children[0].value is the BF stored as a str
    try:  # the branching fraction value as a float
        return float(decay_mode.children[0].children[0].value)
    except RuntimeError as e:
        raise RuntimeError(
            "'decayline' Tree does not seem to have the usual structure. Check it."
        ) from e


def get_final_state_particles(decay_mode: Tree) -> list[Tree]:
    """
    Return a list of Lark Tree instances describing the final-state particles
    for the decay mode defined in the input Tree of name 'decayline'.

    Parameters
    ----------
    decay_mode: Lark Tree instance
        Input Tree satisfying Tree.data=='decayline'.

    Examples
    --------
    For a decay
        Decay MyB_s0
            1.000     K+     K-     SSD_CP 20.e12 0.1 1.0 0.04 9.6 -0.8 8.4 -0.6;
        Enddecay
    the list
        [Tree(particle, [Token(LABEL, 'K+')]), Tree(particle, [Token(LABEL, 'K-')])]
    will be returned.
    """
    if decay_mode.data != "decayline":
        raise RuntimeError("Input not an instance of a 'decayline' Tree!")

    # list of Trees of final-state particles
    return list(decay_mode.find_data("particle"))


def get_final_state_particle_names(decay_mode: Tree) -> list[str]:
    """
    Return a list of final-state particle names for the decay mode defined
    in the input Tree of name 'decayline'.

    Parameters
    ----------
    decay_mode: Lark Tree instance
        Input Tree satisfying Tree.data=='decayline'.

    Examples
    --------
    For a decay
        Decay MyB_s0
            1.000     K+     K-     SSD_CP 20.e12 0.1 1.0 0.04 9.6 -0.8 8.4 -0.6;
        Enddecay
    the list ['K+', 'K-'] will be returned.
    """
    if decay_mode.data != "decayline":
        raise RuntimeError("Input not an instance of a 'decayline' Tree!")

    fsps = get_final_state_particles(decay_mode)
    # list of final-state particle names
    return [str(fsp.children[0].value) for fsp in fsps]


def get_model_name(decay_mode: Tree) -> str:
    """
    Return the decay model name in a Tree of name 'decayline'.

    Parameters
    ----------
    decay_mode: Lark Tree instance
        Input Tree satisfying Tree.data=='decayline'.

    Examples
    --------
    For a decay
        Decay MyB_s0
            1.000     K+     K-     SSD_CP 20.e12 0.1 1.0 0.04 9.6 -0.8 8.4 -0.6;
        Enddecay
    the string 'SSD_CP' will be returned.
    """
    if decay_mode.data != "decayline":
        raise RuntimeError("Input not an instance of a 'decayline' Tree!")

    lm = list(decay_mode.find_data("model"))
    return str(lm[0].children[0].value)


def get_model_parameters(decay_mode: Tree) -> str | list[str | Any]:
    """
    Return a list of decay model parameters in a Tree of name 'decayline',
    if defined, else an empty string.

    Parameters
    ----------
    decay_mode: Lark Tree instance
        Input Tree satisfying Tree.data=='decayline'.

    Examples
    --------
    For a decay
        Decay MyB_s0
            1.000     K+     K-     SSD_CP 20.e12 0.1 1.0 0.04 9.6 -0.8 8.4 -0.6;
        Enddecay
    the list
        [20000000000000.0, 0.1, 1.0, 0.04, 9.6, -0.8, 8.4, -0.6]
    will be returned.

    For a decay
        Decay MyD0
            1.00      K-   pi-   pi+   pi+     LbAmpGen DtoKpipipi_v1 ;
        Enddecay
    the list
        ['DtoKpipipi_v1']
    will be returned.
    """
    if decay_mode.data != "decayline":
        raise RuntimeError("Input not an instance of a 'decayline' Tree!")

    lmo = list(decay_mode.find_data("model_options"))

    def _value(t: Tree) -> str | Any:
        try:
            return t.children[0].value
        except AttributeError:
            return t.value

    return [_value(tree) for tree in lmo[0].children] if len(lmo) == 1 else ""


def get_decays(parsed_file: Tree) -> list[Tree]:
    """
    Return a list of all decay definitions in the input parsed file,
    of the form "Decay <MOTHER>",
    as a tuple of Lark Tree instances with Tree.data=='decay', i.e.,
    [Tree(decay, [Tree(particle, [Token(LABEL, <MOTHER1>]), ...),
     Tree(decay, [Tree(particle, [Token(LABEL, <MOTHER2>]), ...)].

    Parameters
    ----------
    parsed_file: Lark Tree instance
        Input parsed file.
    """
    try:
        return list(parsed_file.find_data("decay"))
    except Exception as err:
        raise RuntimeError(
            "Input parsed file does not seem to have the expected structure."
        ) from err


def get_charge_conjugate_decays(parsed_file: Tree) -> list[str]:
    """
    Return a (sorted) list of all charge conjugate decay definitions
    in the input parsed file, of the form "CDecay <MOTHER>", as
    ['MOTHER1', 'MOTHER2', ...].

    Parameters
    ----------
    parsed_file: Lark Tree instance
        Input parsed file.
    """

    try:
        return sorted(
            tree.children[0].value for tree in parsed_file.find_data("cdecay")
        )
    except Exception as err:
        raise RuntimeError(
            "Input parsed file does not seem to have the expected structure."
        ) from err


def get_decays2copy_statements(parsed_file: Tree) -> dict[str, str]:
    """
    Return a dictionary of all statements in the input parsed file
    defining a decay to be copied, of the form
    "CopyDecay <NAME> <DECAY_TO_COPY>",
    as {'NAME1': DECAY_TO_COPY1, 'NAME2': DECAY_TO_COPY2, ...}.

    Parameters
    ----------
    parsed_file: Lark Tree instance
        Input parsed file.
    """
    try:
        return {
            tree.children[0].children[0].value: tree.children[1].children[0].value
            for tree in parsed_file.find_data("copydecay")
        }
    except Exception as err:
        raise RuntimeError(
            "Input parsed file does not seem to have the expected structure."
        ) from err


def get_definitions(parsed_file: Tree) -> dict[str, float]:
    """
    Return a dictionary of all definitions in the input parsed file, of the form
    "Define <NAME> <VALUE>", as {'NAME1': VALUE1, 'NAME2': VALUE2, ...}.

    Parameters
    ----------
    parsed_file: Lark Tree instance
        Input parsed file.
    """
    try:
        return {
            tree.children[0].value: float(tree.children[1].value)
            for tree in parsed_file.find_data("define")
        }
    except Exception as err:
        raise RuntimeError(
            "Input parsed file does not seem to have the expected structure."
        ) from err


def get_model_aliases(parsed_file: Tree) -> dict[str, list[str]]:
    """
    Return a dictionary of all model alias definitions in the input parsed file, of the form
    "ModelAlias <NAME> <MODEL_NAME> <MODEL_OPTIONS>", as {'NAME1': [MODEL_NAME, MODEL_OPTION1, MODEL_OPTION2,...],
    'NAME2': [MODEL_NAME, ...]...}.

    Parameters
    ----------
    parsed_file: Lark Tree instance
        Input parsed file.

    """
    try:
        model_alias_tokens = [
            list(t.scan_values(lambda v: isinstance(v, Token)))
            for t in parsed_file.find_data("model_alias")
        ]

        return {
            model_alias[0].value: [model.value for model in model_alias[1:]]
            for model_alias in model_alias_tokens
        }
    except Exception as err:
        raise RuntimeError(
            "Input parsed file does not seem to have the expected structure."
        ) from err


def get_aliases(parsed_file: Tree) -> dict[str, str]:
    """
    Return a dictionary of all aliases in the input parsed file, of the form
    "Alias <NAME> <ALIAS>", as {'NAME1': ALIAS1, 'NAME2': ALIAS2, ...}.

    Parameters
    ----------
    parsed_file: Lark Tree instance
        Input parsed file.
    """
    try:
        return {
            tree.children[0].value: tree.children[1].value
            for tree in parsed_file.find_data("alias")
        }
    except Exception as err:
        raise RuntimeError(
            "Input parsed file does not seem to have the expected structure."
        ) from err


def get_charge_conjugate_defs(parsed_file: Tree) -> dict[str, str]:
    """
    Return a dictionary of all charge conjugate definitions
    in the input parsed file, of the form "ChargeConj <PARTICLE> <CC_PARTICLE>",
    as {'PARTICLE1': CC_PARTICLE1, 'PARTICLE2': CC_PARTICLE2, ...}.

    Parameters
    ----------
    parsed_file: Lark Tree instance
        Input parsed file.
    """
    try:
        return {
            tree.children[0].value: tree.children[1].value
            for tree in parsed_file.find_data("chargeconj")
        }
    except Exception as err:
        raise RuntimeError(
            "Input parsed file does not seem to have the expected structure."
        ) from err


def get_particle_property_definitions(parsed_file: Tree) -> dict[str, dict[str, float]]:
    """
    Return a dictionary of all particle property definitions
    in the input parsed file, of the form "Particle <PARTICLE> <MASS> <WIDTH>",
    as {'PARTICLE1': {'mass': MASS1, 'width': WIDTH1},
        'PARTICLE2': {'mass': MASS2, 'width': WIDTH2}, ...}.

    Parameters
    ----------
    parsed_file: Lark Tree instance
        Input parsed file.
    """
    try:
        return {
            tree.children[0].value: {
                "mass": float(tree.children[1].value),
                "width": float(tree.children[2].value),
            }
            for tree in parsed_file.find_data("particle_def")
        }
    except Exception as err:
        raise RuntimeError(
            "Input parsed file does not seem to have the expected structure."
        ) from err


def get_pythia_definitions(parsed_file: Tree) -> dict[str, dict[str, str | float]]:
    """
    Return a dictionary of all Pythia 8 commands
    "PythiaGenericParam" and/or "PythiaAliasParam" and/or "PythiaBothParam",
    with keys corresponding to the 3 types specifying whether the command is for
    generic decays, alias decays, or both.
    The commands are set in the input parsed file with statements of the form
    "Pythia<TYPE>Param <MODULE>:<PARAM>=<LABEL_OR_VALUE>.
    The dictionary takes the form
    {"PythiaAliasParam": {'<MODULE1>:<PARAM1>': 'LABEL1', '<MODULE1>:<PARAM2>': VALUE2, ...},
     "PythiaBothParam": {'<MODULE2>:<PARAM3>': 'LABEL3', '<MODULE3>:<PARAM4>': VALUE4, ...},
     "PythiaGenericParam": {'<MODULE4>:<PARAM5>': 'LABEL5', '<MODULE5>:<PARAM6>': VALUE6, ...}}.

    Parameters
    ----------
    parsed_file: Lark Tree instance
        Input parsed file.
    """
    d: dict[str, dict[str, str | float]] = {}

    try:
        for tree in parsed_file.find_data("pythia_def"):
            if tree.children[0].value in d:
                d[tree.children[0].value].update(
                    {
                        f"{tree.children[1].value}:{tree.children[2].value}": _str_or_float(
                            tree.children[3].value
                        )
                    }
                )
            else:
                d[tree.children[0].value] = {
                    f"{tree.children[1].value}:{tree.children[2].value}": _str_or_float(
                        tree.children[3].value
                    )
                }
        return d
    except Exception as err:
        raise RuntimeError(
            "Input parsed file does not seem to have the expected structure."
        ) from err


def get_jetset_definitions(
    parsed_file: Tree,
) -> dict[str, dict[int, int | float | str]]:
    """
    Return a dictionary of all JETSET definitions in the input parsed file,
    of the form
    "JetSetPar <MODULE>(<PARAMETER>)=<VALUE>"
    as
    {'MODULE1': {PARAMETER1: VALUE1, PARAMETER2: VALUE2, ...},
     'MODULE2': {...},
     ...}.

    Parameters
    ----------
    parsed_file: Lark Tree instance
        Input parsed file.
    """
    get_jetsetpar = re.compile(
        r"""
    ^                                     # Beginning of string
        (?P<pname>      [a-zA-Z]+?  )     # One or more characters, non-greedy
     \( (?P<pnumber>    \d+         ) \)  # parameter number in ()
    """,
        re.VERBOSE,
    )

    def to_int_or_float(n: str) -> int | float | str:
        """
        Trivial helper function to convert the parsed (as strings)
        JETSET parameters into what they are, namely integers or floats.
        """
        try:
            return int(n)
        except ValueError:
            try:
                return float(n)
            except Exception:
                # pass though non-numbers unchanged
                return n

    try:
        dict_params: dict[str, dict[int, int | float | str]] = {}
        for tree in parsed_file.find_data("jetset_def"):
            # This will throw an error if match is None
            param = get_jetsetpar.match(tree.children[0].value).groupdict()  # type: ignore[union-attr]
            try:
                dict_params[param["pname"]].update(
                    {int(param["pnumber"]): to_int_or_float(tree.children[1].value)}
                )
            except KeyError:
                dict_params[param["pname"]] = {
                    int(param["pnumber"]): to_int_or_float(tree.children[1].value)
                }
        return dict_params
    except Exception as err:
        raise RuntimeError(
            "Input parsed file does not seem to have the expected structure."
        ) from err


def get_lineshape_settings(
    parsed_file: Tree,
) -> dict[str, dict[str, str | float]]:
    """
     Return a dictionary of all lineshape settings,
     with keys corresponding to particle names or aliases, as
     {PARTICLE1: {'lineshape': 'NAME1',  # E.g. "LSFLAT" or "LSNONRELBW"
       'BlattWeisskopf': VALUE11,
       'ChangeMassMin': VALUE12,
       'ChangeMassMax': VALUE13},
      PARTICLE2: {'lineshape': 'NAME2',
       'BlattWeisskopf': VALUE21,
       'ChangeMassMin': VALUE22,
       'ChangeMassMax': VALUE23,
       'IncludeBirthFactor': TRUE_OR_FALSE,
       'IncludeDecayFactor': TRUE_OR_FALSE},
      ...
     }
     where not all "sub-dictionaries" may contain all and/or the same keys.

    Parameters
     ----------
     parsed_file: Lark Tree instance
         Input parsed file.
    """
    d: dict[str, dict[str, str | float]] = {}
    try:
        # Lineshape definitions
        for tree in parsed_file.find_data("ls_def"):
            if tree.children[1].value not in d:
                d[tree.children[1].value] = {"lineshape": tree.children[0].value}
            else:
                raise RuntimeError(
                    "Input parsed file does not seem to have the expected structure for the lineshape definitions."
                ) from None

        # Blatt-Weisskopf barrier factor for a lineshape
        for tree in parsed_file.find_data("setlsbw"):
            particle_or_alias = tree.children[0].value
            if particle_or_alias in d:
                if "BlattWeisskopf" in d[particle_or_alias]:
                    raise RuntimeError(
                        f"The Blatt-Weisskopf barrier factor for particle/alias {particle_or_alias} seems to be redefined."
                    ) from None
                d[particle_or_alias]["BlattWeisskopf"] = float(tree.children[1].value)
            else:
                d[particle_or_alias] = {"BlattWeisskopf": float(tree.children[1].value)}

        # Upper and lower mass cuts on a lineshape
        for tree in parsed_file.find_data("changemasslimit"):
            particle_or_alias = tree.children[1].value
            if particle_or_alias in d:
                if tree.children[0].value in d[particle_or_alias]:
                    raise RuntimeError(
                        f"The upper/lower mass cut on the lineshape for particle/alias {particle_or_alias} seems to be redefined."
                    ) from None
                d[particle_or_alias][f"{tree.children[0].value}"] = float(
                    tree.children[2].value
                )
            else:
                d[particle_or_alias] = {
                    f"{tree.children[0].value}": float(tree.children[2].value)
                }

        # Presence of the birth/decay momentum factor and form-factor
        for tree in parsed_file.find_data("inc_factor"):
            particle_or_alias = tree.children[1].value
            if particle_or_alias in d:
                if tree.children[0].value in d[particle_or_alias]:
                    raise RuntimeError(
                        f"The birth/decay momentum factor for particle/alias {particle_or_alias} seems to be redefined."
                    ) from None
                d[particle_or_alias][f"{tree.children[0].value}"] = _str_to_bool(
                    tree.children[2].value
                )
            else:
                d[particle_or_alias] = {
                    f"{tree.children[0].value}": _str_to_bool(tree.children[2].value)
                }

        return d

    except Exception as err:
        raise RuntimeError(
            "Input parsed file does not seem to have the expected structure."
        ) from err


def get_lineshapePW_definitions(
    parsed_file: Tree,
) -> list[tuple[list[str], int]]:
    """
    Return a list of all SetLineshapePW definitions in the input parsed file,
    of the form
    "SetLineshapePW <MOTHER> <DAUGHTER1> <DAUGHTER2> <VALUE>",
    as
    [(['MOTHER1', 'DAUGHTER1-1', 'DAUGHTER1-2'], VALUE1),
     (['MOTHER2', 'DAUGHTER2-1', 'DAUGHTER2-2'], VALUE2),
     ...]

    Parameters
    ----------
    parsed_file: Lark Tree instance
        Input parsed file.
    """
    try:
        d = []
        for tree in parsed_file.find_data("setlspw"):
            particles = [p.value for p in tree.children[:-1]]
            val = int(tree.children[3].value)
            d.append((particles, val))
        return d
    except Exception as err:
        raise RuntimeError(
            "Input parsed file does not seem to have the expected structure."
        ) from err


def get_global_photos_flag(parsed_file: Tree) -> int:
    """
    Return a boolean-like PhotosEnum enum specifying whether or not PHOTOS
    has been enabled.

    Note: PHOTOS is turned on(off) for all decays with the global flag
    yesPhotos(noPhotos).

    Parameters
    ----------
    parsed_file: Lark Tree instance
        Input parsed file.

    Returns
    -------
    out: PhotosEnum, default=PhotosEnum.no
        PhotosEnum.yes / PhotosEnum.no if PHOTOS enabled / disabled
    """
    # Check if the flag is not set more than once, just in case ...
    tree = tuple(parsed_file.find_data("global_photos"))
    if not tree:
        return PhotosEnum.no
    if len(tree) > 1:
        warnings.warn("PHOTOS flag re-set! Using flag set in last ...", stacklevel=2)

    end_item = tree[-1]  # Use the last one if several are present !
    val = end_item.children[0].data
    return PhotosEnum.yes if val == "yes" else PhotosEnum.no


def _str_or_float(arg: str) -> str | float:
    try:
        return float(arg)
    except Exception:
        return arg


def _str_to_bool(arg: str) -> bool:
    if arg == "yes":
        return True
    if arg == "no":
        return False

    raise ValueError(
        f"String {arg!r} cannot be converted to boolean! Only 'yes/no' accepted."
    )
