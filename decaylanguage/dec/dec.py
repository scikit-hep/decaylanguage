from __future__ import absolute_import, division, print_function

import os
import warnings
from lark import Lark, Transformer, Tree

from ..data import open_text
from .. import data
from ..decay.decay import Decay
from .enums import PhotosEnum


class DecFileNotParsed(RuntimeError):
    pass


class DecayNotFound(RuntimeError):
    pass


class DecFileParser(object):
    """
    The class to parse a .dec decay file.

    Example
    -------
    >>> parser = DecFileParser('my-decay-file.dec')
    >>> parser.parse()
    """
    def __init__(self, decay_file):
        """
        Parser constructor.

        Parameters
        ----------
        decay_file: str
            Input .dec decay file.
        """
        # Check input file
        if not os.path.exists(decay_file):
            raise FileNotFoundError("'{0}'!".format(decay_file))

        self._grammar = None       # Loaded Lark grammar definition file
        self._grammar_info = None  # Name of Lark grammar definition file

        self._decay_file = decay_file  # Name of the input decay file
        self._parsed_dec_file = None   # Parsed decay file

        self._parsed_decays = None  # Particle decays found in the decay file

    def parse(self):
        """
        Parse the given .dec decay file according to the default Lark options.

        See method 'load_grammar' for how to explicitly set the Lark parser
        and the parsing options.
        """
        # Has a fine been parsed already?
        if self._parsed_decays is not None:
            warnings.warn("Input file being re-parsed ...")

        decay_file = open(self._decay_file).read()
        parser = Lark(self.grammar, parser='lalr', lexer='standard')

        self._parsed_dec_file = parser.parse(decay_file)

        self._find_parsed_decays()

    @property
    def grammar(self):
        """
        This accesses the internal Lark grammar definition file,
        loading it from the default location if needed.

        Returns
        -------
        out: str
            The Lark grammar definition file.
        """
        if not self.grammar_loaded:
            self.load_grammar()

        return self._grammar

    def load_grammar(self, filename=None, parser='lalr', lexer='standard', **options):
        """
        Load a Lark grammar definition file.

        Parameters
        ----------
        filename: str, optional, default=None
            Input .dec decay file name. By default 'data/decfile.lark' is loaded.
        parser: str, optional, default='lalr'
            The Lark parser engine name.
        lexer: str, optional, default='standard'
            The Lark parser lexer mode to use.
        options: keyword arguments, optional
            Extra options to pass on to the parsing algorithm.
        See Lark's Lark class for a description of available options
        for parser, lexer and options.
        """
        if filename is None:
            filename = 'decfile.lark'
            with data.open_text(data, filename) as f:
                self._grammar = f.read()
        else:
            self._grammar = open(filename).read()

        self._grammar_info = dict(lark_file=filename, parser=parser, lexer=lexer, **options)

    @property
    def grammar_loaded(self):
        """Check to see if the Lark grammar definition file is loaded."""
        return self._grammar is not None

    def _find_parsed_decays(self):
        """Find all Tree instances of Tree.data='decay'."""
        if self._parsed_dec_file is not None:
            self._parsed_decays = tuple(self._parsed_dec_file.find_data('decay'))

        # Check for duplicates - should be considered a bug in the .dec file!
        self._check_parsed_decays()

        return self._parsed_decays

    def _check_parsing(self):
        """Has the .parse() method been called already?"""
        if self._parsed_dec_file is None:
            raise DecFileNotParsed("Hint: call 'parse()'!")

    def _check_parsed_decays(self):
        lmn = self.list_decay_mother_names()
        if self.number_of_decays != len(set(lmn)):
            warnings.warn("Input .dec file redefines decays for particle(s) {0}!".format(set([n for n in lmn if lmn.count(n)>1])))

    @property
    def number_of_decays(self):
        """Return the number of particle decays defined in the parsed .dec file."""
        self._check_parsing()

        return len(self._parsed_decays)

    def list_decay_mother_names(self):
        self._check_parsing()

        return [get_decay_mother_name(d) for d in self._parsed_decays]

    def _find_decay_modes(self, mother):
        self._check_parsing()

        for decay_Tree in self._parsed_decays:
            if get_decay_mother_name(decay_Tree) == mother:
                return tuple(decay_Tree.find_data('decayline'))

        raise DecayNotFound("Decays of particle '%s' not found in .dec file!" % mother)

    def list_decay_modes(self, mother):
        """
        Return a list of decay modes for the given mother particle.

        Example
        -------
        >>> parser = DecFileParser('my-decay-file.dec')
        >>> parser.parse()
        >>> parser.list_decay_mother_names()  # Inspect what decays are defined
        >>> parser.list_decay_modes('pi0')
        """
        return [get_final_state_particle_names(mode)
                for mode in self._find_decay_modes(mother)]

    def _decay_mode_details(self, decay_mode):
        """
        Parse a decay mode (Tree instance)
        and return the relevant bits of information in it.
        """

        bf = get_branching_fraction(decay_mode)
        fsp_names = get_final_state_particle_names(decay_mode)
        model = get_model_name(decay_mode)
        model_params = get_model_parameters(decay_mode)

        return (bf, fsp_names, model, model_params)

    def print_decay_modes(self, mother):
        """Pretty print (debugging) of the decay modes of a given particle."""
        dms = self._find_decay_modes(mother)

        for dm in dms:
            dm_details = self._decay_mode_details(dm)
            print('%12g : %50s %15s %s' % (dm_details[0], '  '.\
                join(p for p in dm_details[1]), dm_details[2], dm_details[3]))

    def build_decay_chain(self, mother, stable_particles=[]):
        """
        Iteratively build the whole decay chain of a given mother particle,
        optionally considering certain particles as stable.

        Parameters
        ----------
        mother: str
            Input mother particle name.
        stable_particles: iterable, optional, default=[]
            If provided, stops the decay-chain parsing, taking the "list" as particles to be considered stable.

        Returns
        -------
        out: dict
            Decay chain as a dictionary of the form
            {mother: [{'bf': float, 'fs': list, 'm': str, 'mp': str}]}
            where
            'bf' stands for the deca mode branching fraction,
            'fs' is a list of final-state particle names (strings)
            and/or dictionaries of the same form as the decay chain above,
            'm' is the model name, if found, else '',
            'mp' are the model parameters, if specified, else ''

        Examples
        --------
        >>> parser = DecFileParser('a-Dplus-decay-file.dec')
        >>> parser.parse()
        >>> parser.build_decay_chain('D+')
        {'D+': [{'bf': 1.0,
           'fs': ['K-',
            'pi+',
            'pi+',
            {'pi0': [{'bf': 0.988228297,
               'fs': ['gamma', 'gamma'],
               'm': 'PHSP',
               'mp': ''},
              {'bf': 0.011738247,
               'fs': ['e+', 'e-', 'gamma'],
               'm': 'PI0_DALITZ',
               'mp': ''},
              {'bf': 3.3392e-05,
              'fs': ['e+', 'e+', 'e-', 'e-'],
              'm': 'PHSP',
              'mp': ''},
              {'bf': 6.5e-08, 'fs': ['e+', 'e-'], 'm': 'PHSP', 'mp': ''}]}],
           'm': 'PHSP',
           'mp': ''}]}
        >>> p.build_decay_chain('D+', stable_particles=['pi0'])
        {'D+': [{'bf': 1.0, 'fs': ['K-', 'pi+', 'pi+', 'pi0'], 'm': 'PHSP', 'mp': ''}]}
        """
        keys = ('bf', 'fs', 'm', 'mp')

        info = list()
        for dm in (self._find_decay_modes(mother)):
            list_dm_details = self._decay_mode_details(dm)
            d = dict(zip(keys,list_dm_details))

            for i, fs in enumerate(d['fs']):
                if fs in stable_particles:
                    continue

                try:
                    # This throws a DecayNotFound exception
                    # if fs does not have decays defined in the parsed file
                    _n_dms = len(self._find_decay_modes(fs))

                    _info = self.build_decay_chain(fs, stable_particles)
                    d['fs'][i] = _info
                except DecayNotFound:
                    pass

            info.append(d)

        info = {mother:info}
        return info

    def __repr__(self):
        if self._parsed_dec_file is not None:
            return "<{self.__class__.__name__}: decfile='{decfile}', n_decays={n_decays}>".format(
                self=self, decfile=self._decay_file, n_decays=self.number_of_decays)
        else:
            return "<{self.__class__.__name__}: decfile='{decfile}'>"\
                    .format(self=self, decfile=self._decay_file)

    def __str__(self):
        return repr(self)


def get_decay_mother_name(decay_tree):
    if not isinstance(decay_tree, Tree) or decay_tree.data != 'decay':
        raise RuntimeError("Input not an instance of a 'decay' Tree!")

    # For a 'decay' Tree, tree.children[0] is the mother particle Tree
    # and tree.children[0].children[0].value is the mother particle name
    return decay_tree.children[0].children[0].value


def get_branching_fraction(decay_mode):
    if not isinstance(decay_mode, Tree) or decay_mode.data != 'decayline':
        raise RuntimeError("Check your input, not an instance of a 'decayline' Tree!")

    # For a 'decayline' Tree, Tree.children[0] is the branching fraction Tree
    # and tree.children[0].children[0].value is the BF stored as a str
    try:  # the branching fraction value as a float
        return float(decay_mode.children[0].children[0].value)
    except RuntimeError:
        raise RuntimeError("'decayline' Tree does not seem to have the usual structure. Check it.")


def get_final_state_particles(decay_mode):
    if not isinstance(decay_mode, Tree) or decay_mode.data != 'decayline':
        raise RuntimeError("Input not an instance of a 'decayline' Tree!")

    # list of Trees of final-state particles
    return list(decay_mode.find_data('particle'))


def get_final_state_particle_names(decay_mode):
    if not isinstance(decay_mode, Tree) or decay_mode.data != 'decayline':
        raise RuntimeError("Input not an instance of a 'decayline' Tree!")

    fsps = get_final_state_particles(decay_mode)
    # list of final-state particle names
    return [fsp.children[0].value for fsp in fsps]


def get_model_name(decay_mode):
    if not isinstance(decay_mode, Tree) or decay_mode.data != 'decayline':
        raise RuntimeError("Input not an instance of a 'decayline' Tree!")

    lm = list(decay_mode.find_data('model'))
    return lm[0].children[0].value


def get_model_parameters(decay_mode):
    if not isinstance(decay_mode, Tree) or decay_mode.data != 'decayline':
        raise RuntimeError("Input not an instance of a 'decayline' Tree!")

    lmo = list(decay_mode.find_data('model_options'))
    return [float(tree.children[0].value) for tree in lmo[0].children] if len(lmo) == 1 else ''


def get_definitions(parsed_file):
    """
    Return a dictionary of all definitions in the input parsed file, of the form
    "Define <NAME> <VALUE>" as {'NAME1': VALUE1, 'NAME2': VALUE2, ...}.

    Parameters
    ----------
    parsed_file: Lark Tree instance
        Input parsed file.
    """
    if not isinstance(parsed_file, Tree) :
        raise RuntimeError("Input not an instance of a Tree!")

    try:
        return {tree.children[0].children[0].value:float(tree.children[1].children[0].value)
            for tree in parsed_file.find_data('define')}
    except:
        warnings.error("Input parsed file does not seem to have the expected structure.")


def get_aliases(parsed_file):
    """
    Return a dictionary of all aliases in the input parsed file, of the form
    "Alias <NAME> <ALIAS>" as {'NAME1': ALIAS1, 'NAME2': ALIAS2, ...}.

    Parameters
    ----------
    parsed_file: Lark Tree instance
        Input parsed file.
    """
    if not isinstance(parsed_file, Tree) :
        raise RuntimeError("Input not an instance of a Tree!")

    try:
        return {tree.children[0].children[0].value:tree.children[1].children[0].value
            for tree in parsed_file.find_data('alias')}
    except:
        warnings.error("Input parsed file does not seem to have the expected structure.")


def get_charge_conjugate_defs(parsed_file):
    """
    Return a dictionary of all aliases in the input parsed file, of the form
    "ChargeConj <PARTICLE> <CC_PARTICLE>" as
    {'PARTICLE1': CC_PARTICLE1, 'PARTICLE2': CC_PARTICLE2, ...}.

    Parameters
    ----------
    parsed_file: Lark Tree instance
        Input parsed file.
    """
    if not isinstance(parsed_file, Tree) :
        raise RuntimeError("Input not an instance of a Tree!")

    try:
        return {tree.children[0].children[0].value:tree.children[1].children[0].value
            for tree in parsed_file.find_data('chargeconj')}
    except:
        warnings.error("Input parsed file does not seem to have the expected structure.")


class TreeToDec(Transformer):
    def yes(self, items):
        return True
    def no(self, items):
        return False
    def global_photos(self, items):
        item, = items
        return PhotosEnum.yes if item else PhotosEnum.no
    def value(self, items):
        item, = items
        return float(item)
    def label(self, items):
        item, = items
        return str(item)
    def photos(self, items):
        return PhotosEnum.yes


def define(transformed):
    return {x.children[0]:x.children[1] for x in transformed.find_data('define')}
def pythia_def(transformed):
    return [x.children for x in transformed.find_data('pythia_def')]
def alias(transformed):
    return {x.children[0]:x.children[1] for x in transformed.find_data('alias')}

def chargeconj(transformed):
    return {x.children[0]:x.children[1] for x in transformed.find_data('chargeconj')}

# Commands
def global_photos(transformed):
    return {x.children[0]:x.children[1] for x in transformed.find_data('global_photos')}

def decay(transformed):
    return Tree('decay', list(transformed.find_data('decay')))
def cdecay(transformed):
    return [x.children[0] for x in transformed.find_data('cdecay')]
def setlspw(transformed):
    return list(transformed.find_data('setlspw'))
