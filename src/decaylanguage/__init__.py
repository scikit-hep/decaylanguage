# Copyright (c) 2018-2023, Eduardo Rodrigues and Henry Schreiner.
#
# Distributed under the 3-clause BSD license, see accompanying file LICENSE
# or https://github.com/scikit-hep/decaylanguage for details.

from __future__ import annotations

# Convenient access to the version number
from ._version import version as __version__

# Direct access to decay file parsing tools
from .dec import DecFileParser

# Direct access to decay chain representation classes and visualization tools
from .decay import DaughtersDict, DecayChain, DecayChainViewer, DecayMode

__all__ = (
    "__version__",
    "DecFileParser",
    "DecayChainViewer",
    "DaughtersDict",
    "DecayMode",
    "DecayChain",
)


def __dir__() -> tuple[str, ...]:
    return __all__
