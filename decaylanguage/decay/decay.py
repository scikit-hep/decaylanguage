
class DaughtersDict(object):
    """
    Class holding a decay final state as a dictionary.
    It is a building block for the digital representation of full decay chains.

    Example
    -------
    A final state such as 'K+ K- K- pi+ pi0' is stored as
    ``{'K+': 1, 'K-': 2, 'pi+': 1, 'pi0': 1}``.
    """

    __slots__ = ('_daughters')

    def __init__(self, daughters={}):
        """
        Default constructor.

        Parameters
        ----------
        daughters: dict
            Final state particles represented as a dictionary,
            e.g. ``{'K+': 1, 'K-': 2, 'pi+': 1, 'pi0': 1}``.
        """
        if not isinstance(daughters, dict):
            raise RuntimeError('invalid input - dict expected!')

        self._daughters = daughters

    @classmethod
    def from_list(cls, daughters):
        """
        Constructor from a list of particle names.
        """
        return cls({k:daughters.count(k) for k in set(daughters)})

    def to_string(self):
        """
        Return the daughters as a string representation ordered list of names.
        """
        strs = []
        for d in sorted(self._daughters):
            strs += [d]*self._daughters[d]
        return ' '.join(strs)

    def __repr__(self):
        return "<{self.__class__.__name__}: {daughters}>".format(
                self=self, daughters=self._daughters)

    def __str__(self):
        return repr(self)

    def __len__(self):
        """
        Return the length, i.e. the number of final-state particles.

        Note
        ----
        This is general *not* the number of dictionary elements.
        """
        return sum(v for v in self._daughters.values())

    def __iadd__(self, other):
        """
        Self-addition with another `DaughterDict` instance, i.e. self += other.
        """
        if not isinstance(other, DaughterDict):
            raise InvalidOperationError("invalid operation '+=' between a 'DaughterDict' and a '{0}'".format(other.__class__.__name__))

        self._daughters = {key: self._daughters.get(key, 0) + other._daughters.get(key, 0)
                           for key in set(self._daughters) | set(other._daughters)}
        return self

    def __add__(self, other):
        """
        Addition with another `DaughterDict` instance.
        """
        if not isinstance(other, DaughterDict):
            raise InvalidOperationError("invalid operation '+=' between a 'DaughterDict' and a '{0}'".format(other.__class__.__name__))

        result = DaughterDict()
        result._daughters = {key: self._daughters.get(key, 0) + other._daughters.get(key, 0)
                           for key in set(self._daughters) | set(other._daughters)}
        return result
