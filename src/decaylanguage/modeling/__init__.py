# Copyright (c) 2018-2026, Eduardo Rodrigues and Henry Schreiner.
#
# Distributed under the 3-clause BSD license, see accompanying file LICENSE
# or https://github.com/scikit-hep/decaylanguage for details.

from __future__ import annotations

try:
    from .amplitudechain import LS, AmplitudeChain
except ModuleNotFoundError as err:
    if err.name in {"numpy", "pandas", "plumbum"}:
        msg = (
            "The decaylanguage modeling subpackage requires extra dependencies; "
            "install them with `pip install decaylanguage[modeling]`."
        )
        raise ModuleNotFoundError(msg) from err
    raise

__all__ = ("LS", "AmplitudeChain")


def __dir__() -> tuple[str, ...]:
    return __all__
