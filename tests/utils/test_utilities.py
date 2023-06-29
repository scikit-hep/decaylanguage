# Copyright (c) 2018-2023, Eduardo Rodrigues and Henry Schreiner.
#
# Distributed under the 3-clause BSD license, see accompanying file LICENSE
# or https://github.com/scikit-hep/decaylanguage for details.

from __future__ import annotations

import pytest

from decaylanguage import DecayChain, DecayMode
from decaylanguage.utils import DescriptorFormat

dm1 = DecayMode(0.6770, "D0 pi+")  # D*+
dm2 = DecayMode(0.0124, "K_S0 pi0")  # D0
dm3 = DecayMode(0.692, "pi+ pi-")  # K_S0
dm4 = DecayMode(0.98823, "gamma gamma")  # pi0


@pytest.mark.parametrize(
    ("decay_pattern", "sub_decay_pattern", "expected"),
    [
        (
            "{mother} -> {daughters}",
            "({mother} -> {daughters})",
            "D*+ -> (D0 -> (K_S0 -> pi+ pi-) (pi0 -> gamma gamma)) pi+",
        ),
        (
            "{mother} --> {daughters}",
            "[{mother} --> {daughters}]",
            "D*+ --> [D0 --> [K_S0 --> pi+ pi-] [pi0 --> gamma gamma]] pi+",
        ),
        (
            "{mother} => {daughters}",
            "{mother} (=> {daughters})",
            "D*+ => D0 (=> K_S0 (=> pi+ pi-) pi0 (=> gamma gamma)) pi+",
        ),
    ],
)
def test_set_descriptor_pattern(
    decay_pattern: str, sub_decay_pattern: str, expected: str
):
    dc = DecayChain("D*+", {"D*+": dm1, "D0": dm2, "K_S0": dm3, "pi0": dm4})
    with DescriptorFormat(decay_pattern, sub_decay_pattern):
        descriptor = dc.to_string()
        assert descriptor == expected
