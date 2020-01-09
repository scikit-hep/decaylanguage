# Copyright (c) 2018-2020, Eduardo Rodrigues and Henry Schreiner.
#
# Distributed under the 3-clause BSD license, see accompanying file LICENSE
# or https://github.com/scikit-hep/decaylanguage for details.

from __future__ import absolute_import

try:
    from functools import lru_cache
    cacher = lru_cache(maxsize=64)
except ImportError:
    from cachetools import cached, LFUCache
    cacher = cached(cache=LFUCache(maxsize=64))

from particle import Particle
from particle.converters import PDG2EvtGenNameMap


@cacher
def charge_conjugate_name(name, pdg_name=False):
    """
    Return the charge-conjugate particle name matching the given name.
    If no matching is found, return "ChargeConj(pname)".

    Parameters
    ----------
    name: str
        Input particle name.
    pdg_name: str, optional, default=False
        Input particle name is the PDG name,
        not the (default) EvtGen name.

    Returns
    -------
    out: str
    Either the EvtGen or PDG charge-conjugate particle name
    depending on the value of parameter `pdg_name`.
    """
    if pdg_name:
        name = PDG2EvtGenNameMap[name]

    try:
        ccname = Particle.from_evtgen_name(name).invert().name  # Returns a PDG name ;-)
        if pdg_name:
            return ccname
        return PDG2EvtGenNameMap[ccname]
    except:
        return 'ChargeConj({0})'.format(name)
