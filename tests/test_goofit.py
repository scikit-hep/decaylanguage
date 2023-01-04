# Copyright (c) 2018-2023, Eduardo Rodrigues and Henry Schreiner.
#
# Distributed under the 3-clause BSD license, see accompanying file LICENSE
# or https://github.com/scikit-hep/decaylanguage for details.

from __future__ import annotations

from particle import Particle

from decaylanguage.modeling.goofit import GooFitChain


def test_simple():
    lines, all_states = GooFitChain.read_ampgen(
        text="""

    # This is a test (should not affect output)

    EventType D0 K- pi+ pi+ pi-

    D0[D]{K*(892)bar0{K-,pi+},rho(770)0{pi+,pi-}} 2 1         0          2 0         0
    """
    )

    assert Particle.from_pdgid(421) == all_states[0]  # D0
    assert Particle.from_pdgid(-321) == all_states[1]  # K-
    assert Particle.from_pdgid(211) == all_states[2]  # pi+
    assert Particle.from_pdgid(211) == all_states[3]  # pi+
    assert Particle.from_pdgid(-211) == all_states[4]  # pi-

    assert len(lines) == 1
    (line,) = lines
