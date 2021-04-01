# -*- coding: utf-8 -*-
# Copyright (c) 2018-2021, Eduardo Rodrigues and Henry Schreiner.
#
# Distributed under the 3-clause BSD license, see accompanying file LICENSE
# or https://github.com/scikit-hep/decaylanguage for details.

"""
A general base class representing decays.
"""


from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import attr
import warnings
from itertools import product

from ..utils import iter_flatten


try:
    import graphviz
except ImportError:
    graphviz = None
    warnings.warn("Graphviz is not installed. Line display not available.")


@attr.s(slots=True)
class ModelDecay(object):
    """
    This describes a decay very generally, with search and print features.
    Subclassed for futher usage.
    """

    particle = attr.ib()
    daughters = attr.ib([], converter=lambda x: x if x else [])  # type: ignore
    name = attr.ib(None)

    def __attrs_post_init__(self):
        if self.name is None:
            self.name = self.particle.name

    def is_vertex(self):
        return len(self) == 2

    def is_strong(self):
        if not self.is_vertex():
            return None
        return set(self.particle.quarks) == set(self[0].particle.quarks).union(
            set(self[1].particle.quarks)
        )

    def __len__(self):
        return len(self.daughters)

    def __getitem__(self, item):
        return self.daughters[item]

    def _get_html(self):
        """
        Get the html dot representation of this node only. Override in subclasses.
        """
        return self.particle.html_name

    def _add_nodes(self, drawing):
        name = self._get_html()
        drawing.node(str(id(self)), "<" + name + ">")
        for p in self.daughters:
            drawing.edge(str(id(self)), str(id(p)))
            p._add_nodes(drawing)

    @property
    def vertexes(self):
        verts = []
        for d in self.daughters:
            if d.is_vertex():
                verts.append(d)
                verts += d.vertexes
        return verts

    @property
    def structure(self):
        """
        The structure of the decay chain, simplified to only final state particles
        """
        if self.daughters:
            return [d.structure for d in self.daughters]
        else:
            return self.particle

    def list_structure(self, final_states):
        """
        The structure in the form [(0,1,2,3)], where the dual-list is used
        for permutations for bose symmatrization.
        So for final_states=[a,b,c,c], [a,c,[c,b]] would be:
        [(0,2,3,1),(0,3,2,1)]
        """

        structure = list(iter_flatten(self.structure))

        if set(structure) - set(final_states):
            raise RuntimeError(
                "The final states must encompass all particles in final states!"
            )

        possibilities = [
            [i for i, v in enumerate(final_states) if v == name] for name in structure
        ]
        return [a for a in product(*possibilities) if len(set(a)) == len(a)]

    def __str__(self):
        name = str(self.particle)

        if self.daughters:
            name += "{" + ",".join(map(str, self.daughters)) + "}"
        return name

    if graphviz:

        def _make_graphviz(self):
            d = graphviz.Digraph()
            d.attr(labelloc="t", label=str(self))
            self._add_nodes(d)
            return d

        def _repr_svg_(self):
            return self._make_graphviz()._repr_svg_()
