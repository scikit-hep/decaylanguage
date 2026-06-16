# Copyright (c) 2020, Eduardo Rodrigues and Henry Schreiner.
#
# Distributed under the 3-clause BSD license, see accompanying file LICENSE
# or https://github.com/scikit-hep/decaylanguage for details.

from __future__ import annotations

from pathlib import Path

import pytest
from lark import Token, Tree, UnexpectedToken

from decaylanguage.dec.dec import (
    ChargeConjugateReplacement,
    DecFileParser,
    get_branching_fraction,
)

DIR = Path(__file__).parent.resolve()


def test_issue_90():
    p = DecFileParser(DIR / "../data/test_issue90.dec")
    with pytest.raises(UnexpectedToken):
        p.parse()


def test_model_alias_shared_subtree():
    # Regression test: a ModelAlias used in more than one decay tree used to
    # share the same Token objects across trees, so the in-place float
    # substitution done while parsing crashed on the second tree with
    # "TypeError: 'float' object is not subscriptable".
    s = """
Define dm 0.507e12
Alias myB B0
ModelAlias myVSS_BMIX VSS_BMIX dm;
Decay B0
1.0 myB myB myVSS_BMIX;
Enddecay
Decay anti-B0
1.0 myB myB myVSS_BMIX;
Enddecay
"""
    p = DecFileParser.from_string(s)
    p.parse()  # used to raise TypeError

    # Both trees should have the value substituted independently.
    for mother in ("B0", "anti-B0"):
        modes = p._find_decay_modes(mother)
        assert modes


def test_from_string_filters_intermediate_end_lines():
    # Regression test: from_string must apply the same intermediate-"End"-line
    # filtering as the file-based constructor, so identical content parses the
    # same way either way.
    s = """
Decay B0
1.0 pi+ pi- PHSP;
Enddecay
End
Decay anti-B0
1.0 pi+ pi- PHSP;
Enddecay
"""
    p = DecFileParser.from_string(s)
    p.parse()  # the stray "End" line used to break string parsing
    assert "B0" in p.list_decay_mother_names()


def test_charge_conjugate_replacement_does_not_mutate_caller_dict():
    # Regression test: ChargeConjugateReplacement used the caller's dict as a
    # cache, silently polluting it (including failure sentinels of the form
    # 'ChargeConj(<name>)').
    user_dict = {"FancyParticle": "FancyAntiParticle"}
    snapshot = dict(user_dict)

    t = Tree(
        "decay",
        [
            Tree("particle", [Token("LABEL", "SomeUnknownParticle")]),
        ],
    )
    ChargeConjugateReplacement(charge_conj_defs=user_dict).visit(t)

    # The user's dict must be untouched ...
    assert user_dict == snapshot
    # ... and failure sentinels must not have been cached anywhere.
    assert all(not v.startswith("ChargeConj(") for v in user_dict.values())


def test_get_branching_fraction_malformed_input():
    # Regression test: malformed input raises AttributeError/IndexError/
    # ValueError, which used to escape the (dead) "except RuntimeError" and was
    # never re-raised as the friendly RuntimeError.
    bad = Tree("decayline", [Tree("value", [Token("SIGNED_NUMBER", "not-a-number")])])
    with pytest.raises(RuntimeError):
        get_branching_fraction(bad)
