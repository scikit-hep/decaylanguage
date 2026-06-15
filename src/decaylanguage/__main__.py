#!/usr/bin/env python
# Copyright (c) 2018-2026, Eduardo Rodrigues and Henry Schreiner.
#
# Distributed under the 3-clause BSD license, see accompanying file LICENSE
# or https://github.com/scikit-hep/decaylanguage for details.


from __future__ import annotations

try:
    from plumbum import cli

    from decaylanguage.modeling.ampgen2goofit import ampgen2goofit, ampgen2goofitpy
except ModuleNotFoundError as err:
    if err.name in {"numpy", "pandas", "plumbum"}:
        msg = (
            "The decaylanguage command-line interface requires extra dependencies; "
            "install them with `pip install decaylanguage[modeling]`."
        )
        raise ModuleNotFoundError(msg) from err
    raise


class DecayLanguageDecay(cli.Application):
    generator = cli.SwitchAttr(
        ["-G", "--generator"], cli.Set("goofit", "goofitpy"), mandatory=True
    )

    # pylint: disable-next=arguments-differ
    def main(self, filename):
        if self.generator == "goofit":
            ampgen2goofit(filename)
        elif self.generator == "goofitpy":
            ampgen2goofitpy(filename)


def main():
    DecayLanguageDecay.run()


if __name__ == "__main__":
    main()
