# Copyright (c) 2018-2026, Eduardo Rodrigues and Henry Schreiner.
#
# Distributed under the 3-clause BSD license, see accompanying file LICENSE
# or https://github.com/scikit-hep/decaylanguage for details.

"""
Submodule with utilities to tabulate decay chains as a ``pandas.DataFrame``.
Decay chains are typically provided by the parser of .dec decay files,
see the ``DecFileParser`` class.

``pandas`` is an optional dependency of ``decaylanguage`` (part of the
``modeling`` extra), so it is only imported when
:func:`decay_chain_to_dataframe` is actually called. Importing this module,
and importing ``decaylanguage`` itself, does not require ``pandas``.
"""

from __future__ import annotations

import itertools
import math
from collections.abc import Iterable, Iterator
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import pandas as pd

    from .decay import DecayChain, DecayModeDict

__all__ = ("decay_chain_to_dataframe",)


def _params(params: str | Iterable[str | int | float]) -> str:
    return params if isinstance(params, str) else " ".join(map(str, params))


def _expand(
    mother: str, modes: Iterable[DecayModeDict]
) -> Iterator[tuple[float, list[tuple[str, str, str]]]]:
    """Yield (bf, steps) per fully expanded chain; steps = [(decay, model, params), ...]."""
    for mode in modes:
        names: list[str] = []
        subs = []
        for part in mode["fs"]:
            if isinstance(part, str):
                names.append(part)
                continue
            for daughter, sub_modes in part.items():
                names.append(daughter)
                subs.append(_expand(daughter, sub_modes))
        step = (
            f"{mother} --> {' '.join(names)}",
            mode["model"],
            _params(mode["model_params"]),
        )
        for combo in itertools.product(*subs):
            yield (
                mode["bf"] * math.prod(bf for bf, _ in combo),
                [step, *itertools.chain.from_iterable(s for _, s in combo)],
            )


def decay_chain_to_dataframe(
    decaychain: dict[str, list[DecayModeDict]] | DecayChain,
    *,
    show_models: bool = True,
    show_model_params: bool = True,
) -> pd.DataFrame:
    """
    Tabulate a decay chain as a ``pandas.DataFrame``.

    Each row corresponds to one fully expanded decay chain, i.e. one
    combination of decay modes obtained by choosing one mode for the
    mother particle and, recursively, one mode for every decaying
    daughter. The ``BF`` column is the effective branching fraction:
    the product of the branching fractions of all modes along the chain.
    An empty decay chain gives an empty table with the requested columns.

    Examples
    --------
    >>> from decaylanguage import DecayChain, DecayMode
    >>> dm1 = DecayMode(0.028, 'K_S0 pi+ pi-', model='PHSP')
    >>> dm2 = DecayMode(0.692, 'pi+ pi-')
    >>> dc = DecayChain('D0', {'D0': dm1, 'K_S0': dm2})
    >>> df = decay_chain_to_dataframe(dc)
    >>> df["Decay"].tolist()
    ['D0 --> K_S0 pi+ pi- ; K_S0 --> pi+ pi-']
    >>> df["BF"].round(6).tolist()
    [0.019376]
    >>> df["Model"].tolist()  # the K_S0 decay used no model
    ['PHSP ; ']

    Decay models and their parameters can be added as extra columns with
    ``show_models=True`` and ``show_model_params=True`` (the defaults).

    Parameters
    ----------
    decaychain: dict or ``DecayChain``
        Input decay chain in dict format, typically created from
        ``decaylanguage.DecFileParser.build_decay_chains`` after parsing
        a .dec decay file, or a ``decaylanguage.DecayChain`` instance.
    show_models: bool, optional
        If True, add a ``Model`` column with the decay model(s) used along
        each decay chain. Default is True.
    show_model_params: bool, optional
        If True, add a ``Model params`` column with the parameters of the
        decay model(s) used along each decay chain. Default is True.

    Notes
    -----
    The ``Model`` and ``Model params`` columns join the values of every
    decay along the chain with ``" ; "``, in chain order. Empty entries
    are preserved, so the position of each value identifies which part
    of the decay chain it belongs to (e.g. ``"PHSP ; "`` means the
    first decay used ``PHSP`` and a sub-decay used no model).

    Returns
    -------
    pandas.DataFrame
        A table with columns ``Decay`` and ``BF``, plus optionally
        ``Model`` and ``Model params``.

    Raises
    ------
    ModuleNotFoundError
        If ``pandas`` is not installed; install it with
        ``pip install decaylanguage[modeling]``.

    See also
    --------
    decaylanguage.DecFileParser.build_decay_chains for creating a decay
    chain dict from parsing a .dec file.
    decaylanguage.DecayChain: class for building a decay chain programmatically.
    decaylanguage.DecayChainViewer: class for visualizing decay chains.
    """
    try:
        import pandas as pd  # noqa: PLC0415  # pylint: disable=import-outside-toplevel
    except ModuleNotFoundError as err:
        if err.name == "pandas":
            msg = (
                "decay_chain_to_dataframe requires pandas; "
                "install it with `pip install decaylanguage[modeling]`."
            )
            raise ModuleNotFoundError(msg) from err
        raise

    chain = decaychain if isinstance(decaychain, dict) else decaychain.to_dict()
    rows: list[tuple[str, float, str, str]] = []
    for mother, modes in chain.items():
        for bf, steps in _expand(mother, modes):
            decays, models, params = zip(*steps, strict=True)
            rows.append(
                (" ; ".join(decays), bf, " ; ".join(models), " ; ".join(params))
            )
    columns = ["Decay", "BF"]
    columns += ["Model"] * show_models + ["Model params"] * show_model_params
    return pd.DataFrame(rows, columns=["Decay", "BF", "Model", "Model params"])[columns]
