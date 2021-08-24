# -*- coding: utf-8 -*-
# Copyright (c) 2018-2021, Eduardo Rodrigues and Henry Schreiner.
#
# Distributed under the 3-clause BSD license, see accompanying file LICENSE
# or https://github.com/scikit-hep/decaylanguage for details.

from __future__ import absolute_import

import sys

from particle import Particle
from particle.converters import (
    EvtGen2PDGNameMap,
    EvtGenName2PDGIDBiMap,
    PDG2EvtGenNameMap,
)
from particle.exceptions import MatchingIDNotFound

if sys.version_info < (3,):
    from cachetools import LFUCache, cached

    cacher = cached(cache=LFUCache(maxsize=64))
else:
    from functools import lru_cache

    cacher = lru_cache(maxsize=64)


@cacher
def charge_conjugate_name(name, pdg_name=False):
    """
    Return the charge-conjugate particle name matching the given name.
    If no matching is found, return "ChargeConj(pname)".

    Note
    ----
    Search/match in order:
    1) Trivial case - does the name correspond to a self-conjugate particle?
       Only works for particles in the DB.
    2) Try to match the antiparticle looking for the opposite PDG ID
       in the list of PDG IDs - EvtGen names.
       This can deal with specific particles or badly-known particles
       not in the DB but not so rare in decay files.

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
        try:
            ccname = charge_conjugate_name(PDG2EvtGenNameMap[name])
            # Convert the EvtGen name back to a PDG name, to match input type
            return EvtGen2PDGNameMap[ccname]
        except MatchingIDNotFound:  # Catch issue in PDG2EvtGenNameMap matching
            return "ChargeConj({})".format(name)

    # Dealing only with EvtGen names at this stage
    try:
        return Particle.from_evtgen_name(name).invert().evtgen_name
    except Exception:
        try:
            return EvtGenName2PDGIDBiMap[-EvtGenName2PDGIDBiMap[name]]
        except Exception:
            return "ChargeConj({})".format(name)
