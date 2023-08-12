# Copyright (c) 2018-2023, Eduardo Rodrigues and Henry Schreiner.
#
# Distributed under the 3-clause BSD license, see accompanying file LICENSE
# or https://github.com/scikit-hep/decaylanguage for details.

from __future__ import annotations

from pathlib import Path

import pytest

from decaylanguage.dec.dec import DecFileParser, get_model_name, get_model_parameters
from decaylanguage.dec.enums import known_decay_models

DIR = Path(__file__).parent.resolve()


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


# TODO: actually test all models - takes time
parsed_models = (
    ("BaryonPCR", [1.0, 1.0, 1.0, 1.0]),
    ("BC_SMN", ""),  # No dec file found in EvtGen repository
    ("BC_TMN", ""),  # No dec file found in EvtGen repository
    ("BC_VHAD", ""),  # No dec file found in EvtGen repository
    ("BC_VMN", ""),  # No dec file found in EvtGen repository
    ("BCL", ""),  # No dec file found in EvtGen repository
    ("BGL", ""),  # No dec file found in EvtGen repository
    ("BLLNUL", ""),  # No dec file found in EvtGen repository
    ("BNOCB0TO4PICP", ""),
    ("BNOCBPTO3HPI0", ""),
    ("BNOCBPTOKSHHH", ""),
    ("BS_MUMUKK", ""),
    ("BSTOGLLISRFSR", ""),
    ("BSTOGLLMNT", ""),
    ("BT02PI_CP_ISO", ""),
    ("BTO3PI_CP", ""),
    ("BTODDALITZCPK", ""),
    ("BToDiBaryonlnupQCD", ""),
    ("BTOSLLALI", ""),
    ("BTOSLLBALL", ""),
    ("BTOSLLMS", ""),
    ("BTOSLLMSEXT", ""),
    ("BTOVLNUBALL", ""),
    ("BTOXSGAMMA", [2.0]),
    ("BTOXELNU", ""),
    ("BTOXSLL", [4.8, 0.2, 0.0, 0.41]),
    ("BQTOLLLLHYPERCP", ""),
    ("BQTOLLLL", ""),
    ("CB3PI-MPP", ""),
    ("CB3PI-P00", ""),
    ("D_DALITZ", ""),
    ("D_hhhh", ""),
    ("D0GAMMADALITZ", ""),
    ("doKm", ""),
    ("DToKpienu", ""),
    ("ETAPRIME_DALITZ", ""),
    ("ETA_DALITZ", ""),
    ("ETA_FULLDALITZ", ""),
    ("ETA_LLPIPI", ""),
    ("ETA_PI0DALITZ", [-0.0135]),
    ("FLATQ2", ""),
    ("FLATSQDALITZ", ""),
    ("FOURBODYPHSP", ""),
    ("GENERIC_DALITZ", ""),
    ("GOITY_ROBERTS", ""),
    ("HELAMP", ""),
    ("HQET3", ""),
    ("HQET2", ""),
    ("HQET", ""),
    ("imqp", ""),
    ("ISGW2", ""),
    ("ISGW", ""),
    ("KS_PI0MUMU", ""),
    ("Lb2Baryonlnu", ""),
    ("Lb2plnuLCSR", ""),
    ("Lb2plnuLQCD", ""),
    ("LbAmpGen", ""),
    ("LLSW", ""),
    ("LNUGAMMA", [0.35, 3.0, 5.0, 0.0]),
    ("LQCD", ""),
    ("MELIKHOV", ""),
    ("OMEGA_DALITZ", ""),
    ("PARTWAVE", ""),
    ("PHI_DALITZ", ""),
    ("PHSPDECAYTIMECUT", ""),
    ("PHSPFLATLIFETIME", ""),
    ("PHSP", ""),
    ("PI0_DALITZ", ""),
    ("PROPSLPOLE", ""),
    ("PTO3P", ""),
    ("PVV_CPLH", ""),
    ("PYCONT", ""),
    ("PYTHIA", [21]),
    ("SLBKPOLE", ""),
    ("SLL", ""),
    ("SLN", ""),
    ("SLPOLE", ""),
    ("SSD_CP", [507000000000.0, 0.0, 1.0, -0.78, 1.0, 0.0, -1.0, 0.0]),
    ("SSD_DirectCP", ""),
    ("SSS_CP_PNG", ""),
    ("SSS_CP", ""),
    ("SSS_CPT", ""),
    ("STS_CP", ""),
    ("STS", ""),
    ("SVP_CP", ""),
    ("SVP_HELAMP", ""),
    ("SVP", ""),
    ("SVS_CP_ISO", ""),
    ("SVS_CPLH", ""),
    ("SVS_CP", ""),
    ("SVS_NONCPEIGEN", ""),
    ("SVS", ""),
    ("SVV_CPLH", ""),
    ("SVV_CP", ""),
    ("SVV_HELAMP", ""),
    ("SVV_NONCPEIGEN", ""),
    ("SVVHELCPMIX", ""),
    ("TAUHADNU", [-0.108, 0.775, 0.149, 1.364, 0.400]),
    ("TAULNUNU", ""),
    ("TAUOLA", ""),
    ("TAUSCALARNU", ""),
    ("TAUVECTORNU", ""),
    ("THREEBODYPHSP", ""),
    ("TSS", ""),
    ("TVP", ""),
    ("TVS_PWAVE", ""),
    ("VLL", ""),
    ("VSP_PWAVE", ""),
    ("VSS_BMIX", [507000000000.0]),
    ("VSS_MIX", ""),
    ("VSS", ""),
    ("VTOSLL", ""),
    ("VUB", ""),
    ("VVPIPI", ""),
    ("VVP", ""),
    ("VVS_PWAVE", ""),
    ("XLL", ""),
    ("YMSTOYNSPIPICLEO", [-0.753, 0.0]),
    ("YMSTOYNSPIPICLEOBOOST", [-0.753, 0.0]),
)


def test_parsing_of_all_known_models_are_tested():
    assert len(parsed_models) == len(known_decay_models)


@pytest.mark.parametrize(("decay_model", "expected_model_parameters"), parsed_models)
def test_model_parsing(decay_model: str, expected_model_parameters: str):
    """
    Verify that the model and all its parameters (in case a model requires them)
    are parsed with no errors but, most importantly, correctly.
    """
    # TODO: actually test all models - takes time
    if decay_model not in {
        "BaryonPCR",
        "BTOXSGAMMA",
        "BTOXSLL",
        "ETA_PI0DALITZ",
        "GOITY_ROBERTS",
        "LNUGAMMA",
        "OMEGA_DALITZ",
        "PHSP",
        "PYTHIA",
        "SSD_CP",
        "TAUHADNU",
        "TAULNUNU",
        "TAUSCALARNU",
        "TAUVECTORNU",
        "TSS",
        "VLL",
        "VSP_PWAVE",
        "VSS_BMIX",
        "VSS",
        "YMSTOYNSPIPICLEO",
        "YMSTOYNSPIPICLEOBOOST",
    }:
        pass
    else:
        dfp = DecFileParser(DIR / f"../data/models/model-{decay_model}.dec")
        dfp.parse()

        # Get the Lark Tree instance of the single decay mode in the file
        parsed_Tree = dfp._find_decay_modes(dfp.list_decay_mother_names()[0])[0]

        assert get_model_name(parsed_Tree) == decay_model
        assert get_model_parameters(parsed_Tree) == expected_model_parameters
