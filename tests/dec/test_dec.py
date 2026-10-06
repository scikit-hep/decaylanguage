# Copyright (c) 2018-2026, Eduardo Rodrigues and Henry Schreiner.
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
    DecayAndCDecayWarning,
    DecayModelAliasReplacement,
    DecayModelParamValueReplacement,
    DecayNotFound,
    DecFileNotParsed,
    DecFileParser,
    DuplicateCDecayWarning,
    DuplicateDecayWarning,
    MisconfiguredAliasWarning,
    MisconfiguredChargeConjWarning,
    MissingCDecaySourceWarning,
    MissingCopyDecaySourceWarning,
    SelfChargeConjWarning,
    get_branching_fraction,
    get_decay_mother_name,
    get_final_state_particle_names,
    get_final_state_particles,
    get_model_name,
    get_model_parameters,
)
from decaylanguage.dec.enums import PhotosEnum

DIR = Path(__file__).parent.resolve()


def test_default_constructor() -> None:
    p = DecFileParser()
    assert p is not None


def test_constructor_1_file() -> None:
    p = DecFileParser(DIR / "../data/test_example_Dst.dec")

    assert p is not None
    assert len(p._dec_file_names) == 1


def test_constructor_multiple_files() -> None:
    p = DecFileParser(
        DIR / "../data/test_Xicc2XicPiPi.dec", DIR / "../data/test_Bc2BsPi_Bs2KK.dec"
    )

    with pytest.warns(MissingCDecaySourceWarning, match="anti-Xi_cc-sig") as record:
        p.parse()
    assert len(record) == 1

    assert len(p._dec_file_names) == 2
    assert p.number_of_decays == 7


def test_from_string() -> None:
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


def test_double_parsing() -> None:
    p = DecFileParser(DIR / "../data/test_example_Dst.dec")
    p.parse()
    # The second call to parse() issues the warning
    #   UserWarning: Input file being re-parsed ...
    #     warnings.warn("Input file being re-parsed ...")
    with pytest.warns(UserWarning, match="Input file being re-parsed ...") as record:
        p.parse()
    assert len(record) == 1


def test_unknown_decfile() -> None:
    with pytest.raises(FileNotFoundError):
        DecFileParser("non-existent.dec")


def test_minimalistic_decfile() -> None:
    p = DecFileParser(DIR / "../data/minimalistic.dec")
    p.parse()
    assert p.number_of_decays == 0


def test_non_parsed_decfile() -> None:
    p = DecFileParser(DIR / "../data/test_example_Dst.dec")
    with pytest.raises(DecFileNotParsed):
        p.list_decay_mother_names()


def test_decfile_defining_stable_particle() -> None:
    p = DecFileParser(DIR / "../data/test_stable-particle.dec")
    p.parse()

    assert (
        p.number_of_decays == 1
    )  # The decay of K_S0, even if no decay modes are defined
    assert p.list_decay_modes("K_S0") == []


def test_non_existent_decay() -> None:
    p = DecFileParser(DIR / "../data/test_example_Dst.dec")
    p.parse()
    with pytest.raises(DecayNotFound):
        p.list_decay_modes("XYZ")


def test_no_grammar_loading_by_default() -> None:
    p = DecFileParser(DIR / "../data/test_example_Dst.dec")
    assert not p.grammar_loaded


def test_default_grammar_loading() -> None:
    p = DecFileParser(DIR / "../data/test_example_Dst.dec")
    assert p.grammar() is not None
    assert p.grammar_loaded


def test_string_representation() -> None:
    p = DecFileParser(DIR / "../data/test_example_Dst.dec")

    assert "n_decays" not in p.__str__()

    p.parse()
    assert "n_decays=5" in p.__str__()


def test_copydecay_statement_parsing() -> None:
    p = DecFileParser(DIR / "../data/test_CopyDecay_RemoveDecay.dec")
    p.parse()

    assert len(p.dict_decays2copy()) == 2
    assert p.number_of_decays == 4  # 2 original + 2 copied
    assert p.list_decay_modes("phi_copy") == p.list_decay_modes("phi")


def test_copydecay_statement_with_missing_decay_statement() -> None:
    s = """Alias phi_copy phi
CopyDecay phi_copy phi
End"""

    dfp = DecFileParser.from_string(s)

    with pytest.raises(MissingCopyDecaySourceWarning):
        dfp.parse()


def test_definitions_parsing() -> None:
    p = DecFileParser(DIR / "../data/defs-aliases-chargeconj.dec")
    p.parse()

    assert len(p.dict_definitions()) == 24


def test_aliases_parsing() -> None:
    p = DecFileParser(DIR / "../data/defs-aliases-chargeconj.dec")
    p.parse()

    assert len(p.dict_aliases()) == 136


def test_alias_to_itself() -> None:
    s = """Alias   B0sig   B0sig
End
"""
    p = DecFileParser.from_string(s)
    with pytest.raises(MisconfiguredAliasWarning):
        p.parse()


def test_alias_not_aliased_to_standard_particle_name() -> None:
    s = """Alias   B0sig   B0Alias
End
"""
    p = DecFileParser.from_string(s)
    with pytest.raises(MisconfiguredAliasWarning):
        p.parse()


def test_alias_name_is_standard_particle_name() -> None:
    s = """Alias   B0   B0
End
"""
    p = DecFileParser.from_string(s)
    with pytest.raises(MisconfiguredAliasWarning):
        p.parse()


def test_alias_statement_swapped() -> None:
    s = """Alias   B0   B0sig
End
"""
    p = DecFileParser.from_string(s)
    with pytest.raises(MisconfiguredAliasWarning):
        p.parse()


def test_model_aliases_parsing() -> None:
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


def test_charge_conjugates_parsing() -> None:
    p = DecFileParser(DIR / "../data/defs-aliases-chargeconj.dec")
    p.parse()

    assert len(p.dict_charge_conjugates()) == 77


def test_ChargeConj_minimalistic_and_incomplete() -> None:
    """
    ChargeConj statements for non-self-conjugate particles are unnecessary/irrrelevant
    but are not wrong.
    """
    s = """ChargeConj   D-   D+
End
"""
    p = DecFileParser.from_string(s)
    with pytest.raises(MisconfiguredChargeConjWarning):
        p.parse()


def test_ChargeConj_statement_mixed() -> None:
    s = """ChargeConj   D+sig   D-
End
"""
    p = DecFileParser.from_string(s)
    with pytest.raises(MisconfiguredChargeConjWarning):
        p.parse()


def test_ChargeConj_statement_mixed_swapped() -> None:
    s = """ChargeConj   D-   D+sig
End
"""
    p = DecFileParser.from_string(s)
    with pytest.raises(MisconfiguredChargeConjWarning):
        p.parse()


def test_ChargeConj_with_related_Aliases() -> None:
    """
    ChargeConj statements for non-self-conjugate particles defined via aliases are necessary/relevant.
    """
    s = """Alias   D+sig   D+
Alias   D-sig   D-
ChargeConj   D-sig   D+sig
End
"""
    p = DecFileParser.from_string(s)
    p.parse()


def test_ChargeConj_minimalistic_and_incomplete_with_Alias() -> None:
    """
    A ChargeConj statement for non-self-conjugate particles defined via aliases is necessary/relevant,
    though this file is of course incomplete since it misses Alias statements
    specifying to what the alias names in ChargeConj actually refer to.
    """
    s = """ChargeConj   D-sig   D+sig
End
"""
    p = DecFileParser.from_string(s)
    p.parse()


def test_ChargeConj_with_related_Alias_for_self_conjugate() -> None:
    """
    A ChargeConj statement for a self-conjugate particle defined via an alias is necessary/relevant
    since the combination of the two statements is what specifies the self-conjugate nature
    of the particle alias.
    """
    s = """Alias My_phi phi
ChargeConj My_phi My_phi
End
"""
    p = DecFileParser.from_string(s)
    p.parse()


def test_ChargeConj_minimalistic_and_incomplete_for_self_conjugate() -> None:
    """
    A ChargeConj statement for a self-conjugate particle defined via an alias is necessary/relevant,
    though this file is of course incomplete since it misses the Alias statement
    specifying to what the alias name in ChargeConj actually refers to.
    """
    s = """ChargeConj My_phi My_phi
End
"""
    p = DecFileParser.from_string(s)
    p.parse()


def test_ChargeConj_self_conjugate() -> None:
    """A ChargeConj statement for a non-alias self-conjugate particle is redundant / a buglet."""
    s = """ChargeConj   phi   phi
End
"""
    p = DecFileParser.from_string(s)
    with (
        pytest.warns(MisconfiguredChargeConjWarning),
        pytest.warns(
            SelfChargeConjWarning,
            match="Found 'ChargeConj' statements for the following non-alias self-conjugate particles",
        ),
    ):
        p.parse()


def test_particle_property_definitions() -> None:
    p = DecFileParser(DIR / "../data/defs-aliases-chargeconj.dec")
    p.parse()

    assert p.get_particle_property_definitions() == {
        "MyK*0": {"mass": 0.892, "width": 0.051},
        "MyPhi": {"mass": 1.02, "width": 0.004},
        "rho0": {"mass": 0.8, "width": 0.2},
        "MyRho0": {"mass": 0.77, "width": 0.1474},
        "chi_c0": {"mass": 3.42, "width": 0.0124},
    }


def test_pythia_definitions_parsing() -> None:
    p = DecFileParser(DIR / "../data/defs-aliases-chargeconj.dec")
    p.parse()

    assert p.dict_pythia_definitions() == {
        "PythiaAliasParam": {
            "ParticleDecays:sophisticatedTau": 3.0,
            "ParticleDecays:tauPolarization": -1.0,
        },
        "PythiaBothParam": {
            "Init:showChangedParticleData": "off",
            "Init:showChangedSettings": "off",
            "Next:numberShowEvent": 0.0,
            "ParticleDecays:mixB": "off",
        },
    }


def test_jetset_definitions_parsing() -> None:
    p = DecFileParser(DIR / "../data/defs-aliases-chargeconj.dec")
    p.parse()

    assert p.dict_jetset_definitions() == {
        "MSTU": {1: 0, 2: 0},
        "PARU": {11: 0.001},
        "MSTJ": {26: 0},
        "PARJ": {21: 0.36},
    }


def test_dict_lineshape_settings() -> None:
    p = DecFileParser(DIR / "../data/defs-aliases-chargeconj.dec")
    p.parse()

    assert p.dict_lineshape_settings() == {
        "MyK*0": {
            "lineshape": "LSNONRELBW",
            "BlattWeisskopf": 0.0,
            "ChangeMassMin": 0.5,
            "ChangeMassMax": 3.5,
        },
        "MyPhi": {
            "lineshape": "LSNONRELBW",
            "BlattWeisskopf": 0.0,
            "ChangeMassMin": 1.0,
            "ChangeMassMax": 1.04,
        },
        "MyKS0pipi": {
            "lineshape": "LSFLAT",
            "ChangeMassMin": 1.1,
            "ChangeMassMax": 2.4,
        },
        "rho0": {
            "lineshape": "LSNONRELBW",
            "BlattWeisskopf": 3.0,
            "ChangeMassMax": 0.9,
            "ChangeMassMin": 0.7,
            "IncludeBirthFactor": False,
            "IncludeDecayFactor": True,
        },
    }


def test_list_lineshapePW_definitions() -> None:
    p = DecFileParser(DIR / "../data/defs-aliases-chargeconj.dec")
    p.parse()

    assert p.list_lineshapePW_definitions() == [
        (["D_1+", "D*+", "pi0"], 2),
        (["D_1+", "D*0", "pi+"], 2),
        (["D_1-", "D*-", "pi0"], 2),
        (["D_1-", "anti-D*0", "pi-"], 2),
        (["D_10", "D*0", "pi0"], 2),
        (["D_10", "D*+", "pi-"], 2),
        (["anti-D_10", "anti-D*0", "pi0"], 2),
        (["anti-D_10", "D*-", "pi+"], 2),
    ]


def test_global_photos_flag() -> None:
    """
    Check that PHOTOS is on for all decays.
    """
    p = DecFileParser(DIR / "../data/defs-aliases-chargeconj.dec")
    p.parse()

    assert p.global_photos_flag()


def test_global_photos_off() -> None:
    """
    Check that PHOTOS is off for all decays.
    """
    s = """
    # Turn off PHOTOS for all decays
    noPhotos

    Decay D0
      1.0   K-      pi+        PHSP;
    Enddecay
    """
    p = DecFileParser.from_string(s)
    p.parse()

    assert p.global_photos_flag() == PhotosEnum.no


def test_missing_global_photos_flag() -> None:
    p = DecFileParser(DIR / "../data/test_example_Dst.dec")
    p.parse()

    assert not p.global_photos_flag()


def test_duplicated_global_photos_flag() -> None:
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
    with pytest.warns(
        UserWarning, match="PHOTOS flag re-set! Using flag set in last ..."
    ) as record:
        assert p.global_photos_flag() == PhotosEnum.yes
    assert len(record) == 1


def test_duplicated_global_photos_flag_take_last() -> None:
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
    with pytest.warns(
        UserWarning, match="PHOTOS flag re-set! Using flag set in last ..."
    ) as record:
        assert p.global_photos_flag() == PhotosEnum.yes
    assert len(record) == 1


def test_list_charge_conjugate_decays() -> None:
    p = DecFileParser(DIR / "../data/test_Bd2DmTauNu_Dm23PiPi0_Tau2MuNu.dec")
    p.parse()

    assert p.list_charge_conjugate_decays() == [
        "MyD+",
        "MyTau+",
        "Mya_1-",
        "anti-B0sig",
    ]


def test_simple_dec() -> None:
    p = DecFileParser(DIR / "../data/test_example_Dst.dec")
    p.parse()

    assert p.list_decay_mother_names() == ["D*+", "D*-", "D0", "D+", "pi0"]

    assert p.list_decay_modes("D0") == [["K-", "pi+"]]


def test_with_missing_info() -> None:
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

    with pytest.warns(MissingCDecaySourceWarning, match="anti-Xi_cc-sig") as record:
        p.parse()

    assert len(record) == 1

    # Decay of anti-Xi_cc-sig missing
    assert p.number_of_decays == 3
    assert "anti-Xi_cc-sig" not in p.list_decay_mother_names()

    # CDecay statements
    assert "anti-Xi_cc-sig" in p.list_charge_conjugate_decays()


def test_decay_mode_details() -> None:
    p = DecFileParser(DIR / "../data/test_example_Dst.dec")
    p.parse()

    tree_Dp = p._find_decay_modes("D+")[0]
    output = {
        "bf": 1.0,
        "fs": ["K-", "pi+", "pi+", "pi0"],
        "model": "PHSP",
        "model_params": "",
    }
    assert p._decay_mode_details(tree_Dp, display_photos_keyword=False) == output


def test_decay_model_parsing() -> None:
    """
    This module tests building blocks rather than the API,
    hence the "strange" way to access parsed Lark Tree instances.
    """
    p = DecFileParser(DIR / "../data/test_Bd2DstDst.dec")
    p.parse()

    # Simple decay model without model parameters
    dl = p._parsed_decays[2].children[1]  # 'MySecondD*+' Tree
    assert get_model_name(dl) == "VSS"
    assert get_model_parameters(dl) == ""

    # Decay model with a set of floating-point model parameters
    dl = p._parsed_decays[0].children[1]  # 'B0sig' Tree
    assert get_model_name(dl) == "SVV_HELAMP"
    assert get_model_parameters(dl) == [0.0, 0.0, 0.0, 0.0, 1.0, 0.0]

    # Decay model where model parameter is a string,
    # which matches an XML file for EvtGen
    dl = p._parsed_decays[4].children[1]  # 'MyD0' Tree
    assert get_model_name(dl) == "LbAmpGen"
    assert get_model_parameters(dl) == ["DtoKpipipi_v1"]


def test_decay_model_parsing_with_model_name_substring() -> None:
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


def test_decay_model_parsing_with_variable_defs() -> None:
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


def test_decay_model_parsing_with_model_alias() -> None:
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
            Token("MODEL_NAME", "SLBKPOLE"),
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


def test_multiline_model() -> None:
    p = DecFileParser(DIR / "../data/test_multiline_model.dec")
    p.parse()

    dl = p._parsed_decays[0].children[1]
    assert get_model_name(dl) == "PTO3P"
    assert len(get_model_parameters(dl)) == 96


def test_custom_model_name() -> None:
    p = DecFileParser(DIR / "../data/test_custom_decay_model.dec")
    p.load_additional_decay_models("CUSTOM_MODEL1", "CUSTOM_MODEL2")

    assert p.grammar() is not None
    assert p.grammar_loaded

    p.parse()

    # Simple decay model without model parameters
    dl = p._parsed_decays[0].children[1]  # 'D*+' Tree
    assert get_model_name(dl) == "CUSTOM_MODEL1"
    assert get_model_parameters(dl) == ""

    # Simple decay model with model parameters
    dl = p._parsed_decays[0].children[2]  # 'D*+' Tree
    assert get_model_name(dl) == "CUSTOM_MODEL2"
    assert get_model_parameters(dl) == [1.0, 2.0, 3.0, 4.0]


def test_duplicate_decay_definitions() -> None:
    p = DecFileParser(DIR / "../data/duplicate-decays.dec")

    with (
        pytest.warns(DuplicateDecayWarning, match="(1775)"),
        pytest.warns(DecayAndCDecayWarning) as w,
    ):
        p.parse()

    assert len(w) == 2

    assert p.number_of_decays == 2

    assert p.list_decay_mother_names() == ["Sigma(1775)0", "anti-Sigma(1775)0"]


def test_CDecay_minimalistic_and_incomplete() -> None:
    s = """CDecay   D-
End
"""
    p = DecFileParser.from_string(s)
    with pytest.warns(
        MissingCDecaySourceWarning,
        match="Corresponding 'Decay' statement for 'CDecay' statement",
    ):
        p.parse()


def test_CDecay_minimalistic() -> None:
    s = """Alias        MyD_s*+        D_s*+
Alias        MyD_s*-        D_s*-
ChargeConj   MyD_s*-        MyD_s*+


Decay MyD_s*+
  1.0   D_s+   pi0   VSS;
Enddecay

CDecay MyD_s*-

End
"""
    p = DecFileParser.from_string(s)
    p.parse()


def test_CDecay_self_conjugate() -> None:
    """
    The issue that the phi is in fact self-conjugate is not even checked
    because the 'CDecay' definition is ignored given the 'Decay' statement for the same particle.
    """
    s = """
Decay phi
 1.0   K+   K-   VSS;
Enddecay

CDecay phi
End
"""
    p = DecFileParser.from_string(s)
    with pytest.warns(
        DecayAndCDecayWarning,
        match="The following particles are defined in the input .dec file with both 'Decay' and 'CDecay'",
    ):
        p.parse()

    assert p.number_of_decays == 1


def test_CDecay_self_conjugate_with_Alias() -> None:
    s = """Alias My_phi phi
ChargeConj My_phi My_phi

Decay My_phi
 1.0   K+   K-   VSS;
Enddecay

CDecay My_phi

End
"""
    p = DecFileParser.from_string(s)
    with pytest.warns(
        DecayAndCDecayWarning,
        match="The following particles are defined in the input .dec file with both 'Decay' and 'CDecay'",
    ):
        p.parse()


def test_duplicate_CDecay_definitions_are_only_applied_once() -> None:
    p = DecFileParser.from_string(
        """Decay D0
1.0 K- pi+ PHSP;
Enddecay
CDecay anti-D0
CDecay anti-D0
End
"""
    )

    with pytest.warns(DuplicateCDecayWarning, match="CDecay") as caught:
        p.parse()

    assert len(caught) == 1
    assert p.list_decay_mother_names() == ["D0", "anti-D0"]


def test_list_decay_modes() -> None:
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


def test_list_decay_modes_on_the_fly() -> None:
    """
    Unlike in the example above the charge conjugate decay modes are created
    on the fly from the non-CC. decay.
    """
    p = DecFileParser(DIR / "../data/test_Xicc2XicPiPi.dec")
    with pytest.warns(MissingCDecaySourceWarning, match="anti-Xi_cc-sig") as record:
        p.parse()
    assert len(record) == 1

    # Parsed directly from the dec file
    assert p.list_decay_modes("MyXic+") == [["p+", "K-", "pi+"]]

    # Decay mode created on-the-fly from the above
    assert p.list_decay_modes("MyantiXic-") == [["anti-p-", "K+", "pi-"]]


def test_print_decay_modes_basics() -> None:
    p = DecFileParser(DIR / "../data/test_example_Dst.dec")
    p.parse()

    with pytest.raises(DecayNotFound):
        p.print_decay_modes("D*(2010)-")

    p.print_decay_modes("D*(2010)-", pdg_name=True)


def list_complement(l_m: list[str], l_s: list[str]) -> list[str]:
    return [i for i in l_m if i not in l_s]


def test_print_decay_modes_full() -> None:
    p = DecFileParser(DIR / "../data/test_Bd2Dst0X_D02KPi.dec")
    p.parse()

    decays = list_complement(
        p.list_decay_mother_names(), p.list_charge_conjugate_decays()
    )

    for d in decays:
        print(f"Decay {d}")
        p.print_decay_modes(d, normalize=True)


def test_print_decay_modes_options() -> None:
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
    p1.print_decay_modes("D*+", print_model=False)
    no_model = tmp_stdout.getvalue()
    s = """  0.677        D0 pi+;
  0.307        D+ pi0;
  0.016        D+ gamma;"""
    assert all(_ in no_model for _ in s.split(";\n"))
    tmp_stdout.truncate(0)

    tmp_stdout = io.StringIO()
    sys.stdout = tmp_stdout
    p2.print_decay_modes("B_c+sig")
    photos_included = tmp_stdout.getvalue()
    assert "PHOTOS " in photos_included
    tmp_stdout.truncate(0)

    # Do not forget to reset sys.stdout and clean up!
    sys.stdout = old_stdout
    del old_stdout, tmp_stdout


def _bf_column(output):
    """Extract the leading branching-fraction column from print_decay_modes output."""
    return [float(line.split()[0]) for line in output.strip().splitlines()]


def test_print_decay_modes_ascending(capsys):
    p = DecFileParser(DIR / "../data/test_example_Dst.dec")
    p.parse()

    p.print_decay_modes("D*+")
    descending = _bf_column(capsys.readouterr().out)

    p.print_decay_modes("D*+", ascending=True)
    ascending = _bf_column(capsys.readouterr().out)

    # Default is descending; ascending=True flips the order
    assert descending == sorted(descending, reverse=True)
    assert ascending == sorted(ascending)
    assert ascending == descending[::-1]


def test_print_decay_modes_scale_uses_largest_bf(capsys):
    p = DecFileParser(DIR / "../data/test_example_Dst.dec")
    p.parse()

    # Regardless of sort order, scaling sets the largest BF to `scale`.
    p.print_decay_modes("D*+", scale=0.5)
    desc = _bf_column(capsys.readouterr().out)

    p.print_decay_modes("D*+", scale=0.5, ascending=True)
    asc = _bf_column(capsys.readouterr().out)

    assert max(desc) == pytest.approx(0.5)
    assert max(asc) == pytest.approx(0.5)


def test_print_decay_modes_forbidden_scale() -> None:
    p = DecFileParser(DIR / "../data/test_example_Dst.dec")
    p.parse()

    with pytest.raises(RuntimeError):
        p.print_decay_modes("D*+", scale=5.0)


def test_load_additional_decay_models_too_late() -> None:
    p = DecFileParser(DIR / "../data/test_custom_decay_model.dec")
    # Force the grammar to load.
    assert p.grammar() is not None
    assert p.grammar_loaded

    with pytest.warns(UserWarning, match="already been loaded"):
        p.load_additional_decay_models("CUSTOM_MODEL1")


def test_load_additional_decay_models_repeated_calls() -> None:
    # Regression test: the second call used to store a one-shot itertools.chain
    # iterator that was exhausted the first time the grammar callback consumed
    # it, so the grammar silently lost the additional models.
    p = DecFileParser(DIR / "../data/test_custom_decay_model.dec")
    p.load_additional_decay_models("CUSTOM_MODEL1")
    p.load_additional_decay_models("CUSTOM_MODEL2")

    assert p.grammar() is not None
    p.parse()

    assert get_model_name(p._parsed_decays[0].children[1]) == "CUSTOM_MODEL1"
    assert get_model_name(p._parsed_decays[0].children[2]) == "CUSTOM_MODEL2"


def test_build_decay_chains() -> None:
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


def test_build_decay_chains_minimum_effective_bf_zero_is_no_filter() -> None:
    """minimum_effective_bf=0.0 is a no-op, equivalent to not filtering at all."""
    p = DecFileParser(DIR / "../data/test_example_Dst.dec")
    p.parse()
    assert p.build_decay_chains(
        "D*+", minimum_effective_bf=0.0
    ) == p.build_decay_chains("D*+")


def test_build_decay_chains_minimum_effective_bf_none_is_no_filter() -> None:
    """minimum_effective_bf=None (the default) applies no filtering at all."""
    p = DecFileParser(DIR / "../data/test_example_Dst.dec")
    p.parse()

    assert p.build_decay_chains(
        "D*+", minimum_effective_bf=None
    ) == p.build_decay_chains("D*+")


def test_build_decay_chains_minimum_effective_bf_no_output() -> None:
    """Too stringent a threshold - no chain survives."""
    p = DecFileParser(DIR / "../data/test_example_Dst.dec")
    p.parse()

    assert p.build_decay_chains("D*+", minimum_effective_bf=0.8) == {"D*+": []}


def test_build_decay_chains_minimum_effective_bf_unit_threshold() -> None:
    """minimum_effective_bf=1.0 filters every mode with BF < 1.0.

    Also tests the boundary condition: a mode with BF exactly 1.0 must survive
    (1.0 is not strictly less than 1.0).
    """
    p = DecFileParser(DIR / "../data/test_example_Dst.dec")
    p.parse()

    # All D*+ modes have BF < 1.0, so nothing survives.
    assert p.build_decay_chains("D*+", minimum_effective_bf=1.0) == {"D*+": []}

    # D0 has a single mode with BF = 1.0 exactly — boundary passes.
    assert p.build_decay_chains("D0", minimum_effective_bf=1.0) == {
        "D0": [{"bf": 1, "fs": ["K-", "pi+"], "model": "PHSP", "model_params": ""}]
    }


def test_build_decay_chains_minimum_effective_bf_cache_cleared_between_calls() -> None:
    """Results are independent across successive calls with different thresholds.

    The internal LRU cache is cleared at the start of each build_decay_chains call.
    Without that clearing, a strict first call would poison the cache and cause a
    subsequent looser call to return an erroneously empty result.
    """
    p = DecFileParser(DIR / "../data/test_example_Dst.dec")
    p.parse()

    assert p.build_decay_chains("D*+", minimum_effective_bf=0.8) == {"D*+": []}

    assert p.build_decay_chains("D*+", minimum_effective_bf=0.6) == {
        "D*+": [
            {
                "bf": 0.677,
                "fs": [
                    {
                        "D0": [
                            {
                                "bf": 1,
                                "fs": ["K-", "pi+"],
                                "model": "PHSP",
                                "model_params": "",
                            }
                        ]
                    },
                    "pi+",
                ],
                "model": "VSS",
                "model_params": "",
            },
        ]
    }


def test_build_decay_chains_minimum_effective_bf_single_chain() -> None:
    """At min_bf=0.6, only the D0 pi+ chain (BF 0.677) passes; D+ pi0 (0.307) is filtered.
    Setting D0 as stable just simplifies to a leaf"""
    p = DecFileParser(DIR / "../data/test_example_Dst.dec")
    p.parse()

    assert p.build_decay_chains("D*+", minimum_effective_bf=0.6) == {
        "D*+": [
            {
                "bf": 0.677,
                "fs": [
                    {
                        "D0": [
                            {
                                "bf": 1,
                                "fs": ["K-", "pi+"],
                                "model": "PHSP",
                                "model_params": "",
                            }
                        ]
                    },
                    "pi+",
                ],
                "model": "VSS",
                "model_params": "",
            },
        ]
    }
    assert p.build_decay_chains(
        "D*+", minimum_effective_bf=0.6, stable_particles=["D0"]
    ) == {
        "D*+": [
            {
                "bf": 0.677,
                "fs": [
                    "D0",
                    "pi+",
                ],
                "model": "VSS",
                "model_params": "",
            },
        ]
    }


def test_build_decay_chains_minimum_effective_bf_exact_boundary() -> None:
    """BF product exactly equal to minimum_effective_bf (not strictly less) should pass.

    The filter condition is ``effective_bf < minimum_effective_bf``, so equality must pass.
    At min_bf = 0.677 the D*+ → D0 pi+ mode (BF = 0.677) sits exactly on the boundary
    and should survive; all other modes (BF < 0.677) are filtered.
    A threshold of 0.678 — just above — must filter the D0 chain too.
    """
    p = DecFileParser(DIR / "../data/test_example_Dst.dec")
    p.parse()

    assert p.build_decay_chains("D*+", minimum_effective_bf=0.677) == {
        "D*+": [
            {
                "bf": 0.677,
                "fs": [
                    {
                        "D0": [
                            {
                                "bf": 1,
                                "fs": ["K-", "pi+"],
                                "model": "PHSP",
                                "model_params": "",
                            }
                        ]
                    },
                    "pi+",
                ],
                "model": "VSS",
                "model_params": "",
            }
        ]
    }

    assert p.build_decay_chains("D*+", minimum_effective_bf=0.678) == {"D*+": []}


def test_build_decay_chains_minimum_effective_bf_partial_pi0_and_stable_comparison() -> (
    None
):
    """Partial filtering of pi0 modes and effect of treating pi0 as stable.

    At min_bf=0.3 with D0 and D+ stable:
    - pi0 gamma-gamma passes   (effective BF 0.307 * 0.988... = 0.303 >= 0.3)
    - pi0 e+e-gamma is filtered (effective BF 0.307 * 0.01174... = 0.00360 < 0.3)
    With pi0 also stable the chain structure simplifies to a leaf.
    """
    p = DecFileParser(DIR / "../data/test_example_Dst.dec")
    p.parse()

    assert p.build_decay_chains(
        "D*+", stable_particles=["D0", "D+"], minimum_effective_bf=0.3
    ) == {
        "D*+": [
            {"bf": 0.677, "fs": ["D0", "pi+"], "model": "VSS", "model_params": ""},
            {
                "bf": 0.307,
                "fs": [
                    "D+",
                    {
                        "pi0": [
                            {
                                "bf": 0.988228297,
                                "fs": ["gamma", "gamma"],
                                "model": "PHSP",
                                "model_params": "",
                            }
                        ]
                    },
                ],
                "model": "VSS",
                "model_params": "",
            },
        ]
    }
    assert p.build_decay_chains(
        "D*+", stable_particles=["D0", "D+", "pi0"], minimum_effective_bf=0.3
    ) == {
        "D*+": [
            {"bf": 0.677, "fs": ["D0", "pi+"], "model": "VSS", "model_params": ""},
            {"bf": 0.307, "fs": ["D+", "pi0"], "model": "VSS", "model_params": ""},
        ]
    }


def test_build_decay_chains_minimum_effective_bf_stable_pi0_rescues_chain() -> None:
    """Treating pi0 as stable rescues the D+ pi0 chain that would otherwise be cut.

    At min_bf=0.304 the pi0 gamma-gamma effective BF (0.307 * 0.988... = 0.303) falls just
    below the threshold, so all pi0 modes are filtered and the chain is skipped entirely.
    With pi0 stable its effective BF is 0.307 * 1.0 = 0.307 >= 0.304, so the chain is kept.
    """
    p = DecFileParser(DIR / "../data/test_example_Dst.dec")
    p.parse()

    assert p.build_decay_chains(
        "D*+", stable_particles=["D0", "D+"], minimum_effective_bf=0.306
    ) == {
        "D*+": [{"bf": 0.677, "fs": ["D0", "pi+"], "model": "VSS", "model_params": ""}]
    }
    assert p.build_decay_chains(
        "D*+", stable_particles=["D0", "D+", "pi0"], minimum_effective_bf=0.306
    ) == {
        "D*+": [
            {"bf": 0.677, "fs": ["D0", "pi+"], "model": "VSS", "model_params": ""},
            {"bf": 0.307, "fs": ["D+", "pi0"], "model": "VSS", "model_params": ""},
        ]
    }


def test_build_decay_chains_minimum_effective_bf_first_daughter_filtered() -> None:
    """Chain is skipped when the first daughter's sub-decays are all filtered.

    In D*+ → D+ Mypi0, D+ is the first daughter (index 0).

    With stable=["Mypi0"] at min_bf=0.304: D+ is expanded and finds pi0 inside its own
    decay filtered (effective ≈ 0.303 < 0.304), so D+ returns {} and the break fires
    at i=0 in the D*+ loop.

    With stable=[D+"] at the same threshold: D+ is a stable leaf (skipped via
    ``continue``), and Mypi0 — the second daughter (i=1) — has all its modes filtered,
    so the break fires at i=1 instead.

    Both paths skip the D*+ → D+ pi0 chain, leaving only the D0 chain.
    """
    input_s = """
    Decay D*+
    0.677             D0 pi+       VSS;
    0.307             D+ Mypi0       VSS;
    Enddecay

    Decay D+
    1.0   K-   pi+   pi+   pi0    PHSP;
    Enddecay

    Decay pi0
    0.988228297   gamma   gamma                   PHSP;
    Enddecay

    Decay Mypi0
    0.988228297   gamma   gamma                   PHSP;
    Enddecay
    """
    p = DecFileParser.from_string(input_s)
    p.parse()

    expected = {
        "D*+": [{"bf": 0.677, "fs": ["D0", "pi+"], "model": "VSS", "model_params": ""}]
    }

    # break at i=0: D+ (first daughter) recurses and returns {}
    assert (
        p.build_decay_chains(
            "D*+", stable_particles=["Mypi0"], minimum_effective_bf=0.304
        )
        == expected
    )

    # break at i=1: Mypi0 (second daughter, after the stable D+) returns {}
    assert (
        p.build_decay_chains("D*+", stable_particles=["D+"], minimum_effective_bf=0.304)
        == expected
    )


def test_expand_decay_chains() -> None:
    p = DecFileParser(DIR / "../data/test_example_Dst.dec")
    p.parse()

    output = {
        "D*+": [
            "D*+ -> (D0 -> K- pi+) pi+",
            "D*+ -> (D+ -> (pi0 -> gamma gamma) K- pi+ pi+) (pi0 -> gamma gamma)",
            "D*+ -> (D+ -> (pi0 -> gamma gamma) K- pi+ pi+) (pi0 -> e+ e- gamma)",
            "D*+ -> (D+ -> (pi0 -> gamma gamma) K- pi+ pi+) (pi0 -> e+ e+ e- e-)",
            "D*+ -> (D+ -> (pi0 -> gamma gamma) K- pi+ pi+) (pi0 -> e+ e-)",
            "D*+ -> (D+ -> (pi0 -> e+ e- gamma) K- pi+ pi+) (pi0 -> gamma gamma)",
            "D*+ -> (D+ -> (pi0 -> e+ e- gamma) K- pi+ pi+) (pi0 -> e+ e- gamma)",
            "D*+ -> (D+ -> (pi0 -> e+ e- gamma) K- pi+ pi+) (pi0 -> e+ e+ e- e-)",
            "D*+ -> (D+ -> (pi0 -> e+ e- gamma) K- pi+ pi+) (pi0 -> e+ e-)",
            "D*+ -> (D+ -> (pi0 -> e+ e+ e- e-) K- pi+ pi+) (pi0 -> gamma gamma)",
            "D*+ -> (D+ -> (pi0 -> e+ e+ e- e-) K- pi+ pi+) (pi0 -> e+ e- gamma)",
            "D*+ -> (D+ -> (pi0 -> e+ e+ e- e-) K- pi+ pi+) (pi0 -> e+ e+ e- e-)",
            "D*+ -> (D+ -> (pi0 -> e+ e+ e- e-) K- pi+ pi+) (pi0 -> e+ e-)",
            "D*+ -> (D+ -> (pi0 -> e+ e-) K- pi+ pi+) (pi0 -> gamma gamma)",
            "D*+ -> (D+ -> (pi0 -> e+ e-) K- pi+ pi+) (pi0 -> e+ e- gamma)",
            "D*+ -> (D+ -> (pi0 -> e+ e-) K- pi+ pi+) (pi0 -> e+ e+ e- e-)",
            "D*+ -> (D+ -> (pi0 -> e+ e-) K- pi+ pi+) (pi0 -> e+ e-)",
            "D*+ -> (D+ -> (pi0 -> gamma gamma) K- pi+ pi+) gamma",
            "D*+ -> (D+ -> (pi0 -> e+ e- gamma) K- pi+ pi+) gamma",
            "D*+ -> (D+ -> (pi0 -> e+ e+ e- e-) K- pi+ pi+) gamma",
            "D*+ -> (D+ -> (pi0 -> e+ e-) K- pi+ pi+) gamma",
        ],
        "D*-": [  # NB: decays of anti-D0 and D- are not defined in this DecFile
            "D*- -> anti-D0 pi-",
            "D*- -> (pi0 -> gamma gamma) D-",
            "D*- -> (pi0 -> e+ e- gamma) D-",
            "D*- -> (pi0 -> e+ e+ e- e-) D-",
            "D*- -> (pi0 -> e+ e-) D-",
            "D*- -> D- gamma",
        ],
    }
    for particle, descriptors in output.items():
        all_decays = p.expand_decay_modes(particle)
        assert set(all_decays) == set(descriptors)


def test_Lark_DecayModelAliasReplacement_Transformer() -> None:
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
            Token("MODEL_NAME", "SLBKPOLE"),
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

    tree_decayline = next(iter(unaliased_tree.find_data("decayline")))
    assert get_model_name(tree_decayline) == "SLBKPOLE"
    assert get_model_parameters(tree_decayline) == ["1.0", "0.303", "1.0", "2.112"]


def test_Lark_DecayModelParamValueReplacement_Visitor_no_params() -> None:
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
                    Tree("model", [Token("MODEL_NAME", "PHSP")]),
                ],
            ),
        ],
    )

    DecayModelParamValueReplacement().visit(t)

    # The visitor should do nothing in this case
    tree_decayline = next(iter(t.find_data("decayline")))
    assert get_model_name(tree_decayline) == "PHSP"
    assert get_model_parameters(tree_decayline) == ""


def test_Lark_DecayModelParamValueReplacement_Visitor_single_value() -> None:
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
                            Token("MODEL_NAME", "VSS_BMIX"),
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
    tree_decayline = next(iter(t.find_data("decayline")))
    assert get_model_name(tree_decayline) == "VSS_BMIX"
    assert get_model_parameters(tree_decayline) == ["dm"]

    dict_define_defs = {"dm": 0.507e12}

    DecayModelParamValueReplacement(define_defs=dict_define_defs).visit(t)

    # The model parameter 'dm' should now be replaced by its value
    assert get_model_name(tree_decayline) == "VSS_BMIX"
    assert get_model_parameters(tree_decayline) == [507000000000.0]


def test_Lark_DecayModelParamValueReplacement_Visitor_list() -> None:
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
                            Token("MODEL_NAME", "SVV_HELAMP"),
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
    tree_decayline = next(iter(t.find_data("decayline")))
    assert get_model_name(tree_decayline) == "SVV_HELAMP"
    assert get_model_parameters(tree_decayline) == [0.0, 0.0, 0.0, 0.0, 1.0, 0.0]


def test_Lark_ChargeConjugateReplacement_Visitor() -> None:
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
                    Tree("model", [Token("MODEL_NAME", "PHSP")]),
                ],
            ),
        ],
    )

    ChargeConjugateReplacement().visit(t)

    assert get_decay_mother_name(t) == "anti-D0"
    assert get_final_state_particle_names(t.children[1]) == ["K+", "pi-"]


def test_Lark_ChargeConjugateReplacement_Visitor_with_aliases() -> None:
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
                    Tree("model", [Token("MODEL_NAME", "PHSP")]),
                ],
            ),
        ],
    )

    dict_ChargeConj_defs = {"MyD0": "MyAnti-D0"}

    ChargeConjugateReplacement(charge_conj_defs=dict_ChargeConj_defs).visit(t)

    assert get_decay_mother_name(t) == "MyAnti-D0"
    assert get_final_state_particle_names(t.children[1]) == ["K+", "pi-"]


def test_creation_charge_conjugate_decays_in_decfile_with_aliases() -> None:
    """
    Decay file contains 5 particle decays defined via a 'Decay' statement
    and the 5 charge-conjugate decays defined via a 'CDecay' statement.
    The decay modes for the latter 5 should be created on the fly,
    hence providing in total 10 sets of particle decays parsed.
    """
    p = DecFileParser(DIR / "../data/test_Bd2DstDst.dec")
    p.parse()

    assert p.number_of_decays == 10


def test_creation_charge_conjugate_decays_in_decfile_without_CDecay_defs() -> None:
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


def test_main_DECAYdotDEC_file() -> None:
    p = DecFileParser(DIR / "../../src/decaylanguage/data/DECAY_LHCB.DEC")
    # This warning is issued because the file contains aliases
    # to heavy particles such as B_c(2S)+ for which no PDG ID is yet available
    # in the Particle package.
    # To be fixed soon ...
    with pytest.raises(MisconfiguredAliasWarning) as _w:
        p.parse()

    assert p.number_of_decays == 510


def test_BELLE2_decfile() -> None:
    p = DecFileParser(DIR / "../../src/decaylanguage/data/DECAY_BELLE2.DEC")
    p.parse()

    assert p.number_of_decays == 363


def test_get_decay_mother_name_wrong_Tree() -> None:
    bad = Tree("decayline", [Tree("value", [Token("SIGNED_NUMBER", "1.0")])])
    with pytest.raises(RuntimeError):
        get_decay_mother_name(bad)


def test_get_branching_fraction_wrong_Tree() -> None:
    bad = Tree("particle", [Token("LABEL", "B0sig")])
    with pytest.raises(RuntimeError):
        get_branching_fraction(bad)


def test_get_final_state_particles_wrong_Treem() -> None:
    bad = Tree("particle", [Token("LABEL", "B0sig")])
    with pytest.raises(RuntimeError):
        get_final_state_particles(bad)


def test_get_final_state_particle_names_wrong_Tree() -> None:
    bad = Tree("particle", [Token("LABEL", "B0sig")])
    with pytest.raises(RuntimeError):
        get_final_state_particle_names(bad)


def test_get_model_name_wrong_Tree() -> None:
    bad = Tree("particle", [Token("LABEL", "B0sig")])
    with pytest.raises(RuntimeError):
        get_model_name(bad)


def test_get_model_parameters_wrong_Tree() -> None:
    bad = Tree("particle", [Token("LABEL", "B0sig")])
    with pytest.raises(RuntimeError):
        get_model_parameters(bad)


def test_align_items_simple() -> None:
    to_align = ["a", "quick", "brown", "fox"]
    aligned = DecFileParser._align_items(to_align)

    assert aligned == ["a    ", "quick", "brown", "fox  "]


def test_align_items_simple_right_align() -> None:
    to_align = ["a", "quick", "brown", "fox"]
    aligned = DecFileParser._align_items(to_align, align_mode="right")

    assert aligned == ["    a", "quick", "brown", "  fox"]


def test_align_items_complex() -> None:
    to_align = [
        ("alpha", "beta", "gamma"),
        ("a", "b", "c"),
        ("01", "02", "03"),
    ]

    aligned = DecFileParser._align_items(to_align)

    assert aligned == ["alpha beta gamma", "a     b    c    ", "01    02   03   "]


def test_align_items_complex_right_align() -> None:
    to_align = [
        ("alpha", "beta", "gamma"),
        ("a", "b", "c"),
        ("01", "02", "03"),
    ]

    aligned = DecFileParser._align_items(to_align, align_mode="right")

    assert aligned == ["alpha beta gamma", "    a    b     c", "   01   02    03"]


def test_align_items_simple_wrong_align_mode() -> None:
    to_align = ["a", "quick", "brown", "fox"]

    with pytest.raises(ValueError, match="Unknown align mode"):
        _ = DecFileParser._align_items(to_align, align_mode="nonexistent")


def test_align_items_complex_wrong_align_mode() -> None:
    to_align = [
        ("alpha", "beta", "gamma"),
        ("a", "b", "c"),
        ("01", "02", "03"),
    ]

    with pytest.raises(ValueError, match="Unknown align mode"):
        _ = DecFileParser._align_items(to_align, align_mode="nonexistent")
