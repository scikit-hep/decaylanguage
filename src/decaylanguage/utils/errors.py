# Copyright (c) 2018-2022, Eduardo Rodrigues and Henry Schreiner.
#
# Distributed under the 3-clause BSD license, see accompanying file LICENSE
# or https://github.com/scikit-hep/decaylanguage for details.


class LineFailure(RuntimeError):
    def __init__(self, line, message):
        super().__init__(f"{line}: {message}")
