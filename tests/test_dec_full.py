# Copyright (c) 2018-2025, Eduardo Rodrigues and Henry Schreiner.
#
# Distributed under the 3-clause BSD license, see accompanying file LICENSE
# or https://github.com/scikit-hep/decaylanguage for details.

from __future__ import annotations

from typing import ClassVar

import pytest
from lark import Lark, Transformer, Tree
from particle import ParticleNotFound

from decaylanguage import data
from decaylanguage.dec import dec
from decaylanguage.dec.enums import PhotosEnum
from decaylanguage.utils.particleutils import particle_from_string_name


class TreeToDec(Transformer):
    def yes(self, _items):
        return True

    def no(self, _items):
        return False

    def global_photos(self, items):
        (item,) = items
        return PhotosEnum.yes if item else PhotosEnum.no

    def value(self, items):
        (item,) = items
        return float(item)

    def label(self, items):
        (item,) = items
        return str(item)

    def photos(self, _items):
        return PhotosEnum.yes


def define(transformed):
    return {x.children[0]: x.children[1] for x in transformed.find_data("define")}


def pythia_def(transformed):
    return [x.children for x in transformed.find_data("pythia_def")]


def alias(transformed):
    return {x.children[0]: x.children[1] for x in transformed.find_data("alias")}


def chargeconj(transformed):
    return {x.children[0]: x.children[1] for x in transformed.find_data("chargeconj")}


# Commands
def global_photos(transformed):
    return {
        x.children[0]: x.children[1] for x in transformed.find_data("global_photos")
    }


def decay(transformed):
    return Tree("decay", list(transformed.find_data("decay")))


def cdecay(transformed):
    return [x.children[0] for x in transformed.find_data("cdecay")]


def setlspw(transformed):
    return list(transformed.find_data("setlspw"))


class TreeToDec2(Transformer):
    missing: ClassVar[str] = set()
    keyerrs: ClassVar[str] = set()

    def __init__(self, alias_dict):
        self.alias_dict = alias_dict

    def particle(self, items):
        (label,) = items
        if label in self.alias_dict:
            label = self.alias_dict[label]
        try:
            return particle_from_string_name(str(label))
        except ParticleNotFound:
            self.missing.add(str(label))
            return str(label)
        except KeyError:
            self.keyerrs.add(str(label))
            return str(label)


@pytest.mark.skip
def test_dec_full():
    txt = data.basepath.joinpath("DECAY_LHCB.DEC").read_text()
    grammar = data.basepath.joinpath("decfile.lark").read_text()

    la = Lark(grammar, parser="lalr", lexer="auto")  # , transformer = TreeToDec())

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
