# Copyright (c) 2018-2026, Eduardo Rodrigues and Henry Schreiner.
#
# Distributed under the 3-clause BSD license, see accompanying file LICENSE
# or https://github.com/scikit-hep/decaylanguage for details.

from __future__ import annotations

from types import SimpleNamespace

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

    # AmpGen Fix=2 for both components -> a fixed GooFit variable.
    assert line.fix is True


def test_fix_flag_free():
    # AmpGen Free=0 -> a free (floating) GooFit variable.
    (line,), _ = GooFitChain.read_ampgen(
        text="""
    EventType D0 K- pi+ pi+ pi-

    D0[D]{K*(892)bar0{K-,pi+},rho(770)0{pi+,pi-}} 0 0.5 0.01 0 0.3 0.02
    """
    )
    assert line.fix is False


def test_use_cartesian_zero():
    # FastCoherentSum::UseCartesian 0 must parse and select polar (non-Cartesian).
    GooFitChain.read_ampgen(
        text="""
    EventType D0 K- pi+ pi+ pi-

    FastCoherentSum::UseCartesian 0

    D0[D]{K*(892)bar0{K-,pi+},rho(770)0{pi+,pi-}} 2 1 0 2 0 0
    """
    )
    assert GooFitChain.cartesian is False


def test_use_cartesian_one():
    GooFitChain.read_ampgen(
        text="""
    EventType D0 K- pi+ pi+ pi-

    FastCoherentSum::UseCartesian 1

    D0[D]{K*(892)bar0{K-,pi+},rho(770)0{pi+,pi-}} 2 1 0 2 0 0
    """
    )
    assert GooFitChain.cartesian is True


def test_read_ampgen_repeatable():
    # Parsing the same input twice must yield identical particle sets and output.
    text = """
    EventType D0 K- pi+ pi+ pi-

    D0[D]{K*(892)bar0{K-,pi+},rho(770)0{pi+,pi-}} 2 1 0 2 0 0
    """
    lines1, states1 = GooFitChain.read_ampgen(text=text)
    particles1 = set(GooFitChain.all_particles)
    lines2, states2 = GooFitChain.read_ampgen(text=text)
    particles2 = set(GooFitChain.all_particles)

    assert states1 == states2
    assert particles1 == particles2
    assert [str(line) for line in lines1] == [str(line) for line in lines2]


def test_L_range_pseudoscalar_to_two_vectors():
    # D0 (J=0) -> two vectors (J=1): |s1-s2|=0 <= S=0 <= s1+s2=2, so L starts at 0.
    (line,), _ = GooFitChain.read_ampgen(
        text="""
    EventType D0 K- pi+ pi+ pi-

    D0{K*(892)bar0{K-,pi+},rho(770)0{pi+,pi-}} 0 1 0 0 0 0
    """
    )
    assert line.L_range() == (0, 2)


def test_L_range_includes_intermediate_couplings():
    # Directly exercise the L_range math for the spin-1 -> vector + vector case,
    # where the true minimum L is 0 (not 1, as the old endpoint-only code gave).
    class FakeChain:
        def __init__(self, j, daughters=()):
            self.particle = SimpleNamespace(J=j)
            self._daughters = list(daughters)

        def __getitem__(self, i):
            return self._daughters[i]

    parent = FakeChain(1, [FakeChain(1), FakeChain(1)])
    assert GooFitChain.L_range(parent) == (0, 3)
