from __future__ import absolute_import, division, print_function

from copy import copy
from enum import Enum
from itertools import product, combinations

import graphviz
import attr

import numpy as np
import pandas as pd

from .utilities import split, iter_flatten, filter_lines

from ..particle import Particle, SpinType, Par_mapping

from . import ampline

class LS(Enum):
    'Line shapes supported (currently)'
    RBW = 0
    GSpline = 1
    kMatrix = 2
    FOCUS = 3


@attr.s(slots=True)
class AmplitudeChain:
    particle = attr.ib()
    daughters = attr.ib([], convert=lambda x: x if x else [])
    lineshape = attr.ib(None)
    spinfactor = attr.ib(None)
    amp = attr.ib(1+0j, cmp=False, validator=attr.validators.instance_of(complex))
    err = attr.ib(0+0j, cmp=False, validator=attr.validators.instance_of(complex))
    fix = attr.ib(True, cmp=False, validator=attr.validators.instance_of(bool))
    name = attr.ib(None)

    def __attrs_post_init__(self):
        if self.name is None:
            self.name = self.particle.name

    # Class members keep track of additions
    all_particles = set()
    final_particles = set()

    # This is set class-wide, and only used when a line is made
    cartesian = False


    @classmethod
    def from_matched_line(cls, mat):
        '''
        This operates on an already-matched line.

        :param mat: The groupdict output of a match
        :return: A new amplitude chain instance
        '''
        mat['particle'] = Particle.from_AmpGen(mat['name'])

        if mat['particle'] not in cls.all_particles:
            cls.all_particles |= {mat['particle']}

        if mat['daughters']:
            mat['daughters'] = [cls.from_matched_line(ampline.partial.match(x).groupdict()) for x in split(mat['daughters'])]

        # This is only true if not a parital line
        if 'fix_r' in mat:
            # Slightly odd, since we use cartesian, so fixing theta or mag
            # of amplitude only doesn't work
            mat['fix'] = mat['fix_r'] == '2' and mat['fix_i'] == '2'
            del mat['fix_r'], mat['fix_i']

            if cls.cartesian:
                mat['amp'] = float(mat['A']) + float(mat['theta'])*1j
                mat['err'] = float(mat['theta']) + float(mat['dtheta'])*1j

            else:
                A = float(mat['A'])
                dA = float(mat['dA'])
                theta = float(mat['theta'])
                dtheta = float(mat['dtheta'])
                mat['amp'] = A* np.exp(theta*1j)

                mat['err'] = (  (dA*np.cos(theta) + A*np.sin(dtheta)   )
                              + (dA*np.sin(theta) + A*np.cos(dtheta))*1j)

            del mat['A'],  mat['dA'], mat['theta'], mat['dtheta']

        return cls(**mat)


    def expand_lines(self, linelist):
        '''
        Take a DecayTree -> list of DecayTrees with each dead-end daughter
        expanded to every possible combination. (recursive)

        '''

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
        new_trees = [l for line in linelist if line.name == self.name for l in line.expand_lines(linelist)]
        if new_trees:
            return new_trees
        else:
            self.__class__.final_particles |= {self.particle}
            return [self]

    @property
    def ls_enum(self):
        if not self.lineshape:
            return LS.RBW
        elif 'GSpline.EFF' == self.lineshape:
            return LS.GSpline
        elif self.lineshape.startswith('kMatrix'):
            return LS.kMatrix
        elif self.lineshape.startswith('FOCUS'):
            return LS.FOCUS
        else:
            raise RuntimeError("Unimplemented lineshape {0}".format(self.lineshape))

    @property
    def full_amp(self):
        amp = self.amp
        for d in self.daughters:
            amp *= d.full_amp
        return amp

    def is_vertex(self):
        return len(self) == 2

    def is_strong(self):
        if not self.is_vertex():
            return None
        return set(self.particle.quarks) == set(self[0].particle.quarks).union(set(self[1].particle.quarks))

    def L_range(self, conserveParity=False):
        S = self.particle.J
        s1 = self[0].particle.J
        s2 = self[1].particle.J
        min_spin = abs(S-s1-s2)
        min_spin = min(abs(S+s1-s2), min_spin)
        min_spin = min(abs(S-s1+s2), min_spin)
        max_spin = S + s1 + s2
        if not conserveParity:
            return (min_spin, max_spin)
        else:
            raise RuntimeError("Strong decays not implemented yet")

    @property
    def L(self):
        if self.spinfactor:
            return 'S P D F'.split().index(self.spinfactor)
        min_L, _ = self.L_range()
        return min_L # Ground state unless specified


    def __len__(self):
        return len(self.daughters)

    def __getitem__(self, item):
        return self.daughters[item]

    def _get_html(self):
        name = self.particle.html_name

        if self.spinfactor or self.lineshape:
            name += '<br/><br/>'
        if self.spinfactor:
            name += '<font color="blue">[' + self.spinfactor + ']</font>'
        if self.lineshape:
            name += '<font color="red">[' + self.lineshape + ']</font>'
        return name

    def _add_nodes(self, drawing):
        name = self._get_html()
        drawing.node(str(id(self)), "<" + name + ">")
        for p in self.daughters:
            drawing.edge(str(id(self)), str(id(p)))
            p._add_nodes(drawing)

    def _make_graphvis(self):
        d = graphviz.Digraph()
        d.attr(labelloc='t', label=str(self))
        self._add_nodes(d)
        return d

    def _repr_svg_(self):
        return self._make_graphvis()._repr_svg_()

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
        '''
        The structure of the decay chain, simplified to only final state particles
        '''
        if self.daughters:
            return [d.structure for d in self.daughters]
        else:
            return self.particle

    def list_structure(self, final_states):
        '''
        The structure in the form [(0,1,2,3)], where the dual-list is used
        for permutations for bose symmatrization.
        So for final_states=[a,b,c,c], [a,c,[c,b]] would be:
        [(0,2,3,1),(0,3,2,1)]
        '''

        structure = list(iter_flatten(self.structure))

        if set(structure) - set(final_states):
            raise RuntimeError("The final states must encompass all particles in final states!")

        possibilities = [[i for i,v in enumerate(final_states) if v == name] for name in structure]
        return [a for a in product(*possibilities) if len(set(a)) == len(a)]

    def __str__(self):
        name = str(self.particle)
        if self.lineshape and self.spinfactor:
            name += '[' + self.spinfactor + ';' + self.lineshape + ']'
        elif self.lineshape:
            name += '[' + self.lineshape + ']'
        elif self.spinfactor:
            name += '[' + self.spinfactor + ']'
        if self.daughters:
            name += '{'+','.join(map(str,self.daughters))+'}'
        return name

    @classmethod
    def read_AmpGen(cls, filename):
        '''
        Read in an ampgen file

        :param filename: Filename
        :return: array of AmplitudeChains, parameters, constants, event type
        '''

        # Read the file in, ignore empty lines and comments
        with open(filename) as f:
            valid_lines =  [l.strip().rstrip(',') for l in f if l and not l.startswith('#')]

        # Collect known options
        option_lines, valid_lines = filter_lines(ampline.settings, valid_lines)

        # Collect lines with an = in them
        relation_lines, valid_lines = filter_lines(ampline.inverted, valid_lines)

        # Collect "normal" non-Cartesian lines
        real_lines, valid_lines = filter_lines(ampline.dual, valid_lines)

        # Collect Cartesian lines (need combining)
        cart_lines, valid_lines = filter_lines(ampline.cartesian, valid_lines)

        # The other lines do not need explicit filtering
        variable_lines =  [l for l in valid_lines if len(l.split()) == 4]
        constant_lines = [l for l in valid_lines if len(l.split()) == 2]


        # Process the options
        all_states = None
        for mat in option_lines:
            if mat['name'] == 'EventType':
                all_states = [Particle.from_AmpGen(name) for name in mat['value'].split()]
            elif mat['name'] == 'FastCoherentSum::UseCartesian':
                cls.cartesian = bool(mat['value'])

        # Make sure this exists!
        if all_states is None:
            raise RuntimeError("EventType is missing! Cannot compute decay.")

        # Combine dual line Cartesian lines into traditional cartesian lines
        for a, b in combinations(cart_lines, 2):
            if a['name'] == b['name']:
                if a['cart'] == 'Re' and b['cart'] == 'Im':
                    pass
                elif a['cart'] == 'Im' and b['cart'] == 'Re':
                    a,b = b,a
                else:
                    raise RuntimeError("Can't process a line with *both* components Re or Im")
                new_string = "{a[name]} {a[fix]} {a[amp]} {a[err]} {b[fix]} {b[amp]} {b[err]}".format(a=a,b=b)
                real_lines.append(ampline.dual.match(new_string).groupdict())



        # Make the partial lines and constants as dataframes
        parameters = pd.DataFrame(((v.strip() for v in p.split()) for p in variable_lines),
                            columns='name fix value error'.split()).set_index('name')

        constants = pd.DataFrame(((v.strip() for v in p.split()) for p in constant_lines),
                              columns='name value'.split()).set_index('name')


        # Convert the matches into AmplitudeChains
        line_arr = [cls.from_matched_line(a) for a in real_lines]

        # Expand partial lines into complete lines
        new_line_arr = [l for line in line_arr if line.particle == all_states[0] for l in line.expand_lines(line_arr)]

        # Return
        return new_line_arr, parameters, constants, all_states

