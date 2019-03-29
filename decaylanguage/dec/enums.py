"""
Collection of enums to help characterising .dec decay files.
"""

# Backport needed if Python 2 is used
from enum import IntEnum


class PhotosEnum(IntEnum):
    no = 0
    yes = 1
