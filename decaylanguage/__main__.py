#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (c) 2018-2021, Eduardo Rodrigues and Henry Schreiner.
#
# Distributed under the 3-clause BSD license, see accompanying file LICENSE
# or https://github.com/scikit-hep/decaylanguage for details.

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

from plumbum import cli

from decaylanguage.modeling.ampgen2goofit import ampgen2goofit


class DecayLanguageDecay(cli.Application):
    generator = cli.SwitchAttr(["-G", "--generator"], cli.Set("goofit"), mandatory=True)

    def main(self, filename):
        if self.generator == "goofit":
            ampgen2goofit(filename)


def main():
    DecayLanguageDecay.run()


if __name__ == "__main__":
    main()
