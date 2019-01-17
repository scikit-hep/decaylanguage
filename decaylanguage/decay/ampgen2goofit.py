#!/usr/bin/env python
# coding: utf-8

'''
This is a function that takes a filename and either prints out or returns
a string output with the converted set of decay chains and variables.
'''

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import datetime
from functools import partial

from plumbum import colors
from six import StringIO

from decaylanguage.decay.goofit import GooFitChain
from decaylanguage.decay.goofit import SF_4Body
from decaylanguage.particle import SpinType


def ampgen2goofit(filename, ret_output=False):
    if ret_output:
        output = StringIO()
        printer = partial(print, file=output)
    else:
        printer = print

    lines, all_states = GooFitChain.read_ampgen(str(filename))

    printer(r'/* Autogenerated file by AmpGen2GooFit')
    printer('Generated on ', datetime.datetime.now())

    printer('\n')
    for seen_factor in {p.spindetails() for p in lines}:
        my_lines = [p for p in lines if p.spindetails() == seen_factor]
        printer(colors.bold | seen_factor, ":", *my_lines[0].spinfactors)
        for line in my_lines:
            printer(' ', colors.blue | str(line))

    printer('\n')
    for spintype in SpinType:
        ps = [format(str(p), '11')
              for p in sorted(GooFitChain.all_particles) if p.spin_type == spintype]
        printer("{spintype.name:>12}:".format(spintype=spintype), *ps)

    printer('\n')
    for n, line in enumerate(lines):
        printer('{n:2} {line!s:<70} spinfactors: {lensf}  L: {line.L} [{Lr[0]}-{Lr[1]}]'
                .format(n=n, line=line, lensf=len(line.spinfactors), Lr=line.L_range()))

    # We can make the GooFit Intro code:

    printer(colors.bold & colors.green | '\n\nAll discovered spin configurations:')

    for line in sorted({line.spindetails() for line in lines}):
        printer(colors.green | line)

    printer(colors.bold & colors.blue | '\n\nAll known spin configurations:')

    # TODO: 4 body only
    for e in SF_4Body:
        printer(colors.blue | e.name)

    printer('\n*/\n\n    // Intro')
    printer(GooFitChain.make_intro(all_states))

    printer('\n\n    // Parameters')
    printer(GooFitChain.make_pars())

    # And the lines can be turned into code, as well:

    printer('\n\n    // Lines')
    for n, line in enumerate(lines):
        printer('    // Line', n)
        printer(line.to_goofit(all_states[1:]), end='\n\n\n')

    if(ret_output):
        return output.getvalue()
