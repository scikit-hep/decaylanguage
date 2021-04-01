# -*- coding: utf-8 -*-
# Copyright (c) 2018-2021, Eduardo Rodrigues and Henry Schreiner.
#
# Distributed under the 3-clause BSD license, see accompanying file LICENSE
# or https://github.com/scikit-hep/decaylanguage for details.

from lark import Transformer, Tree


def get_from_parser(parser, key):
    return [v.children for v in parser.find_data(key)]


class AmpGenTransformer(Transformer):
    def constant(self, lines):
        particle, value = lines
        return Tree("constant", [str(particle.children[0]), float(value)])

    def event_type(self, lines):
        return Tree("event_type", [str(p.children[0]) for p in lines])

    def fixed(self, lines):
        return False

    def free(self, lines):
        return True

    def variable(self, lines):
        p, free, value, error = lines
        return Tree("variable", [str(p.children[0]), free, float(value), float(error)])

    def cplx_decay_line(self, lines):
        decay, real, imag = lines
        real_free, real_val, real_err = real.children
        imag_free, imag_val, imag_err = imag.children

        decay["fix"] = not (real_free and imag_free)
        decay["amp"] = complex(float(real_val), float(imag_val))
        decay["err"] = complex(float(real_err), float(imag_err))

        return Tree("cplx_decay_line", decay)

    def decay(self, lines):
        (particle,) = lines[0].children
        dic = {"name": str(particle), "daughters": []}

        for line in lines[1:]:
            if line.data == "subdecay":
                dic["daughters"] += line.children
            elif line.data == "decaytype":
                for children in line.children:
                    if children.data == "spinfactor":
                        (dic["spinfactor"],) = children.children
                    elif children.data == "lineshape":
                        (dic["lineshape"],) = children.children

        return dic
