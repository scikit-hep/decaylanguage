'''
A class representing a set of decays. Can be subclassed to provide custom converters.
'''


from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

from copy import copy
from enum import Enum
from itertools import combinations
from itertools import product

import attr
import numpy as np
import pandas as pd

from .decay import Decay
from ..particle import Particle
from ..utils import filter_lines
from ..utils import split

from ..data import open_text_file


from lark import Lark
from .ampgentransform import AmpGenTransformer, get_from_parser

class LS(Enum):
    'Line shapes supported (currently)'
    RBW = 0
    GSpline = 1
    kMatrix = 2
    FOCUS = 3


@attr.s(slots=True)
class AmplitudeChain(Decay):
    'This is a chain of decays (a "line")'

    lineshape = attr.ib(None)
    spinfactor = attr.ib(None)
    amp = attr.ib(1+0j, cmp=False, validator=attr.validators.instance_of(complex))
    err = attr.ib(0+0j, cmp=False, validator=attr.validators.instance_of(complex))
    fix = attr.ib(True, cmp=False, validator=attr.validators.instance_of(bool))
    name = attr.ib(None)


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
            mat['daughters'] = [cls.from_matched_line(d) for d in mat['daughters']]

        # if master line only
        if 'amp' in mat and not cls.cartesian:
            A = mat['amp'].real
            dA = mat['err'].real
            theta = mat['amp'].imag
            dtheta = mat['err'].imag

            mat['amp'] = A * np.exp(theta*1j)

            mat['err'] = ((dA*np.cos(theta) + A*np.sin(dtheta))
                          + (dA*np.sin(theta) + A*np.cos(dtheta))*1j)


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
        new_trees = [l for line in linelist if line.name ==
                     self.name for l in line.expand_lines(linelist)]
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
        return min_L  # Ground state unless specified


    def _get_html(self):
        name = self.particle.html_name

        if self.spinfactor or self.lineshape:
            name += '<br/><br/>'
        if self.spinfactor:
            name += '<font color="blue">[' + self.spinfactor + ']</font>'
        if self.lineshape:
            name += '<font color="red">[' + self.lineshape + ']</font>'
        return name

    def __str__(self):
        name = str(self.particle)
        if self.lineshape and self.spinfactor:
            name += '[' + self.spinfactor + ';' + self.lineshape + ']'
        elif self.lineshape:
            name += '[' + self.lineshape + ']'
        elif self.spinfactor:
            name += '[' + self.spinfactor + ']'
        if self.daughters:
            name += '{'+','.join(map(str, self.daughters))+'}'
        return name

    @classmethod
    def read_ampgen(cls, filename=None, text=None, grammar=None, parser='lalr', **kargs):
        '''
        Read in an ampgen file

        :param filename: Filename to read
        :param text: Text to read (use instead of filename)
        :return: array of AmplitudeChains, parameters, constants, event type
        '''

        if grammar is None:
            grammar = open_text_file('ampgen.lark')

        # Read the file in, ignore empty lines and comments
        if filename is not None:
            with open(filename) as f:
                text = f.read()
        elif text is None:
            raise RuntimeError("Must have filename or text")

        lark = Lark(grammar, parser=parser, transformer=AmpGenTransformer(), **kargs)
        parsed = lark.parse(text)

        event_type, = get_from_parser(parsed, 'event_type')

        invert_lines = get_from_parser(parsed, 'invert_line')
        cplx_decay_lines = get_from_parser(parsed, 'cplx_decay_line')
        cart_decay_lines = get_from_parser(parsed, 'cart_decay_line')
        variables = get_from_parser(parsed, 'variable')
        constants = get_from_parser(parsed, 'constant')

        all_states = [Particle.from_AmpGen(n) for n in event_type]

        fcs = get_from_parser(parsed, 'fast_coherent_sum')
        if fcs:
            fcs, = fcs
            fcs, = fcs.children
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
        parameters = pd.DataFrame(variables,
                                  columns='name fix value error'.split()).set_index('name')

        constants = pd.DataFrame(constants,
                                 columns='name value'.split()).set_index('name')


        #from IPython.core.debugger import Pdb
        #Pdb().set_trace()
        # Convert the matches into AmplitudeChains
        line_arr = [cls.from_matched_line(c) for c in cplx_decay_lines]

        # Expand partial lines into complete lines
        new_line_arr = [l for line in line_arr if line.particle == all_states[0]
                        for l in line.expand_lines(line_arr)]

        # Return
        return new_line_arr, parameters, constants, all_states
