# Copyright (c) 2018-2023, Eduardo Rodrigues and Henry Schreiner.
#
# Distributed under the 3-clause BSD license, see accompanying file LICENSE
# or https://github.com/scikit-hep/decaylanguage for details.

from __future__ import annotations

import pytest

from decaylanguage import DecayChain, DecayMode

dm1 = DecayMode(0.6770, "D0 pi+")  # D*+
dm2 = DecayMode(0.0124, "K_S0 pi0")  # D0
dm3 = DecayMode(0.692, "pi+ pi-")  # K_S0
dm4 = DecayMode(0.98823, "gamma gamma")  # pi0
dm5 = DecayMode(0.0105, "D- tau+ nu_tau")  # B0
dm6 = DecayMode(0.0938, "K+ pi- pi-")  # D-
dm7 = DecayMode(0.0931, "pi+ pi+ pi- anti-nu_tau")  # tau+
dm8 = DecayMode(1.85e-6, "phi phi'")  #  B_s0
dm9a = DecayMode(0.491, "K+ K-")  #  phi
dm9b = DecayMode(0.154, "pi+ pi- pi0")  #  phi


@pytest.mark.parametrize(
    ("dc", "expected"),
    [
        (
            DecayChain("D0", {"D0": dm2, "K_S0": dm3, "pi0": dm4}),
            "D0 -> (K_S0 -> pi+ pi-) (pi0 -> gamma gamma)",
        ),
        (
            DecayChain("D*+", {"D*+": dm1, "D0": dm2, "K_S0": dm3, "pi0": dm4}),
            "D*+ -> (D0 -> (K_S0 -> pi+ pi-) (pi0 -> gamma gamma)) pi+",
        ),
        (
            DecayChain("B0", {"B0": dm5, "D-": dm6, "tau+": dm7}),
            "B0 -> (D- -> K+ pi- pi-) (tau+ -> anti-nu_tau pi+ pi+ pi-) nu_tau",
        ),
        (
            DecayChain("B_s0", {"B_s0": dm8, "phi": dm9a, "phi'": dm9b}),
            "B_s0 -> (phi -> K+ K-) (phi' -> pi+ pi- pi0)",
        ),
    ],
)
def test_descriptor(dc: DecayChain, expected: str):
    descriptor = dc.to_string()
    assert descriptor == expected
