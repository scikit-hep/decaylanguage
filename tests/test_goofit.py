from decaylanguage.decay.goofit import GooFitChain
from decaylanguage.particle import Particle


def test_simple():
    lines, all_states = GooFitChain.read_AmpGen(text='''

    # This is a test (should not affect output)

    EventType D0 K- pi+ pi+ pi-

    D0[D]{K*(892)bar0{K-,pi+},rho(770)0{pi+,pi-}} 2 1         0          2 0         0
    ''')

    assert Particle.from_pdgid(421) == all_states[0]  # D0
    assert Particle.from_pdgid(-321) == all_states[1]  # K-
    assert Particle.from_pdgid(211) == all_states[2]  # pi+
    assert Particle.from_pdgid(211) == all_states[3]  # pi+
    assert Particle.from_pdgid(-211) == all_states[4]  # pi-
