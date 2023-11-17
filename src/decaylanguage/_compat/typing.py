from __future__ import annotations

import sys
import typing

if sys.version_info < (3, 8):
    from typing_extensions import TypedDict
else:
    from typing import TypedDict

if sys.version_info < (3, 11):
    if typing.TYPE_CHECKING:
        from typing_extensions import Self
    else:
        Self = object
else:
    from typing import Self


__all__ = ["TypedDict", "Self"]
