#!/usr/bin/env python
# coding: utf-8

from decaylanguage.decay.ampgen2goofit import ampgen2goofit

from plumbum import cli

class AmpGen2GooFit(cli.Application):
    def main(self, filename):
        ampgen2goofit(filename)

def main():
    AmpGen2GooFit.run()

if __name__ == "__main__":
    main()
