# Copyright (c) 2018-2026, Eduardo Rodrigues and Henry Schreiner.
#
# Distributed under the 3-clause BSD license, see accompanying file LICENSE
# or https://github.com/scikit-hep/decaylanguage for details.

from __future__ import annotations

import builtins
import sys
from pathlib import Path

import pytest
from pytest import approx

from decaylanguage import DecayChain, DecayMode, DecFileParser, decay_chain_to_dataframe

DIR = Path(__file__).parent.resolve()


def _dst_chain(mother: str, **kwargs):
    """Build a decay chain from the realistic D* example in tests/data."""
    parser = DecFileParser(DIR / "../data/test_example_Dst.dec")
    parser.parse()
    return parser.build_decay_chains(mother, **kwargs)


def test_table_without_models():
    table = decay_chain_to_dataframe(
        _dst_chain("D*+", stable_particles=["D+", "D0", "pi0"]),
        show_models=False,
        show_model_params=False,
    )

    assert list(table.columns) == ["Decay", "BF"]
    assert list(table["Decay"]) == [
        "D*+ --> D0 pi+",
        "D*+ --> D+ pi0",
        "D*+ --> D+ gamma",
    ]
    assert list(table["BF"]) == [0.677, 0.307, 0.016]


def test_table_with_models_and_model_params():
    table = decay_chain_to_dataframe(
        _dst_chain("D*+", stable_particles=["D+", "D0", "pi0"])
    )

    assert list(table.columns) == ["Decay", "BF", "Model", "Model params"]
    assert list(table["Model"]) == ["VSS", "VSS", "VSP_PWAVE"]
    assert list(table["Model params"]) == ["", "", ""]


def test_table_without_models_but_with_model_params():
    table = decay_chain_to_dataframe(
        _dst_chain("D*+", stable_particles=["D+", "D0", "pi0"]),
        show_models=False,
    )

    assert list(table.columns) == ["Decay", "BF", "Model params"]
    assert list(table["Model params"]) == ["", "", ""]


def test_table_full_dst_chain_cross_product():
    table = decay_chain_to_dataframe(_dst_chain("D*+"))

    # 1 (D0 pi+) + 4 x 4 (D+ pi0, two independent pi0s) + 4 (D+ gamma) rows.
    assert table.shape == (21, 4)
    assert table["BF"].sum() == approx(1.0)

    assert table["Decay"].iloc[0] == "D*+ --> D0 pi+ ; D0 --> K- pi+"
    assert table["BF"].iloc[0] == approx(0.677)
    assert table["Model"].iloc[0] == "VSS ; PHSP"
    assert table["Model params"].iloc[0] == " ; "

    assert table["Decay"].iloc[1] == (
        "D*+ --> D+ pi0 ; D+ --> K- pi+ pi+ pi0 ; "
        "pi0 --> gamma gamma ; pi0 --> gamma gamma"
    )
    assert table["BF"].iloc[1] == approx(0.307 * 0.988228297**2)
    assert table["Model"].iloc[1] == "VSS ; PHSP ; PHSP ; PHSP"
    assert table["Model params"].iloc[1] == " ;  ;  ; "

    assert table["Decay"].iloc[-1] == (
        "D*+ --> D+ gamma ; D+ --> K- pi+ pi+ pi0 ; pi0 --> e+ e-"
    )
    assert table["Model"].iloc[-1] == "VSP_PWAVE ; PHSP ; PHSP"


def test_table_model_params_from_multiline_model():
    parser = DecFileParser(DIR / "../data/test_multiline_model.dec")
    parser.parse()

    table = decay_chain_to_dataframe(parser.build_decay_chains("B+"))

    assert list(table["Decay"]) == ["B+ --> K+ K- pi+"]
    assert list(table["BF"]) == [1.0]
    assert list(table["Model"]) == ["PTO3P"]
    assert (
        table["Model params"]
        .iloc[0]
        .startswith("MAXPDF 0.09 AMPLITUDE RESONANCE BC K*0")
    )
    assert "PHASESPACE" in table["Model params"].iloc[0]


def test_table_preserves_empty_model_entries():
    dc = DecayChain(
        "D0",
        {
            "D0": DecayMode(0.028, "K_S0 pi+ pi-", model="PHSP"),
            "K_S0": DecayMode(0.692, "pi+ pi-"),
        },
    )

    table = decay_chain_to_dataframe(dc)

    assert list(table["Decay"]) == ["D0 --> K_S0 pi+ pi- ; K_S0 --> pi+ pi-"]
    assert list(table["BF"]) == [approx(0.028 * 0.692)]
    assert list(table["Model"]) == ["PHSP ; "]
    assert list(table["Model params"]) == [" ; "]


def test_table_accepts_decay_chain_object():
    chain = _dst_chain(
        "D*+", stable_particles=["D+", "D0", "pi0"], minimum_effective_bf=0.5
    )
    dc = DecayChain.from_dict(chain)

    table = decay_chain_to_dataframe(dc, show_models=False, show_model_params=False)

    assert list(table["Decay"]) == ["D*+ --> D0 pi+"]
    assert list(table["BF"]) == [0.677]


def test_decay_chain_to_dataframe_method():
    chain = _dst_chain(
        "D*+", stable_particles=["D+", "D0", "pi0"], minimum_effective_bf=0.5
    )
    dc = DecayChain.from_dict(chain)

    table = dc.to_dataframe(show_models=False, show_model_params=False)

    assert list(table.columns) == ["Decay", "BF"]
    assert list(table["Decay"]) == ["D*+ --> D0 pi+"]


def test_table_empty_modes_gives_empty_table_with_columns():
    table = decay_chain_to_dataframe(_dst_chain("D*+", minimum_effective_bf=0.8))

    assert list(table.columns) == ["Decay", "BF", "Model", "Model params"]
    assert len(table) == 0


def test_table_empty_chain_gives_empty_table_with_columns():
    table = decay_chain_to_dataframe({})

    assert list(table.columns) == ["Decay", "BF", "Model", "Model params"]
    assert len(table) == 0


def test_table_without_pandas(monkeypatch: pytest.MonkeyPatch):
    # Simulate pandas being unavailable, as in an install without the
    # ``modeling`` extra. Setting ``sys.modules["pandas"]`` to None makes
    # ``import pandas`` raise ModuleNotFoundError with name == "pandas".
    monkeypatch.setitem(sys.modules, "pandas", None)

    with pytest.raises(ModuleNotFoundError, match="requires pandas") as excinfo:
        decay_chain_to_dataframe({})

    assert "decaylanguage[modeling]" in str(excinfo.value)
    assert excinfo.value.__cause__ is not None


def test_table_reraises_unrelated_module_not_found(monkeypatch: pytest.MonkeyPatch):
    # A ModuleNotFoundError for a module other than pandas must not be
    # masked by the helpful message above; it is re-raised unchanged.
    real_import = builtins.__import__

    def fake_import(name, *args, **kwargs):
        if name == "pandas":
            raise ModuleNotFoundError("No module named 'other'", name="other")
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", fake_import)

    with pytest.raises(ModuleNotFoundError, match="other") as excinfo:
        decay_chain_to_dataframe({})

    assert excinfo.value.name == "other"
