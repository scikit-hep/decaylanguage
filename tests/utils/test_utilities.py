# Copyright (c) 2018-2026, Eduardo Rodrigues and Henry Schreiner.
#
# Distributed under the 3-clause BSD license, see accompanying file LICENSE
# or https://github.com/scikit-hep/decaylanguage for details.

from __future__ import annotations

import re

import pytest

from decaylanguage import DecayChain, DecayMode
from decaylanguage.utils import DescriptorFormat, filter_lines, split


@pytest.mark.parametrize(
    ("inp", "expected"),
    [
        ("a,b", ["a", "b"]),
        ("a,b,c", ["a", "b", "c"]),
        ("a", ["a"]),
        ("", []),
        # trailing comma: previously returned ["a,"] (bug)
        ("a,", ["a", ""]),
        # leading comma
        (",a", ["", "a"]),
        # bare comma
        (",", ["", ""]),
        # nesting: comma inside {} does not split
        ("a{b,c},d", ["a{b,c}", "d"]),
        # deep nesting
        ("a{b{c,d},e},f", ["a{b{c,d},e}", "f"]),
        # comma only inside braces — no top-level split
        ("{a,b}", ["{a,b}"]),
    ],
)
def test_split(inp: str, expected: list[str]) -> None:
    assert split(inp) == expected


@pytest.mark.parametrize(
    ("lines", "matched_keys", "remaining"),
    [
        (
            ["foo 1", "bar 2", "foo 3", "baz"],
            [{"word": "foo", "num": "1"}, {"word": "foo", "num": "3"}],
            ["bar 2", "baz"],
        ),
        ([], [], []),
        (["no_match"], [], ["no_match"]),
    ],
)
def test_filter_lines(
    lines: list[str],
    matched_keys: list[dict[str, str]],
    remaining: list[str],
) -> None:
    pattern = re.compile(r"^(?P<word>foo) (?P<num>\d+)$")
    output, new_inp = filter_lines(pattern, lines)
    assert output == matched_keys
    assert new_inp == remaining


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
