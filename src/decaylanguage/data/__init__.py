from __future__ import annotations

import sys

from deprecated import deprecated

if sys.version_info < (3, 9):
    import importlib_resources as resources
else:
    from importlib import resources


__all__ = ["basepath", "open_text"]


basepath = resources.files(__name__)


open_text = deprecated(
    version="0.12.0", reason="Use decaylanguage.data.basepath instead."
)(resources.open_text)
