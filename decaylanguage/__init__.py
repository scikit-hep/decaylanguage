import re

__version__ = '__version__ = '0.1.0''
version = __version__

version_info = tuple(re.split(r"[-\.]", __version__))

del re
