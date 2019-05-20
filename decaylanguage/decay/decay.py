from collections import Counter


class DaughtersDict(Counter):
    """
    Class holding a decay final state as a dictionary.
    It is a building block for the digital representation of full decay chains.

    Example
    -------
    A final state such as 'K+ K- K- pi+ pi0' is stored as
    ``{'K+': 1, 'K-': 2, 'pi+': 1, 'pi0': 1}``.
    """

    __slots__ = ('_daughters')

    def __init__(self, iterable=None, **kwds):
        """
        Default constructor.

        Parameters
        ----------
        in: dict
            Final state particles represented as a dictionary,
            e.g. ``{'K+': 1, 'K-': 2, 'pi+': 1, 'pi0': 1}``.
        """
        super(DaughtersDict, self).__init__(iterable, **kwds)

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
        for d in sorted(self):
            strs += [d]*self[d]
        return ' '.join(list(self.elements()))

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
        This is general *not* the number of dictionary elements.
        """
        return sum(n for n in self.values())

    def __add__(self, other):
        dd = self.copy()
        dd += other
        return dd

    def __iter__(self):
        return self.elements()
