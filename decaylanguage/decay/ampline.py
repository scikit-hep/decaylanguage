'''
ampline.py

A collection of regular expressions that pick out information about line.

The regular expressions make named groups that you can access.
'''

from __future__ import absolute_import, division, print_function

import re


inverted = re.compile(r'''
^                                          # Beginning of string
      (?P<line>    [^=]+      )            # All chars until =
      =                                    # Must have an equals sign
\s*   (?P<factor>  [0-9\-\.]* )            # Optional
\s*   \*?                                  # Eat a * sign if needed
\s*   (?P<invline> [^=]+      )            # The inverted line
$                                          # End of string
''', re.VERBOSE)

dual = re.compile(r'''
^                                          # Beginning of string
      (?P<name>   [^\{^\[]+       )        # All chars until { or [
(?:\[                                      # Start of []
      (?P<spinfactor> \w                     # Optional 1 char spin factor
      (?=               \W )                 #  - Look ahead for non-word
       )? ;?                                 # Remove ; if exists
      (?P<lineshape>  [^\]]*      )?         # The rest of the lineshape
   \]                             )?         # Done with []
(?:\{ (?P<daughters>   .*         ) \} )?  # All daughters
\s+ (?P<fix_r>       [02]         )        # Real fix
\s+ (?P<A>           [0-9\.\-]+   )        # Real value
\s+ (?P<dA>          [0-9\.\-]+   )        # Real error
\s+ (?P<fix_i>       [02]         )        # Imag fix
\s+ (?P<theta>       [0-9\.\-]+   )        # Imag value
\s+ (?P<dtheta>      [0-9\.\-]+   )        # Imag error
$                                          # End of string
''', re.VERBOSE)

cartesian = re.compile(r'''
^                                          # Beginning of string
      (?P<name>   .+               )       # All chars of name
_   (?P<cart>        Re|Im         )       # Real or imaginary
\s+ (?P<fix>         [02]          )       # Value fix
\s+ (?P<amp>          [0-9\.\-]+   )       # Value
\s+ (?P<err>          [0-9\.\-]+   )       # Error
$                                          # End of string
''', re.VERBOSE)

partial = re.compile(r'''
^                                          # Beginning of string
      (?P<name>   [^\{^\[]+       )        # All chars until { or [
(?:\[                                      # Start of []
      (?P<spinfactor> \w                     # Optional 1 char spin factor
      (?=               \W )                 #  - Look ahead for non-word
       )? ;?                                 # Remove ; if exists
      (?P<lineshape>  [^\]]*      )?         # The rest of the lineshape
   \]                             )?         # Done with []
(?:\{ (?P<daughters>   .*         ) \} )?  # All daughters
$                                          # End of string
''', re.VERBOSE)

settings = re.compile(r'''
^                                          # Beginning of string
      (?P<name>                            # Choice list
      FastCoherentSum::UseCartesian
    | output
    | nEvents
    | EventType
      )
      \s+                                  # White space
      (?P<value>    .*? )                  # Everything else
      \s*                                  # Strip remainging whitespace
$                                          # End of string
''', re.VERBOSE)