# -*- coding: utf-8 -*-
# Copyright (c) 2018-2021, Eduardo Rodrigues and Henry Schreiner.
#
# Distributed under the 3-clause BSD license, see accompanying file LICENSE
# or https://github.com/scikit-hep/decaylanguage for details.

from decaylanguage.modeling.ampgen2goofit import ampgen2goofit

try:
    from pathlib2 import Path
except ImportError:
    from pathlib import Path

import pytest


DIR = Path(__file__).parent.resolve()


@pytest.mark.skip
def test_full_convert():
    text = ampgen2goofit(DIR / "../models/DtoKpipipi_v2.txt", ret_output=True)
    with (DIR / "output/DtoKpipipi_v2.cu").open() as f:
        assert {x.strip() for x in text.splitlines() if "Generated on" not in x} == {
            x.strip() for x in f.readlines() if "Generated on" not in x
        }
