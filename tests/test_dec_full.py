# Copyright (c) 2018-2020, Eduardo Rodrigues and Henry Schreiner.
#
# Distributed under the 3-clause BSD license, see accompanying file LICENSE
# or https://github.com/scikit-hep/decaylanguage for details.

from particle import Particle, ParticleNotFound

from decaylanguage import data
from decaylanguage.dec import dec
from lark import Lark, Transformer, Tree

import pytest

class TreeToDec2(Transformer):
    missing = set()
    keyerrs = set()

    def __init__(self, alias_dict):
        self.alias_dict = alias_dict

    def particle(self, items):
        label, = items
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
    with data.open_text(data, 'DECAY_LHCB.DEC') as f:
        txt = f.read()

    with data.open_text(data, 'decfile.lark') as f:
        grammar = f.read()

    l = Lark(grammar, parser='lalr', lexer='standard')  # , transformer = TreeToDec())

    parsed = l.parse(txt)
    assert bool(parsed)

    transformed = dec.TreeToDec().transform(parsed)

    define = dec.define(transformed)
    pythia_def = dec.pythia_def(transformed)
    alias = dec.alias(transformed)
    chargeconj = dec.chargeconj(transformed)
    global_photos = dec.global_photos(transformed)
    decay = dec.decay(transformed)
    cdecay = dec.cdecay(transformed)
    setlspw = dec.setlspw(transformed)

    for item in pythia_def:
        print(item[0], ":", item[1], "=", item[2])


    labelled = TreeToDec2(alias).transform(decay)

    print(TreeToDec2.missing)
    print(TreeToDec2.keyerrs)

    assert len(TreeToDec2.missing) == 0
