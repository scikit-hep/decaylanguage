# Copyright (c) 2018-2020, Eduardo Rodrigues and Henry Schreiner.
#
# Distributed under the 3-clause BSD license, see accompanying file LICENSE
# or https://github.com/scikit-hep/decaylanguage for details.

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function


class LineFailure(RuntimeError):
    def __init__(self, line, message, *args, **kwargs):
        super(LineFailure, self).__init__("{0}: {1}".format(line, message), *args, **kwargs)
