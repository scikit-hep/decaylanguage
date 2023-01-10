# Copyright (c) 2018-2023, Eduardo Rodrigues and Henry Schreiner.
#
# Distributed under the 3-clause BSD license, see accompanying file LICENSE
# or https://github.com/scikit-hep/decaylanguage for details.

import pytest

from decaylanguage.utils.particleutils import charge_conjugate_name


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


@pytest.mark.parametrize("p_name,ccp_name", matches_evtgen)
def test_charge_conjugate_name_defaults(p_name, ccp_name):
    assert charge_conjugate_name(p_name) == ccp_name


@pytest.mark.parametrize("p_name,ccp_name", matches_pdg)
def test_charge_conjugate_name_with_pdg_name(p_name, ccp_name):
    assert charge_conjugate_name(p_name, pdg_name=True) == ccp_name
