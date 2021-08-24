# -*- coding: utf-8 -*-
# Copyright (c) 2018-2021, Eduardo Rodrigues and Henry Schreiner.
#
# Distributed under the 3-clause BSD license, see accompanying file LICENSE
# or https://github.com/scikit-hep/decaylanguage for details.

"""
A class representing a set of decays. Can be subclassed to provide custom converters.
"""

from __future__ import absolute_import, division, print_function

import os
import re
import sys
from copy import copy
from enum import Enum
from itertools import product

import attr
import numpy as np
import pandas as pd
from lark import Lark
from particle import Particle

from .. import data
from ..data import open_text
from .ampgentransform import AmpGenTransformer, get_from_parser
from .decay import ModelDecay


class LS(Enum):
    "Line shapes supported (currently)"
    RBW = 0
    GSpline = 1
    kMatrix = 2
    FOCUS = 3


@attr.s(slots=True)
class AmplitudeChain(ModelDecay):
    'This is a chain of decays (a "line")'

    lineshape = attr.ib(None)
    spinfactor = attr.ib(None)
    amp = attr.ib(
        1 + 0j, eq=False, order=False, validator=attr.validators.instance_of(complex)
    )
    err = attr.ib(
        0 + 0j, eq=False, order=False, validator=attr.validators.instance_of(complex)
    )
    fix = attr.ib(
        True, eq=False, order=False, validator=attr.validators.instance_of(bool)
    )
    name = attr.ib(None)

    # Class members keep track of additions
    all_particles = set()  # type: ignore
    final_particles = set()  # type: ignore

    # This is set class-wide, and only used when a line is made
    cartesian = False

    @classmethod
    def from_matched_line(cls, mat):
        """
        This operates on an already-matched line.

        :param mat: The groupdict output of a match
        :return: A new amplitude chain instance
        """

        getall = "all" if hasattr(Particle, "all") else "table"  # Support 0.4.4

        # Check to see if new particles loaded; if not, load them.
        if 998100 not in getattr(Particle, getall)():
            data_dir = os.path.dirname(os.path.realpath(__file__))
            special_filename = os.path.join(
                data_dir, "..", "data", "MintDalitzSpecialParticles.csv"
            )
            Particle.load_table(special_filename, append=True)

        try:
            mat["particle"] = Particle.from_string(mat["name"])
        except Exception:
            print(
                "Failed to find particle",
                mat["name"],
                "with parsed dictionary:",
                mat,
                file=sys.stderr,
            )
            raise

        if mat["particle"] not in cls.all_particles:
            cls.all_particles |= {mat["particle"]}

        if mat["daughters"]:
            mat["daughters"] = [cls.from_matched_line(d) for d in mat["daughters"]]

        # if master line only
        if "amp" in mat and not cls.cartesian:
            A = mat["amp"].real
            dA = mat["err"].real
            theta = mat["amp"].imag
            dtheta = mat["err"].imag

            mat["amp"] = A * np.exp(theta * 1j)

            mat["err"] = (dA * np.cos(theta) + A * np.sin(dtheta)) + (
                dA * np.sin(theta) + A * np.cos(dtheta)
            ) * 1j

        return cls(**mat)

    def expand_lines(self, linelist):
        """
        Take a DecayTree -> list of DecayTrees with each dead-end daughter
        expanded to every possible combination. (recursive)

        """

        # If the Tree has daugthers, run on those
        if self.daughters:
            dlist = [d.expand_lines(linelist) for d in self.daughters]
            retlist = []
            for ds in product(*dlist):
                newd = copy(self)
                newd.daughters = ds
                retlist.append(newd)
            return retlist

        # If the tree ends
        new_trees = [
            ln
            for line in linelist
            if line.name == self.name
            for ln in line.expand_lines(linelist)
        ]
        if new_trees:
            return new_trees
        self.__class__.final_particles |= {self.particle}
        return [self]

    @property
    def ls_enum(self):
        if not self.lineshape:
            return LS.RBW
        elif self.lineshape == "GSpline.EFF":
            return LS.GSpline
        elif self.lineshape.startswith("kMatrix"):
            return LS.kMatrix
        elif self.lineshape.startswith("FOCUS"):
            return LS.FOCUS
        else:
            raise RuntimeError("Unimplemented lineshape {}".format(self.lineshape))

    @property
    def full_amp(self):
        amp = self.amp
        for d in self.daughters:
            amp *= d.full_amp
        return amp

    def L_range(self, conserveParity=False):
        S = self.particle.J
        s1 = self[0].particle.J
        s2 = self[1].particle.J
        min_spin = abs(S - s1 - s2)
        min_spin = min(abs(S + s1 - s2), min_spin)
        min_spin = min(abs(S - s1 + s2), min_spin)
        max_spin = S + s1 + s2
        if not conserveParity:
            return (min_spin, max_spin)
        else:
            raise RuntimeError("Strong decays not implemented yet")

    @property
    def L(self):
        if self.spinfactor:
            return "S P D F".split().index(self.spinfactor)
        min_L, _ = self.L_range()
        return min_L  # Ground state unless specified

    def _get_html(self):
        name = self.particle.html_name
        name = re.sub(
            r'<SPAN STYLE="text-decoration:overline">(.*)</SPAN>', u"\\1\u0305", name
        )

        if self.spinfactor or self.lineshape:
            name += "<br/><br/>"
        if self.spinfactor:
            name += '<font color="blue">[' + self.spinfactor + "]</font>"
        if self.lineshape:
            name += '<font color="red">[' + self.lineshape + "]</font>"
        return name

    def __str__(self):
        name = str(self.particle)
        if self.lineshape and self.spinfactor:
            name += "[" + self.spinfactor + ";" + self.lineshape + "]"
        elif self.lineshape:
            name += "[" + self.lineshape + "]"
        elif self.spinfactor:
            name += "[" + self.spinfactor + "]"
        if self.daughters:
            name += "{" + ",".join(map(str, self.daughters)) + "}"
        return name

    @classmethod
    def read_ampgen(
        cls, filename=None, text=None, grammar=None, parser="lalr", **kargs
    ):
        """
        Read in an ampgen file

        :param filename: Filename to read
        :param text: Text to read (use instead of filename)
        :return: array of AmplitudeChains, parameters, constants, event type
        """

        if grammar is None:
            grammar = open_text(data, "ampgen.lark")

        # Read the file in, ignore empty lines and comments
        if filename is not None:
            with open(filename) as f:
                text = f.read()
        elif text is None:
            raise RuntimeError("Must have filename or text")

        lark = Lark(grammar, parser=parser, transformer=AmpGenTransformer(), **kargs)
        parsed = lark.parse(text)

        (event_type,) = get_from_parser(parsed, "event_type")

        # invert_lines = get_from_parser(parsed, "invert_line")
        cplx_decay_lines = get_from_parser(parsed, "cplx_decay_line")
        # cart_decay_lines = get_from_parser(parsed, "cart_decay_line")
        variables = get_from_parser(parsed, "variable")
        constants = get_from_parser(parsed, "constant")

        try:
            all_states = [Particle.from_string(n) for n in event_type]
        except Exception:
            print("Did not find at least one of the state particles from", *event_type)
            raise

        fcs = get_from_parser(parsed, "fast_coherent_sum")
        if fcs:
            (fcs,) = fcs
            (fcs,) = fcs.children
            cls.cartesian = bool(fcs)

        # TODO: re-enable this
        # Combine dual line Cartesian lines into traditional cartesian lines
        # for a, b in combinations(cart_decay_lines, 2):
        #     if a['name'] == b['name']:
        #        if a['cart'] == 'Re' and b['cart'] == 'Im':
        #            pass
        #        elif a['cart'] == 'Im' and b['cart'] == 'Re':
        #            a, b = b, a
        #        else:
        #            raise RuntimeError("Can't process a line with *both* components Re or Im")
        #        new_string = "{a[name]} {a[fix]} {a[amp]} {a[err]} {b[fix]} {b[amp]} {b[err]}".format(
        #            a=a, b=b)
        #        real_lines.append(ampline.dual.match(new_string).groupdict())

        # Make the partial lines and constants as dataframes
        parameters = pd.DataFrame(
            variables, columns="name fix value error".split()
        ).set_index("name")

        constants = pd.DataFrame(constants, columns="name value".split()).set_index(
            "name"
        )

        # Convert the matches into AmplitudeChains
        line_arr = [cls.from_matched_line(c) for c in cplx_decay_lines]

        # Expand partial lines into complete lines
        new_line_arr = [
            ln
            for line in line_arr
            if line.particle == all_states[0]
            for ln in line.expand_lines(line_arr)
        ]

        # Return
        return new_line_arr, parameters, constants, all_states
