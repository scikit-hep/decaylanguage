# Copyright (c) 2018-2023, Eduardo Rodrigues and Henry Schreiner.
#
# Distributed under the 3-clause BSD license, see accompanying file LICENSE
# or https://github.com/scikit-hep/decaylanguage for details.

from __future__ import annotations

import pytest
from particle import ParticleNotFound

from decaylanguage.utils.particleutils import (
    charge_conjugate_name,
    particle_from_string_name,
)

matches_evtgen = (
    ("pi0", "pi0"),
    ("K+", "K-"),
    # 'K(S)0' unrecognised in charge conjugation unless specified that these are PDG names
    ("K(S)0", "ChargeConj(K(S)0)"),
    ("Unknown", "ChargeConj(Unknown)"),
)


matches_pdg = (
    ("pi0", "pi0"),
    ("K+", "K-"),
    ("K(S)0", "K(S)0"),
    ("Unknown", "ChargeConj(Unknown)"),
)


@pytest.mark.parametrize(("p_name", "ccp_name"), matches_evtgen)
def test_charge_conjugate_name_defaults(p_name, ccp_name):
    assert charge_conjugate_name(p_name) == ccp_name


@pytest.mark.parametrize(("p_name", "ccp_name"), matches_pdg)
def test_charge_conjugate_name_with_pdg_name(p_name, ccp_name):
    assert charge_conjugate_name(p_name, pdg_name=True) == ccp_name


def test_particle_from_string_name():
    pi = particle_from_string_name("pi+")
    assert pi.pdgid == 211

    with pytest.raises(ParticleNotFound):
        particle_from_string_name("unknown")


def test_fuzzy_string():
    """
    The input name is not specific enough, in which case the search is done
    by pdg_name after failing a match by name.
    """
    p = particle_from_string_name("a(0)(980)")  # all 3 charge stages match
    assert p.pdgid == 9000111


ampgen_style_names = (
    ("b", 5),
    ("b~", -5),
    ("pi+", 211),
    ("pi-", -211),
    ("K~*0", -313),
    ("K*(892)bar0", -313),
    ("a(1)(1260)+", 20213),
    ("rho(1450)0", 100113),
    ("rho(770)0", 113),
    ("K(1)(1270)bar-", -10323),
    # ("K(1460)bar-", -100321),
    ("K(2)*(1430)bar-", -325),
)


@pytest.mark.parametrize(("name", "pid"), ampgen_style_names)
def test_ampgen_style_names(name, pid):
    particle = particle_from_string_name(name)

    assert particle.pdgid == pid
    assert particle == pid
