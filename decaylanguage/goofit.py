#!/usr/bin/env python
# coding: utf-8

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

from plumbum import cli

from decaylanguage.decay.ampgen2goofit import ampgen2goofit


class AmpGen2GooFit(cli.Application):
    def main(self, filename):
        ampgen2goofit(filename)


def main():
    AmpGen2GooFit.run()


if __name__ == "__main__":
    main()
