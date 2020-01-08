# Copyright (c) 2018-2020, Eduardo Rodrigues and Henry Schreiner.
#
# Distributed under the 3-clause BSD license, see accompanying file LICENSE
# or https://github.com/scikit-hep/decaylanguage for details.

"""
Collection of enums and info to help characterising .dec decay files.
"""

# Backport needed if Python 2 is used
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
    "GOITY_ROBERTS",
    "HELAMP",
    "HQET",
    "ISGW2",
    "LbAmpGen",
    "LLSW",
    "OMEGA_DALITZ",
    "PARTWAVE",
    "PHSP",
    "PI0_DALITZ",
    "PYCONT",
    "PYTHIA",
    "SLN",
    "SSD_CP",
    "SSS_CP",
    "STS",
    "SVP_HELAMP",
    "SVS",
    "SVV_CP",
    "SVV_HELAMP",
    "TAUHADNU",
    "TAULNUNU",
    "TAUSCALARNU",
    "TAUVECTORNU",
    "TSS",
    "TVS_PWAVE",
    "VLL",
    "VSP_PWAVE",
    "VSS_BMIX",
    "VSS",
    "VUB",
    "VVPIPI",
    "VVP",
    "VVS_PWAVE",
    "YMSTOYNSPIPICLEO"
    )
