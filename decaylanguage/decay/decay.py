from collections import Counter
from cachetools import cached, LFUCache

from particle import Particle, ParticleNotFound


@cached(cache=LFUCache(maxsize=64))
def charge_conjugate(pname):
    """
    Return the charge-conjugate particle name matching the given PDG name.
    If no matching is found, return "ChargeConj(pname)".
    """
    try:
        return Particle.find(name=pname).invert().name
    except ParticleNotFound:
        return 'ChargeConj({0})'.format(pname)


class DaughtersDict(Counter):
    """
    Class holding a decay final state as a dictionary.
    It is a building block for the digital representation of full decay chains.

    Example
    -------
    A final state such as 'K+ K- K- pi+ pi0' is stored as
    ``{'K+': 1, 'K-': 2, 'pi+': 1, 'pi0': 1}``.
    """

    def __init__(self, iterable=None, **kwds):
        """
        Default constructor.

        Examples
        --------
        >>> # An empty final state
        >>> dd = DaughtersDict()

        >>> # Constructor from a dictionary
        >>> dd = DaughtersDict({'K+': 1, 'K-': 2, 'pi+': 1, 'pi0': 1})

        >>> # Constructor from a list of particle names
        >>> dd = DaughtersDict(['K+', 'K-', 'K-', 'pi+', 'pi0'])

        >>> # Constructor from a string representing the final state
        >>> dd = DaughtersDict('K+ K- pi0')
        """
        if iterable and isinstance(iterable, str):
            iterable = iterable.split()
        super(DaughtersDict, self).__init__(iterable, **kwds)

    def to_string(self):
        """
        Return the daughters as a string representation (ordered list of names).
        """
        return ' '.join(sorted(self.elements()))

    def charge_conjugate(self):
        """
        Return the charge-conjugate final state.

        Note
        ----
        Charge conjugation mapping expects PDG particle names.

        Examples
        --------
        >>> dd = DaughtersDict({'K+': 2, 'pi0': 1})
        >>> dd.charge_conjugate()
        <DaughtersDict: ['K-', 'K-', 'pi0']>
        """
        return self.__class__({charge_conjugate(p):n for p, n in self.items()})

    def __repr__(self):
        return "<{self.__class__.__name__}: {daughters}>".format(
                self=self, daughters=sorted(list(self.elements())))

    def __str__(self):
        return repr(self)

    def __len__(self):
        """
        Return the length, i.e. the number of final-state particles.

        Note
        ----
        This is generally *not* the number of dictionary elements.
        """
        return sum(n for n in self.values())

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
    and a list of final-state particles.
    The class can also contain metadata such as decay model and optional
    decay-model parameters, as defined for example in .dec decay files.

    This class is a building block for the digital representation
    of full decay chains.
    """

    __slots__ = ("bf",
                 "daughters",
                 "metadata")

    def __init__(self, bf = 0, daughters = None, **info):
        """
        Default constructor.

        Parameters
        ----------
        bf: float, optional, default=0
            Decay mode branching fraction
        daughters: iterable or DaughtersDict, optional, default=None
            The final-state particles
        info: keyword arguments, optional
            Decay mode model information and/or user metadata (aka extra info)
            By default the following elements are always created:
            dict(model=None, model_params=None)
            The user can provide any metadata, see the examples below.

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

        self.metadata = dict(model=None, model_params=None)
        self.metadata.update(**info)

    @classmethod
    def from_pdgids(cls, bf, daughters, **info):
        """
        Constructor for a final state given as a list of particle PDG IDs.

        Examples
        --------
        >>> dm = DecayMode.from_pdgids(0.5, [321, -321])
        """
        # Check inputs
        try:
            from particle import Particle, ParticleNotFound
            daughters = [Particle.from_pdgid(d).name for d in daughters]
        except ParticleNotFound:
            raise ParticleNotFound('Please check your input PDG IDs!')
        daughters = DaughtersDict(daughters)

        # Override the default settings with the user input, if any
        return cls(bf=bf, daughters=daughters, **info)

    def describe(self):
        """
        Make a nice high-density string for all decay-mode properties and info.
        """
        val = """Daughters: {daughters} , BF: {bf:<15.8g}
    Decay model: {model} {model_params}""".format(daughters=' '.join(self.daughters),
           bf=self.bf,
           model=self.metadata['model'],
           model_params=self.metadata['model_params']
                        if self.metadata['model_params'] is not None else '')

        keys = [k for k in self.metadata
              if k not in ('model', 'model_params')]
        if len(keys) > 0:
            val += "\n    Extra info:\n"
        for key in keys:
            val += "        {k}: {v}\n".format(k=key, v=self.metadata[key])

        return val

    def charge_conjugate(self):
        """
        Return the charge-conjugate decay mode.

        Note
        ----
        Charge conjugation mapping expects PDG particle names.

        Examples
        --------
        >>> dm = DecayMode(1.0, 'K+ K+ pi-')
        >>> dm.charge_conjugate()
        <DecayMode: daughters=K- K- pi+, BF=1.0>
        """
        return self.__class__(self.bf,
                              self.daughters.charge_conjugate(),
                              **self.metadata)

    def __len__(self):
        """
        The "length" of a decay mode is the number of final-state particles.
        """
        return len(self.daughters)

    def __repr__(self):
        return "<{self.__class__.__name__}: daughters={daughters}, BF={bf}>".format(
                self=self,
                daughters=self.daughters.to_string() if len(self.daughters)>0 else '[]',
                bf=self.bf)

    def __str__(self):
        return repr(self)
