# Copyright (c) 2018-2023, Eduardo Rodrigues and Henry Schreiner.
#
# Distributed under the 3-clause BSD license, see accompanying file LICENSE
# or https://github.com/scikit-hep/decaylanguage for details.

"""
Collection of enums and info to help characterising .dec decay files.
"""

from __future__ import annotations

from enum import IntEnum


class PhotosEnum(IntEnum):
    no = 0
    yes = 1


# This list should match the list specified in the decay file parser file
# 'decaylanguage/data/decfile.lark'!
known_decay_models = (
    "BaryonPCR",
    "BCL",
    "BGL",
    "BT02PI_CP_ISO",
    "BTO3PI_CP",
    "BTOSLLALI",
    "BTOSLLBALL",
    "BTOXSGAMMA",
    "BTOXSLL",
    "CB3PI-MPP",
    "CB3PI-P00",
    "D_DALITZ",
    "ETAPRIME_DALITZ",
    "ETA_DALITZ",
    "ETA_FULLDALITZ",
    "ETA_PI0DALITZ",
    "FLATQ2",
    "GENERIC_DALITZ",
    "GOITY_ROBERTS",
    "HELAMP",
    "HQET3",
    "HQET2",
    "HQET",
    "ISGW2",
    "ISGW",
    "LbAmpGen",
    "LLSW",
    "MELIKHOV",
    "OMEGA_DALITZ",
    "PARTWAVE",
    "PHSP",
    "PI0_DALITZ",
    "PROPSLPOLE",
    "PVV_CPLH",
    "PYCONT",
    "PYTHIA",
    "SLBKPOLE",
    "SLN",
    "SLPOLE",
    "SSD_CP",
    "SSD_DirectCP",
    "SSS_CP",
    "SSS_CP_PNG",
    "SSS_CPT",
    "STS_CP",
    "STS",
    "SVP_CP",
    "SVP_HELAMP",
    "SVP",
    "SVS_CP_ISO",
    "SVS_CPLH",
    "SVS_CP",
    "SVS_NONCPEIGEN",
    "SVS",
    "SVV_CPLH",
    "SVV_CP",
    "SVV_HELAMP",
    "SVV_NONCPEIGEN",
    "SVVHELCPMIX",
    "TAUHADNU",
    "TAULNUNU",
    "TAUSCALARNU",
    "TAUVECTORNU",
    "TSS",
    "TVP",
    "TVS_PWAVE",
    "VLL",
    "VSP_PWAVE",
    "VSS_BMIX",
    "VSS_MIX",
    "VSS",
    "VUB",
    "VVPIPI",
    "VVP",
    "VVS_PWAVE",
    "YMSTOYNSPIPICLEO",
    "YMSTOYNSPIPICLEOBOOST",
)
