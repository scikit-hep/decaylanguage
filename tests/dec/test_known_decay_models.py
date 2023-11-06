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
            if "MODEL_NAME.2 :" in line:
                break
        models = (
            line.split(":")[1][: -len(r"//\b/")].strip(" ()").strip("\n").split('"|"')
        )
        models = [m.strip('"') for m in models]

        assert models == list(known_decay_models)


# TODO: actually test all models - takes time
parsed_models = (
    ("BaryonPCR", [1.0, 1.0, 1.0, 1.0]),
    ("BC_SMN", [2.0]),
    ("BC_TMN", [3.0]),
    ("BC_VHAD", [1.0]),
    ("BC_VMN", [2.0]),
    ("BCL", [0.419, -0.495, -0.43, 0.22, 0.51, -1.70, 1.53, 4.52]),
    ("BGL", [0.02596, -0.06049, 0.01311, 0.01713, 0.00753, -0.09346]),
    ("BLLNUL", [0.026, 0.01, 2.9]),
    ("BNOCB0TO4PICP", [-1.507964474, 0.5065e12, 0.0, 1.1, 0.0, 1.86965]),
    ("BNOCBPTO3HPI0", [0.0, 2.0, 0.0, 2.0]),
    ("BNOCBPTOKSHHH", ""),
    (
        "BS_MUMUKK",
        [
            0.0,
            0.0,
            -0.03,
            1.0,
            0.11,
            3.315,
            -0.03,
            1.0,
            0.5241,
            0.0,
            -0.03,
            1.0,
            0.2504,
            0.06159,
            -0.03,
            1.0,
            -3.26,
            -0.03,
            1.0,
            0.6603,
            0.0805,
            17.7,
            0.9499,
            1.2,
            1,
        ],
    ),
    (
        "BSTOGLLISRFSR",
        [5.0, 5, 0, 0, 1, 0.000001, 0.8250, 0.22509, 0.1598, 0.3499, 4.5],
    ),
    ("BSTOGLLMNT", [5.0, 5, 1, 1, 0.02, 0.88, 0.227, 0.22, 0.34]),
    # ("BT02PI_CP_ISO", ""),  # No dec file available from LHCb or Belle-II
    ("BTO3PI_CP", [0.507e12, 1.365]),
    ("BTODDALITZCPK", [1.22, 2.27, 0.10]),
    ("BToDiBaryonlnupQCD", [67.7, -280.0, -38.3, -840.0, -10.1, -157.0, 800000]),
    # ("BTOSLLALI", ""),
    # ("BTOSLLBALL", ""),
    ("BTOSLLMS", [5.0, 5.0, 0.0, 1.0, 0.88, 0.227, 0.22, 0.34]),
    # ("BTOSLLMSEXT", ""),
    # ("BTOVLNUBALL", ""),
    ("BTOXSGAMMA", [2.0]),
    # ("BTOXELNU", ""),
    ("BTOXSLL", [4.8, 0.2, 0.0, 0.41]),
    # ("BQTOLLLLHYPERCP", ""),
    # ("BQTOLLLL", ""),
    # ("CB3PI-MPP", ""),
    # ("CB3PI-P00", ""),
    ("D_DALITZ", ""),
    ("D_hhhh", [11.0]),
    ("D0GAMMADALITZ", ""),
    ("D0MIXDALITZ", [0.0, 0.0, 1.0, 0.0, 0.0]),
    ("DToKpienu", ""),
    ("ETAPRIME_DALITZ", [-0.047, -0.069, 0.0, 0.073]),
    ("ETA_DALITZ", ""),
    ("ETA_FULLDALITZ", [-1.128, 0.153, 0.0, 0.085, 0.0, 0.173]),
    # ("ETA_LLPIPI", ""),
    ("ETA_PI0DALITZ", [-0.0135]),
    # ("FLATQ2", ""),
    ("FLATSQDALITZ", ""),
    # ("FOURBODYPHSP", ""),
    # ("GENERIC_DALITZ", ""),  # no dec file currently available for a test
    ("GOITY_ROBERTS", ""),
    # ("HELAMP", ""),
    ("HQET3", [0.920, 1.205, 1.21, 1.404, 0.854]),
    ("HQET2", [1.18, 1.074]),
    # ("HQET", ""),
    # ("imqp", ""),
    # ("ISGW2", ""),
    # ("ISGW", ""),
    # ("KS_PI0MUMU", ""),
    # ("Lb2Baryonlnu", ""),
    # ("Lb2plnuLCSR", ""),
    # ("Lb2plnuLQCD", ""),
    # ("LbAmpGen", ""),
    ("LLSW", [0.71, -1.6, -0.5, 2.9]),
    ("LNUGAMMA", [0.35, 3.0, 5.0, 0.0]),
    # ("LQCD", ""),
    # ("MELIKHOV", ""),
    ("OMEGA_DALITZ", ""),
    ("PARTWAVE", [0.0, 0.0, 1.0, 0.0, 0.0, 0.0]),
    ("PHI_DALITZ", ""),
    # ("PHSPDECAYTIMECUT", ""),
    # ("PHSPFLATLIFETIME", ""),
    ("PHSP", ""),
    ("PI0_DALITZ", ""),
    # ("PROPSLPOLE", ""),
    # ("PTO3P", ""),
    # ("PVV_CPLH", ""),
    # ("PYCONT", ""),
    ("PYTHIA", [21]),
    # ("SLBKPOLE", ""),
    # ("SLL", ""),
    # ("SLN", ""),
    # ("SLPOLE", ""),
    ("SSD_CP", [507000000000.0, 0.0, 1.0, -0.78, 1.0, 0.0, -1.0, 0.0]),
    # ("SSD_DirectCP", ""),
    # ("SSS_CP_PNG", ""),
    # ("SSS_CP", ""),
    # ("SSS_CPT", ""),
    # ("STS_CP", ""),
    # ("STS", ""),
    # ("SVP_CP", ""),
    # ("SVP_HELAMP", ""),
    # ("SVP", ""),
    # ("SVS_CP_ISO", ""),
    # ("SVS_CPLH", ""),
    # ("SVS_CP", ""),
    # ("SVS_NONCPEIGEN", ""),
    # ("SVS", ""),
    # ("SVV_CPLH", ""),
    # ("SVV_CP", ""),
    # ("SVV_HELAMP", ""),
    # ("SVV_NONCPEIGEN", ""),
    # ("SVVHELCPMIX", ""),
    ("TAUHADNU", [-0.108, 0.775, 0.149, 1.364, 0.400]),
    ("TAULNUNU", ""),
    # ("TAUOLA", ""),
    ("TAUSCALARNU", ""),
    ("TAUVECTORNU", ""),
    ("THREEBODYPHSP", [14.00, 16.40]),
    ("TSS", ""),
    # ("TVP", ""),
    # ("TVS_PWAVE", ""),
    ("VLL", ""),
    ("VSP_PWAVE", ""),
    ("VSS_BMIX", [507000000000.0]),
    # ("VSS_MIX", ""),
    ("VSS", ""),
    # ("VTOSLL", ""),
    # ("VUB", ""),
    # ("VVPIPI", ""),
    # ("VVP", ""),
    # ("VVS_PWAVE", ""),
    # ("XLL", ""),
    ("YMSTOYNSPIPICLEO", [-0.753, 0.0]),
    ("YMSTOYNSPIPICLEOBOOST", [-0.753, 0.0]),
)


def test_parsing_of_all_known_models_are_tested():
    assert (
        len(parsed_models) == len(known_decay_models) - 65
    )  # subtract for now the number of models not yet tested


@pytest.mark.parametrize(("decay_model", "expected_model_parameters"), parsed_models)
def test_model_parsing(decay_model: str, expected_model_parameters: str):
    """
    Verify that the model and all its parameters (in case a model requires them)
    are parsed with no errors but, most importantly, correctly.
    """
    dfp = DecFileParser(DIR / f"../data/models/model-{decay_model}.dec")
    dfp.parse()

    # Get the Lark Tree instance of the single decay mode in the file
    parsed_Tree = dfp._find_decay_modes(dfp.list_decay_mother_names()[0])[0]

    assert get_model_name(parsed_Tree) == decay_model
    assert get_model_parameters(parsed_Tree) == expected_model_parameters
