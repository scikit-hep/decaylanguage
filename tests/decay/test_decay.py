# -*- coding: utf-8 -*-
# Copyright (c) 2018-2021, Eduardo Rodrigues and Henry Schreiner.
#
# Distributed under the 3-clause BSD license, see accompanying file LICENSE
# or https://github.com/scikit-hep/decaylanguage for details.


import pytest
from pytest import approx

from decaylanguage.decay.decay import DaughtersDict
from decaylanguage.decay.decay import DecayMode
from decaylanguage.decay.decay import DecayChain


def test_DaughtersDict_constructor_from_dict():
    dd = DaughtersDict({"K+": 1, "K-": 2, "pi+": 1, "pi0": 1})
    assert dd == {"K+": 1, "K-": 2, "pi+": 1, "pi0": 1}


def test_DaughtersDict_constructor_from_list():
    dd = DaughtersDict(["K+", "K-", "K-", "pi+", "pi0"])
    assert dd == {"K+": 1, "K-": 2, "pi+": 1, "pi0": 1}


def test_DaughtersDict_constructor_from_string():
    dd = DaughtersDict("K+ K- pi0")
    assert dd == {"K+": 1, "K-": 1, "pi0": 1}


def test_DaughtersDict_string_repr():
    dd = DaughtersDict(["K+", "K-", "K-", "pi+", "pi0"])
    assert dd.__str__() == "<DaughtersDict: ['K+', 'K-', 'K-', 'pi+', 'pi0']>"


def test_DaughtersDict_len():
    dd = DaughtersDict({"K+": 1, "K-": 3, "pi0": 1})
    assert len(dd) == 5


def test_DaughtersDict_add():
    dd1 = DaughtersDict({"K+": 1, "K-": 2, "pi0": 3})
    dd2 = DaughtersDict({"K+": 1, "K-": 1})
    dd3 = dd1 + dd2
    assert len(dd3) == 8


def test_DaughtersDict_to_string():
    dd1 = DaughtersDict({"K+": 1, "K-": 2, "pi0": 3})
    assert dd1.to_string() == "K+ K- K- pi0 pi0 pi0"


def test_DecayMode_constructor_default():
    dm = DecayMode()
    assert dm.bf == 0
    assert dm.daughters == DaughtersDict()
    assert dm.metadata == dict(model="", model_params="")


def test_DecayMode_constructor_simplest():
    dm = DecayMode(0.1234, "K+ K-")
    assert dm.bf == 0.1234
    assert dm.daughters == DaughtersDict("K+ K-")
    assert dm.metadata == dict(model="", model_params="")


def test_DecayMode_constructor_simple():
    dd = DaughtersDict("K+ K-")
    dm = DecayMode(0.1234, dd)
    assert dm.bf == 0.1234
    assert dm.daughters == DaughtersDict("K+ K-")
    assert dm.metadata == dict(model="", model_params="")


def test_DecayMode_constructor_with_model_info():
    dd = DaughtersDict("pi- pi0 nu_tau")
    dm = DecayMode(
        0.2551, dd, model="TAUHADNU", model_params=[-0.108, 0.775, 0.149, 1.364, 0.400]
    )
    assert dm.metadata == {
        "model": "TAUHADNU",
        "model_params": [-0.108, 0.775, 0.149, 1.364, 0.4],
    }


def test_DecayMode_constructor_with_user_metadata():
    dd = DaughtersDict("K+ K-")
    dm = DecayMode(0.5, dd, model="PHSP", study="toy", year=2019)
    assert dm.metadata == {
        "model": "PHSP",
        "model_params": "",
        "study": "toy",
        "year": 2019,
    }


def test_DecayMode_constructor_from_pdgids_default():
    dm = DecayMode.from_pdgids()
    assert dm.bf == 0
    assert dm.daughters == DaughtersDict()
    assert dm.metadata == dict(model="", model_params="")


def test_DecayMode_constructor_from_pdgids():
    dm = DecayMode.from_pdgids(
        0.5,
        [321, -321],
        model="TAUHADNU",
        model_params=[-0.108, 0.775, 0.149, 1.364, 0.400],
    )
    assert dm.daughters == DaughtersDict("K+ K-")


def test_DecayMode_constructor_from_dict():
    dm = DecayMode.from_dict(
        {"bf": 0.98823, "fs": ["gamma", "gamma"], "model": "PHSP", "model_params": ""}
    )
    assert str(dm) == "<DecayMode: daughters=gamma gamma, BF=0.98823>"


def test_DecayMode_describe_simple():
    dd = DaughtersDict("pi- pi0 nu_tau")
    dm = DecayMode(
        0.2551, dd, model="TAUHADNU", model_params=[-0.108, 0.775, 0.149, 1.364, 0.400]
    )
    assert "BF: 0.2551" in dm.describe()
    assert "Decay model: TAUHADNU [-0.108, 0.775, 0.149, 1.364, 0.4]" in dm.describe()


def test_DecayMode_describe_with_user_metadata():
    dd = DaughtersDict("K+ K-")
    dm = DecayMode(1.0e-6, dd, model="PHSP", study="toy", year=2019)
    assert "Extra info:" in dm.describe()
    assert "study: toy" in dm.describe()
    assert "year: 2019" in dm.describe()


def test_DecayMode_charge_conjugate():
    dd = DaughtersDict("pi- pi0 nu_tau")
    dm = DecayMode(
        0.2551, dd, model="TAUHADNU", model_params=[-0.108, 0.775, 0.149, 1.364, 0.400]
    )
    dm_cc = dm.charge_conjugate()
    assert dm_cc.daughters == DaughtersDict("pi+ pi0 anti-nu_tau")
    assert "BF: 0.2551" in dm.describe()
    assert "Decay model: TAUHADNU [-0.108, 0.775, 0.149, 1.364, 0.4]" in dm.describe()

    dd = DaughtersDict("pi- pi0 nu(tau)")
    assert dd.charge_conjugate(pdg_name=True) == DaughtersDict("pi+ pi0 nu(tau)~")


def test_DecayMode_string_repr():
    dd = DaughtersDict("p p~ K+ pi-")
    dm = DecayMode(1.0e-6, dd, model="PHSP")
    assert str(dm) == "<DecayMode: daughters=K+ p pi- p~, BF=1e-06>"


def test_DecayMode_number_of_final_states():
    dd = DaughtersDict("p p~ K+ pi-")
    dm = DecayMode(1.0e-6, dd, model="PHSP")
    assert len(dm) == 4


@pytest.fixture()
def dc():
    dm1 = DecayMode(0.0124, "K_S0 pi0", model="PHSP")
    dm2 = DecayMode(0.692, "pi+ pi-")
    dm3 = DecayMode(0.98823, "gamma gamma")
    return DecayChain("D0", {"D0": dm1, "K_S0": dm2, "pi0": dm3})


@pytest.fixture()
def dc2():
    dm1 = DecayMode(0.6770, "D0 pi+")
    dm2 = DecayMode(0.0124, "K_S0 pi0")
    dm3 = DecayMode(0.692, "pi+ pi-")
    dm4 = DecayMode(0.98823, "gamma gamma")
    return DecayChain("D*+", {"D*+": dm1, "D0": dm2, "K_S0": dm3, "pi0": dm4})


def test_DecayChain_constructor_subdecays(dc):
    assert len(dc.decays) == 3
    assert dc.mother == "D0"


def test_DecayChain_constructor_from_dict():
    dc_dict = {
        "D0": [
            {
                "bf": 0.0124,
                "fs": [
                    {
                        "K_S0": [
                            {
                                "bf": 0.692,
                                "fs": ["pi+", "pi-"],
                                "model": "",
                                "model_params": "",
                            }
                        ]
                    },
                    {
                        "pi0": [
                            {
                                "bf": 0.98823,
                                "fs": ["gamma", "gamma"],
                                "model": "",
                                "model_params": "",
                            }
                        ]
                    },
                ],
                "model": "PHSP",
                "model_params": "",
            }
        ]
    }
    assert DecayChain.from_dict(dc_dict).to_dict() == dc_dict


def test_DecayChain_to_dict(dc2):
    assert dc2.to_dict() == {
        "D*+": [
            {
                "bf": 0.677,
                "fs": [
                    {
                        "D0": [
                            {
                                "bf": 0.0124,
                                "fs": [
                                    {
                                        "K_S0": [
                                            {
                                                "bf": 0.692,
                                                "fs": ["pi+", "pi-"],
                                                "model": "",
                                                "model_params": "",
                                            }
                                        ]
                                    },
                                    {
                                        "pi0": [
                                            {
                                                "bf": 0.98823,
                                                "fs": ["gamma", "gamma"],
                                                "model": "",
                                                "model_params": "",
                                            }
                                        ]
                                    },
                                ],
                                "model": "",
                                "model_params": "",
                            }
                        ]
                    },
                    "pi+",
                ],
                "model": "",
                "model_params": "",
            }
        ]
    }


def test_DecayChain_properties(dc):
    assert dc.bf == 0.0124
    assert dc.visible_bf == approx(0.008479803984)


def test_DecayChain_flatten(dc2):
    dc2_flatten = dc2.flatten()
    assert dc2_flatten.mother == dc2.mother
    assert dc2_flatten.bf == dc2_flatten.visible_bf
    assert dc2_flatten.decays[dc2.mother].daughters == DaughtersDict(
        ["gamma", "gamma", "pi+", "pi+", "pi-"]
    )


def test_DecayChain_flatten_complex():
    dm1 = DecayMode(1.0, "D0 K_S0 pi+ pi0")
    dm2 = DecayMode(0.0124, "K_S0 pi0 pi0")
    dm3 = DecayMode(0.692, "pi+ pi-")
    dm4 = DecayMode(0.98823, "gamma gamma")
    dc = DecayChain("X+", {"X+": dm1, "D0": dm2, "K_S0": dm3, "pi0": dm4})
    dc_flatten = dc.flatten()
    assert dc_flatten.decays[dc_flatten.mother].daughters == DaughtersDict(
        {"gamma": 6, "pi+": 3, "pi-": 2}
    )
    assert dc_flatten.bf == approx(1.0 * 0.0124 * (0.692 ** 2) * (0.98823 ** 3))


def test_DecayChain_flatten_with_stable_particles():
    dm1 = DecayMode(0.5, "D0 anti-D0 pi+ pi0 pi0")
    dm2 = DecayMode(0.0124, "K_S0 pi0")
    dm3 = DecayMode(0.692, "pi+ pi-")
    dm4 = DecayMode(0.98823, "gamma gamma")
    dc = DecayChain(
        "X+", {"X+": dm1, "D0": dm2, "anti-D0": dm2, "K_S0": dm3, "pi0": dm4}
    )
    dc_flatten = dc.flatten(stable_particles=["pi0"])
    assert dc_flatten.decays[dc_flatten.mother].daughters == DaughtersDict(
        {"pi0": 4, "pi+": 3, "pi-": 2}
    )
    assert dc_flatten.bf == approx(0.5 * (0.0124 ** 2) * (0.692 ** 2))


def test_DecayChain_string_repr(dc):
    assert str(dc) == "<DecayChain: D0 -> K_S0 pi0 (2 sub-decays), BF=0.0124>"
