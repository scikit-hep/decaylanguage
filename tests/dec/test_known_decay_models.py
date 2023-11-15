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
    # ("BT02PI_CP_ISO", ""),  # No dec file available for testing from LHCb or Belle-II
    ("BTO3PI_CP", [0.507e12, 1.365]),
    ("BTODDALITZCPK", [1.22, 2.27, 0.10]),
    ("BToDiBaryonlnupQCD", [67.7, -280.0, -38.3, -840.0, -10.1, -157.0, 800000]),
    ("BTOSLLALI", ""),
    ("BTOSLLBALL", [6.0]),
    ("BTOSLLMS", [5.0, 5.0, 0.0, 1.0, 0.88, 0.227, 0.22, 0.34]),
    ("BTOSLLMSEXT", [5.0, 5.0, 0.0, 1.0, 0.88, 0.227, 0.22, 0.34, 1.0, 0.0, -1.0, 0.0]),
    ("BTOVLNUBALL", [0.308, 36.54, -0.054, 0.288, 48.94, 1.484, -1.049, 39.52]),
    ("BTOXSGAMMA", [2.0]),
    # ("BTOXELNU", ""),
    ("BTOXSLL", [4.8, 0.2, 0.0, 0.41]),
    (
        "BQTOLLLLHYPERCP",
        [
            2.5,
            0.214,
            0.0001,
            0.0001,
            1.0,
            1.0,
            450.0,
            0.0,
            450.0,
            0.0,
            380.0,
            0.0,
            380.0,
            0.0,
        ],
    ),
    ("BQTOLLLL", [5.0, 5.0, 0.0, 1.0, 0.88, 0.227, 0.22, 0.34]),
    ("CB3PI-MPP", [1.365]),
    ("CB3PI-P00", [1.365]),
    ("D_DALITZ", ""),
    ("D_hhhh", [11.0]),
    ("D0GAMMADALITZ", ""),
    ("D0MIXDALITZ", [0.0, 0.0, 1.0, 0.0, 0.0]),
    ("DToKpienu", ""),
    ("ETAPRIME_DALITZ", [-0.047, -0.069, 0.0, 0.073]),
    ("ETA_DALITZ", ""),
    ("ETA_FULLDALITZ", [-1.128, 0.153, 0.0, 0.085, 0.0, 0.173]),
    ("ETA_LLPIPI", ""),
    ("ETA_PI0DALITZ", [-0.0135]),
    ("FLATQ2", [1.0]),
    ("FLATSQDALITZ", ""),
    ("FOURBODYPHSP", [1.3, 2.5, 1.3, 2.5]),
    # ("GENERIC_DALITZ", ""),  # No dec file available for testing from LHCb or Belle-II
    ("GOITY_ROBERTS", ""),
    ("HELAMP", [1.0, 0.0, 1.0, 0.0]),
    ("HQET3", [0.920, 1.205, 1.21, 1.404, 0.854]),
    ("HQET2", [1.18, 1.074]),
    ("HQET", [0.77, 1.33, 0.92]),
    ("ISGW2", ""),
    # ("ISGW", ""),
    ("KS_PI0MUMU", [1.2, 0.49, -3.9, 0.2, 2.5]),
    ("Lb2Baryonlnu", [1.0, 1.0, 1.0, 1.0]),
    ("Lb2plnuLCSR", [1.0, 1.0, 1.0, 1.0]),
    ("Lb2plnuLQCD", [1.0, 1.0, 1.0, 1.0]),
    ("LbAmpGen", ["DtoKpipipi"]),
    ("LLSW", [0.71, -1.6, -0.5, 2.9]),
    ("LNUGAMMA", [0.35, 3.0, 5.0, 0.0]),
    # ("LQCD", ""),
    # ("MELIKHOV", ""),  # No dec file available for testing from LHCb or Belle-II
    ("OMEGA_DALITZ", ""),
    ("PARTWAVE", [0.0, 0.0, 1.0, 0.0, 0.0, 0.0]),
    ("PHI_DALITZ", ""),
    ("PHSPDECAYTIMECUT", [0.29]),
    ("PHSPFLATLIFETIME", [12]),
    ("PHSP", ""),
    ("PI0_DALITZ", ""),
    # ("PROPSLPOLE", ""),  # No dec file available for testing from LHCb or Belle-II
    (
        "PTO3P",
        [
            "MAXPDF",
            0.09,
            "AMPLITUDE",
            "RESONANCE",
            "BC",
            "K*0",
            "ANGULAR",
            "AC",
            "TYPE",
            "RBW_ZEMACH",
            "DVFF",
            "BLATTWEISSKOPF",
            4.0,
            "COEFFICIENT",
            "POLAR_RAD",
            1.0,
            0.0,
            "AMPLITUDE",
            "LASS",
            "BC",
            1.412,
            0.294,
            2.07,
            3.32,
            1.8,
            "COEFFICIENT",
            "POLAR_RAD",
            32.9,
            -0.38,
            "AMPLITUDE",
            "RESONANCE",
            "AB",
            "phi",
            "ANGULAR",
            "CA",
            "TYPE",
            "RBW_ZEMACH",
            "DVFF",
            "BLATTWEISSKOPF",
            4.0,
            "COEFFICIENT",
            "POLAR_RAD",
            6.04,
            2.99,
            "AMPLITUDE",
            "RESONANCE",
            "AB",
            "f_0",
            0.965,
            0.695,
            "ANGULAR",
            "CA",
            "TYPE",
            "FLATTE",
            0.165,
            0.13957,
            0.13957,
            "COEFFICIENT",
            "POLAR_RAD",
            5.28,
            0.48,
            "AMPLITUDE",
            "RESONANCE",
            "AB",
            "f_0(1500)",
            1.539,
            0.257,
            "ANGULAR",
            "CA",
            "TYPE",
            "RBW_ZEMACH",
            "COEFFICIENT",
            "POLAR_RAD",
            24.0,
            1.29,
            "AMPLITUDE",
            "RESONANCE",
            "AB",
            "chi_c0",
            "ANGULAR",
            "CA",
            "TYPE",
            "RBW_ZEMACH",
            "DVFF",
            "BLATTWEISSKOPF",
            4.0,
            "COEFFICIENT",
            "POLAR_RAD",
            0.437,
            -1.02,
            "AMPLITUDE",
            "PHASESPACE",
            "COEFFICIENT",
            "POLAR_RAD",
            6.9,
            -2.29,
        ],
    ),
    ("PVV_CPLH", [0.02, 1.0, 0.49, 2.50, 0.775, 0.0, 0.4, -0.17]),
    ("PYCONT", ""),
    ("PYTHIA", [21]),
    # ("SLBKPOLE", ""),
    ("SLL", ""),
    ("SLN", ""),
    # ("SLPOLE", ""),
    ("SSD_CP", [507000000000.0, 0.0, 1.0, -0.78, 1.0, 0.0, -1.0, 0.0]),
    ("SSD_DirectCP", [0.39]),
    # ("SSS_CP_PNG", ""),  # No dec file available for testing from LHCb or Belle-II
    ("SSS_CP", [0.0, 0.507e12, -1.0, 1.0, 0.0, 1.0, 0.0]),
    # ("SSS_CPT", ""),  # No dec file available for testing from LHCb or Belle-II
    # ("STS_CP", ""),  # No dec file available for testing from LHCb or Belle-II
    ("STS", ""),
    # ("SVP_CP", ""),  # No dec file available for testing from LHCb or Belle-II
    ("SVP_HELAMP", [1.0, 0.0, 1.0, 0.0]),
    ("SVP", ""),
    # ("SVS_CP_ISO", ""),  # No dec file available for testing from LHCb or Belle-II
    # ("SVS_CPLH", ""),  # No dec file available for testing from LHCb or Belle-II
    (
        "SVS_CP",
        [
            0.3814,
            0.507e12,
            1,
            1,
            0,
            1,
            0,
        ],
    ),
    ("SVS_NONCPEIGEN", [1.365, 0.507e12, 1.0, 3.0, 0.0, 1.0, 0.0, 1.0, 0.0, 3.0, 0.0]),
    ("SVS", ""),
    # ("SVV_CPLH", ""),  # No dec file available for testing from LHCb or Belle-II
    ("SVV_CP", [0.39, 0.507e12, 1, 0.490, 2.5, 1.10, 0.0, 0.4, -0.17]),
    ("SVV_HELAMP", [0.48, 0.0, 0.734, 0.0, 0.48, 0.0]),
    # ("SVV_NONCPEIGEN", ""),  # No dec file available for testing from LHCb or Belle-II
    # ("SVVHELCPMIX", ""),  # No dec file available for testing from LHCb or Belle-II
    ("TAUHADNU", [-0.108, 0.775, 0.149, 1.364, 0.400]),
    ("TAULNUNU", ""),
    ("TAUOLA", [5]),
    ("TAUSCALARNU", ""),
    ("TAUVECTORNU", ""),
    ("THREEBODYPHSP", [14.00, 16.40]),
    ("TSS", ""),
    ("TVP", ""),
    ("TVS_PWAVE", [0, 0, 1, 0, 0, 0.0]),
    ("VLL", ""),
    ("VSP_PWAVE", ""),
    ("VSS_BMIX", [507000000000.0]),
    # ("VSS_MIX", ""),  # No dec file available for testing from LHCb or Belle-II
    ("VSS", ""),
    ("VTOSLL", ""),
    ("VUB", [4.691, 1.869, 0.22, 1.0, 0.28, 1.0]),
    ("VVPIPI", ""),
    ("VVP", [1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]),
    ("VVS_PWAVE", [0.9788, 0.0, 0.0, 0.0, 0.0212, 0.0]),
    ("XLL", [1]),
    ("YMSTOYNSPIPICLEO", [-0.753, 0.0]),
    ("YMSTOYNSPIPICLEOBOOST", [-0.753, 0.0]),
)


def test_parsing_of_all_known_models_are_tested():
    assert (
        len(parsed_models) == len(known_decay_models) - 19
    )  # subtract for now the number of models not yet tested + the number of models presently with no test available


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
