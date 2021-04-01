# -*- coding: utf-8 -*-
import sys

if sys.version_info < (3, 7):
    from importlib_resources import open_text
else:
    from importlib.resources import open_text

__all__ = ("open_text",)
