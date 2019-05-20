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
