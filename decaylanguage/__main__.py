#!/usr/bin/env python
# coding: utf-8

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

from plumbum import cli

from decaylanguage.decay.ampgen2goofit import ampgen2goofit


class DecayLanguageDecay(cli.Application):
    generator = cli.SwitchAttr(['-G', '--generator'], cli.Set('goofit'), mandatory=True)

    def main(self, filename):
        if self.generator == 'goofit':
            ampgen2goofit(filename)


def main():
    DecayLanguageDecay.run()


if __name__ == "__main__":
    main()
