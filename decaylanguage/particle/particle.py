# -*- encoding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

# Python standard library
import operator
import os
import re
from copy import copy
# Backport needed if Python 2 is used
from enum import IntEnum
from fractions import Fraction
from functools import reduce
from functools import total_ordering

# External dependencies
import attr
import pandas as pd

# The path of this file (used to load data files)
dir_path = os.path.dirname(os.path.realpath(__file__))

# Default files to load
FILE_LATEX = os.path.join(dir_path, 'pdgID_to_latex.txt')
FILE_MASSES = os.path.join(dir_path, 'mass_width.csv')
FILE_EXTENDED = os.path.join(dir_path, 'MintDalitzSpecialParticles.csv')


def programatic_name(name):
    'Return a name safe to use as a variable name'
    return (name.replace('(', '').replace(')', '')
            .replace('*', '').replace('::', '_')
            .replace('-', 'm').replace('+', 'p')
            .replace('~', 'bar'))


getname = re.compile(r'''
^                                           # Beginning of string
      (?P<name>       \w+?        )         # One or more characters, non-greedy
(?:\( (?P<state>      \d+         ) \)      # Optional state in ()
      (?=             \*? \(      )  )?     #   - lookahead for mass
      (?P<star>       \*          )?        # Optional star
(?:\( (?P<mass>       \d+         ) \) )?   # Optional mass in ()
      (?P<bar>        bar         )?        # Optional bar
      (?P<charge>     [0\+\-][+-]?)         # Required 0, -, --, or +, ++
$                                           # End of string
''', re.VERBOSE)


class SpinType(IntEnum):
    'The spin type of a particle'
    Scalar = 1  # (0, 1)
    PseudoScalar = -1  # (0,-1)
    Vector = 2  # (1,-1)
    Axial = -2  # (1, 1)
    Tensor = 3  # (2, 1)
    PseudoTensor = -3  # (2,-1)
    Unknown = 0  # (0, 0)


class Par(IntEnum):
    'Represents parity or charge'
    pp = 2
    p = 1
    o = 0
    m = -1
    mm = -2
    u = 5


Charge = Par


class Inv(IntEnum):
    'Definition of what happens when particle is inverted'
    Same = 0
    Full = 1
    Barless = 2


class Status(IntEnum):
    'The status of the particle'
    Common = 0
    Rare = 1
    Unsure = 2
    Further = 3
    Nonexistant = 4


# Mappings that allow the above classes to be produced from text mappings
Par_mapping = {'+': Par.p, '0': Par.o, '+2/3': Par.u,
               '++': Par.pp, '-': Par.m, '-1/3': Par.u, '?': Par.u, '': Par.o}
Inv_mapping = {'': Inv.Same, 'F': Inv.Full, 'B': Inv.Barless}
Status_mapping = {'R': Status.Common, 'D': Status.Rare, 'S': Status.Unsure, 'F': Status.Further}

# Mappings that allow the above classes to be turned into text mappings
Par_undo = {Par.pp: '++', Par.p: '+', Par.o: '0', Par.m: '-', Par.mm: '--', Par.u: '?'}
Par_prog = {Par.pp: 'pp', Par.p: 'p', Par.o: '0', Par.m: 'm', Par.mm: 'mm', Par.u: 'u'}


def get_from_latex(filename):
    'Produce a pandas series from a file with latex mappings in it'
    latex_table = pd.read_csv(filename, delim_whitespace=True, names='id a b'.split(), index_col=0)
    series_real = latex_table.a
    series_anti = latex_table.b
    series_anti.index = -series_anti.index
    return pd.concat([series_real, series_anti])


def get_from_PDG(filename, latexes=(FILE_LATEX,)):
    'Read a file, plus a list of latex files, to produce a pandas DataFrame with particle information'

    def unmap(mapping):
        return lambda x: mapping[x.strip()]

    # Convert each column from text to appropriate data type
    PDG_converters = dict(
        Charge=unmap(Par_mapping),
        G=unmap(Par_mapping),
        P=unmap(Par_mapping),
        C=unmap(Par_mapping),
        A=unmap(Inv_mapping),
        Rank=lambda x: int(x.strip()) if x.strip() else 0,
        ID=lambda x: int(x.strip()) if x.strip() else -1,
        Status=unmap(Status_mapping),
        Name=lambda x: x.strip(),
        I=lambda x: x.strip(),  # noqa: E741
        J=lambda x: x.strip(),
        Quarks=lambda x: x.strip()
    )

    # Read in the table, apply the converters, add names, ignore comments
    pdg_table = pd.read_csv(filename, comment='*', names='Mass,MassUpper,MassLower,Width,WidthUpper,WidthLower,I,G,J,P,C,A,'
                            'ID,Charge,Rank,Status,Name,Quarks'.split(','),
                            converters=PDG_converters
                            )

    # Filtering out non-particles (quarks, negative IDs)
    pdg_table = pdg_table[pdg_table.Charge != Par.u]
    pdg_table = pdg_table[pdg_table.ID >= 0]

    # PDG's ID should be the key to table
    pdg_table.set_index('ID', inplace=True)

    # Some post processing to produce inverted particles
    pdg_table_inv = pdg_table[(pdg_table.A == Inv.Full)
                              | ((pdg_table.A == Inv.Barless)
                                 # Maybe add?    & (pdg_table.Charge != Par.u)
                                 & (pdg_table.Charge != Par.o))].copy()
    pdg_table_inv.index = -pdg_table_inv.index
    pdg_table_inv.loc[(pdg_table_inv.A != Inv.Same) & (
        pdg_table_inv.Charge != Par.u), 'Charge'] *= -1
    pdg_table_inv.Quarks = (pdg_table_inv.Quarks.str.swapcase()
                            .str.replace('SQRT', 'sqrt')
                            .str.replace('P', 'p').str.replace('Q', 'q')
                            .str.replace('mAYBE NON', 'Maybe non')
                            .str.replace('X', 'x').str.replace('Y', 'y'))

    # Make a combined table with + and - ID numbers
    full = pd.concat([pdg_table, pdg_table_inv])

    # Add the latex
    latex_series = pd.concat([get_from_latex(latex) for latex in latexes])
    full = full.assign(Latex=latex_series)

    # Return the table, making sure NaNs are just empty strings
    return full.fillna('')


def mkul(upper, lower):
    'Utility to print out an uncertainty with different or identical upper/lower bounds'
    if upper == lower:
        if upper == 0:
            return ''
        else:
            return '± {upper:g}'.format(upper=upper)
    else:
        return '+ {upper:g} - {lower:g}'.format(upper=upper, lower=lower)


@total_ordering
@attr.s(slots=True, cmp=False)
class Particle(object):
    'The Particle object class. Hold a series of properties for a particle.'
    val = attr.ib()
    name = attr.ib()
    mass = attr.ib()
    width = attr.ib()
    charge = attr.ib()
    A = attr.ib()  # Info about particle name for anti-particles
    rank = attr.ib(0)  # Next line is Isospin
    I = attr.ib(None)  # noqa: E741
    J = attr.ib(None)  # Total angular momentum
    G = attr.ib(Par.u)  # Parity: '', +, -, or ?
    P = attr.ib(Par.u)  # Space parity
    C = attr.ib(Par.u)  # Charge conjugation parity
    # (B (just charge), F (add bar) , and '' (No change))
    quarks = attr.ib('')
    status = attr.ib(Status.Nonexistant)
    latex = attr.ib('')
    mass_upper = attr.ib(0.0)
    mass_lower = attr.ib(0.0)
    width_upper = attr.ib(0.0)
    width_lower = attr.ib(0.0)

    # Make a class level property that holds the PDG table. Loads on first access (via method)
    _pdg_table = None

    @classmethod
    def load_pdg_table(cls, files=(FILE_MASSES, FILE_EXTENDED), latexes=(FILE_LATEX,)):
        'Load a PDG table. Will be called on first access to the PDG table'
        tables = [get_from_PDG(f, latexes) for f in files]
        cls._pdg_table = pd.concat(tables)

    @classmethod
    def pdg_table(cls):
        'Get the PDG table. Loads on first access.'
        if cls._pdg_table is None:
            cls.load_pdg_table()
        return cls._pdg_table

    # The following needed for total ordering (sort, etc)

    def __le__(self, other):
        return abs(self.val) < (abs(other.val)-.5)

    def __eq__(self, other):
        return self.val == other.val

    def __hash__(self):
        return hash(self.val)

    @property
    def radius(self):
        'Particle radius, hard coded'
        if abs(self.val) in [411, 421, 431]:
            return 5
        else:
            return 1.5

    @property
    def bar(self):
        'Check to see if particle is inverted'
        return self.val < 0 and self.A == Inv.Full

    @property
    def spintype(self):  # -> SpinType:
        'Access the SpinType enum'
        if self.J in [0, 1, 2]:
            J = int(self.J)

            if self.P == Par.p:
                return (SpinType.Scalar, SpinType.Axial, SpinType.Tensor)[J]
            elif self.P == Par.m:
                return (SpinType.PseudoScalar, SpinType.Vector, SpinType.PseudoTensor)[J]

        return SpinType.Unknown

    def invert(self):
        "Get the antiparticle"
        other = copy(self)
        if self.A == Inv.Full or (self.A == Inv.Barless and self.charge != Par.o):
            other.val = -self.val

            if self.charge != Par.u:
                other.charge = -self.charge

            try:
                other.quarks = (self.quarks.swapcase()
                                .replace('SQRT', 'sqrt')
                                .replace('P', 'p').replace('Q', 'q')
                                .replace('mAYBE NON', 'Maybe non')
                                .replace('X', 'x').replace('Y', 'y'))
            except AttributeError:
                pass
        return other

    # Pretty descriptions

    def __str__(self):
        return self.name + ('~' if self.A == Inv.Full and self.val < 0 else '') + Par_undo[self.charge]

    def _repr_latex_(self):
        name = self.latex
        if self.bar:
            name = re.sub(r'^(\\mathrm{|)([\w\\]\w*)', r'\1\\bar{\2}', name)
        return ("$" + name + '$') if self.latex else '?'

    def describe(self):
        'Make a nice high-density string for a particle\'s properties.'
        if self.val == 0:
            return "Name: Unknown"

        val = """Name: {self.name:<10} ID: {self.val:<12} Fullname: {self!s:<14} Latex: {self._repr_latex_()}
    Mass  = {self.mass!s:<10} {mass} GeV
    Width = {self.width!s:<10} {width} GeV
    I (isospin)       = {self.I!s:<6} G (parity)        = {Par_undo[self.G]:<5}  Q (charge)       = {Par_undo[self.charge]}
    J (total angular) = {self.J!s:<6} C (charge parity) = {Par_undo[self.C]:<5}  P (space parity) = {Par_undo[self.P]}
""".format(self=self, Par_undo=Par_undo, mass=mkul(self.mass_upper, self.mass_lower), width=mkul(self.width_upper, self.width_lower))

        if self.spintype != SpinType.Unknown:
            val += "    SpinType: {self.spintype!s}\n".format(self=self)
        if self.quarks:
            val += "    Quarks: {self.quarks}\n".format(self=self)
        val += "    Antiparticle status: {self.A.name}\n".format(self=self)
        val += "    Radius: {self.radius} GeV".format(self=self)
        return val

    @property
    def programatic_name(self):
        'This name could be used for a variable name'
        name = self.name
        name += '_' + Par_prog[self.charge]
        return programatic_name(name)

    @property
    def html_name(self):
        'This is the name using HTML instead of LaTeX'
        name = self.latex
        name = re.sub(r'\^\{(.*?)\}', r'<SUP>\1</SUP>', name)
        name = re.sub(r'\_\{(.*?)\}', r'<SUB>\1</SUB>', name)
        name = re.sub(r'\\mathrm\{(.*?)\}', r'\1', name)
        name = re.sub(r'\\left\[(.*?)\\right\]', r'[\1] ', name)
        name = name.replace(r'\pi', 'π').replace(r'\rho', 'ρ').replace(r'\omega', 'ω')
        if self.bar:
            name += '~'
        return name

    @classmethod
    def empty(cls):
        'Get a new empty particle'
        return cls(0, 'Unknown', 0., 0., 0, Inv.Same)

    @classmethod
    def from_pdg(cls, val):
        'Get a particle from a PDG number'
        if val == 0:
            return cls.empty()
        else:
            col = cls.pdg_table().loc[val]
            J = Fraction(col.J) if col.J not in {'2or4', '?'} else col.J
            I = Fraction(col.I) if col.I not in {'', '<2', '?'} else col.I  # noqa: 741
            name = col.Name
            if abs(val) == 313:
                name += '(892)'
            return cls(val, name, col.Mass/1000, col.Width/1000, Par(col.Charge), Inv(col.A),
                       col.Rank,
                       I, J,
                       Par(col.G), Par(col.P), Par(col.C),
                       col.Quarks, Status(col.Status),
                       latex=col.Latex,
                       mass_upper=col.MassUpper/1000,
                       mass_lower=col.MassLower/1000,
                       width_upper=col.WidthUpper/1000,
                       width_lower=col.WidthLower/1000,)

    @classmethod
    def from_search_list(cls, name=None, latex=None, name_re=None, latex_re=None, particle=None, **search_terms):
        'Search for a particle, returning a list of candidates'

        for term in list(search_terms):
            if search_terms[term] is None:
                del search_terms[term]

        # If J or I is passed, make sure it is a string
        if not isinstance(search_terms.get('J', ''), str):
            search_terms['J'] = str(search_terms['J'])
        if not isinstance(search_terms.get('J', ''), str):
            search_terms['I'] = str(search_terms['I'])

        bools = [cls.pdg_table()[term] == match for term, match in search_terms.items()]

        if name is not None:
            bools.append(cls.pdg_table().Name.str.contains(str(name), regex=False))
        if name_re is not None:
            bools.append(cls.pdg_table().Name.str.contains(name_re, regex=True))
        if latex is not None:
            bools.append(cls.pdg_table().Latex.str.contains(str(latex), regex=False))
        if latex_re is not None:
            bools.append(cls.pdg_table().Latex.str.contains(latex_re, regex=True))
        if particle is not None:
            bools.append(cls.pdg_table().index > 0 if particle else cls.pdg_table().index < 0)

        results = cls.pdg_table()[reduce(operator.and_, bools)]
        return [cls.from_pdg(r) for r in results.index]

    @classmethod
    def from_search(cls, name=None, latex=None, name_re=None, latex_re=None, **search_terms):
        'Require that your each returns one and only one result'
        results = cls.from_search_list(name, latex, name_re=name_re,
                                       latex_re=latex_re, **search_terms)
        if len(results) == 1:
            return results[0]
        elif len(results) == 0:
            raise RuntimeError('Did not find particle')
        else:
            raise RuntimeError("Found too many particles")

    @classmethod
    def from_AmpGen(cls, name):
        'Get a particle from an AmpGen style name'
        mat = getname.match(name)
        mat = mat.groupdict()

        Par_mapping = {'++': 2, '+': 1, '0': 0, '-': -1, '--': 2}
        particle = False if mat['bar'] is not None else (True if mat['charge'] == '0' else None)

        fullname = mat['name']
        if mat['state']:
            fullname += '({mat[state]})'.format(mat=mat)

        if mat['mass']:
            maxname = fullname + '({mat[mass]})'.format(mat=mat)
        else:
            maxname = fullname

        vals = cls.from_search_list(Name=maxname,
                                    Charge=Par_mapping[mat['charge']],
                                    particle=particle,
                                    J=mat['state'])
        if not vals:
            vals = cls.from_search_list(Name=fullname,
                                        Charge=Par_mapping[mat['charge']],
                                        particle=particle,
                                        J=mat['state'])

        if len(vals) > 1 and mat['mass'] is not None:
            vals = [val for val in vals if mat['mass'] in val.latex]

        if len(vals) > 1:
            vals = sorted(vals)

        return vals[0]
