# Copyright (c) 2018-2023, Eduardo Rodrigues and Henry Schreiner.
#
# Distributed under the 3-clause BSD license, see accompanying file LICENSE
# or https://github.com/scikit-hep/decaylanguage for details.

from __future__ import annotations

import io
import sys
from pathlib import Path

import pytest
from lark import Token, Tree

from decaylanguage.dec.dec import (
    ChargeConjugateReplacement,
    DecayModelAliasReplacement,
    DecayModelParamValueReplacement,
    DecayNotFound,
    DecFileNotParsed,
    DecFileParser,
    ModelNameCleanup,
    get_decay_mother_name,
    get_final_state_particle_names,
    get_model_name,
    get_model_parameters,
)
from decaylanguage.dec.enums import PhotosEnum, known_decay_models

DIR = Path(__file__).parent.resolve()


def test_default_constructor():
    p = DecFileParser()
    assert p is not None


def test_constructor_1_file():
    p = DecFileParser(DIR / "../data/test_example_Dst.dec")

    assert p is not None
    assert len(p._dec_file_names) == 1


def test_constructor_multiple_files():
    p = DecFileParser(
        DIR / "../data/test_Xicc2XicPiPi.dec", DIR / "../data/test_Bc2BsPi_Bs2KK.dec"
    )

    # The following parse() command issues the warning
    #   UserWarning: Corresponding 'Decay' statement for 'CDecay' statement(s) of following particle(s) not found: anti-Xi_cc-sig.
    #   Skipping creation of these charge-conjugate decay trees.
    with pytest.warns(UserWarning) as record:
        p.parse()
    assert len(record) == 1

    assert len(p._dec_file_names) == 2
    assert p.number_of_decays == 7


def test_from_string():
    s = """Decay pi0
0.988228297   gamma   gamma                   PHSP;
0.011738247   e+      e-      gamma           PI0_DALITZ;
0.000033392   e+      e+      e-      e-      PHSP;
0.000000065   e+      e-                      PHSP;
Enddecay
"""

    p = DecFileParser.from_string(s)
    p.parse()

    assert p.number_of_decays == 1


def test_double_parsing():
    p = DecFileParser(DIR / "../data/test_example_Dst.dec")
    p.parse()
    # The second call to parse() issues the warning
    #   UserWarning: Input file being re-parsed ...
    #     warnings.warn("Input file being re-parsed ...")
    with pytest.warns(UserWarning) as record:
        p.parse()
    assert len(record) == 1


def test_unknown_decfile():
    with pytest.raises(FileNotFoundError):
        DecFileParser("non-existent.dec")


def test_non_parsed_decfile():
    p = DecFileParser(DIR / "../data/test_example_Dst.dec")
    with pytest.raises(DecFileNotParsed):
        p.list_decay_mother_names()


def test_non_existent_decay():
    p = DecFileParser(DIR / "../data/test_example_Dst.dec")
    p.parse()
    with pytest.raises(DecayNotFound):
        p.list_decay_modes("XYZ")


def test_no_grammar_loading_by_default():
    p = DecFileParser(DIR / "../data/test_example_Dst.dec")
    assert not p.grammar_loaded


def test_default_grammar_loading():
    p = DecFileParser(DIR / "../data/test_example_Dst.dec")
    assert p.grammar() is not None
    assert p.grammar_loaded


def test_explicit_grammar_loading():
    p = DecFileParser(DIR / "../data/test_example_Dst.dec")
    p.load_grammar(DIR / "../../src/decaylanguage/data/decfile.lark")

    assert p.grammar_loaded is True


def test_string_representation():
    p = DecFileParser(DIR / "../data/test_example_Dst.dec")

    assert "n_decays" not in p.__str__()

    p.parse()
    assert "n_decays=5" in p.__str__()


def test_copydecay_statement_parsing():
    p = DecFileParser(DIR / "../data/test_CopyDecay_RemoveDecay.dec")
    p.parse()

    assert len(p.dict_decays2copy()) == 2
    assert p.number_of_decays == 4  # 2 original + 2 copied
    assert p.list_decay_modes("phi_copy") == p.list_decay_modes("phi")


def test_definitions_parsing():
    p = DecFileParser(DIR / "../data/defs-aliases-chargeconj.dec")
    p.parse()

    assert len(p.dict_definitions()) == 24


def test_aliases_parsing():
    p = DecFileParser(DIR / "../data/defs-aliases-chargeconj.dec")
    p.parse()

    assert len(p.dict_aliases()) == 132


def test_model_aliases_parsing():
    p = DecFileParser(DIR / "../data/defs-aliases-chargeconj.dec")
    p.parse()

    assert len(p.dict_model_aliases()) == 7
    assert p.dict_model_aliases()["SLBKPOLE_DtoKlnu"] == [
        "SLBKPOLE",
        "1.0",
        "0.303",
        "1.0",
        "2.112",
    ]

    assert p.dict_model_aliases()["SLBKPOLE_Dtopilnu"] == [
        "SLBKPOLE",
        "1.0",
        "0.281",
        "1.0",
        "2.010",
    ]


def test_charge_conjugates_parsing():
    p = DecFileParser(DIR / "../data/defs-aliases-chargeconj.dec")
    p.parse()

    assert len(p.dict_charge_conjugates()) == 77


def test_pythia_definitions_parsing():
    p = DecFileParser(DIR / "../data/defs-aliases-chargeconj.dec")
    p.parse()

    assert p.dict_pythia_definitions() == {
        "ParticleDecays:mixB": "off",
        "Init:showChangedSettings": "off",
        "Init:showChangedParticleData": "off",
        "Next:numberShowEvent": 0.0,
    }


def test_jetset_definitions_parsing():
    p = DecFileParser(DIR / "../data/defs-aliases-chargeconj.dec")
    p.parse()

    assert p.dict_jetset_definitions() == {
        "MSTU": {1: 0, 2: 0},
        "PARU": {11: 0.001},
        "MSTJ": {26: 0},
        "PARJ": {21: 0.36},
    }


def test_list_lineshape_definitions():
    p = DecFileParser(DIR / "../data/defs-aliases-chargeconj.dec")
    p.parse()

    assert p.list_lineshape_definitions() == [
        (["D_1+", "D*+", "pi0"], 2),
        (["D_1+", "D*0", "pi+"], 2),
        (["D_1-", "D*-", "pi0"], 2),
        (["D_1-", "anti-D*0", "pi-"], 2),
        (["D_10", "D*0", "pi0"], 2),
        (["D_10", "D*+", "pi-"], 2),
        (["anti-D_10", "anti-D*0", "pi0"], 2),
        (["anti-D_10", "D*-", "pi+"], 2),
    ]


def test_global_photos_flag():
    p = DecFileParser(DIR / "../data/defs-aliases-chargeconj.dec")
    p.parse()

    assert p.global_photos_flag()


def test_missing_global_photos_flag():
    p = DecFileParser(DIR / "../data/test_example_Dst.dec")
    p.parse()

    assert not p.global_photos_flag()


def test_duplicated_global_photos_flag():
    s = """
    # Turn on PHOTOS for all decays
    yesPhotos
    yesPhotos

    Decay D0
      1.0   K-      pi+        PHSP;
    Enddecay
    """
    p = DecFileParser.from_string(s)
    p.parse()
    # The following call issues the warning
    # UserWarning: PHOTOS flag re-set! Using flag set in last ...
    #   warnings.warn("PHOTOS flag re-set! Using flag set in last ...")
    with pytest.warns(UserWarning) as record:
        assert p.global_photos_flag() == PhotosEnum.yes
    assert len(record) == 1


def test_duplicated_global_photos_flag_take_last():
    s = """
    # Turn on PHOTOS for all decays
    noPhotos
    yesPhotos

    Decay D0
      1.0   K-      pi+        PHSP;
    Enddecay
    """
    p = DecFileParser.from_string(s)
    p.parse()
    # The following call issues the warning
    # UserWarning: PHOTOS flag re-set! Using flag set in last ...
    #   warnings.warn("PHOTOS flag re-set! Using flag set in last ...")
    with pytest.warns(UserWarning) as record:
        assert p.global_photos_flag() == PhotosEnum.yes
    assert len(record) == 1


def test_list_charge_conjugate_decays():
    p = DecFileParser(DIR / "../data/test_Bd2DmTauNu_Dm23PiPi0_Tau2MuNu.dec")
    p.parse()

    assert p.list_charge_conjugate_decays() == [
        "MyD+",
        "MyTau+",
        "Mya_1-",
        "anti-B0sig",
    ]


def test_simple_dec():
    p = DecFileParser(DIR / "../data/test_example_Dst.dec")
    p.parse()

    assert p.list_decay_mother_names() == ["D*+", "D*-", "D0", "D+", "pi0"]

    assert p.list_decay_modes("D0") == [["K-", "pi+"]]


def test_with_missing_info():
    """
    This decay file misses a ChargeConj statement relating the particle aliases
    Xi_cc+sig and anti-Xi_cc-sig. As a consequence, only 3 decays are parsed
    and the following warning is issued:
    ``
    Corresponding 'Decay' statement for 'CDecay' statement(s) of following particle(s) not found:
    anti-Xi_cc-sig.
    Skipping creation of these charge-conjugate decay trees.
      warnings.warn(msg)
    ``
    """
    p = DecFileParser(DIR / "../data/test_Xicc2XicPiPi.dec")
    with pytest.warns(UserWarning) as record:
        p.parse()
    assert len(record) == 1

    # Decay of anti-Xi_cc-sig missing
    assert p.number_of_decays == 3
    assert "anti-Xi_cc-sig" not in p.list_decay_mother_names()

    # CDecay statements
    assert "anti-Xi_cc-sig" in p.list_charge_conjugate_decays()


def test_decay_mode_details():
    p = DecFileParser(DIR / "../data/test_example_Dst.dec")
    p.parse()

    tree_Dp = p._find_decay_modes("D+")[0]
    output = (1.0, ["K-", "pi+", "pi+", "pi0"], "PHSP", "")
    assert p._decay_mode_details(tree_Dp, display_photos_keyword=False) == output


def test_decay_model_parsing():
    """
    This module tests building blocks rather than the API,
    hence the "strange" way to access parsed Lark Tree instances.
    """
    p = DecFileParser(DIR / "../data/test_Bd2DstDst.dec")
    p.parse()

    # Simple decay model without model parameters
    dl = p._parsed_decays[2].children[1]  # 'MySecondD*+' Tree
    assert get_model_name(dl) == "VSS"
    assert get_model_parameters(dl) == ""  # noqa: PLC1901

    # Decay model with a set of floating-point model parameters
    dl = p._parsed_decays[0].children[1]  # 'B0sig' Tree
    assert get_model_name(dl) == "SVV_HELAMP"
    assert get_model_parameters(dl) == [0.0, 0.0, 0.0, 0.0, 1.0, 0.0]

    # Decay model where model parameter is a string,
    # which matches an XML file for EvtGen
    dl = p._parsed_decays[4].children[1]  # 'MyD0' Tree
    assert get_model_name(dl) == "LbAmpGen"
    assert get_model_parameters(dl) == ["DtoKpipipi_v1"]


def test_decay_model_parsing_with_model_name_substring():
    """
    This module tests if a model name can be a substring of another
    model name (without respecting the order in the Lark grammar).
    """
    p = DecFileParser(DIR / "../data/test_Upsilon2S2UpsilonPiPi.dec")
    p.parse()

    dl = p._parsed_decays[0].children[1]  # First decay mode
    assert get_model_name(dl) == "YMSTOYNSPIPICLEOBOOST"
    assert get_model_parameters(dl) == [-0.753, 0.0]

    dl = p._parsed_decays[0].children[2]  # First decay mode
    assert get_model_name(dl) == "YMSTOYNSPIPICLEO"
    assert get_model_parameters(dl) == [-0.753, 0.0]


def test_decay_model_parsing_with_variable_defs():
    """
    In this example the decay model details are "VSS_BMIX dm",
    where dm stands for a variable name whose value is defined via the statement
    'Define dm 0.507e12'. The parser should recognise this and return
    [0.507e12] rather than ['dm'] as model parameters.
    """
    p = DecFileParser(DIR / "../data/test_Upsilon4S2B0B0bar.dec")
    p.parse()

    assert p.dict_definitions() == {"dm": 507000000000.0}

    dl = p._parsed_decays[0].children[1]
    assert get_model_name(dl) == "VSS_BMIX"
    assert get_model_parameters(dl) == [0.507e12]


def test_decay_model_parsing_with_model_alias():
    """
    In this example the decay model details are "SLBKPOLE_DtoKlnu",
    where SLBKPOLE_DtoKlnu stands for an alias whose value is defined via the statement
    "ModelAlias SLBKPOLE_DtoKlnu SLBKPOLE 1.0 param1;" (semicolon matters here).
    "param1" is here defined via the statement "Define param1 -0.303".
    The parser should recognise this and return SLBKPOLE as the model name and [1.0, -0.303] as the model parameters.
    """
    p = DecFileParser(DIR / "../data/test_DtoKlnu.dec")
    p.parse()
    assert p._dict_raw_model_aliases() == {
        "SLBKPOLE_DtoKlnu": [
            Token("MODEL_NAME_AND_WS", "SLBKPOLE"),
            Tree(
                "model_options",
                [
                    Tree("value", [Token("SIGNED_NUMBER", "1.0")]),
                    Token("LABEL", "param1"),
                ],
            ),
        ]
    }

    assert p.dict_model_aliases() == {"SLBKPOLE_DtoKlnu": ["SLBKPOLE", "1.0", "param1"]}

    dl = p._parsed_decays[0].children[1]
    assert get_model_name(dl) == "SLBKPOLE"
    assert get_model_parameters(dl) == [1.0, -0.303]


def test_duplicate_decay_definitions():
    p = DecFileParser(DIR / "../data/duplicate-decays.dec")

    with pytest.warns(UserWarning) as w:
        p.parse()

    assert len(w) == 2

    assert p.number_of_decays == 2

    assert p.list_decay_mother_names() == ["Sigma(1775)0", "anti-Sigma(1775)0"]


def test_list_decay_modes():
    p = DecFileParser(DIR / "../data/test_example_Dst.dec")
    p.parse()

    assert p.list_decay_modes("D*-") == [
        ["anti-D0", "pi-"],
        ["D-", "pi0"],
        ["D-", "gamma"],
    ]
    assert p.list_decay_modes("D*(2010)-", pdg_name=True) == [
        ["anti-D0", "pi-"],
        ["D-", "pi0"],
        ["D-", "gamma"],
    ]


def test_list_decay_modes_on_the_fly():
    """
    Unlike in the example above the charge conjugate decay modes are created
    on the fly from the non-CC. decay.
    """
    p = DecFileParser(DIR / "../data/test_Xicc2XicPiPi.dec")
    with pytest.warns(UserWarning) as record:
        p.parse()
    assert len(record) == 1

    # Parsed directly from the dec file
    assert p.list_decay_modes("MyXic+") == [["p+", "K-", "pi+"]]

    # Decay mode created on-the-fly from the above
    assert p.list_decay_modes("MyantiXic-") == [["anti-p-", "K+", "pi-"]]


def test_print_decay_modes_basics():
    p = DecFileParser(DIR / "../data/test_example_Dst.dec")
    p.parse()

    with pytest.raises(DecayNotFound):
        p.print_decay_modes("D*(2010)-")

    p.print_decay_modes("D*(2010)-", pdg_name=True)


def test_print_decay_modes_options():
    p1 = DecFileParser(DIR / "../data/test_example_Dst.dec")
    p1.parse()

    p2 = DecFileParser(DIR / "../data/test_Bc2BsPi_Bs2KK.dec")
    p2.parse()

    # Temporarily direct prints of several calls below to a string
    old_stdout = sys.stdout
    tmp_stdout = io.StringIO()
    sys.stdout = tmp_stdout

    p1.print_decay_modes("D*+")
    out_default = tmp_stdout.getvalue()

    tmp_stdout = io.StringIO()
    sys.stdout = tmp_stdout
    p1.print_decay_modes("D*+", normalize=True)
    out_normalized = tmp_stdout.getvalue()

    with pytest.raises(RuntimeError):
        p1.print_decay_modes("D*+", normalize=True, scale=1)

    tmp_stdout = io.StringIO()
    sys.stdout = tmp_stdout
    p2.print_decay_modes("B_c+sig", display_photos_keyword=False)
    no_photos = tmp_stdout.getvalue()
    tmp_stdout.truncate(0)

    assert "PHOTOS" not in no_photos
    # This specific dec file happens to have been defined normalized
    assert out_default == out_normalized

    tmp_stdout = io.StringIO()
    sys.stdout = tmp_stdout
    p2.print_decay_modes("B_c+sig")
    photos_included = tmp_stdout.getvalue()
    assert "PHOTOS " in photos_included
    tmp_stdout.truncate(0)

    # Do not forget to reset sys.stdout and clean up!
    sys.stdout = old_stdout
    del old_stdout, tmp_stdout


def test_build_decay_chains():
    p = DecFileParser(DIR / "../data/test_example_Dst.dec")
    p.parse()

    output = {
        "D+": [
            {
                "bf": 1.0,
                "fs": ["K-", "pi+", "pi+", "pi0"],
                "model": "PHSP",
                "model_params": "",
            }
        ]
    }
    assert p.build_decay_chains("D+", stable_particles=["pi0"]) == output


def test_Lark_ModelNameCleanup_Transformer_no_params():
    t = Tree(
        "decay",
        [
            Tree("particle", [Token("LABEL", "D0")]),
            Tree(
                "decayline",
                [
                    Tree("value", [Token("SIGNED_NUMBER", "1.0")]),
                    Tree("particle", [Token("LABEL", "K-")]),
                    Tree("particle", [Token("LABEL", "pi+")]),
                    Tree("model", [Token("MODEL_NAME_AND_SC", "PHSP;")]),
                ],
            ),
        ],
    )

    cleaned_tree = ModelNameCleanup().transform(t)
    tree_decayline = list(cleaned_tree.find_data("decayline"))[0]
    assert get_model_name(tree_decayline) == "PHSP"


def test_Lark_ModelNameCleanup_Transformer_with_params():
    t = Tree(
        "decay",
        [
            Tree("particle", [Token("LABEL", "B0sig")]),
            Tree(
                "decayline",
                [
                    Tree("value", [Token("SIGNED_NUMBER", "1.000")]),
                    Tree("particle", [Token("LABEL", "MyFirstD*-")]),
                    Tree("particle", [Token("LABEL", "MySecondD*+")]),
                    Tree(
                        "model",
                        [
                            Token("MODEL_NAME_AND_WS", "SVV_HELAMP  "),
                            Tree(
                                "model_options",
                                [
                                    Tree("value", [Token("SIGNED_NUMBER", "0.0")]),
                                    Tree("value", [Token("SIGNED_NUMBER", "0.0")]),
                                    Tree("value", [Token("SIGNED_NUMBER", "0.0")]),
                                    Tree("value", [Token("SIGNED_NUMBER", "0.0")]),
                                    Tree("value", [Token("SIGNED_NUMBER", "1.0")]),
                                    Tree("value", [Token("SIGNED_NUMBER", "0.0")]),
                                ],
                            ),
                        ],
                    ),
                ],
            ),
        ],
    )

    cleaned_tree = ModelNameCleanup().transform(t)
    tree_decayline = list(cleaned_tree.find_data("decayline"))[0]
    assert get_model_name(tree_decayline) == "SVV_HELAMP"
    assert get_model_parameters(tree_decayline) == [
        "0.0",
        "0.0",
        "0.0",
        "0.0",
        "1.0",
        "0.0",
    ]


def test_Lark_DecayModelAliasReplacement_Transformer():
    t = Tree(
        "decay",
        [
            Tree("particle", [Token("LABEL", "D+")]),
            Tree(
                "decayline",
                [
                    Tree("value", [Token("SIGNED_NUMBER", "1.000")]),
                    Tree("particle", [Token("LABEL", "anti-K0")]),
                    Tree("particle", [Token("LABEL", "e+")]),
                    Tree("particle", [Token("LABEL", "nu_e")]),
                    Tree(
                        "model",
                        [Tree("model_label", [Token("LABEL", "SLBKPOLE_DtoKlnu")])],
                    ),
                ],
            ),
        ],
    )
    dict_model_aliases = {
        "SLBKPOLE_DtoKlnu": [
            Token("MODEL_NAME_AND_WS", "SLBKPOLE"),
            Tree(
                "model_options",
                [
                    Tree("value", [Token("SIGNED_NUMBER", "1.0")]),
                    Tree("value", [Token("SIGNED_NUMBER", "0.303")]),
                    Tree("value", [Token("SIGNED_NUMBER", "1.0")]),
                    Tree("value", [Token("SIGNED_NUMBER", "2.112")]),
                ],
            ),
        ]
    }

    unaliased_tree = DecayModelAliasReplacement(
        model_alias_defs=dict_model_aliases
    ).transform(t)

    tree_decayline = list(unaliased_tree.find_data("decayline"))[0]
    assert get_model_name(tree_decayline) == "SLBKPOLE"
    assert get_model_parameters(tree_decayline) == ["1.0", "0.303", "1.0", "2.112"]


def test_Lark_DecayModelParamValueReplacement_Visitor_no_params():
    t = Tree(
        "decay",
        [
            Tree("particle", [Token("LABEL", "D0")]),
            Tree(
                "decayline",
                [
                    Tree("value", [Token("SIGNED_NUMBER", "1.0")]),
                    Tree("particle", [Token("LABEL", "K-")]),
                    Tree("particle", [Token("LABEL", "pi+")]),
                    Tree("model", [Token("MODEL_NAME_AND_SC", "PHSP")]),
                ],
            ),
        ],
    )

    DecayModelParamValueReplacement().visit(t)

    # The visitor should do nothing in this case
    tree_decayline = list(t.find_data("decayline"))[0]
    assert get_model_name(tree_decayline) == "PHSP"
    assert get_model_parameters(tree_decayline) == ""  # noqa: PLC1901


def test_Lark_DecayModelParamValueReplacement_Visitor_single_value():
    t = Tree(
        "decay",
        [
            Tree("particle", [Token("LABEL", "Upsilon(4S)")]),
            Tree(
                "decayline",
                [
                    Tree("value", [Token("SIGNED_NUMBER", "1.0")]),
                    Tree("particle", [Token("LABEL", "B0")]),
                    Tree("particle", [Token("LABEL", "anti-B0")]),
                    Tree(
                        "model",
                        [
                            Token("MODEL_NAME_AND_WS", "VSS_BMIX"),
                            Tree("model_options", [Token("LABEL", "dm")]),
                        ],
                    ),
                ],
            ),
        ],
    )

    DecayModelParamValueReplacement().visit(t)

    # Nothing done since model parameter name has no corresponding
    # 'Define' statement from which the actual value can be inferred
    tree_decayline = list(t.find_data("decayline"))[0]
    assert get_model_name(tree_decayline) == "VSS_BMIX"
    assert get_model_parameters(tree_decayline) == ["dm"]

    dict_define_defs = {"dm": 0.507e12}

    DecayModelParamValueReplacement(define_defs=dict_define_defs).visit(t)

    # The model parameter 'dm' should now be replaced by its value
    assert get_model_name(tree_decayline) == "VSS_BMIX"
    assert get_model_parameters(tree_decayline) == [507000000000.0]


def test_Lark_DecayModelParamValueReplacement_Visitor_list():
    t = Tree(
        "decay",
        [
            Tree("particle", [Token("LABEL", "B0sig")]),
            Tree(
                "decayline",
                [
                    Tree("value", [Token("SIGNED_NUMBER", "1.000")]),
                    Tree("particle", [Token("LABEL", "MyFirstD*-")]),
                    Tree("particle", [Token("LABEL", "MySecondD*+")]),
                    Tree(
                        "model",
                        [
                            Token("MODEL_NAME_AND_WS", "SVV_HELAMP"),
                            Tree(
                                "model_options",
                                [
                                    Tree("value", [Token("SIGNED_NUMBER", "0.0")]),
                                    Tree("value", [Token("SIGNED_NUMBER", "0.0")]),
                                    Tree("value", [Token("SIGNED_NUMBER", "0.0")]),
                                    Tree("value", [Token("SIGNED_NUMBER", "0.0")]),
                                    Tree("value", [Token("SIGNED_NUMBER", "1.0")]),
                                    Tree("value", [Token("SIGNED_NUMBER", "0.0")]),
                                ],
                            ),
                        ],
                    ),
                ],
            ),
        ],
    )

    DecayModelParamValueReplacement().visit(t)

    # The visitor should do nothing in this case
    tree_decayline = list(t.find_data("decayline"))[0]
    assert get_model_name(tree_decayline) == "SVV_HELAMP"
    assert get_model_parameters(tree_decayline) == [0.0, 0.0, 0.0, 0.0, 1.0, 0.0]


def test_Lark_ChargeConjugateReplacement_Visitor():
    """
    A simple example usage of the ChargeConjugateReplacement implementation
    of a Lark's Visitor, here replacing all particles in a 'decay' Tree
    by their antiparticles.
    """
    t = Tree(
        "decay",
        [
            Tree("particle", [Token("LABEL", "D0")]),
            Tree(
                "decayline",
                [
                    Tree("value", [Token("SIGNED_NUMBER", "1.0")]),
                    Tree("particle", [Token("LABEL", "K-")]),
                    Tree("particle", [Token("LABEL", "pi+")]),
                    Tree("model", [Token("MODEL_NAME_AND_SC", "PHSP")]),
                ],
            ),
        ],
    )

    ChargeConjugateReplacement().visit(t)

    assert get_decay_mother_name(t) == "anti-D0"
    assert get_final_state_particle_names(t.children[1]) == ["K+", "pi-"]


def test_Lark_ChargeConjugateReplacement_Visitor_with_aliases():
    """
    Example with a D0 decay specified via an alias (MyD0).
    As such, it is necessary to state what the particle-antiparticle match is,
    which in decay files would mean the following lines:
       Alias       MyD0        D0
       Alias       MyAnti-D0   anti-D0
       ChargeConj  MyD0        MyAnti-D0
    A dictionary of matches should be passed to the Lark Visitor instance.
    """
    t = Tree(
        "decay",
        [
            Tree("particle", [Token("LABEL", "MyD0")]),
            Tree(
                "decayline",
                [
                    Tree("value", [Token("SIGNED_NUMBER", "1.0")]),
                    Tree("particle", [Token("LABEL", "K-")]),
                    Tree("particle", [Token("LABEL", "pi+")]),
                    Tree("model", [Token("MODEL_NAME_AND_SC", "PHSP")]),
                ],
            ),
        ],
    )

    dict_ChargeConj_defs = {"MyD0": "MyAnti-D0"}

    ChargeConjugateReplacement(charge_conj_defs=dict_ChargeConj_defs).visit(t)

    assert get_decay_mother_name(t) == "MyAnti-D0"
    assert get_final_state_particle_names(t.children[1]) == ["K+", "pi-"]


def test_creation_charge_conjugate_decays_in_decfile_with_aliases():
    """
    Decay file contains 5 particle decays defined via a 'Decay' statement
    and the 5 charge-conjugate decays defined via a 'CDecay' statement.
    The decay modes for the latter 5 should be created on the fly,
    hence providing in total 10 sets of particle decays parsed.
    """
    p = DecFileParser(DIR / "../data/test_Bd2DstDst.dec")
    p.parse()

    assert p.number_of_decays == 10


def test_creation_charge_conjugate_decays_in_decfile_without_CDecay_defs():
    """
    Decay file contains 5 particle decays defined via a 'Decay' statement,
    but no related charge-conjugate (CC) decays defined via a 'CDecay' statement
    since the CC particle decays are also defined via a 'Decay' statement
    for all cases except self-conjugate (mother) particles, obviously ;-).
    This being said, this decay file is in fact incomplete by itself,
    as there are no instructions on how to decay the anti-D0 and the D-!
    In short, there should only be 5 sets of decay modes parsed.
    """
    p = DecFileParser(DIR / "../data/test_example_Dst.dec")
    p.parse()

    assert p.number_of_decays == 5


def test_master_DECAYdotDEC_file():
    p = DecFileParser(DIR / "../../src/decaylanguage/data/DECAY_LHCB.DEC")
    p.parse()

    assert p.number_of_decays == 506


def test_BELLE2_decfile():
    p = DecFileParser(DIR / "../../src/decaylanguage/data/DECAY_BELLE2.DEC")
    p.parse()

    # Just check the dec file will parse since I do not know
    # how many decays are in the dec file.
    assert p.number_of_decays == 363


def test_lark_file_model_list_consistency():
    """
    Make sure that the list of known decay models in the grammar file
    'decaylanguage/data/decfile.lark' is consistent with that provided
    to the user via
    'from decaylanguage.dec.enums import known_decay_models'.
    """
    filename = str(DIR / "../../src/decaylanguage/data/decfile.lark")
    with Path(filename).open(encoding="utf-8") as lark_file:
        lines = lark_file.readlines()
        for line in lines:
            if "MODEL_NAME :" in line:
                break
        models = line.split(":")[1].strip(" ").strip("\n").split('"|"')
        models = [m.strip('"') for m in models]

        assert models == list(known_decay_models)


def test_align_items_simple():
    to_align = ["a", "quick", "brown", "fox"]
    aligned = DecFileParser._align_items(to_align)

    assert aligned == ["a    ", "quick", "brown", "fox  "]


def test_align_items_simple_right_align():
    to_align = ["a", "quick", "brown", "fox"]
    aligned = DecFileParser._align_items(to_align, align_mode="right")

    assert aligned == ["    a", "quick", "brown", "  fox"]


def test_align_items_complex():
    to_align = [
        ("alpha", "beta", "gamma"),
        ("a", "b", "c"),
        ("01", "02", "03"),
    ]

    aligned = DecFileParser._align_items(to_align)

    assert aligned == ["alpha beta gamma", "a     b    c    ", "01    02   03   "]


def test_align_items_complex_right_align():
    to_align = [
        ("alpha", "beta", "gamma"),
        ("a", "b", "c"),
        ("01", "02", "03"),
    ]

    aligned = DecFileParser._align_items(to_align, align_mode="right")

    assert aligned == ["alpha beta gamma", "    a    b     c", "   01   02    03"]
