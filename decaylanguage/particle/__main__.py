from __future__ import absolute_import
from __future__ import print_function

from .particle import Particle

from plumbum import cli


class DecayLanguageParticle(cli.Application):
    
    def main(self, *values):
        print()
        for value in values:
            if value.isnumeric():
                particle = Particle.from_pdgid(int(value))
            else:
                particle = Particle.from_string(value)

            print(particle.describe())
            print()
        

DecayLanguageParticle.run()