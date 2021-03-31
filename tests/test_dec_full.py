# -*- coding: utf-8 -*-
# Copyright (c) 2018-2021, Eduardo Rodrigues and Henry Schreiner.
#
# Distributed under the 3-clause BSD license, see accompanying file LICENSE
# or https://github.com/scikit-hep/decaylanguage for details.

from particle import Particle, ParticleNotFound

from decaylanguage import data
from decaylanguage.dec import dec
from lark import Lark, Transformer

import pytest


class TreeToDec2(Transformer):
    missing = set()
    keyerrs = set()

    def __init__(self, alias_dict):
        self.alias_dict = alias_dict

    def particle(self, items):
        (label,) = items
        if label in self.alias_dict:
            label = self.alias_dict[label]
        try:
            return Particle.from_string(str(label))
        except ParticleNotFound:
            self.missing.add(str(label))
            return str(label)
        except KeyError:
            self.keyerrs.add(str(label))
            return str(label)


@pytest.mark.skip
def test_dec_full():
    with data.open_text(data, "DECAY_LHCB.DEC") as f:
        txt = f.read()

    with data.open_text(data, "decfile.lark") as f:
        grammar = f.read()

    la = Lark(grammar, parser="lalr", lexer="standard")  # , transformer = TreeToDec())

    parsed = la.parse(txt)
    assert bool(parsed)

    transformed = dec.TreeToDec().transform(parsed)

    dec.define(transformed)
    pythia_def = dec.pythia_def(transformed)
    alias = dec.alias(transformed)
    dec.chargeconj(transformed)
    dec.global_photos(transformed)
    decay = dec.decay(transformed)
    dec.cdecay(transformed)
    dec.setlspw(transformed)

    for item in pythia_def:
        print(item[0], ":", item[1], "=", item[2])

    TreeToDec2(alias).transform(decay)

    print(TreeToDec2.missing)
    print(TreeToDec2.keyerrs)

    assert len(TreeToDec2.missing) == 0
