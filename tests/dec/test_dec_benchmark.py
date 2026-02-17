# Copyright (c) 2018-2026, Eduardo Rodrigues and Henry Schreiner.
#
# Distributed under the 3-clause BSD license, see accompanying file LICENSE
# or https://github.com/scikit-hep/decaylanguage for details.

from __future__ import annotations

from pathlib import Path

import pytest

from decaylanguage.dec.dec import (
    DecFileParser,
)

DIR = Path(__file__).parent.resolve()


@pytest.fixture
def belle2_dec_file():
    p = DecFileParser(DIR / "../../src/decaylanguage/data/DECAY_BELLE2.DEC")
    p.parse()
    return p


def build_decay_chains_benchmark(p):
    return p.build_decay_chains("D_s*+", stable_particles=[])


def test_build_decay_chains_benchmark(belle2_dec_file, benchmark):
    result = benchmark(build_decay_chains_benchmark, belle2_dec_file)
    assert result
