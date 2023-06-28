# Copyright (c) 2018-2023, Eduardo Rodrigues and Henry Schreiner.
#
# Distributed under the 3-clause BSD license, see accompanying file LICENSE
# or https://github.com/scikit-hep/decaylanguage for details.

from __future__ import annotations

import string
from copy import copy
from typing import Any, ClassVar, Iterator, Pattern


def iter_flatten(iterable: list[str] | tuple[str, ...]) -> Iterator[str]:
    """
    Flatten nested tuples and lists
    """
    for e in iterable:
        if isinstance(e, (list, tuple)):
            yield from iter_flatten(e)
        else:
            yield e


def split(x: str) -> list[str]:
    """
    Break up a comma separated list, but respect curly brackets.

    For example:
    this, that { that { this, that } }
    would only break on the first comma, since the second is in a {} list
    """

    c = 0
    i = 0
    out = []
    while len(x) > 0:
        if i + 1 == len(x):
            out.append(x[: i + 1])
            return out
        if x[i] == "," and c == 0:
            out.append(x[:i])
            x = x[i + 1 :]
            i = -1
        elif x[i] == "{":
            c += 1
        elif x[i] == "}":
            c -= 1
        i += 1
    return out


def filter_lines(
    matcher: Pattern[str], inp: list[str]
) -> tuple[list[dict[str, str | Any]], list[str]]:
    """
    Filter out lines into new variable if they match a regular expression
    """
    matches = (matcher.match(ln) for ln in inp)
    output = [match.groupdict() for match in matches if match is not None]
    new_inp = [ln for ln in inp if matcher.match(ln) is None]
    return output, new_inp


class DescriptorFormat:
    """
    Class to help with setting the decay descriptor format. The format is stored as a
    class-level variable: `DescriptorFormat.config`.

    Examples
    --------
    >>> from decaylanguage import DecayMode, DecayChain
    >>> dm1 = DecayMode(0.6770, "D0 pi+")  # D*+
    >>> dm2 = DecayMode(0.0124, "K_S0 pi0")  # D0
    >>> dm3 = DecayMode(0.692, "pi+ pi-")  # K_S0
    >>> dm4 = DecayMode(0.98823, "gamma gamma")  # pi0
    >>> dc = DecayChain("D*+", {"D*+": dm1, "D0": dm2, "K_S0": dm3, "pi0": dm4})
    >>> with DescriptorFormat("{mother} --> {daughters}", "[{mother} --> {daughters}]"): dc.to_string()
    ...
    'D*+ --> [D0 --> [K_S0 --> pi+ pi-] [pi0 --> gamma gamma]] pi+'
    >>> with DescriptorFormat("{mother} => {daughters}", "{mother} (=> {daughters})"): dc.to_string();
    ...
    'D*+ => D0 (=> K_S0 (=> pi+ pi-) pi0 (=> gamma gamma)) pi+'
    >>> dc.to_string()
    'D*+ -> (D0 -> (K_S0 -> pi+ pi-) (pi0 -> gamma gamma)) pi+'
    """

    config: ClassVar[dict[str, str]] = {
        "decay_pattern": "{mother} -> {daughters}",
        "sub_decay_pattern": "({mother} -> {daughters})",
    }

    def __init__(self, decay_pattern: str, sub_decay_pattern: str) -> None:
        self.new_config = {
            "decay_pattern": decay_pattern,
            "sub_decay_pattern": sub_decay_pattern,
        }
        self.old_config = copy(DescriptorFormat.config)

    def __enter__(self) -> None:
        self.set_config(**self.new_config)

    def __exit__(self, *args: list[Any]) -> None:
        self.set_config(**self.old_config)

    @staticmethod
    def set_config(decay_pattern: str, sub_decay_pattern: str) -> None:
        """
        Configure the descriptor patterns after checking that each pattern
        has named-wildcards "mother" and "daughters".

        Parameters
        ----------

        decay_pattern: str
            Format-string expression for a top-level decay,
            e.g. "{mother} -> {daughters}"
        sub_decay_pattern: str
            Format-string expression for a sub-decay,
            e.g. "({mother} -> {daughters}"
        """
        new_config = {
            "decay_pattern": decay_pattern,
            "sub_decay_pattern": sub_decay_pattern,
        }
        expected_wildcards = {"mother", "daughters"}
        for pattern in new_config.values():
            wildcards = {
                t[1] for t in string.Formatter().parse(pattern) if isinstance(t[1], str)
            }
            if wildcards != expected_wildcards:
                error_msg = (
                    "The pattern should only have the wildcards "
                    f"{expected_wildcards}, while '{pattern}' has the wildcards "
                    f"{wildcards}."
                )
                raise ValueError(error_msg)
        DescriptorFormat.config = new_config

    @staticmethod
    def format_descriptor(mother: str, daughters: str, top: bool = True) -> str:
        """
        Apply the format to one "layer" of the decay. Does not handle nested
        decays itself. It is assumed that the `daughters` string already contains
        any sub-decays.

        Parameters
        ----------

        mother: str
            The decaying particle.
        daughters: str
            The final-state particles.
        """
        args = {
            "mother": mother,
            "daughters": daughters,
        }
        if top:
            return DescriptorFormat.config["decay_pattern"].format(**args)
        return DescriptorFormat.config["sub_decay_pattern"].format(**args)
