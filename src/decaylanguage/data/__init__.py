from __future__ import annotations

from importlib import resources

__all__ = ["basepath"]


basepath = resources.files(__name__)
