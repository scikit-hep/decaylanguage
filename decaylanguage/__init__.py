from __future__ import absolute_import


__version__ = '0.2.0'

version = __version__
version_info = __version__.split('.')


# Direct access to decay file parsing tools
from .dec import DecFileParser
