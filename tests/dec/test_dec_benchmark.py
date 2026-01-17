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


@pytest.mark.benchmark
def test_build_decay_chains_benchmark(belle2_dec_file, benchmark):
    result = benchmark.pedantic(
        build_decay_chains_benchmark, args=(belle2_dec_file,), rounds=3
    )
    assert result


def build_decay_chains_minimum_effective_bf_benchmark(p):
    return p.build_decay_chains("D_s*+", minimum_effective_bf=0.1)


@pytest.mark.benchmark
def test_build_decay_chains_min_bf_benchmark(belle2_dec_file, benchmark):
    result = benchmark.pedantic(
        build_decay_chains_minimum_effective_bf_benchmark,
        args=(belle2_dec_file,),
        rounds=3,
    )
    assert result
