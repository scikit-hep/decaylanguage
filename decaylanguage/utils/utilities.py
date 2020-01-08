# Copyright (c) 2018-2020, Eduardo Rodrigues and Henry Schreiner.
#
# Distributed under the 3-clause BSD license, see accompanying file LICENSE
# or https://github.com/scikit-hep/decaylanguage for details.

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function


def iter_flatten(iterable):
    '''
    Flatten nested tuples and lists
    '''
    for e in iterable:
        if isinstance(e, (list, tuple)):
            for f in iter_flatten(e):
                yield f
        else:
            yield e


def split(x):
    '''
    Break up a comma separated list, but respect curly brackets.

    For example:
    this, that { that { this, that } }
    would only break on the first comma, since the second is in a {} list
    '''

    c = 0
    i = 0
    out = []
    while len(x) > 0:
        if i + 1 == len(x):
            out.append(x[:i + 1])
            return out
        elif (x[i] == ',' and c == 0):
            out.append(x[:i])
            x = x[i + 1:]
            i = -1
        elif x[i] == '{':
            c += 1
        elif x[i] == '}':
            c -= 1
        i += 1


def filter_lines(matcher, input):
    '''
    Filter out lines into new variable if they match a regular expression
    '''
    output = [matcher.match(l).groupdict() for l in input if matcher.match(l) is not None]
    input = [l for l in input if matcher.match(l) is None]
    return output, input
