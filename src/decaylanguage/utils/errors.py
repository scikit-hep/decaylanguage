# -*- coding: utf-8 -*-
# Copyright (c) 2018-2021, Eduardo Rodrigues and Henry Schreiner.
#
# Distributed under the 3-clause BSD license, see accompanying file LICENSE
# or https://github.com/scikit-hep/decaylanguage for details.

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function


class LineFailure(RuntimeError):
    def __init__(self, line, message):
        super(LineFailure, self).__init__("{}: {}".format(line, message))
