#!/usr/bin/env python
# Copyright (c) 2018-2022, Eduardo Rodrigues and Henry Schreiner.
#
# Distributed under the 3-clause BSD license, see accompanying file LICENSE
# or https://github.com/scikit-hep/decaylanguage for details.


from __future__ import annotations

from plumbum import cli

from decaylanguage.modeling.ampgen2goofit import ampgen2goofit


class DecayLanguageDecay(cli.Application):
    generator = cli.SwitchAttr(["-G", "--generator"], cli.Set("goofit"), mandatory=True)

    # pylint: disable-next=arguments-differ
    def main(self, filename):
        if self.generator == "goofit":
            ampgen2goofit(filename)


def main():
    DecayLanguageDecay.run()


if __name__ == "__main__":
    main()
