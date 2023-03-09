# Copyright (c) 2018-2023, Eduardo Rodrigues and Henry Schreiner.
#
# Distributed under the 3-clause BSD license, see accompanying file LICENSE
# or https://github.com/scikit-hep/decaylanguage for details.


from __future__ import annotations

import pytest
from particle import ParticleNotFound
from pytest import approx

from decaylanguage.decay.decay import (
    DaughtersDict,
    DecayChain,
    DecayMode,
    _build_decay_modes,
)


def test_DaughtersDict_constructor_from_dict():
    dd = DaughtersDict({"K+": 1, "K-": 2, "pi+": 1, "pi0": 1})
    assert dd == {"K+": 1, "K-": 2, "pi+": 1, "pi0": 1}


def test_DaughtersDict_constructor_from_list():
    dd = DaughtersDict(["K+", "K-", "K-", "pi+", "pi0"])
    assert dd == {"K+": 1, "K-": 2, "pi+": 1, "pi0": 1}


def test_DaughtersDict_constructor_fromkeys():
    with pytest.raises(NotImplementedError):
        _ = DaughtersDict.fromkeys({"K+": 1, "K-": 2, "pi+": 1})


def test_DaughtersDict_constructor_from_string():
    dd = DaughtersDict("K+ K- pi0")
    assert dd == {"K+": 1, "K-": 1, "pi0": 1}


def test_DaughtersDict_constructor_kwargs():
    dd = DaughtersDict("K+ K-", pi0=1, gamma=2)
    assert dd == {"K+": 1, "K-": 1, "pi0": 1, "gamma": 2}


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


def test_DaughtersDict_charge_conjugate():
    dd = DaughtersDict({"K+": 2, "pi0": 1})
    assert dd.charge_conjugate() == {"K-": 2, "pi0": 1}


def test_DaughtersDict_charge_conjugate_pdg_names():
    dd = DaughtersDict({"K(S)0": 1, "pi+": 1})  # PDG names!
    assert dd == {"K(S)0": 1, "pi+": 1}  # PDG names kept as-is
    assert dd.charge_conjugate() == {"ChargeConj(K(S)0)": 1, "pi-": 1}
    assert dd.charge_conjugate(pdg_name=True) == {"K(S)0": 1, "pi-": 1}


def test_DecayMode_constructor_default():
    dm = DecayMode()
    assert dm.bf == 0
    assert dm.daughters == DaughtersDict()
    assert dm.metadata == {"model": "", "model_params": ""}


def test_DecayMode_constructor_simplest():
    dm = DecayMode(0.1234, "K+ K-")
    assert dm.bf == 0.1234
    assert dm.daughters == DaughtersDict("K+ K-")
    assert dm.metadata == {"model": "", "model_params": ""}


def test_DecayMode_constructor_simple():
    dd = DaughtersDict("K+ K-")
    dm = DecayMode(0.1234, dd)
    assert dm.bf == 0.1234
    assert dm.daughters == DaughtersDict("K+ K-")
    assert dm.metadata == {"model": "", "model_params": ""}


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
    assert dm.metadata == {"model": "", "model_params": ""}


def test_DecayMode_constructor_from_pdgids():
    dm = DecayMode.from_pdgids(
        0.5,
        [321, -321],
        model="TAUHADNU",
        model_params=[-0.108, 0.775, 0.149, 1.364, 0.400],
    )
    assert dm.daughters == DaughtersDict("K+ K-")


def test_DecayMode_constructor_from_pdgids_ParticleNotFound():
    with pytest.raises(ParticleNotFound):
        _ = DecayMode.from_pdgids(0.5, [321, -1234567])


def test_DecayMode_constructor_from_dict():
    dm = DecayMode.from_dict(
        {"bf": 0.98823, "fs": ["gamma", "gamma"], "model": "PHSP", "model_params": ""}
    )
    assert str(dm) == "<DecayMode: daughters=gamma gamma, BF=0.98823>"


def test_DecayMode_constructor_from_dict_RuntimeError():
    with pytest.raises(RuntimeError):
        _ = DecayMode.from_dict({"bf": 0.98823, "model": "PHSP"})

    with pytest.raises(RuntimeError):
        _ = DecayMode.from_dict({"fs": ["gamma", "gamma"], "model": "PHSP"})


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


def test_DecayMode_to_dict():
    dm = DecayMode(
        0.2551,
        "pi- pi0 nu_tau",
        model="TAUHADNU",
        model_params=[-0.108, 0.775, 0.149, 1.364, 0.400],
        study="toy",
        year=2019,
    )
    assert dm.to_dict() == {
        "bf": 0.2551,
        "fs": ["nu_tau", "pi-", "pi0"],
        "model": "TAUHADNU",
        "model_params": [-0.108, 0.775, 0.149, 1.364, 0.400],
        "study": "toy",
        "year": 2019,
    }


def test_DecayMode_to_dict_default():
    dm = DecayMode()
    assert dm.to_dict() == {"bf": 0, "fs": [], "model": "", "model_params": ""}


def test_DecayMode_to_dict_simple():
    dm = DecayMode(0.5, "K+ K- K- pi- pi0 nu_tau", model="PHSP", model_params=None)
    assert dm.to_dict() == {
        "bf": 0.5,
        "fs": ["K+", "K-", "K-", "nu_tau", "pi-", "pi0"],
        "model": "PHSP",
        "model_params": "",
    }


def test_DecayMode_to_dict_simpler():
    dm = DecayMode(0.5, "K+ K- K- pi- pi0 nu_tau")
    assert dm.to_dict() == {
        "bf": 0.5,
        "fs": ["K+", "K-", "K-", "nu_tau", "pi-", "pi0"],
        "model": "",
        "model_params": "",
    }


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


def test_DecayChain_constructor_default():
    d = DecayChain(mother="a", decays={"a": DecayMode()})
    assert d.mother == "a"
    assert d.ndecays == 1
    assert d.bf == 0


def test_DecayChain_constructor_RuntimeError():
    with pytest.raises(RuntimeError):
        _ = DecayChain(mother="a", decays={"b": DecayMode()})


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


def test_DecayChain_constructor_from_dict_RuntimeError(dc2):
    # For the sake of example remove some parts of a valid dict
    bad_dict_repr = dc2.to_dict()["D*+"][0]
    with pytest.raises(RuntimeError):
        _ = DecayChain.from_dict(bad_dict_repr)


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
    assert dc.ndecays == 3


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
    assert dc_flatten.bf == approx(1.0 * 0.0124 * (0.692**2) * (0.98823**3))


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
    assert dc_flatten.bf == approx(0.5 * (0.0124**2) * (0.692**2))


def test_DecayChain_string_repr(dc):
    assert str(dc) == "<DecayChain: D0 -> K_S0 pi0 (2 sub-decays), BF=0.0124>"


def test_build_decay_modes(dc2):
    decay_modes = {}
    _build_decay_modes(decay_modes, dc2.to_dict())
    assert len(decay_modes) == 4


def test_build_decay_modes_RuntimeError(dc2):
    # For the sake of example remove some part of a valid dict
    bad_dc_of_mother_as_dict = dc2.to_dict()
    del bad_dc_of_mother_as_dict["D*+"][0]["fs"]
    decay_modes = {}
    with pytest.raises(RuntimeError):
        _ = _build_decay_modes(decay_modes, bad_dc_of_mother_as_dict)
