# -*- coding: utf-8 -*-
# Copyright (c) 2018-2021, Eduardo Rodrigues and Henry Schreiner.
#
# Distributed under the 3-clause BSD license, see accompanying file LICENSE
# or https://github.com/scikit-hep/decaylanguage for details.

from __future__ import absolute_import, print_function

from collections import Counter
from copy import deepcopy

from ..utils import charge_conjugate_name


class DaughtersDict(Counter):
    """
    Class holding a decay final state as a dictionary.
    It is a building block for the digital representation of full decay chains.

    Note
    ----
    This class assumes EvtGen particle names, though this assumption is only relevant
    for the `charge_conjugate` method.
    Otherwise, all other class methods smoothly deal with
    any kind of particle names (basically an iterable of strings).

    Example
    -------
    A final state such as 'K+ K- K- pi+ pi0' is stored as
    ``{'K+': 1, 'K-': 2, 'pi+': 1, 'pi0': 1}``.
    """

    def __init__(self, iterable=None, **kwds):
        """
        Default constructor.

        Note
        ----
        This class assumes EvtGen particle names, though this assumption is only relevant
        for the `charge_conjugate` method (refer to its documentation).
        Otherwise, all other class methods smoothly deal with
        any kind of particle names (basically an iterable of strings).

        Examples
        --------
        >>> # An empty final state
        >>> dd = DaughtersDict()

        >>> # Constructor from a dictionary
        >>> dd = DaughtersDict({'K+': 1, 'K-': 2, 'pi+': 1, 'pi0': 3})

        >>> # Constructor from a list of particle names
        >>> dd = DaughtersDict(['K+', 'K-', 'K-', 'pi+', 'pi0'])

        >>> # Constructor from a string representing the final state
        >>> dd = DaughtersDict('K+ K- pi0')
        """
        if isinstance(iterable, dict):
            iterable = {k: v for k, v in iterable.items() if v > 0}
        elif iterable and isinstance(iterable, str):
            iterable = iterable.split()
        super(DaughtersDict, self).__init__(iterable, **kwds)

    def to_string(self):
        """
        Return the daughters as a string representation (ordered list of names).
        """
        return " ".join(sorted(self.elements()))

    def to_list(self):
        """
        Return the daughters as an ordered list of names.
        """
        return sorted(list(self.elements()))

    def charge_conjugate(self, pdg_name=False):
        """
        Return the charge-conjugate final state.

        Parameters
        ----------
        pdg_name: str, optional, default=False
            Input particle name is the PDG name,
            not the (default) EvtGen name.

        Examples
        --------
        >>> dd = DaughtersDict({'K+': 2, 'pi0': 1})
        >>> dd.charge_conjugate()
        <DaughtersDict: ['K-', 'K-', 'pi0']>
        >>>
        >>> dd = DaughtersDict({'K_S0': 1, 'pi0': 1})
        >>> dd.charge_conjugate()
        <DaughtersDict: ['K_S0', 'pi0']>
        >>>
        >>> dd = DaughtersDict({'K(S)0': 1, 'pi0': 1})  # PDG names!
        >>> dd.charge_conjugate(pdg_name=True)
        <DaughtersDict: ['K(S)0', 'pi0']>
        """
        return self.__class__(
            {charge_conjugate_name(p, pdg_name): n for p, n in self.items()}
        )

    def __repr__(self):
        return "<{self.__class__.__name__}: {daughters}>".format(
            self=self, daughters=self.to_list()
        )

    def __str__(self):
        return repr(self)

    def __len__(self):
        """
        Return the length, i.e. the number of final-state particles.

        Note
        ----
        This is generally *not* the number of dictionary elements.
        """
        return sum(self.values())

    def __add__(self, other):
        """
        Add two final states, particle-type-wise.
        """
        dd = super(DaughtersDict, self).__add__(other)
        return self.__class__(dd)

    def __iter__(self):
        return self.elements()


class DecayMode(object):
    """
    Class holding a particle decay mode, which is typically a branching fraction
    and a list of final-state particles (i.e. a list of DaughtersDict instances).
    The class can also contain metadata such as decay model and optional
    decay-model parameters, as defined for example in .dec decay files.

    This class is a building block for the digital representation
    of full decay chains.

    Note
    ----
    This class assumes EvtGen particle names, though this assumption is only
    relevant for the `charge_conjugate` method.
    Otherwise, all other class methods smoothly deal
    with any kind of particle names (basically an iterable of strings).
    """

    __slots__ = ("bf", "daughters", "metadata")

    def __init__(self, bf=0, daughters=None, **info):
        """
        Default constructor.

        Parameters
        ----------
        bf: float, optional, default=0
            Decay mode branching fraction.
        daughters: iterable or DaughtersDict, optional, default=None
            The final-state particles.
        info: keyword arguments, optional
            Decay mode model information and/or user metadata (aka extra info)
            By default the following elements are always created:
            dict(model=None, model_params=None).
            The user can provide any metadata, see the examples below.

        Note
        ----
        This class assumes EvtGen particle names, though this assumption is only
        relevant for the `charge_conjugate` method.
        Otherwise, all other class methods smoothly deal
        with any kind of particle names (basically an iterable of strings).

        Examples
        --------
        >>> # A 'default' and hence empty, decay mode
        >>> dm = DecayMode()

        >>> # Decay mode with minimal input information
        >>> dd = DaughtersDict('K+ K-')
        >>> dm = DecayMode(0.5, dd)

        >>> # Decay mode with minimal input information, simpler version
        >>> dm = DecayMode(0.5, 'K+ K-')

        >>> # Decay mode with decay model information
        >>> dd = DaughtersDict('pi- pi0 nu_tau')
        >>> dm = DecayMode(0.2551, dd,
                           model='TAUHADNU',
                           model_params=[-0.108, 0.775, 0.149, 1.364, 0.400])

        >>> # Decay mode with user metadata
        >>> dd = DaughtersDict('K+ K-')
        >>> dm = DecayMode(0.5, dd, model='PHSP', study='toy', year=2019)
        """
        self.bf = bf
        self.daughters = DaughtersDict(daughters)

        self.metadata = dict(model="", model_params="")
        self.metadata.update(**info)

    @classmethod
    def from_dict(cls, decay_mode_dict):
        """
        Constructor from a dictionary of the form
        {'bf': <float>, 'fs': [...], ...}.
        These two keys are mandatory. All others are interpreted as
        model information or metadata, see the constructor signature and doc.

        Note
        ----
        This class assumes EvtGen particle names, though this assumption is only
        relevant for the `charge_conjugate` method.
        Otherwise, all other class methods smoothly deal
        with any kind of particle names (basically an iterable of strings).

        Examples
        --------
        >>> DecayMode.from_dict({'bf': 0.98823,
                                 'fs': ['gamma', 'gamma'],
                                 'model': 'PHSP',
                                 'model_params': ''})
        <DecayMode: daughters=gamma gamma, BF=0.98823>
        """
        dm = deepcopy(decay_mode_dict)

        try:
            bf = dm.pop("bf")
            daughters = dm.pop("fs")
        except Exception:
            raise RuntimeError("Input not in the expected format!")

        return cls(bf=bf, daughters=daughters, **dm)

    @classmethod
    def from_pdgids(cls, bf=0, daughters=None, **info):
        """
        Constructor for a final state given as a list of particle PDG IDs.

        Parameters
        ----------
        bf: float, optional, default=0
            Decay mode branching fraction.
        daughters: iterable, optional, default=None
            The final-state particle PDG IDs.
        info: keyword arguments, optional
            Decay mode model information and/or user metadata (aka extra info)
            By default the following elements are always created:
            dict(model=None, model_params=None).
            The user can provide any metadata, see the examples below.

        Note
        ----
        All particle names are internally saved as EvtGen names,
        to be consistent with the default class assumption, see class docstring.

        Examples
        --------
        >>> DecayMode.from_pdgids(0.5, [321, -321])
        <DecayMode: daughters=K+ K-, BF=0.5>
        >>>
        >>> DecayMode.from_pdgids(0.5, (310, 310))
        <DecayMode: daughters=K_S0 K_S0, BF=0.5>
        """
        if not daughters:
            return cls(bf=bf, daughters=daughters, **info)

        try:
            from particle import PDGID, ParticleNotFound
            from particle.converters import EvtGenName2PDGIDBiMap

            daughters = [EvtGenName2PDGIDBiMap[PDGID(d)] for d in daughters]
        except ParticleNotFound:
            raise ParticleNotFound("Please check your input PDG IDs!")

        # Override the default settings with the user input, if any
        return cls(bf=bf, daughters=daughters, **info)

    def describe(self):
        """
        Make a nice high-density string for all decay-mode properties and info.
        """
        val = """Daughters: {daughters} , BF: {bf:<15.8g}
    Decay model: {model} {model_params}""".format(
            daughters=" ".join(self.daughters),
            bf=self.bf,
            model=self.metadata["model"],
            model_params=self.metadata["model_params"]
            if self.metadata["model_params"] is not None
            else "",
        )

        keys = [k for k in self.metadata if k not in ("model", "model_params")]
        if keys:
            val += "\n    Extra info:\n"
        for key in keys:
            val += "        {k}: {v}\n".format(k=key, v=self.metadata[key])

        return val

    def to_dict(self):
        """
        Return the decay mode as a dictionary in the format understood
        by the `DecayChainViewer` class.

        Examples
        --------
        >>> dm = DecayMode(0.5, 'K+ K- K- pi- pi0 nu_tau',
                           model='PHSP', study='toy', year=2019)
        >>> dm.to_dict()
        {'bf': 0.5,
         'fs': ['K+', 'K-', 'K-', 'nu_tau', 'pi-', 'pi0'],
         'model': 'PHSP',
         'model_params': '',
         'study': 'toy',
         'year': 2019}
        """
        d = {"bf": self.bf, "fs": self.daughters.to_list()}
        d.update(self.metadata)
        if d["model_params"] is None:
            d["model_params"] = ""
        return d

    def charge_conjugate(self, pdg_name=False):
        """
        Return the charge-conjugate decay mode.

        Parameters
        ----------
        pdg_name: str, optional, default=False
            Input particle name is the PDG name,
            not the (default) EvtGen name.

        Examples
        --------
        >>> dm = DecayMode(1.0, 'K+ K+ pi-')
        >>> dm.charge_conjugate()
        <DecayMode: daughters=K- K- pi+, BF=1.0>
        >>>
        >>> dm = DecayMode(1.0, 'K_S0 pi+')
        >>> dm.charge_conjugate()
        <DecayMode: daughters=K_S0 pi-, BF=1.0>
        >>>
        >>> dm = DecayMode(1.0, 'K(S)0 pi+')  # PDG names!
        >>> dm.charge_conjugate(pdg_name=True)
        <DecayMode: daughters=K(S)0 pi-, BF=1.0>
        """
        return self.__class__(
            self.bf, self.daughters.charge_conjugate(pdg_name), **self.metadata
        )

    def __len__(self):
        """
        The "length" of a decay mode is the number of final-state particles.
        """
        return len(self.daughters)

    def __repr__(self):
        return "<{self.__class__.__name__}: daughters={daughters}, BF={bf}>".format(
            self=self,
            daughters=self.daughters.to_string() if len(self.daughters) > 0 else "[]",
            bf=self.bf,
        )

    def __str__(self):
        return repr(self)


class DecayChain(object):
    """
    Class holding a particle decay chain, which is typically a top-level decay
    (mother particle, branching fraction and final-state particles)
    and a set of sub-decays for any non-stable particle in the top-level decay.
    The whole chain can be seen as a mother particle and a list of decay modes.

    This class is the main building block for the digital representation
    of full decay chains.

    Note
    ----
    This class does not assume any kind of particle names (EvtGen, PDG).
    It is nevertheless advised to default use EvtGen names for consistency
    with the defaults used in the related classes `DecayMode` and `DaughtersDict`,
    unless there is a good motivation not to.
    """

    __slots__ = ("mother", "decays")

    def __init__(self, mother, decays):
        """
        Default constructor.

        Parameters
        ----------
        mother: str
            Input mother particle of the top-level decay.
        decays: iterable
            The decay modes.

        Examples
        --------
        >>> dm1 = DecayMode(0.0124, 'K_S0 pi0', model='PHSP')
        >>> dm2 = DecayMode(0.692, 'pi+ pi-')
        >>> dm3 = DecayMode(0.98823, 'gamma gamma')
        >>> dc = DecayChain('D0', {'D0':dm1, 'K_S0':dm2, 'pi0':dm3})
        """
        self.mother = mother
        self.decays = decays

    @classmethod
    def from_dict(cls, decay_chain_dict):
        """
        Constructor from a decay chain represented as a dictionary.
        The format is the same as that returned by
        `DecFileParser.build_decay_chains(...)`.
        """
        try:
            assert len(decay_chain_dict.keys()) == 1
        except Exception:
            raise RuntimeError("Input not in the expected format!")

        def has_no_subdecay(ds):
            return all(isinstance(p, str) for p in ds)

        def build_decay_modes(dc_dict):
            mother = list(dc_dict.keys())[0]
            dms = dc_dict[mother]

            for dm in dms:
                if has_no_subdecay(dm["fs"]):
                    decay_modes[mother] = DecayMode.from_dict(dm)
                else:
                    d = deepcopy(dm)
                    for i in range(len(d["fs"])):
                        if isinstance(d["fs"][i], dict):
                            # Replace the element with the key and
                            # store the present decay mode ignoring sub-decays
                            d["fs"][i] = list(d["fs"][i].keys())[0]
                            # Recursively continue ...
                            build_decay_modes(dm["fs"][i])
                    # Create the decay mode now that none of its particles
                    # has a sub-decay
                    decay_modes[mother] = DecayMode.from_dict(d)

        decay_modes = dict()  # type: dict
        mother = list(decay_chain_dict.keys())[0]
        build_decay_modes(decay_chain_dict)

        return cls(mother, decay_modes)

    def top_level_decay(self):
        """
        Return the top-level decay as a `DecayMode` instance.
        """
        return self.decays[self.mother]

    @property
    def bf(self):
        """
        Branching fraction of the top-level decay.
        """
        return self.top_level_decay().bf

    @property
    def visible_bf(self):
        """
        Visible branching fraction of the whole decay chain.

        Note
        ----
        Calculation requires a flattening of the entire decay chain.
        """
        return self.flatten().bf

    @property
    def ndecays(self):
        """
        Return the number of decay modes including the top-level decay.
        """
        return len(self.decays)

    def print_as_tree(self):
        """
        Tree-structure like print of the entire decay chain.

        Examples
        --------
        >>> dm1 = DecayMode(0.028, 'K_S0 pi+ pi-')
        >>> dm2 = DecayMode(0.692, 'pi+ pi-')
        >>> dc = DecayChain('D0', {'D0':dm1, 'K_S0':dm2})
        >>> dc.print_as_tree()
        D0
        +--> K_S0
        |    +--> pi+
        |    +--> pi-
        +--> pi+
        +--> pi-

        >>> dm1 = DecayMode(0.0124, 'K_S0 pi0')
        >>> dm2 = DecayMode(0.692, 'pi+ pi-')
        >>> dm3 = DecayMode(0.98823, 'gamma gamma')
        >>> dc = DecayChain('D0', {'D0':dm1, 'K_S0':dm2, 'pi0':dm3})
        >>> dc.print_as_tree()
        D0
        +--> K_S0
        |    +--> pi+
        |    +--> pi-
        +--> pi0
             +--> gamma
             +--> gamma

        >>> dm1 = DecayMode(0.6770, 'D0 pi+')
        >>> dm2 = DecayMode(0.0124, 'K_S0 pi0')
        >>> dm3 = DecayMode(0.692, 'pi+ pi-')
        >>> dm4 = DecayMode(0.98823, 'gamma gamma')
        >>> dc = DecayChain('D*+', {'D*+':dm1, 'D0':dm2, 'K_S0':dm3, 'pi0':dm4})
        >>> dc.print_as_tree()
        D*+
        +--> D0
        |    +--> K_S0
        |    |    +--> pi+
        |    |    +--> pi-
        |    +--> pi0
        |         +--> gamma
        |         +--> gamma
        +--> pi+
        """
        indent = 4
        arrow = "+--> "
        bar = "|"

        # TODO: simplify logic and perform further checks
        def _print(decay_dict, depth=0, link=False, last=False):
            mother = list(decay_dict.keys())[0]
            prefix = bar if (link and depth > 1) else ""
            prefix = prefix + " " * indent * (depth - 1)
            for i_decay in decay_dict[mother]:
                print(prefix, arrow if depth > 0 else "", mother, sep="")
                fsps = i_decay["fs"]
                n = len(list(fsps))
                depth += 1
                for j, fsp in enumerate(fsps):
                    prefix = bar if (link and depth > 1) else ""
                    if last:
                        prefix = prefix + " " * indent * (depth - 1) + " "
                    else:
                        prefix = (prefix + " " * indent) * (depth - 1)
                    if isinstance(fsp, str):
                        print(prefix, arrow, fsp, sep="")
                    else:
                        _print(
                            fsp,
                            depth=depth,
                            link=(link or (j < n - 1)),
                            last=(j == n - 1),
                        )

        dc_dict = self.to_dict()
        _print(dc_dict)

    def to_dict(self):
        """
        Return the decay chain as a dictionary representation.
        The format is the same as `DecFileParser.build_decay_chains(...)`.

        Examples
        --------
        >>> dm1 = DecayMode(0.028, 'K_S0 pi+ pi-')
        >>> dm2 = DecayMode(0.692, 'pi+ pi-')
        >>> dc = DecayChain('D0', {'D0':dm1, 'K_S0':dm2})
        >>> dc.to_dict()
        {'D0': [{'bf': 0.028,
            'fs': [{'K_S0': [{'bf': 0.692,
                'fs': ['pi+', 'pi-'],
                'model': '',
                'model_params': ''}]},
             'pi+',
             'pi-'],
            'model': '',
            'model_params': ''}]}
        """

        def recursively_replace(mother):
            dm = self.decays[mother].to_dict()
            result = []
            list_fsp = dm["fs"]

            for pos, fsp in enumerate(list_fsp):
                if fsp in self.decays.keys():
                    list_fsp[pos] = recursively_replace(fsp)
            result.append(dm)
            return {mother: result}

        return recursively_replace(self.mother)

    def flatten(self, stable_particles=()):
        """
        Flatten the decay chain replacing all intermediate, decaying particles,
        with their final states.

        Parameters
        ----------
        stable_particles: iterable, optional, default=()
            If provided, ignores the sub-decays of the listed particles,
            considering them as stable.

        Note
        ----
        After flattening the only `DecayMode` metadata kept is that of the top-level decay,
        i.e. that of the mother particle (nothing else would make sense).

        Examples
        --------
        >>> dm1 = DecayMode(0.0124, 'K_S0 pi0', model='PHSP')
        >>> dm2 = DecayMode(0.692, 'pi+ pi-')
        >>> dm3 = DecayMode(0.98823, 'gamma gamma')
        >>> dc = DecayChain('D0', {'D0':dm1, 'K_S0':dm2, 'pi0':dm3})
        >>>
        >>> dc.flatten()
        <DecayChain: D0 -> gamma gamma pi+ pi- (0 sub-decays), BF=0.008479803984>
        >>> dc.flatten().to_dict()
        {'D0': [{'bf': 0.008479803984,
           'fs': ['gamma', 'gamma', 'pi+', 'pi-'],
           'model': 'PHSP',
           'model_params': ''}]}

        >>> dc.flatten(stable_particles=('K_S0', 'pi0')).decays
        {'D0': <DecayMode: daughters=K_S0 pi0, BF=0.0124>}
        """

        vis_bf = self.bf
        fs = DaughtersDict(self.decays[self.mother].daughters)

        if stable_particles:
            keys = [k for k in self.decays.keys() if k not in stable_particles]
        else:
            keys = [k for k in self.decays.keys()]
        keys.insert(0, keys.pop(keys.index(self.mother)))

        further_to_replace = True
        while further_to_replace:
            for k in keys:
                if k in fs:
                    n_k = fs[k]
                    vis_bf *= self.decays[k].bf ** n_k
                    for _ in range(n_k):
                        fs += self.decays[k].daughters  # type: ignore
                    fs[k] -= n_k
            further_to_replace = any(fs[_k] > 0 for _k in keys)

        return DecayChain(
            self.mother,
            {self.mother: DecayMode(vis_bf, fs, **self.top_level_decay().metadata)},
        )

    def __repr__(self):
        if self.mother is None:
            return "Decay mode: undefined"

        return "<{self.__class__.__name__}: {mother} -> {tldecay} ({n} sub-decays), BF={bf}>".format(
            self=self,
            mother=self.mother,
            tldecay=self.top_level_decay().daughters.to_string(),
            n=len(self.decays) - 1,
            bf=self.bf,
        )

    def __str__(self):
        return repr(self)
