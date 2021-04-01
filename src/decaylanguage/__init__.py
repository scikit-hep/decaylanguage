# -*- coding: utf-8 -*-
# Copyright (c) 2018-2021, Eduardo Rodrigues and Henry Schreiner.
#
# Distributed under the 3-clause BSD license, see accompanying file LICENSE
# or https://github.com/scikit-hep/decaylanguage for details.


# Convenient access to the version number
from ._version import version as __version__

# Direct access to decay file parsing tools
from .dec import DecFileParser

# Direct access to decay chain visualization tools
from .decay import DecayChainViewer

# Direct access to decay chain representation classes
from .decay import DaughtersDict, DecayMode, DecayChain

__all__ = (
    "__version__",
    "DecFileParser",
    "DecayChainViewer",
    "DaughtersDict",
    "DecayMode",
    "DecayChain",
)
