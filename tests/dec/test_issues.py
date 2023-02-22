# Copyright (c) 2020, Eduardo Rodrigues and Henry Schreiner.
#
# Distributed under the 3-clause BSD license, see accompanying file LICENSE
# or https://github.com/scikit-hep/decaylanguage for details.

from __future__ import annotations

from pathlib import Path

import pytest
from lark import UnexpectedToken

from decaylanguage.dec.dec import DecFileParser

DIR = Path(__file__).parent.resolve()


def test_issue_90():
    p = DecFileParser(DIR / "../data/test_issue90.dec")
    with pytest.raises(UnexpectedToken):
        p.parse()
