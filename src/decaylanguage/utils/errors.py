# Copyright (c) 2018-2023, Eduardo Rodrigues and Henry Schreiner.
#
# Distributed under the 3-clause BSD license, see accompanying file LICENSE
# or https://github.com/scikit-hep/decaylanguage for details.


from __future__ import annotations


class LineFailure(RuntimeError):
    def __init__(self, line: str, message: str) -> None:
        super().__init__(f"{line}: {message}")
