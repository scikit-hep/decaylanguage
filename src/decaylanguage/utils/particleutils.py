# Copyright (c) 2018-2023, Eduardo Rodrigues and Henry Schreiner.
#
# Distributed under the 3-clause BSD license, see accompanying file LICENSE
# or https://github.com/scikit-hep/decaylanguage for details.


from __future__ import annotations

import re
from functools import lru_cache
from typing import Any

from particle import Particle, ParticleNotFound
from particle.converters import (
    EvtGen2PDGNameMap,
    EvtGenName2PDGIDBiMap,
    PDG2EvtGenNameMap,
)
from particle.exceptions import MatchingIDNotFound
from particle.particle.enums import Charge_mapping

cacher = lru_cache(maxsize=64)


@cacher
def charge_conjugate_name(name: str, pdg_name: bool = False) -> str:
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
            return f"ChargeConj({name})"

    # Dealing only with EvtGen names at this stage
    try:
        return Particle.from_evtgen_name(name).invert().evtgen_name
    except Exception:
        try:
            return EvtGenName2PDGIDBiMap[-EvtGenName2PDGIDBiMap[name]]
        except Exception:
            return f"ChargeConj({name})"


def particle_from_string_name(name: str) -> Particle:
    """
    Get a particle from an AmpGen style name.

    Note: the best match is returned.
    """
    matches = particle_list_from_string_name(name)
    if matches:
        return matches[0]
    raise ParticleNotFound(
        f"Particle with AmpGen style name {name!r} not found in particle table"
    )


def particle_list_from_string_name(name: str) -> list[Particle]:
    "Get a list of particles from an AmpGen style name."

    # Forcible override
    particle = None

    short_name = name
    if "~" in name:
        short_name = name.replace("~", "")
        particle = False

    # Try the simplest searches first
    list_can = Particle.findall(name=name, particle=particle)
    if list_can:
        return list_can
    list_can = Particle.findall(pdg_name=short_name, particle=particle)
    if list_can:
        return list_can

    mat_str = _getname.match(short_name)

    if mat_str is None:
        return []

    mat = mat_str.groupdict()

    if particle is False:
        mat["bar"] = "bar"

    try:
        return _from_group_dict_list(mat)
    except ParticleNotFound:
        return []


def _from_group_dict_list(mat: dict[str, Any]) -> list[Particle]:
    """
    Internal helper class for the functions `from_string` and `from_string_list`
    for fuzzy finding of particle names used by AmpGen.
    """
    kw: dict[str, Any] = {
        "particle": False
        if mat["bar"] is not None
        else True
        if mat["charge"] == "0"
        else None
    }

    name = mat["name"]

    if mat["family"]:
        if "_" in mat["family"]:
            mat["family"] = mat["family"].strip("_")
        name += f'({mat["family"]})'
    if mat["state"]:
        name += f'({mat["state"]})'

    if "prime" in mat and mat["prime"]:
        name += "'"

    if mat["star"]:
        name += "*"

    if mat["state"] is not None:
        kw["J"] = float(mat["state"])

    maxname = name + f'({mat["mass"]})' if mat["mass"] else name
    if "charge" in mat and mat["charge"] is not None:
        kw["three_charge"] = Charge_mapping[mat["charge"]]

    vals = Particle.findall(name=lambda x: maxname in x, **kw)
    if not vals:
        vals = Particle.findall(name=lambda x: name in x, **kw)

    if not vals:
        raise ParticleNotFound(f"Could not find particle {maxname} or {name}")

    if len(vals) > 1 and mat["mass"] is not None:
        vals = [val for val in vals if mat["mass"] in val.latex_name]

    if len(vals) > 1:
        return sorted(vals)

    return vals


_getname = re.compile(
    r"""
^                                           # Beginning of string
      (?P<name>       \w+?        )         # One or more characters, non-greedy
(?:\( (?P<family>    [udsctb][\w]*) \) )?   # Optional family like (s)
(?:\( (?P<state>      \d+         ) \)      # Optional state in ()
      (?=             \*? \(      )  )?     #   - lookahead for mass
      (?P<star>       \*          )?        # Optional star
(?:\( (?P<mass>       \d+         ) \) )?   # Optional mass in ()
      (?P<bar>        (bar|~)     )?        # Optional bar
      (?P<charge>     [0\+\-][+-]?)         # Required 0, -, --, or +, ++
$                                           # End of string
""",
    re.VERBOSE,
)
